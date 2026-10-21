"""Build generated candidates; validation builds are separate from timed builds."""
from pathlib import Path
import subprocess


def compile_and_test(cpp_file_path, output_exe_path, *, checked=False, timeout=60):
    """Return (success, diagnostics), not a claim of semantic correctness.

    Checked builds trap signed add/subtract/multiply overflow and enable standard
    library assertions. They are not a full sanitizer or arbitrary-precision math.
    """
    if timeout <= 0:
        raise ValueError("Compilation timeout must be positive.")
    output = Path(output_exe_path).resolve()
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.unlink(missing_ok=True)
        flags = ["-O1", "-ftrapv", "-D_GLIBCXX_ASSERTIONS"] if checked else ["-O3"]
        command = ["g++", "-std=c++17", *flags,
                   str(Path(cpp_file_path).resolve()), "-o", str(output)]
        process = subprocess.run(command, capture_output=True, text=True,
                                 timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        output.unlink(missing_ok=True)
        return False, f"Compilation timed out after {timeout}s."
    except OSError as exc:
        return False, f"Compiler/build path error: {exc}"
    if process.returncode != 0:
        output.unlink(missing_ok=True)
        return False, process.stderr or f"Compiler exited with code {process.returncode}."
    return True, "Compilation successful."
