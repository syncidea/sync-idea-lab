"""ВНЕШНЕЕ действие: только отдельный доверенный job после явного opt-in владельца."""
import base64
import os
import re
import subprocess

from lab import ROOT, require, main_guard
from prepare_workflow import prepare


def run(*args: str, **kwargs):
    return subprocess.run(list(args), cwd=ROOT, check=True, timeout=90, **kwargs)


def main():
    require(os.environ.get("GITHUB_ACTIONS") == "true", "Use only in an explicitly authorized trusted GitHub workflow")
    challenge_id = os.environ.get("CHALLENGE_ID", "")
    require(re.fullmatch(r"SIL-[0-9]{3,5}", challenge_id) is not None, "Invalid challenge ID")
    plan = prepare(challenge_id)
    require(plan["changed"], "Already prepared; nothing to publish")
    branch = f"challenge/{challenge_id}"
    # Existing branch/PR is a successful no-op; never force-push or overwrite editor changes.
    existing = run("gh", "pr", "list", "--head", branch, "--state", "all", "--json", "number", capture_output=True, text=True)
    require(existing.stdout.strip() == "[]", "A PR already exists for this ID; inspect it instead of creating a duplicate")
    remote = run("git", "ls-remote", "--heads", "origin", f"refs/heads/{branch}", capture_output=True, text=True)
    require(not remote.stdout.strip(), "Branch already exists; inspect it manually (no overwrite)")
    run("git", "switch", "-c", branch)
    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    run("git", "add", "--", plan["module"], "catalog/topics.json", "pom.xml", f"docs/releases/{challenge_id}")
    run("git", "commit", "-m", f"[challenge-publication] Prepare {challenge_id} draft")
    # Credential exists only for the push command and is not persisted in Git config.
    credential = base64.b64encode(f"x-access-token:{os.environ['GH_TOKEN']}".encode()).decode()
    env = os.environ.copy()
    env.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
                "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {credential}"})
    run("git", "push", "--set-upstream", "origin", branch, env=env)
    run("gh", "pr", "create", "--draft", "--base", os.environ.get("GITHUB_BASE_REF") or "main", "--head", branch,
        "--title", f"[challenge-publication] {challenge_id}", "--body-file", f"docs/releases/{challenge_id}/pr.md")


if __name__ == "__main__":
    main_guard(main)
