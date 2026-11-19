"""Общий код локальных инструментов. Только Python 3.12+ и стандартная библиотека."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

# Windows redirected output must stay readable in PowerShell, CI logs and Codex.
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"SIL-[0-9]{3,5}\Z")
SLUG_RE = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
STATUSES = {"backlog", "draft", "approved", "published"}
CATEGORIES = {"java-core", "spring-boot", "persistence", "sql", "messaging"}
LEVELS = {"Junior+", "Middle", "Middle+/Senior"}
NS = {"m": "http://maven.apache.org/POM/4.0.0"}


class ValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def read_json(path: Path):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def module_path(topic: dict) -> str:
    require(ID_RE.fullmatch(topic["id"]) is not None, "Invalid challenge ID")
    require(SLUG_RE.fullmatch(topic["slug"]) is not None, "Invalid slug")
    require(topic["category"] in CATEGORIES, "Invalid category")
    return f"challenges/{topic['category']}/{topic['id']}-{topic['slug']}"


def challenge_by_id(root: Path, challenge_id: str) -> tuple[Path, dict]:
    require(ID_RE.fullmatch(challenge_id) is not None, "Invalid challenge ID")
    matches = [(p.parent, read_json(p)) for p in sorted((root / "challenges").glob("*/*/challenge.json"))
               if read_json(p).get("id") == challenge_id]
    require(len(matches) == 1, f"Expected one challenge: {challenge_id}")
    return matches[0]


def run_maven(root: Path, args: list[str], timeout: int = 240) -> subprocess.CompletedProcess:
    wrapper = root / ("mvnw.cmd" if os.name == "nt" else "mvnw")
    # No shell interpolation. All callers pass controlled arguments, not model output.
    return subprocess.run([str(wrapper), "-B", "-ntp", *args], cwd=root, timeout=timeout, check=False)


def modules(root: Path) -> list[str]:
    tree = ET.parse(root / "pom.xml")
    return [e.text for e in tree.findall("m:modules/m:module", NS)]


def main_guard(callback) -> None:
    try:
        callback()
    except (ValueError, KeyError, TypeError, OSError, ET.ParseError,
            subprocess.SubprocessError) as error:
        raise SystemExit(f"ERROR: {error}") from None
