"""Differential checks use real Python processes and real C++ binaries."""
from pathlib import Path
import shutil

import pytest

from optimizer.compile import compile_and_test

pytestmark = pytest.mark.skipif(shutil.which("g++") is None, reason="g++ is required")


def build(tmp_path, python_source, cpp_source):
    python_file = tmp_path / "input.py"
    cpp_file = tmp_path / "candidate.cpp"
    executable = tmp_path / "candidate.exe"
    python_file.write_text(python_source, encoding="utf-8")
    cpp_file.write_text(cpp_source, encoding="utf-8")
    success, message = compile_and_test(cpp_file, executable)
    assert success, message
    return python_file, cpp_file, executable


def test_wrong_stdout_is_rejected(tmp_path):
    from optimizer.validation import validate_candidate

    paths = build(tmp_path, 'print(42)\n',
                  '#include <iostream>\nint main(){std::cout << -1 << "\\n";}')
    result = validate_candidate(*paths)
    assert not result.success
    assert "42" in result.feedback and "-1" in result.feedback


def test_matching_default_output_does_not_hide_constant_function(tmp_path):
    from optimizer.validation import validate_candidate

    paths = build(tmp_path,
                  'def square(n):\n    return n*n\n'
                  'if __name__ == "__main__":\n    print(square(3))\n',
                  '#include <iostream>\nint square(int n){return 9;}\n'
                  'int main(){std::cout << square(3) << "\\n";}')
    result = validate_candidate(*paths)
    assert not result.success, "A matching hard-coded default must not pass validation"
    assert "square" in result.feedback


def test_correct_function_passes_multiple_deterministic_inputs(tmp_path):
    from optimizer.validation import validate_candidate

    paths = build(tmp_path,
                  'def square(n):\n    return n*n\n'
                  'if __name__ == "__main__":\n    print(square(3))\n',
                  '#include <iostream>\nlong long square(long long n){return n*n;}\n'
                  'int main(){std::cout << square(3) << "\\n";}')
    result = validate_candidate(*paths)
    assert result.success, result.feedback
    assert result.coverage == "baseline+integer-functions"
    assert result.case_count >= 8


def test_printing_integer_function_preserves_stdout(tmp_path):
    from optimizer.validation import validate_candidate

    paths = build(tmp_path,
                  'def echo(n):\n    print(n)\n    return n\n'
                  'if __name__ == "__main__":\n    print(echo(3))\n',
                  '#include <iostream>\n'
                  'long long echo(long long n){std::cout << n << "\\n"; return n;}\n'
                  'int main(){std::cout << echo(3) << "\\n";}')
    result = validate_candidate(*paths)
    assert result.success, result.feedback
    assert result.coverage == "baseline+integer-functions"
    assert result.case_count == 10


def test_printing_validation_marker_is_accepted(tmp_path):
    from optimizer.validation import validate_candidate

    paths = build(tmp_path,
                  'def echo(n):\n    print("__TRANSPILE_VALIDATION__")\n    return n\n'
                  'if __name__ == "__main__":\n    print(echo(3))\n',
                  '#include <iostream>\n'
                  'long long echo(long long n){std::cout << "__TRANSPILE_VALIDATION__\\n"; return n;}\n'
                  'int main(){std::cout << echo(3) << "\\n";}')
    result = validate_candidate(*paths, function_cases={"echo": [3]})
    assert result.success, result.feedback
    assert result.coverage == "baseline+integer-functions"
    assert result.case_count == 2


def test_printing_carriage_return_is_accepted(tmp_path):
    from optimizer.validation import validate_candidate

    paths = build(tmp_path,
                  'def echo(n):\n    print("progress", end=chr(13))\n    return n\n'
                  'if __name__ == "__main__":\n    print(echo(3))\n',
                  '#include <iostream>\n'
                  'long long echo(long long n){std::cout << "progress\\r"; return n;}\n'
                  'int main(){std::cout << echo(3) << "\\n";}')
    result = validate_candidate(*paths, function_cases={"echo": [3]})
    assert result.success, result.feedback
    assert result.coverage == "baseline+integer-functions"
    assert result.case_count == 2


def test_explicit_large_input_rejects_overflow(tmp_path):
    from optimizer.validation import validate_candidate

    paths = build(tmp_path,
                  'def square(n):\n    return n*n\n'
                  'if __name__ == "__main__":\n    print(square(3))\n',
                  '#include <iostream>\nint square(int n){return n*n;}\n'
                  'int main(){std::cout << square(3) << "\\n";}')
    result = validate_candidate(*paths, function_cases={"square": [50000]})
    assert not result.success
    assert "square(50000)" in result.feedback
    # Depending on constant folding, the checked build may trap or emit the
    # wrong result; either outcome must reject the candidate.
    assert "runtime failed" in result.feedback or "output mismatch" in result.feedback


def test_missing_optimized_binary_does_not_pass(tmp_path):
    from optimizer.validation import validate_candidate

    paths = build(tmp_path, 'print(42)\n',
                  '#include <iostream>\nint main(){std::cout << 42 << "\\n";}')
    paths[2].unlink()
    result = validate_candidate(*paths)
    assert not result.success
    assert "optimized runtime failed" in result.feedback


def test_baseline_only_coverage_is_explicit(tmp_path):
    from optimizer.validation import validate_candidate

    paths = build(tmp_path, 'print(42)\n',
                  '#include <iostream>\nint main(){std::cout << 42 << "\\n";}')
    result = validate_candidate(*paths)
    assert result.success, result.feedback
    assert result.coverage == "baseline-only"
    assert "baseline-only" in result.feedback


def test_reference_failure_is_not_a_cpp_correctness_success(tmp_path):
    from optimizer.validation import validate_candidate

    paths = build(tmp_path, 'raise ValueError("bad reference")\n', 'int main(){return 0;}')
    result = validate_candidate(*paths)
    assert not result.success
    assert "Python reference failed" in result.feedback
