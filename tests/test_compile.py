"""Real-compiler regression tests; no API credentials are needed."""
from pathlib import Path
import shutil
import subprocess

import pytest

from optimizer.compile import compile_and_test


@pytest.mark.skipif(shutil.which("g++") is None, reason="g++ is required")
def test_checked_build_traps_signed_integer_overflow(tmp_path):
    source = tmp_path / "overflow.cpp"
    source.write_text(
        '#include <iostream>\n'
        'int main() { volatile int n = 2147483647; '
        'int sum = n + 1; std::cout << sum << "\\n"; }\n',
        encoding="utf-8",
    )
    binary = tmp_path / "overflow.exe"
    success, message = compile_and_test(source, binary, checked=True)
    assert success, message
    process = subprocess.run([str(binary)], capture_output=True, timeout=10)
    assert process.returncode != 0, "Validation must reject signed overflow"
