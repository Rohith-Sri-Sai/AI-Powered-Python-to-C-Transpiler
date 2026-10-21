"""Repair-loop integration tests replace only the remote generation call."""
import ast
import shutil

import pytest

pytestmark = pytest.mark.skipif(shutil.which("g++") is None, reason="g++ is required")


def test_loop_repairs_output_mismatch_and_includes_previous_candidate(tmp_path, monkeypatch):
    from optimizer import feedback_loop

    python_source = ('def square(n):\n    return n*n\n'
                     'if __name__ == "__main__":\n    print(square(3))\n')
    python_file = tmp_path / "square.py"
    python_file.write_text(python_source, encoding="utf-8")
    wrong = '#include <iostream>\nint main(){std::cout << -1 << "\\n";}'
    correct = ('#include <iostream>\nlong long square(long long n){return n*n;}\n'
               'int main(){std::cout << square(3) << "\\n";}')
    attempts = []

    def generator(ast_data, feedback, model, *, previous_cpp=""):
        attempts.append((feedback, previous_cpp))
        return wrong if len(attempts) == 1 else correct

    monkeypatch.setattr(feedback_loop, "generate_cpp", generator)
    success = feedback_loop.autonomous_compilation_loop(
        ast.dump(ast.parse(python_source)), tmp_path / "candidate.cpp",
        tmp_path / "candidate.exe", "groq", max_retries=2,
        python_file_path=python_file,
    )
    assert success
    assert len(attempts) == 2
    assert "mismatch" in attempts[1][0]
    assert attempts[1][1] == wrong


def test_main_passes_reference_source_to_validation(tmp_path, monkeypatch):
    import main

    source = tmp_path / "input.py"
    source.write_text('print(42)\n', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    seen = []

    def loop(ast_data, cpp, binary, model, **kwargs):
        seen.append(kwargs.get("python_file_path"))
        return True

    monkeypatch.setattr(main, "autonomous_compilation_loop", loop)
    monkeypatch.setattr(main, "run_benchmark", lambda *args, **kwargs: 1.5)
    speedup = main.run_pipeline(str(source), "groq")
    assert seen == [source.resolve()]
    assert speedup == 1.5
