"""Прогон публичных поведенческих тестов одного задания (starter ожидаемо красный)."""
import argparse
from pathlib import Path

from lab import ROOT, challenge_by_id, require, run_maven, main_guard


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("challenge_id")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    path, _ = challenge_by_id(root, args.challenge_id)
    result = run_maven(root, ["-pl", path.relative_to(root).as_posix(), "clean", "test"])
    require(result.returncode == 0, "Behavior tests failed; inspect target/surefire-reports and implement the challenge")
    print(f"OK solution {args.challenge_id}")


if __name__ == "__main__":
    main_guard(main)
