"""Проверяет доверенную реализацию из внешней папки во временной копии. Код не логируется."""
import argparse
from pathlib import Path
import shutil
import tempfile
import re
import xml.etree.ElementTree as ET

from lab import ROOT, challenge_by_id, require, run_maven, write_json, main_guard


def verify(root: Path, challenge_id: str, source: Path) -> dict:
    require(source.is_dir() and not source.is_relative_to(root), "Implementation must be in a directory OUTSIDE the public repository")
    module, meta = challenge_by_id(root, challenge_id)
    sources = list(source.rglob("*"))
    require(sources and all(not p.is_symlink() and (p.is_dir() or p.suffix == ".java") for p in sources), "Only regular .java sources allowed")
    require((source / Path(meta["entrypoint"]).relative_to("src/main/java")).is_file(), "Missing entrypoint in external source tree")
    with tempfile.TemporaryDirectory(prefix="sync-idea-verify-") as tmp:
        isolated = Path(tmp)
        for name in ("pom.xml", "mvnw", "mvnw.cmd", ".mvn"):
            src, dest = root / name, isolated / name
            shutil.copytree(src, dest) if src.is_dir() else shutil.copy2(src, dest)
        # Keep only the selected reactor module; other challenges are independent.
        pom = isolated / "pom.xml"
        text = pom.read_text(encoding="utf-8")
        text = re.sub(r"<modules>.*?</modules>", f"<modules><module>{module.relative_to(root).as_posix()}</module></modules>", text, flags=re.S)
        pom.write_text(text, encoding="utf-8")
        dest_module = isolated / module.relative_to(root)
        shutil.copytree(module, dest_module, ignore=shutil.ignore_patterns("target"))
        for p in source.rglob("*.java"):
            dest = dest_module / "src/main/java" / p.relative_to(source)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
        result = run_maven(isolated, ["-pl", module.relative_to(root).as_posix(), "clean", "test"])
        require(result.returncode == 0, "External implementation failed public tests")
        totals = {k: 0 for k in ("tests", "failures", "errors", "skipped")}
        for report in (dest_module / "target/surefire-reports").glob("TEST-*.xml"):
            suite = ET.parse(report).getroot()
            for key in totals:
                totals[key] += int(suite.attrib.get(key, 0))
        require(totals["tests"] > 0 and totals["failures"] == totals["errors"] == totals["skipped"] == 0, "Incomplete test evidence")
        return {"challenge_id": challenge_id, "contract_version": meta["contract_version"],
                "external_implementation": "not retained", "public_tests": totals, "result": "passed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("challenge_id")
    parser.add_argument("--source", type=Path, required=True, help="External src/main/java tree; trusted local code only")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/local/external-check.json")
    args = parser.parse_args()
    report = verify(ROOT, args.challenge_id, args.source.resolve())
    write_json(args.report, report)
    print(f"OK external check: {report['public_tests']['tests']} public tests; implementation not retained")


if __name__ == "__main__":
    main_guard(main)
