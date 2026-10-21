"""Regression tests for benchmark correctness, sampling, and CSV safety."""
import csv
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

SPEC = importlib.util.spec_from_file_location(
    "benchmark_under_test", Path(__file__).parents[1] / "optimizer" / "benchmark.py"
)
benchmark = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark)


@pytest.fixture
def programs(tmp_path):
    """Build tiny real native programs without touching tracked results."""
    def create(python_body="print('same')", cpp_body='std::cout << "same\\n";'):
        script = tmp_path / "program.py"
        script.write_text(python_body, encoding="utf-8")
        source = tmp_path / "program.cpp"
        source.write_text('#include <iostream>\n#include <fstream>\nint main(){' + cpp_body + '}\n', encoding="utf-8")
        executable = tmp_path / "program.exe"
        subprocess.run(["g++", str(source), "-o", str(executable)], check=True, capture_output=True)
        return executable, script
    return create


def test_sampling_uses_current_interpreter_and_medians(programs, tmp_path, monkeypatch):
    executable, script = programs()
    calls = []
    real_run = subprocess.run

    def record(command, **kwargs):
        calls.append((command, kwargs))
        return real_run(command, **kwargs)

    # Two warmups then three samples; outliers must not dominate medians.
    durations = [100, 50, 80, 40, 4, 1, 6, 2, 1000, 100]
    ticks = iter(value for duration in durations for value in (0, duration))
    monkeypatch.setattr(benchmark.subprocess, "run", record)
    monkeypatch.setattr(benchmark.time, "perf_counter", lambda: next(ticks))
    csv_path = tmp_path / "nested" / "custom.csv"
    assert benchmark.run_benchmark(executable, script, warmups=2, repetitions=3,
                                   timeout=7, csv_path=csv_path) == 3
    assert len(calls) == 10
    assert all(command[0] == sys.executable for command, _ in calls[::2])
    assert all(kwargs["timeout"] == 7 for _, kwargs in calls)
    assert rows(csv_path)[-1][1:4] == ["6.000000", "2.000000", "3.00x"]


@pytest.mark.parametrize("option,value", [
    ("warmups", -1), ("warmups", 1.5), ("warmups", True),
    ("repetitions", 0), ("repetitions", -1), ("repetitions", 1.5),
    ("repetitions", True), ("timeout", 0), ("timeout", -1),
    ("timeout", float("nan")), ("timeout", float("inf")),
    ("timeout", "60"), ("timeout", True),
])
def test_invalid_arguments_rejected_before_execution(tmp_path, option, value, monkeypatch):
    calls = []
    real_run = subprocess.run

    def record(*args, **kwargs):
        calls.append(args)
        return real_run(*args, **kwargs)

    monkeypatch.setattr(benchmark.subprocess, "run", record)
    marker = tmp_path / "executed"
    script = tmp_path / "side_effect.py"
    script.write_text(f"from pathlib import Path; Path({str(marker)!r}).touch()")
    with pytest.raises(ValueError):
        benchmark.run_benchmark(tmp_path / "missing.exe", script,
                                csv_path=tmp_path / "out.csv", **{option: value})
    assert not calls
    assert not marker.exists()
    assert not (tmp_path / "out.csv").exists()


@pytest.mark.parametrize("header", ["wrong,header\n", '"File Name","Speedup"\n'])
def test_incompatible_csv_rejected_before_subprocess(tmp_path, monkeypatch, header):
    path = tmp_path / "out.csv"
    path.write_text(header + "historical,row\n", encoding="utf-8")
    original = path.read_bytes()
    calls = []
    real_run = subprocess.run

    def record(*args, **kwargs):
        calls.append(args)
        return real_run(*args, **kwargs)

    monkeypatch.setattr(benchmark.subprocess, "run", record)
    with pytest.raises(ValueError, match="header"):
        benchmark.run_benchmark(tmp_path / "missing.exe", tmp_path / "missing.py",
                                warmups=0, repetitions=1, csv_path=path)
    assert not calls
    assert path.read_bytes() == original


@pytest.mark.parametrize("header", [
    '',
    '"File Name","Python Time (s)", "C++ Time (s)", "Speedup", "Status"\n',
    'Algorithm,Python Time (s),C++ Time (s),Speedup,Status\n',
])
def test_csv_preserves_supported_history_or_initializes_empty(programs, tmp_path, header):
    executable, script = programs()
    path = tmp_path / "out.csv"
    historical = "old.py,1,2,0.50x,Py:Success|C++:Success\n" if header else ""
    path.write_text(header + historical, encoding="utf-8", newline="")
    original = path.read_bytes()
    assert benchmark.run_benchmark(executable, script, warmups=0, repetitions=1,
                                   csv_path=path) > 0
    assert path.read_bytes().startswith(original)
    parsed = rows(path)
    assert parsed[0][0] == ("Algorithm" if header.startswith("Algorithm") else "File Name")
    assert parsed[-1][0] == "program.py"
    assert len(parsed[-1]) == 5
    assert len(parsed) == (3 if header else 2)


