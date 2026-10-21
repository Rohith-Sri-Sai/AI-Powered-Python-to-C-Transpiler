"""Differential validation for generated local programs (not a sandbox)."""
import ast
from dataclasses import dataclass
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile

from optimizer.compile import compile_and_test


@dataclass(frozen=True)
class ValidationResult:
    success: bool
    feedback: str
    case_count: int = 0
    coverage: str = "baseline-only"


def _run(command, timeout):
    try:
        process = subprocess.run(command, capture_output=True, text=True,
                                 timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, "", str(exc)
    if process.returncode != 0:
        return False, process.stdout, (
            f"Exit code {process.returncode}. stderr: {process.stderr[:4000]}"
        )
    return True, process.stdout, ""


def _discover_function_cases(python_file):
    """Probe single-integer functions actually called with integers in the source.

    This covers the existing prime-counting/BFS examples without rewriting their
    inputs. More complex interfaces need explicit cases, not invented arguments.
    """
    tree = ast.parse(python_file.read_text(encoding="utf-8-sig"))
    functions = {
        node.name for node in tree.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
        and node.name != "main"
        and len(node.args.posonlyargs + node.args.args) == 1
        and not node.args.vararg and not node.args.kwarg and not node.args.kwonlyargs
        and not any(isinstance(child, (ast.Yield, ast.YieldFrom)) for child in ast.walk(node))
    }
    called = {
        node.func.id for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id in functions and len(node.args) == 1 and not node.keywords
        and isinstance(node.args[0], ast.Constant) and type(node.args[0].value) is int
    }
    values = [0, 1, 2, 3, 7, 31, *random.Random(0).sample(range(4, 65), 3)]
    return {name: values for name in sorted(called)}


def _validate_functions(python_file, cpp_file, folder, timeout, function_cases):
    explicit = function_cases is not None
    cases = function_cases if explicit else _discover_function_cases(python_file)
    if not cases:
        return ValidationResult(True, "No integer function cases available; baseline-only coverage.", 1)
    for name, values in cases.items():
        if not isinstance(name, str) or not name.isascii() or not name.isidentifier():
            return ValidationResult(False, "Function test names must be ASCII identifiers.")
        if not values or any(type(value) is not int or not -(2**63) <= value < 2**63 for value in values):
            return ValidationResult(False, f"{name}: cases must be nonempty signed 64-bit integers.")
    # The reference runs in a subprocess, never exec() inside the application.
    marker = "__TRANSPILE_VALIDATION__"
    driver = (
        "import runpy,json,io,contextlib\n"
        f"namespace=runpy.run_path({str(python_file)!r}, run_name='_transpiler_validation_')\n"
        f"cases=json.loads({json.dumps(cases)!r})\n"
        "records=[]\n"
        "for name, values in cases.items():\n"
        " for value in values:\n"
        "  stdout=io.StringIO()\n"
        "  try:\n"
        "   with contextlib.redirect_stdout(stdout):\n"
        "    result=namespace[name](value)\n"
        "   records.append([name,value,type(result) is int,result if type(result) is int else 'non-integer result',stdout.getvalue()])\n"
        "  except Exception as exc:\n"
        "   records.append([name,value,False,type(exc).__name__+': '+str(exc),stdout.getvalue()])\n"
        f"print('\\n{marker}'+json.dumps(records))\n"
    )
    success, output, error = _run([sys.executable, "-c", driver], timeout)
    if not success:
        return ValidationResult(False, f"Function reference failed: {error}")
    try:
        record_line = output.splitlines()[-1]
        if not record_line.startswith(marker):
            raise ValueError("Missing function reference marker prefix")
        records = json.loads(record_line[len(marker):])
    except (IndexError, ValueError) as exc:
        return ValidationResult(False, f"Cannot read function reference results: {exc}")
    valid = [record for record in records if record[2]]
    excluded = [record for record in records if not record[2]]
    if explicit and excluded:
        return ValidationResult(False, f"Explicit Python case failed: {excluded[0]!r}")
    if not valid:
        return ValidationResult(True, "No supported integer results; baseline-only coverage.", 1)
    # Rename only the candidate entry point; keep and call its real functions.
    # Quoted include paths are safe here because the filename is generated locally.
    harness = folder / "function_cases.cpp"
    source = '#include <iostream>\n#define main transpiler_original_main\n'
    source += f'#include "{cpp_file.as_posix()}"\n#undef main\nint main() {{\n'
    for record in valid:
        name, value = record[:2]
        literal = "(-9223372036854775807LL - 1)" if value == -(2**63) else f"{value}LL"
        source += f'std::cout << {name}({literal}) << "\\n";\n'
    source += 'return 0;\n}\n'
    harness.write_text(source, encoding="utf-8")
    expected_output = "".join(f"{record[4]}{record[3]}\n" for record in valid)
    expected_output = expected_output.replace("\r\n", "\n").replace("\r", "\n")
    labels = ", ".join(f"{record[0]}({record[1]})" for record in valid)
    for checked in (True, False):
        binary = folder / ("functions_checked.exe" if checked else "functions_optimized.exe")
        success, message = compile_and_test(harness, binary, checked=checked, timeout=timeout)
        if not success:
            return ValidationResult(False, f"Function-case build failed ({labels}): {message}")
        success, actual, error = _run([str(binary)], timeout)
        if not success:
            return ValidationResult(False, f"Function-case runtime failed ({labels}): {error}")
        if actual != expected_output:
            return ValidationResult(False, f"Function-case output mismatch ({labels}). "
                                    f"Expected: {expected_output[:4000]!r}; actual: {actual[:4000]!r}")
    return ValidationResult(True, f"Default output and {len(valid)} integer function cases match. "
                            f"Excluded reference-invalid/non-integer cases: {excluded!r}",
                            1 + len(valid), "baseline+integer-functions")


def validate_candidate(python_file_path, cpp_file_path, executable_path, *, timeout=60,
                       function_cases=None):
    """Check optimized and overflow-checked builds against Python stdout.

    Only trusted local source should be executed. Output equality is evidence for
    the tested input, not proof of equivalent Python semantics on all inputs.
    """
    if timeout <= 0:
        raise ValueError("Validation timeout must be positive.")
    python_file = Path(python_file_path).resolve()
    cpp_file = Path(cpp_file_path).resolve()
    executable = Path(executable_path).resolve()
    success, expected, error = _run([sys.executable, str(python_file)], timeout)
    if not success:
        return ValidationResult(False, f"Python reference failed: {error}")
    with tempfile.TemporaryDirectory(prefix="validation-", dir=cpp_file.parent) as folder:
        checked = Path(folder) / "checked.exe"
        success, message = compile_and_test(cpp_file, checked, checked=True, timeout=timeout)
        if not success:
            return ValidationResult(False, f"Checked build failed: {message}")
        for name, binary in [("checked", checked), ("optimized", executable)]:
            success, actual, error = _run([str(binary)], timeout)
            if not success:
                return ValidationResult(False, f"{name} runtime failed: {error}")
            if actual != expected:
                return ValidationResult(False, f"{name} output mismatch. "
                                        f"Expected: {expected[:4000]!r}; actual: {actual[:4000]!r}")
        return _validate_functions(python_file, cpp_file, Path(folder), timeout, function_cases)
