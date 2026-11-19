"""Классификация PR и перенос только разрешённых исходников в доверенную сборку."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess

from lab import ROOT, challenge_by_id, require, read_json, main_guard

JAVA_PATH = re.compile(r"(?:[A-Za-z_][A-Za-z0-9_]*/)*[A-Za-z_][A-Za-z0-9_]*\.java\Z")


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=root, timeout=30)


def changes(root: Path, base: str, head: str) -> list[tuple[str, str, str]]:
    ancestor = git(root, "merge-base", base, head).decode().strip()
    records = git(root, "diff", "--raw", "--no-renames", "-z", ancestor, head).split(b"\0")
    result = []
    for i in range(0, len(records) - 1, 2):
        header = records[i].decode("ascii").split()
        require(len(header) == 5, "Unexpected git diff record")
        path = records[i + 1].decode("utf-8", errors="strict")
        require(header[4] in {"A", "M", "D"}, "Unsupported change type")
        require(header[1] in {"100644", "000000"}, "Symlinks/executable files/submodules are forbidden")
        result.append((path, header[4], header[1]))
    require(0 < len(result) <= 200, "Empty or oversized PR")
    return result


def classify(root: Path, base: str, head: str, title: str, same_repository: bool) -> dict:
    changed = changes(root, base, head)
    match = re.match(r"^\[submission (SIL-[0-9]{3,5})\](?:\s|$)", title)
    if match:
        challenge_id = match[1]
        module, _ = challenge_by_id(root, challenge_id)
        prefix = module.relative_to(root).as_posix() + "/src/main/java/"
        for path, _, _ in changed:
            require(path.startswith(prefix) and JAVA_PATH.fullmatch(path[len(prefix):]) is not None,
                    f"Submission may change only {prefix}**/*.java; forbidden: {path}")
        return {"mode": "submission", "id": challenge_id, "module": module.relative_to(root).as_posix()}
    if title.startswith("[documentation]"):
        for path, _, _ in changed:
            require(re.fullmatch(r"(?:docs/[A-Za-z0-9_./-]+|README|CONTRIBUTING|CODE_OF_CONDUCT|SECURITY)\.md", path) is not None
                    and ".." not in Path(path).parts, f"Documentation PR changes forbidden path: {path}")
        return {"mode": "editorial", "id": "", "module": ""}
    require(same_repository and (title.startswith("[challenge-publication]") or title.startswith("[bug]")),
            "Use [submission SIL-NNN], [documentation], or a trusted in-repository [challenge-publication]/[bug] PR")
    return {"mode": "editorial", "id": "", "module": ""}


def materialize_submission(root: Path, base: str, head: str, policy: dict, destination: Path) -> None:
    require(policy["mode"] == "submission", "Not a submission")
    require(not destination.exists() and not destination.is_relative_to(root), "Output must be a NEW directory outside checkout")
    shutil.copytree(root, destination, ignore=shutil.ignore_patterns(".git", "target", "__pycache__", ".local", ".private"))
    size = 0
    for path, status, _ in changes(root, base, head):
        target = destination / path
        if status == "D":
            if target.exists():
                target.unlink()
            continue
        data = git(root, "show", f"{head}:{path}")
        size += len(data)
        require(len(data) <= 100_000 and size <= 2_000_000, "Oversized Java sources")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    # Both revisions are validated: no option injection or Git revision expressions from PR input.
    require(re.fullmatch(r"[a-f0-9]{40}", args.base) is not None, "Invalid base SHA")
    require(re.fullmatch(r"[a-f0-9]{40}", args.head) is not None, "Invalid head SHA")
    event = read_json(args.event)
    pr = event["pull_request"]
    policy = classify(ROOT, args.base, args.head, pr["title"], pr["head"]["repo"]["full_name"] == pr["base"]["repo"]["full_name"])
    if args.output and policy["mode"] == "submission":
        materialize_submission(ROOT, args.base, args.head, policy, args.output.resolve())
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            for key, value in policy.items():
                output.write(f"{key}={value}\n")
    print(f"OK PR policy: {policy['mode']} {policy['id']}")


if __name__ == "__main__":
    main_guard(main)