@pytest.mark.parametrize("failure,expected", [
    ("missing", "Py:Success|C++:Missing executable"),
    ("python", "Py:Error|C++:Success"),
    ("native", "Py:Success|C++:Error"),
    ("both", "Py:Error|C++:Error"),
    ("python_timeout", "Py:Timeout|C++:Success"),
    ("native_timeout", "Py:Success|C++:Timeout"),
    ("both_timeout", "Py:Timeout|C++:Timeout"),
])
def test_execution_failures_are_independent_and_logged(programs, tmp_path, monkeypatch,
                                                       failure, expected):
    executable, script = programs(
        python_body="raise SystemExit(3)" if failure in ("python", "both") else "print('same')",
        cpp_body="return 4;" if failure in ("native", "both") else 'std::cout << "same\\n";',
    )
    if failure == "missing":
        executable.unlink()
    if "timeout" in failure:
        real_run = subprocess.run

        def timeout_one(command, **kwargs):
            is_python = command[0] == sys.executable
            if failure == "both_timeout" or is_python == (failure == "python_timeout"):
                raise subprocess.TimeoutExpired(command, kwargs["timeout"])
            return real_run(command, **kwargs)

        monkeypatch.setattr(benchmark.subprocess, "run", timeout_one)
    path = tmp_path / "out.csv"
    assert benchmark.run_benchmark(executable, script, warmups=0, repetitions=2,
                                   csv_path=path) == 0
    result = rows(path)[-1]
    assert result[3] == ""
    assert result[4] == expected


def test_unlaunchable_native_program_is_logged(programs, tmp_path):
    executable, script = programs()
    executable.write_bytes(b"not an executable")
    path = tmp_path / "out.csv"
    assert benchmark.run_benchmark(executable, script, warmups=0, repetitions=1,
                                   csv_path=path) == 0
    assert rows(path)[-1][3:] == ["", "Py:Success|C++:Execution error"]


def test_append_preserves_history_without_final_newline(programs, tmp_path):
    executable, script = programs()
    path = tmp_path / "out.csv"
    original = (','.join(benchmark.HEADER) + '\nold.py,1,2,0.50x,Py:Success|C++:Success').encode()
    path.write_bytes(original)
    benchmark.run_benchmark(executable, script, warmups=0, repetitions=1, csv_path=path)
    assert path.read_bytes().startswith(original)
    assert len(rows(path)) == 3
    assert rows(path)[1] == ["old.py", "1", "2", "0.50x", "Py:Success|C++:Success"]


@pytest.mark.parametrize("mismatch_at", [2, 3, 12])
def test_default_checks_warmups_and_every_measured_output(programs, tmp_path, monkeypatch,
                                                          mismatch_at):
    executable, script = programs(cpp_body=(
        'int n=0; {std::ifstream in("counter"); in >> n;} '
        '++n; {std::ofstream out("counter"); out << n;} '
        f'std::cout << (n == {mismatch_at} ? "different\\n" : "same\\n");'
    ))
    monkeypatch.chdir(tmp_path)
    assert benchmark.run_benchmark(executable, script) == 0
    assert int((tmp_path / "counter").read_text()) == mismatch_at
    assert rows(tmp_path / "results" / "benchmarks.csv")[-1][3:] == [
        "", "Py:Success|C++:Output mismatch"
    ]


def test_successful_default_runs_two_warmups_and_ten_samples(programs, tmp_path, monkeypatch):
    executable, script = programs()
    real_run = subprocess.run
    calls = []

    def record(command, **kwargs):
        calls.append((command, kwargs))
        return real_run(command, **kwargs)

    monkeypatch.setattr(benchmark.subprocess, "run", record)
    monkeypatch.chdir(tmp_path)
    assert benchmark.run_benchmark(executable, script) > 0
    assert len(calls) == 24
    assert all(kwargs["timeout"] == 60 for _, kwargs in calls)
    assert rows(tmp_path / "results" / "benchmarks.csv")[-1][4] == "Py:Success|C++:Success"


def rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.reader(stream, skipinitialspace=True))


def test_default_rejects_exact_output_mismatch(programs, tmp_path, monkeypatch):
    executable, script = programs(cpp_body='std::cout << "same \\n";')
    monkeypatch.chdir(tmp_path)
    assert benchmark.run_benchmark(executable, script) == 0
    result = rows(tmp_path / "results" / "benchmarks.csv")[-1]
    assert result[3] == ""
    assert result[4] == "Py:Success|C++:Output mismatch"
