"""Валидация каталога, модулей, метаданных и запрещённых публичных файлов."""
import argparse
from pathlib import Path
import re

from lab import ROOT, STATUSES, LEVELS, require, read_json, module_path, modules, main_guard
from validate_challenge import validate_challenge

SKIP = {".git", "target", "__pycache__", ".idea", ".vscode", ".local", ".private"}
FORBIDDEN = {"solutions", "reference-solutions", "reference", "private", "hidden-tests"}
SECRET = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bgh[pousr]_[A-Za-z0-9]{30,}|\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}")


def public_files(root: Path):
    for directory, subdirs, names in root.walk():
        subdirs[:] = [d for d in subdirs if d not in SKIP]
        for name in subdirs:
            require(name.lower() not in FORBIDDEN, f"Forbidden public directory: {directory / name}")
        for name in names:
            p = directory / name
            if p in {root / "PROJECT_BRIEF.md", root / "Sync_IDEA_Lab_Codex_Brief.md"} or p.is_relative_to(root / "reports/local"):
                continue
            yield p


def validate_catalog(root: Path, scan: bool = True):
    topics_doc = read_json(root / "catalog/topics.json")
    published_doc = read_json(root / "catalog/published.json")
    require(set(topics_doc) == {"schema_version", "topics"} and topics_doc["schema_version"] == 1, "Invalid topics schema")
    require(set(published_doc) == {"schema_version", "challenges"} and published_doc["schema_version"] == 1, "Invalid published schema")
    topics = topics_doc["topics"]
    require(isinstance(topics, list) and topics, "Empty topic plan")
    ids, slugs = set(), set()
    for topic in topics:
        require(set(topic) == {"id", "slug", "category", "topic", "level", "status", "fixture"}, "Invalid topic fields")
        module_path(topic)
        require(topic["id"] not in ids and topic["slug"] not in slugs, "Duplicate ID/slug")
        ids.add(topic["id"])
        slugs.add(topic["slug"])
        require(topic["status"] in STATUSES and topic["level"] in LEVELS and topic["topic"], "Invalid topic state")
        fixture = topic["fixture"]
        require(fixture is None or fixture == "stable-distinct", "Unknown fixture adapter")
    metas = {}
    paths = []
    for p in sorted((root / "challenges").glob("*/*/challenge.json")):
        meta = validate_challenge(p.parent, root)
        require(meta["id"] not in metas, "Duplicate challenge ID")
        metas[meta["id"]] = meta
        paths.append(p.parent.relative_to(root).as_posix())
    for topic in topics:
        if topic["status"] == "backlog":
            require(topic["id"] not in metas, "Backlog topic already has a module")
        else:
            require(topic["id"] in metas, "Non-backlog topic has no module")
            meta = metas[topic["id"]]
            require(all(topic[k] == meta[k] for k in ("id", "slug", "category", "topic", "level", "status")), "Topic/challenge mismatch")
    require(set(metas) <= ids, "Challenge missing from topic plan")
    listed_modules = modules(root)
    require(len(listed_modules) == len(set(listed_modules)) and set(listed_modules) == set(paths), "Maven module/catalog mismatch")
    published = published_doc["challenges"]
    require(isinstance(published, list), "Invalid published entries")
    seen = set()
    for item in published:
        require(set(item) == {"id", "slug", "publication_date"}, "Invalid published entry")
        require(item["id"] not in seen and item["id"] in metas, "Duplicate/unknown published ID")
        seen.add(item["id"])
        meta = metas[item["id"]]
        require(meta["status"] == "published" and all(item[k] == meta[k] for k in item), "Published metadata mismatch")
    require(seen == {i for i, m in metas.items() if m["status"] == "published"}, "Published index is incomplete")
    if scan:
        for p in public_files(root):
            rel = p.relative_to(root).as_posix()
            require(not p.is_symlink(), f"Public symlink forbidden: {rel}")
            require(p.suffix.lower() not in {".pem", ".key", ".p12", ".jks", ".class", ".jar", ".zip"}, f"Forbidden public artifact: {rel}")
            require(not p.name.startswith(".env"), f"Environment file forbidden: {rel}")
            require(rel == "tools/check_solution.py" or not re.search(
                r"(?:^|[._-])(?:solution|reference|hidden-test)(?:[._-]|$)", p.name.lower()), f"Suspicious public file: {rel}")
            require(p.stat().st_size < 2_000_000, f"Oversize public file: {rel}")
            require(SECRET.search(p.read_text(encoding="utf-8")) is None, f"Possible secret in {rel}")
    return metas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--id")
    parser.add_argument("--topic")
    parser.add_argument("--level")
    args = parser.parse_args()
    metas = validate_catalog(args.root.resolve())
    for meta in metas.values():
        if all(value is None or meta[key] == value for key, value in (("id", args.id), ("topic", args.topic), ("level", args.level))):
            print(f"{meta['id']} | {meta['level']} | {meta['topic']} | {meta['status']} | {meta['title']}")
    print(f"OK catalog: {len(metas)} challenge(s)")


if __name__ == "__main__":
    main_guard(main)
