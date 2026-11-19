"""Регрессии безопасности и целостности генерации: реальные временные деревья и Git diff."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS / "challenge_generator"))
from lab import ROOT, ValidationError, read_json, write_json
from validate_catalog import validate_catalog
from generate import generate, package_files
from pr_policy import classify, materialize_submission
from audit_publication import audit_git

TEST_TOPIC = {"id": "SIL-999", "slug": "stable-distinct", "category": "java-core",
              "topic": "collections", "level": "Junior+", "status": "backlog", "fixture": "stable-distinct"}


class RepositoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sync-idea-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "target", "__pycache__", ".local", ".private", "reports", "PROJECT_BRIEF.md", "Sync_IDEA_Lab_Codex_Brief.md"))

    def test_duplicate_id_and_slug_are_rejected(self):
        path = self.root / "catalog/topics.json"
        original = read_json(path)
        for key in ("id", "slug"):
            with self.subTest(key=key):
                changed = original.copy()
                changed["topics"] = original["topics"] + [{**TEST_TOPIC, key: original["topics"][0][key]}]
                write_json(path, changed)
                with self.assertRaises(ValidationError):
                    validate_catalog(self.root)
        write_json(path, original)

    def test_missing_metadata_and_module_are_rejected(self):
        path = next((self.root / "challenges").glob("*/*/challenge.json"))
        meta = read_json(path)
        del meta["acceptance_criteria"]
        write_json(path, meta)
        with self.assertRaises(ValidationError):
            validate_catalog(self.root)

    def test_forbidden_files_and_secrets_are_rejected(self):
        cases = [("solutions/Answer.java", "class Answer {}"), ("leak.txt", "ghp_" + "x" * 36),
                 ("hidden-tests/Test.java", "class Test {}"), ("leak.pem", "certificate")]
        for relative, content in cases:
            with self.subTest(relative=relative):
                path = self.root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                with self.assertRaises(ValidationError):
                    validate_catalog(self.root)
                path.unlink()
                if path.parent != self.root:
                    path.parent.rmdir()

    def test_dry_run_is_deterministic_and_does_not_write(self):
        before = self.snapshot()
        one = generate(self.root, None, "fixture", False, pending_topic=TEST_TOPIC)
        two = generate(self.root, None, "fixture", False, pending_topic=TEST_TOPIC)
        self.assertEqual(one, two)
        self.assertEqual(before, self.snapshot())

    def test_preparation_is_idempotent_and_preserves_local_changes(self):
        first = generate(self.root, None, "fixture", True, pending_topic=TEST_TOPIC)
        readme = self.root / first["module"] / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\nДополнительный пример.\n", encoding="utf-8")
        before = self.snapshot()
        retry = generate(self.root, None, "fixture", True, pending_topic=TEST_TOPIC)
        self.assertEqual(retry["status"], "already-prepared")
        self.assertFalse(retry["changed"])
        self.assertEqual(before, self.snapshot())
        self.assertEqual(2, len(validate_catalog(self.root)))

    def test_local_topic_cannot_replace_existing_challenge(self):
        before = self.snapshot()
        existing_id = read_json(self.root / "catalog/topics.json")["topics"][0]["id"]
        with self.assertRaisesRegex(ValidationError, "conflicts with an existing challenge"):
            generate(self.root, None, "fixture", True, pending_topic={**TEST_TOPIC, "id": existing_id})
        self.assertEqual(before, self.snapshot())

    def test_publication_without_external_check_is_rejected(self):
        path = next((self.root / "challenges").glob("*/*/challenge.json"))
        meta = read_json(path)
        meta.update(status="published", publication_date="2026-11-18", reference_verified=False)
        write_json(path, meta)
        with self.assertRaises(ValidationError):
            validate_catalog(self.root)

    def test_provider_commands_and_path_traversal_are_rejected(self):
        fixture = read_json(self.root / "tools/challenge_generator/fixtures/stable-distinct.json")
        for field, value in (("commands", ["echo not-executed"]), ("package", "../../escape"), ("class_name", "../Escape")):
            with self.subTest(field=field):
                payload = dict(fixture)
                payload[field] = value
                with self.assertRaises(ValidationError):
                    package_files(TEST_TOPIC, payload)

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}


class PullRequestPolicyTest(RepositoryTest):
    # Do not inherit the generator tests; this class has an explicit test loader below.
    def setUp(self):
        super().setUp()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Local policy test")
        self.git("config", "user.email", "policy@example.invalid")
        self.git("add", ".")
        self.git("commit", "-m", "baseline")
        self.base = self.git("rev-parse", "HEAD").strip()
        self.source = "challenges/java-core/SIL-001-idempotency-registry/src/main/java/dev/syncidea/lab/idempotency/IdempotencyRegistry.java"

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True, stderr=subprocess.DEVNULL, timeout=30)

    def commit_change(self, path: str, content: str = "\n") -> str:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as output:
            output.write(content)
        self.git("add", ".")
        self.git("commit", "-m", "candidate")
        return self.git("rev-parse", "HEAD").strip()

    def test_submission_overlay_uses_trusted_tests_and_pom(self):
        head = self.commit_change(self.source, "\n// participant marker\n")
        # Return to trusted base; no PR checkout is used by the implementation.
        self.git("checkout", "--detach", self.base)
        policy = classify(self.root, self.base, head, "[submission SIL-001] My attempt", False)
        destination = Path(self.temp.name) / "submission"
        materialize_submission(self.root, self.base, head, policy, destination)
        self.assertIn("participant marker", (destination / self.source).read_text(encoding="utf-8"))
        self.assertEqual((self.root / "pom.xml").read_bytes(), (destination / "pom.xml").read_bytes())
        test = self.source.replace("/main/", "/test/").replace("Registry.java", "RegistryTest.java")
        self.assertEqual((self.root / test).read_bytes(), (destination / test).read_bytes())

    def test_submission_cannot_change_tests_workflows_or_another_task(self):
        paths = ["pom.xml", ".mvn/maven.config", ".github/workflows/submission-ci.yml", "tools/pr_policy.py",
                 self.source.replace("/main/", "/test/"), "challenges/java-core/SIL-999-other/src/main/java/Evil.java"]
        for path in paths:
            with self.subTest(path=path):
                self.git("checkout", "--detach", self.base)
                head = self.commit_change(path)
                with self.assertRaises(ValidationError):
                    classify(self.root, self.base, head, "[submission SIL-001] Attempt", True)

    def test_external_pr_cannot_spoof_editorial_title(self):
        head = self.commit_change("pom.xml")
        for title in ("[challenge-publication] Trusted?", "[bug] Fix", "[documentation] Docs"):
            with self.subTest(title=title), self.assertRaises(ValidationError):
                classify(self.root, self.base, head, title, False)

    def test_documentation_title_does_not_allow_java_changes(self):
        head = self.commit_change(self.source)
        with self.assertRaises(ValidationError):
            classify(self.root, self.base, head, "[documentation] Attempt", True)

    def test_symlink_mode_rejected_without_windows_symlink_privileges(self):
        blob = subprocess.check_output(["git", "hash-object", "-w", "--stdin"], cwd=self.root,
                                       input=b"../../../../pom.xml", timeout=30).decode().strip()
        self.git("update-index", "--cacheinfo", f"120000,{blob},{self.source}")
        self.git("commit", "-m", "symlink")
        head = self.git("rev-parse", "HEAD").strip()
        with self.assertRaises(ValidationError):
            classify(self.root, self.base, head, "[submission SIL-001] Attempt", False)

    def test_git_audit_finds_secret_even_after_it_is_removed(self):
        self.commit_change("leak.txt", "ghp_" + "x" * 36)
        self.git("rm", "leak.txt")
        self.git("commit", "-m", "remove leak")
        with self.assertRaises(ValidationError):
            audit_git(self.root)

    def test_git_audit_rejects_forced_add_of_local_brief(self):
        path = self.root / "PROJECT_BRIEF.md"
        path.write_text("Internal project brief", encoding="utf-8")
        self.git("add", "--force", path.name)
        with self.assertRaisesRegex(ValidationError, "Local project brief"):
            audit_git(self.root)


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(RepositoryTest))
    for name in PullRequestPolicyTest.__dict__:
        if name.startswith("test_"):
            suite.addTest(PullRequestPolicyTest(name))
    return suite
