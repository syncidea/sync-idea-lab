"""Детерминированный генератор: dry-run по умолчанию, --prepare меняет только локальные файлы."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab import ROOT, require, read_json, write_json, module_path, main_guard
from validate_catalog import validate_catalog
from providers import get_provider

PAYLOAD_KEYS = {"title", "estimated_minutes", "skills", "prerequisites", "acceptance_criteria",
                "package", "class_name", "readme", "main_source", "test_source"}


def package_files(topic: dict, payload: dict) -> dict[str, str]:
    require(isinstance(payload, dict) and set(payload) == PAYLOAD_KEYS, "Provider output has unexpected/missing fields")
    require(re.fullmatch(r"dev\.syncidea\.lab(?:\.[a-z][a-z0-9]*)+", payload["package"]) is not None, "Unsafe Java package")
    require(re.fullmatch(r"[A-Z][A-Za-z0-9]{0,60}", payload["class_name"]) is not None, "Unsafe class name")
    for field in ("main_source", "test_source", "readme"):
        require(isinstance(payload[field], str) and 0 < len(payload[field]) < 100_000, f"Invalid {field}")
    require("UnsupportedOperationException" in payload["main_source"], "Provider must return a starter")
    require("@Test" in payload["test_source"], "Provider must return public tests")
    require("package " + payload["package"] + ";" in payload["main_source"], "Source/package mismatch")
    relative = payload["package"].replace(".", "/") + "/" + payload["class_name"]
    entrypoint = f"src/main/java/{relative}.java"
    meta = {
        "schema_version": 1, "contract_version": "1.0", **{k: topic[k] for k in ("id", "slug", "category", "topic", "level")},
        **{k: payload[k] for k in ("title", "estimated_minutes", "skills", "prerequisites", "acceptance_criteria")},
        "java_version": 21, "status": "draft", "publication_date": None, "planned_publication_date": None,
        "telegram_url": None, "entrypoint": entrypoint, "reference_verified": False,
    }
    # POM and paths come from trusted templates, never from model instructions.
    pom = f'''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>dev.syncidea.lab</groupId><artifactId>sync-idea-lab</artifactId>
    <version>1.0-SNAPSHOT</version><relativePath>../../../pom.xml</relativePath>
  </parent>
  <artifactId>{topic['id'].lower()}-{topic['slug']}</artifactId>
  <dependencies><dependency>
    <groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter</artifactId><scope>test</scope>
  </dependency></dependencies>
</project>
'''
    readme = payload["readme"].replace("{{ID}}", topic["id"]).replace("{{MODULE}}", module_path(topic))
    return {"README.md": readme, "challenge.json": json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
            "pom.xml": pom, entrypoint: payload["main_source"], f"src/test/java/{relative}Test.java": payload["test_source"]}


def select_topic(topics: list[dict], challenge_id: str | None) -> dict:
    if challenge_id:
        found = [t for t in topics if t["id"] == challenge_id]
    else:
        # First pending fixture topic by ID, including existing draft: retry is idempotent.
        found = sorted((t for t in topics if t["fixture"] and t["status"] in {"backlog", "draft"}), key=lambda t: t["id"])
    require(bool(found), "No eligible topic; pass --topic-file with a local topic")
    return found[0]


def generate(root: Path, challenge_id: str | None, provider_name: str, prepare: bool, *,
             pending_topic: dict | None = None) -> dict:
    validate_catalog(root)
    topics = read_json(root / "catalog/topics.json")
    if pending_topic is not None:
        topic_keys = {"id", "slug", "category", "topic", "level", "status", "fixture"}
        require(isinstance(pending_topic, dict) and set(pending_topic) == topic_keys, "Invalid local topic fields")
        require(pending_topic["status"] == "backlog", "Local topic must have backlog status")
        module_path(pending_topic)
        require(challenge_id is None or challenge_id == pending_topic["id"], "ID does not match local topic")
        challenge_id = pending_topic["id"]
        existing = next((entry for entry in topics["topics"] if entry["id"] == challenge_id), None)
        if existing is None:
            topics["topics"].append(pending_topic.copy())
        else:
            require(all(existing[key] == pending_topic[key] for key in topic_keys - {"status"}),
                    "Local topic conflicts with an existing challenge")
    topic = select_topic(topics["topics"], challenge_id)
    module = module_path(topic)
    if topic["status"] != "backlog":
        require((root / module / "challenge.json").is_file(), "Prepared topic missing package")
        return {"id": topic["id"], "status": "already-prepared", "changed": False, "module": module}
    payload = get_provider(provider_name).generate(topic)
    files = package_files(topic, payload)
    digest = hashlib.sha256(json.dumps(files, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    plan = {"id": topic["id"], "status": "prepared" if prepare else "dry-run", "changed": prepare,
            "module": module, "files": sorted(files), "sha256": digest,
            "reference_check": "required locally before approval", "behavior_tests": "not run"}
    # Validate in a disposable tree before touching the working repository.
    with tempfile.TemporaryDirectory(prefix="sync-idea-generator-") as tmp:
        staged = Path(tmp) / "repo"
        shutil.copytree(root, staged, ignore=shutil.ignore_patterns(".git", "target", "__pycache__", ".local", ".private", "PROJECT_BRIEF.md", "Sync_IDEA_Lab_Codex_Brief.md"))
        for name, content in files.items():
            target = staged / module / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        next(t for t in topics["topics"] if t["id"] == topic["id"])["status"] = "draft"
        write_json(staged / "catalog/topics.json", topics)
        pom = (staged / "pom.xml").read_text(encoding="utf-8")
        require(pom.count("</modules>") == 1, "Cannot locate reactor modules")
        (staged / "pom.xml").write_text(pom.replace("</modules>", f"  <module>{module}</module>\n  </modules>"), encoding="utf-8")
        validate_catalog(staged)
        if prepare:
            destination = root / module
            require(not destination.exists(), "Refusing to overwrite an existing package")
            old_pom = (root / "pom.xml").read_bytes()
            old_topics = (root / "catalog/topics.json").read_bytes()
            try:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(staged / module, destination)
                shutil.copy2(staged / "pom.xml", root / "pom.xml")
                shutil.copy2(staged / "catalog/topics.json", root / "catalog/topics.json")
            except OSError:
                (root / "pom.xml").write_bytes(old_pom)
                (root / "catalog/topics.json").write_bytes(old_topics)
                # destination is a fixed validated child created by this invocation.
                if destination.exists():
                    shutil.rmtree(destination)
                raise
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--id")
    parser.add_argument("--topic-file", type=Path, help="Local JSON object with a single backlog topic")
    parser.add_argument("--provider", choices=["fixture"], default="fixture")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    pending_topic = read_json(args.topic_file) if args.topic_file is not None else None
    require(args.topic_file is None or isinstance(pending_topic, dict), "Topic file must contain an object")
    plan = generate(args.root.resolve(), args.id, args.provider, args.prepare, pending_topic=pending_topic)
    print(json.dumps(plan, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main_guard(main)
