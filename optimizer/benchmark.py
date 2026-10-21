<<<<<<< HEAD
=======
"""Repeated, output-checked benchmarks with append-only CSV results."""
>>>>>>> d65842a (new example and tests)
import csv
import math
import os
<<<<<<< HEAD
import statistics
import subprocess
import sys
import time
from pathlib import Path


def run_command(command, timeout=60):
    """Execute a program and measure wall-clock execution time."""

    start = time.perf_counter()

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Execution timed out after {timeout}s: {command}"
        ) from exc

    elapsed = time.perf_counter() - start

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {command}\n"
            f"Exit code: {result.returncode}\n"
            f"Error: {result.stderr}"
        )

    return elapsed, result.stdout.strip()


def run_benchmark(
    executable_path,
    python_file_path,
    warmups=2,
    repetitions=10,
):
    """Benchmark Python against generated C++."""

    python_file_path = str(Path(python_file_path).resolve())
    executable_path = str(Path(executable_path).resolve())

    python_command = [sys.executable, python_file_path]
    cpp_command = [executable_path]

    algo_name = Path(python_file_path).name

    print(f"\n{'=' * 55}")
    print(f"BENCHMARKING: {algo_name}")
    print(f"{'=' * 55}")

    py_median = None
    cpp_median = None
    speedup = 0.0
    status = "Py:Error|C++:Error"

    try:
        # Step 1: Validate both implementations
        print("\n[1/4] Checking output correctness...")

        _, python_output = run_command(python_command)
        _, cpp_output = run_command(cpp_command)

        if python_output != cpp_output:
            status = "Py:Success|C++:OutputMismatch"

            print("Output mismatch detected!")
            print(f"Python output: {python_output}")
            print(f"C++ output:    {cpp_output}")

            raise ValueError(
                "Python and C++ outputs are different."
            )

        print("Outputs match.")

        # Step 2: Warm-up runs
        print(f"\n[2/4] Performing {warmups} warm-up runs...")

        for _ in range(warmups):
            run_command(python_command)
            run_command(cpp_command)

        # Step 3: Benchmark both implementations
        print(
            f"\n[3/4] Running {repetitions} benchmark repetitions..."
        )

        python_times = []
        cpp_times = []

        for i in range(repetitions):
            py_time, py_output = run_command(python_command)
            cpp_time, cpp_output = run_command(cpp_command)

            if py_output != cpp_output:
                status = "Py:Success|C++:OutputMismatch"
                raise ValueError(
                    f"Output mismatch during repetition {i + 1}"
                )

            python_times.append(py_time)
            cpp_times.append(cpp_time)

        # Step 4: Calculate median-based speedup
        py_median = statistics.median(python_times)
        cpp_median = statistics.median(cpp_times)

        if cpp_median <= 0:
            raise ValueError("Invalid C++ execution time.")

        speedup = py_median / cpp_median
        status = "Py:Success|C++:Success"

        print("\n[4/4] Benchmark completed successfully.")

        print(f"\n{'=' * 55}")
        print("BENCHMARK RESULTS")
        print(f"{'=' * 55}")

        print(f"File Name:      {algo_name}")
        print(f"Python Time:    {py_median:.6f}s")
        print(f"C++ Time:       {cpp_median:.6f}s")
        print(f"Speedup:        {speedup:.2f}x")
        print(f"Status:         {status}")
        print(f"Repetitions:    {repetitions}")

        if speedup > 1:
            print("Result: C++ is faster than Python.")
        elif speedup < 1:
            print("Result: Python is faster than C++.")
        else:
            print("Result: Equal execution speed.")

    except (RuntimeError, ValueError) as exc:
        print(f"\nBenchmark failed: {exc}")

    # Save results using the original CSV schema
    os.makedirs("results", exist_ok=True)

    csv_path = "results/benchmarks.csv"

    expected_header = [
        "File Name",
        "Python Time (s)",
        "C++ Time (s)",
        "Speedup",
        "Status",
    ]

    # Prevent appending incompatible rows to an old CSV
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        with open(csv_path, "r", newline="") as file:
            reader = csv.reader(file)
            existing_header = next(reader, [])

        if existing_header != expected_header:
            raise ValueError(
                "Existing CSV has a different header. "
                "Rename or archive results/benchmarks.csv "
                "before running again."
            )

    write_header = (
        not os.path.exists(csv_path)
        or os.path.getsize(csv_path) == 0
    )

    with open(csv_path, "a", newline="") as file:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL)

        if write_header:
            writer.writerow(expected_header)

        writer.writerow([
            algo_name,
            f"{py_median:.6f}" if py_median is not None else "",
            f"{cpp_median:.6f}" if cpp_median is not None else "",
            f"{speedup:.2f}x" if status == "Py:Success|C++:Success" else "",
            status,
        ])

    print(f"\nResults saved to {csv_path}")

    return speedup
