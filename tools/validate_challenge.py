"""Проверка контракта и starter; не запускает код задания."""
import argparse
from datetime import date
from pathlib import Path, PurePosixPath

from lab import ROOT, LEVELS, require, read_json, module_path, main_guard

REQUIRED = {
    "schema_version", "contract_version", "id", "slug", "title", "category", "topic", "level",
    "estimated_minutes", "skills", "prerequisites", "java_version", "status", "publication_date",
    "planned_publication_date", "telegram_url", "entrypoint", "acceptance_criteria", "reference_verified",
}
SECTIONS = ("Контекст", "Контракт", "Примеры", "Требования", "Граничные случаи",
            "Критерии приёмки", "Ограничения", "Подсказка", "Усложнение", "Запуск")


def validate_challenge(path: Path, root: Path) -> dict:
    meta = read_json(path / "challenge.json")
    require(isinstance(meta, dict) and set(meta) == REQUIRED, f"{path.name}: unexpected/missing metadata fields")
    require(meta["schema_version"] == 1 and meta["contract_version"] == "1.0", "Unsupported contract/schema")
    require(path.relative_to(root).as_posix() == module_path(meta), "Metadata/path mismatch")
    require(meta["level"] in LEVELS and meta["java_version"] == 21, "Invalid level/Java")
    require(meta["status"] in {"draft", "approved", "published"}, "Invalid challenge status")
    require(type(meta["estimated_minutes"]) is int and 10 <= meta["estimated_minutes"] <= 480, "Invalid estimate")
    for key in ("title", "topic"):
        require(isinstance(meta[key], str) and meta[key].strip(), f"Empty {key}")
    for key in ("skills", "prerequisites", "acceptance_criteria"):
        require(isinstance(meta[key], list) and len(meta[key]) > 0
                and all(isinstance(v, str) and v.strip() for v in meta[key]), f"Invalid {key}")
    require(type(meta["reference_verified"]) is bool, "Invalid reference verification flag")
    for key in ("publication_date", "planned_publication_date"):
        require(meta[key] is None or isinstance(meta[key], str), f"Invalid {key}")
        if meta[key] is not None:
            require(date.fromisoformat(meta[key]).isoformat() == meta[key], f"Invalid {key}")
    require(meta["telegram_url"] is None or (
        isinstance(meta["telegram_url"], str) and meta["telegram_url"].startswith("https://t.me/sync_idea_java/")),
        "Invalid Telegram post URL")
    if meta["status"] == "published":
        require(meta["publication_date"] is not None and meta["reference_verified"], "Publication requires date/reference check")
    else:
        require(meta["publication_date"] is None, "Unpublished challenge cannot have publication_date")
    if meta["status"] == "approved":
        require(meta["reference_verified"], "Approval requires a local reference check")
    entry = PurePosixPath(meta["entrypoint"])
    require(not entry.is_absolute() and ".." not in entry.parts and "\\" not in str(entry)
            and str(entry).startswith("src/main/java/") and entry.suffix == ".java", "Unsafe entrypoint")
    require((path / entry).is_file() and (path / "pom.xml").is_file(), "Missing starter/pom")
    sources = list((path / "src/main/java").rglob("*.java"))
    require(any("UnsupportedOperationException" in p.read_text(encoding="utf-8") for p in sources),
            "Starter must retain an explicit unimplemented operation")
    tests = list((path / "src/test/java").rglob("*Test.java"))
    require(tests and any("@Test" in p.read_text(encoding="utf-8") for p in tests), "Missing public JUnit tests")
    for p in tests:
        text = p.read_text(encoding="utf-8")
        require("Thread.sleep(" not in text and "@Disabled" not in text, "Unstable or disabled public test")
    readme = (path / "README.md").read_text(encoding="utf-8")
    require(all(f"## {section}" in readme for section in SECTIONS), "Missing required README sections")
    require(meta["id"] in readme and "test-compile" in readme, "README lacks ID/starter command")
    return meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    meta = validate_challenge(args.path.resolve(), args.root.resolve())
    print(f"OK challenge {meta['id']}")


if __name__ == "__main__":
    main_guard(main)
