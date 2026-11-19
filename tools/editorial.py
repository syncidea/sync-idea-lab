"""Editorial: каталог + Python-тесты инструментов + компиляция всех starter и JUnit-тестов."""
import argparse
from pathlib import Path
import subprocess
import sys

from lab import ROOT, require, run_maven, main_guard
from validate_catalog import validate_catalog
from audit_publication import audit_git


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    validate_catalog(root)
    if (root / ".git").exists():
        indexed, historical = audit_git(root)
        print(f"Git audit: {indexed} indexed files, {historical} historical blobs", flush=True)
    result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tools/tests", "-v"], cwd=root, check=False, timeout=120)
    require(result.returncode == 0, "Tool tests failed")
    require(run_maven(root, ["clean", "test-compile"]).returncode == 0, "Starter/test compilation failed")
    print("OK editorial: metadata, tool tests, starter + test compilation (behavior tests NOT executed)")


if __name__ == "__main__":
    main_guard(main)