=======
from pathlib import Path
from statistics import median
import subprocess
import sys
import time


HEADER = ["File Name", "Python Time (s)", "C++ Time (s)", "Speedup", "Status"]


def run_benchmark(executable_path, python_file_path, warmups=2, repetitions=10,
                  timeout=60, csv_path=None):
    """Return median Python/native speedup, or zero for failed or unequal runs.

    Compare stdout bytes on every warmup and sample; exclude warmups from timing.
    Stop after the first failed pair, retaining independent execution statuses.
    Reject incompatible CSV headers before executing either program.
    """
    for name, value, minimum in (("warmups", warmups, 0), ("repetitions", repetitions, 1)):
        if type(value) is not int or value < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a finite positive number")
    destination = Path(csv_path) if csv_path is not None else Path("results/benchmarks.csv")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Validate the existing schema and append access before executing user code.
    with destination.open("a+", newline="", encoding="utf-8") as stream:
        stream.seek(0)
        header = next(csv.reader(stream, skipinitialspace=True), None)
        if header is not None and header not in (HEADER, ["Algorithm", *HEADER[1:]]):
            raise ValueError(f"Incompatible benchmark CSV header: {header!r}")
        if header is None:
            csv.writer(stream).writerow(HEADER)
        else:
            with destination.open("rb") as raw:
                raw.seek(-1, os.SEEK_END)
                needs_newline = raw.read(1) not in (b"\n", b"\r")
            if needs_newline:
                stream.write("\n")
    commands = [[sys.executable, os.fspath(python_file_path)], [os.fspath(executable_path)]]
    statuses = ["Success", "Success"]
    samples = [[], []]
    for iteration in range(warmups + repetitions):
        outputs = [None, None]
        for index, command in enumerate(commands):
            started = time.perf_counter()
            try:
                process = subprocess.run(command, capture_output=True, timeout=timeout)
                elapsed = time.perf_counter() - started
                statuses[index] = "Success" if process.returncode == 0 else "Error"
                outputs[index] = process.stdout
                if iteration >= warmups:
                    samples[index].append(elapsed)
            except subprocess.TimeoutExpired:
                statuses[index] = "Timeout"
            except FileNotFoundError:
                statuses[index] = "Missing executable"
            except OSError:
                statuses[index] = "Execution error"
        if statuses == ["Success", "Success"] and outputs[0] != outputs[1]:
            statuses[1] = "Output mismatch"
        if statuses != ["Success", "Success"]:
            break
    timings = [median(sample) if sample else 0.0 for sample in samples]
    speedup = timings[0] / timings[1] if statuses == ["Success", "Success"] and timings[1] > 0 else 0.0
    with destination.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow([os.path.basename(python_file_path),
                         *(f"{value:.6f}" for value in timings),
                         f"{speedup:.2f}x" if speedup else "",
                         f"Py:{statuses[0]}|C++:{statuses[1]}"])
    print(f"Benchmark: Py:{statuses[0]}|C++:{statuses[1]}; speedup={speedup:.2f}x")
    return speedup
>>>>>>> d65842a (new example and tests)
