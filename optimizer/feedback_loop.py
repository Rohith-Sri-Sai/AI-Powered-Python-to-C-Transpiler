"""Repair candidates on compiler, runtime and differential-validation failures."""
from pathlib import Path

from translator.cpp_generator import generate_cpp
from optimizer.compile import compile_and_test
from optimizer.validation import validate_candidate


def autonomous_compilation_loop(ast_data, cpp_output_path, exe_output_path, model_choice,
                                max_retries=3, *, python_file_path=None,
                                timeout=60, function_cases=None):
    """Return True only after a candidate builds and passes its validation cases.

    python_file_path is required: an AST dump alone is not an executable reference.
    Existing positional arguments remain unchanged; callers supply the source path
    as a keyword. This function runs trusted local code, not sandboxed submissions.
    """
    if python_file_path is None:
        raise ValueError("python_file_path is required for correctness validation.")
    if type(max_retries) is not int or max_retries < 1 or timeout <= 0:
        raise ValueError("max_retries must be positive and timeout must be positive.")
    source = Path(python_file_path).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    cpp_path = Path(cpp_output_path).resolve()
    executable = Path(exe_output_path).resolve()
    cpp_path.parent.mkdir(parents=True, exist_ok=True)
    executable.parent.mkdir(parents=True, exist_ok=True)
    executable.unlink(missing_ok=True)
    error_log = "None"
    previous_cpp = ""
    for attempt in range(max_retries):
        print(f"   [Loop {attempt + 1}/{max_retries}] Generating C++ using {model_choice.upper()}...")
        try:
            cpp_code = generate_cpp(ast_data, error_log, model_choice, previous_cpp=previous_cpp)
        except Exception as exc:
            error_log = f"Generation failed ({type(exc).__name__}): {exc}"
            print(f"   {error_log[:500]}")
            continue
        previous_cpp = cpp_code
        cpp_path.write_text(cpp_code, encoding="utf-8")
        success, message = compile_and_test(cpp_path, executable, timeout=timeout)
        if success:
            result = validate_candidate(source, cpp_path, executable, timeout=timeout,
                                        function_cases=function_cases)
            if result.success:
                print(f"   Validation passed ({result.coverage}, {result.case_count} cases).")
                print(f"   {result.feedback}")
                return True
            message = result.feedback
        error_log = message
        print(f"   Candidate rejected: {message[:1000]}")
    executable.unlink(missing_ok=True)
    print("   Reached maximum attempts without a validated candidate.")
    return False
