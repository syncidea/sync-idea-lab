"""Эвристический аудит индекса и всей достижимой Git-истории перед публикацией."""
import subprocess

from lab import ROOT, require, main_guard
from validate_catalog import SECRET, validate_public_png

FORBIDDEN_PARTS = {".private", ".local", "private", "solutions", "reference-solutions", "reference", "hidden-tests", "target"}
STARTER_CLASSES = {"idempotencyregistry.java", "stabledistinct.java", "stockcounter.java",
                   "usernamenormalizer.java", "orderstatuscounter.java", "bookingwindow.java"}


def check_blob(path: str, data: bytes):
    parts = path.lower().split("/")
    require(not (set(parts) & FORBIDDEN_PARTS), f"Forbidden indexed/historical path: {path}")
    require(not any(p.startswith(".env") for p in parts), f"Environment file in Git: {path}")
    require(parts[-1] not in {"project_brief.md", "sync_idea_lab_codex_brief.md"},
            "Local project brief must stay outside the public index")
    require(not path.endswith((".pem", ".key", ".jks", ".p12", ".jar", ".class", ".zip")), f"Forbidden Git artifact: {path}")
    if parts[-1].endswith(".png"):
        validate_public_png(path, data)
    text = data.decode("utf-8", errors="replace")
    require(SECRET.search(text) is None, f"Possible secret in Git blob: {path}")
    if "/src/main/java/" in path and parts[-1] in STARTER_CLASSES:
        require("UnsupportedOperationException" in text, f"Possible completed starter in Git history: {path}")


def audit_git(root):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, timeout=30)
    count = 0
    for path in git("ls-files", "-z").decode().split("\0"):
        if path:
            check_blob(path, git("show", f":{path}"))
            count += 1
    revisions = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=root, capture_output=True, check=False)
    history_count = 0
    if revisions.returncode == 0:
        for line in git("rev-list", "--objects", "--all").decode().splitlines():
            object_id, _, path = line.partition(" ")
            if path and git("cat-file", "-t", object_id).strip() == b"blob":
                check_blob(path, git("cat-file", "blob", object_id))
                history_count += 1
    return count, history_count


def main():
    index, history = audit_git(ROOT)
    print(f"OK Git audit: {index} indexed files, {history} reachable historical blobs; manual source review still required")


if __name__ == "__main__":
    main_guard(main)
