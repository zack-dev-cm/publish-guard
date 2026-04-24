import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_LEAKS = REPO_ROOT / "skill/publish-guard/scripts/scan_leaks.py"
SCAN_SURFACE = REPO_ROOT / "skill/publish-guard/scripts/scan_public_surface.py"
SCORE_COPY = REPO_ROOT / "skill/publish-guard/scripts/score_launch_copy.py"
RENDER_AUDIT = REPO_ROOT / "skill/publish-guard/scripts/render_public_audit.py"


class PublishGuardScriptTests(unittest.TestCase):
    def make_repo(self) -> Path:
        repo = Path(tempfile.mkdtemp(prefix="publish-guard-test-"))
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        return repo

    def git_add(self, repo: Path, *paths: str) -> None:
        subprocess.run(["git", "-C", str(repo), "add", *paths], check=True)

    def run_script(self, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), *args],
            check=True,
            text=True,
            capture_output=True,
        )

    def read_json(self, path: Path) -> dict[str, object]:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_scan_leaks_flags_private_key_blocks_in_tracked_key_files(self) -> None:
        repo = self.make_repo()
        key_path = repo / "deploy.key"
        key_path.write_text("-----BEGIN " + "PRIVATE KEY-----\nabc123\n", encoding="utf-8")
        self.git_add(repo, "deploy.key")

        out_path = repo / "leaks.json"
        self.run_script(SCAN_LEAKS, "--root", str(repo), "--out", str(out_path))
        payload = self.read_json(out_path)

        codes = {item["code"] for item in payload["findings"]}
        self.assertIn("private-key-block", codes)

    def test_scan_leaks_flags_sk_proj_tokens(self) -> None:
        repo = self.make_repo()
        readme = repo / "README.md"
        readme.write_text("token " + "sk-proj-" + "abcdefghijklmnopqrstuvwxyz123456\n", encoding="utf-8")
        self.git_add(repo, "README.md")

        out_path = repo / "leaks.json"
        self.run_script(SCAN_LEAKS, "--root", str(repo), "--out", str(out_path))
        payload = self.read_json(out_path)

        codes = {item["code"] for item in payload["findings"]}
        self.assertIn("openai-key", codes)

    def test_scan_leaks_redacts_snippets_and_flags_windows_paths(self) -> None:
        repo = self.make_repo()
        leak_file = repo / "notes.txt"
        leak_file.write_text(
            "\n".join(
                [
                    "token " + "sk-proj-" + "abcdefghijklmnopqrstuvwxyz123456",
                    "path C:\\Users\\zack\\Secrets\\demo.txt",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.git_add(repo, "notes.txt")

        out_path = repo / "leaks.json"
        self.run_script(SCAN_LEAKS, "--root", str(repo), "--out", str(out_path))
        payload = self.read_json(out_path)

        codes = {item["code"] for item in payload["findings"]}
        snippets = [str(item["snippet"]) for item in payload["findings"]]

        self.assertIn("openai-key", codes)
        self.assertIn("absolute-path", codes)
        self.assertTrue(any("<redacted-openai-key>" in snippet for snippet in snippets))
        self.assertTrue(any("<redacted-path>" in snippet for snippet in snippets))
        self.assertFalse(any("sk-proj-" in snippet for snippet in snippets))
        self.assertFalse(any("C:\\Users\\zack" in snippet for snippet in snippets))

    def test_scan_leaks_flags_aws_credentials_and_fully_redacts_paths(self) -> None:
        repo = self.make_repo()
        env_file = repo / ".env"
        env_file.write_text(
            "\n".join(
                [
                    "AWS_ACCESS_KEY_ID=" + "AKIA" + "1234567890ABCDEF",
                    "AWS_SECRET_ACCESS_KEY=" + "abcdEFGH" + "ijklMNOPqrstUVWXyz0123456789/+=",
                    "PRIVATE_KEY_PATH=/Users/" + "zack/.ssh/id_rsa",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.git_add(repo, ".env")

        out_path = repo / "leaks.json"
        self.run_script(SCAN_LEAKS, "--root", str(repo), "--out", str(out_path))
        payload = self.read_json(out_path)

        codes = {item["code"] for item in payload["findings"]}
        snippets = [str(item["snippet"]) for item in payload["findings"]]

        self.assertIn("aws-access-key-id", codes)
        self.assertIn("aws-secret-access-key", codes)
        self.assertTrue(any("<redacted-path>" in snippet for snippet in snippets))
        self.assertFalse(any(".ssh/id_rsa" in snippet for snippet in snippets))

    def test_scan_leaks_scans_tracked_extensionless_text_files_and_sanitizes_root(self) -> None:
        repo = self.make_repo()
        dockerfile = repo / "Dockerfile"
        gitignore = repo / ".gitignore"
        dockerfile.write_text("FROM python:3.11\nENV APP_URL=http://local" + "host:3000\n", encoding="utf-8")
        gitignore.write_text("/Users/" + "zack/Secrets/demo.txt\n", encoding="utf-8")
        self.git_add(repo, "Dockerfile", ".gitignore")

        out_path = repo / "leaks.json"
        self.run_script(SCAN_LEAKS, "--root", str(repo), "--out", str(out_path))
        payload = self.read_json(out_path)

        files = {item["file"] for item in payload["findings"]}
        serialized = json.dumps(payload)

        self.assertIn("Dockerfile", files)
        self.assertIn(".gitignore", files)
        self.assertEqual(payload["root"], repo.name)
        self.assertNotIn(str(repo), serialized)

    def test_scan_leaks_scans_tracked_multi_suffix_dotenv_files(self) -> None:
        repo = self.make_repo()
        env_local = repo / ".env.local"
        env_production = repo / ".env.production"
        env_local.write_text("OPENAI_API_KEY=" + "sk-proj-" + "abcdefghijklmnopqrstuvwxyz123456\n", encoding="utf-8")
        env_production.write_text("OPENAI_API_KEY=" + "sk-proj-" + "abcdefghijklmnopqrstuvwxyz654321\n", encoding="utf-8")
        self.git_add(repo, ".env.local", ".env.production")

        out_path = repo / "leaks.json"
        self.run_script(SCAN_LEAKS, "--root", str(repo), "--out", str(out_path))
        payload = self.read_json(out_path)

        files = {item["file"] for item in payload["findings"]}
        self.assertIn(".env.local", files)
        self.assertIn(".env.production", files)

    def test_scan_leaks_scans_untracked_release_candidate_files(self) -> None:
        repo = self.make_repo()
        untracked_env = repo / ".env.local"
        untracked_notes = repo / "notes.txt"
        untracked_env.write_text("OPENAI_API_KEY=" + "sk-proj-" + "abcdefghijklmnopqrstuvwxyz123456\n", encoding="utf-8")
        untracked_notes.write_text("token " + "sk-proj-" + "abcdefghijklmnopqrstuvwxyz654321\n", encoding="utf-8")

        out_path = repo / "leaks.json"
        self.run_script(SCAN_LEAKS, "--root", str(repo), "--out", str(out_path))
        payload = self.read_json(out_path)

        files = {item["file"] for item in payload["findings"]}
        self.assertIn(".env.local", files)
        self.assertIn("notes.txt", files)

    def test_scan_public_surface_flags_multiline_default_prompt(self) -> None:
        repo = self.make_repo()
        yaml_path = repo / "skill/demo/agents/openai.yaml"
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        yaml_path.write_text(
            "\n".join(
                [
                    "interface:",
                    '  display_name: "Demo"',
                    "  default_prompt: |",
                    "    Use the control plane and benchmark contract before you start.",
                    "    Keep subagent notes in the main thread.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.git_add(repo, "skill/demo/agents/openai.yaml")

        out_path = repo / "surface.json"
        self.run_script(SCAN_SURFACE, "--root", str(repo), "--out", str(out_path))
        payload = self.read_json(out_path)

        codes = {item["code"] for item in payload["findings"]}
        self.assertIn("public-prompt-too-internal", codes)

    def test_scan_public_surface_flags_strong_single_phrase_in_chomped_default_prompts(self) -> None:
        repo = self.make_repo()
        literal_prompt = repo / "skill/demo/agents/openai.yaml"
        folded_prompt = repo / "skill/demo-folded/agents/openai.yaml"
        literal_prompt.parent.mkdir(parents=True, exist_ok=True)
        folded_prompt.parent.mkdir(parents=True, exist_ok=True)
        folded_prompt.write_text(
            "\n".join(
                [
                    "interface:",
                    '  display_name: "Assistant"',
                    "  default_prompt: >-",
                    "    Follow the workflow contract.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        literal_prompt.write_text(
            "\n".join(
                [
                    "interface:",
                    '  display_name: "Demo"',
                    "  default_prompt: |-",
                    "    Use the control plane before you start.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.git_add(repo, "skill/demo/agents/openai.yaml", "skill/demo-folded/agents/openai.yaml")

        out_path = repo / "surface.json"
        self.run_script(SCAN_SURFACE, "--root", str(repo), "--out", str(out_path))
        payload = self.read_json(out_path)

        files = {item["file"] for item in payload["findings"]}
        serialized = json.dumps(payload)

        self.assertIn("skill/demo/agents/openai.yaml", files)
        self.assertIn("skill/demo-folded/agents/openai.yaml", files)
        self.assertEqual(payload["root"], repo.name)
        self.assertNotIn(str(repo), serialized)

    def test_scan_public_surface_flags_large_included_inventory(self) -> None:
        repo = self.make_repo()
        readme = repo / "README.md"
        readme.write_text(
            "\n".join(
                ["# Demo", "", "## Included", *[f"- item {index}" for index in range(25)]]
            )
            + "\n",
            encoding="utf-8",
        )
        self.git_add(repo, "README.md")

        out_path = repo / "surface.json"
        self.run_script(SCAN_SURFACE, "--root", str(repo), "--out", str(out_path))
        payload = self.read_json(out_path)

        codes = {item["code"] for item in payload["findings"]}
        self.assertIn("giant-file-inventory", codes)

    def test_scan_public_surface_scans_untracked_openai_yaml(self) -> None:
        repo = self.make_repo()
        yaml_path = repo / "skill/demo/agents/openai.yaml"
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        yaml_path.write_text(
            "\n".join(
                [
                    "interface:",
                    '  display_name: "Demo"',
                    "  default_prompt: |-",
                    "    Use the control plane before you start.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        out_path = repo / "surface.json"
        self.run_script(SCAN_SURFACE, "--root", str(repo), "--out", str(out_path))
        payload = self.read_json(out_path)

        files = {item["file"] for item in payload["findings"]}
        self.assertIn("skill/demo/agents/openai.yaml", files)

    def test_scan_public_surface_flags_untracked_launch_docs_as_present(self) -> None:
        repo = self.make_repo()
        launch_doc = repo / "social-posts.md"
        launch_doc.write_text("# Draft\n", encoding="utf-8")

        out_path = repo / "surface.json"
        self.run_script(SCAN_SURFACE, "--root", str(repo), "--out", str(out_path))
        payload = self.read_json(out_path)

        details = {(item["code"], item["file"], item["detail"]) for item in payload["findings"]}
        self.assertIn(
            ("internal-launch-doc-present", "social-posts.md", "Internal launch or marketing doc is present in the repo working tree."),
            details,
        )

    def test_scan_public_surface_flags_false_assurance_in_security_docs(self) -> None:
        repo = self.make_repo()
        security = repo / "SECURITY.md"
        security.write_text("# Security\n\nThis tool provides exhaustive security coverage.\n", encoding="utf-8")

        out_path = repo / "surface.json"
        self.run_script(SCAN_SURFACE, "--root", str(repo), "--out", str(out_path))
        payload = self.read_json(out_path)

        codes = {item["code"] for item in payload["findings"]}
        files = {item["file"] for item in payload["findings"]}
        self.assertIn("false-assurance-language", codes)
        self.assertIn("SECURITY.md", files)

    def test_scan_public_surface_flags_mixed_disclaimer_and_overclaim(self) -> None:
        repo = self.make_repo()
        security = repo / "SECURITY.md"
        security.write_text(
            "# Security\n\nThis is not exhaustive, but it is a perfect scanner and guaranteed safe.\n",
            encoding="utf-8",
        )

        out_path = repo / "surface.json"
        self.run_script(SCAN_SURFACE, "--root", str(repo), "--out", str(out_path))
        payload = self.read_json(out_path)

        codes = {item["code"] for item in payload["findings"]}
        self.assertIn("false-assurance-language", codes)

    def test_scan_public_surface_flags_false_assurance_in_codex_docs(self) -> None:
        repo = self.make_repo()
        codex_doc = repo / "docs/codex/overview.md"
        codex_doc.parent.mkdir(parents=True, exist_ok=True)
        codex_doc.write_text("# Overview\n\nThis is a perfect scanner.\n", encoding="utf-8")

        out_path = repo / "surface.json"
        self.run_script(SCAN_SURFACE, "--root", str(repo), "--out", str(out_path))
        payload = self.read_json(out_path)

        files = {item["file"] for item in payload["findings"]}
        self.assertIn("docs/codex/overview.md", files)

    def test_score_launch_copy_redacts_absolute_readme_path_in_json(self) -> None:
        repo = self.make_repo()
        readme = repo / "README.md"
        readme.write_text(
            "\n".join(
                [
                    "# Demo",
                    "",
                    "**Small public audit skill.**",
                    "",
                    "## Quick Start",
                    "",
                    "```bash",
                    "python demo.py",
                    "```",
                    "",
                    "## What It Checks",
                    "",
                    "Shows output and what it catches.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        out_path = repo / "copy.json"
        self.run_script(SCORE_COPY, "--readme", str(readme), "--out", str(out_path))
        payload = self.read_json(out_path)

        serialized = json.dumps(payload)
        self.assertEqual(payload["readme"], "README.md")
        self.assertNotIn(str(repo), serialized)

    def test_score_launch_copy_does_not_mark_thin_readme_publish_ready(self) -> None:
        repo = self.make_repo()
        readme = repo / "README.md"
        readme.write_text(
            "\n".join(
                [
                    "# Demo",
                    "",
                    "## Quick Start",
                    "",
                    "```bash",
                    "python demo.py",
                    "```",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        out_path = repo / "copy.json"
        self.run_script(SCORE_COPY, "--readme", str(readme), "--out", str(out_path))
        payload = self.read_json(out_path)

        self.assertLess(payload["score"], 60)
        self.assertEqual(payload["verdict"], "not-ready")

    def test_score_launch_copy_requires_quick_start_for_publish_ready(self) -> None:
        repo = self.make_repo()
        readme = repo / "README.md"
        readme.write_text(
            "\n".join(
                [
                    "# Demo",
                    "",
                    "**Public audit tool.**",
                    "",
                    "```bash",
                    "python demo.py",
                    "```",
                    "",
                    "## When To Use",
                    "",
                    "Use this before you publish.",
                    "",
                    "## What It Checks",
                    "",
                    "Shows output and what it catches.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        out_path = repo / "copy.json"
        self.run_script(SCORE_COPY, "--readme", str(readme), "--out", str(out_path))
        payload = self.read_json(out_path)

        self.assertEqual(payload["verdict"], "revise-before-publish")
        self.assertGreaterEqual(payload["score"], 80)

    def test_render_public_audit_blocks_publish_when_warnings_exist(self) -> None:
        repo = self.make_repo()
        leaks_path = repo / "leaks.json"
        surface_path = repo / "surface.json"
        copy_path = repo / "copy.json"
        out_path = repo / "audit.md"

        leaks_path.write_text(
            json.dumps(
                {
                    "finding_count": 1,
                    "error_count": 0,
                    "warning_count": 1,
                    "findings": [{"severity": "warning", "code": "localhost-url", "file": "README.md", "line": 1, "snippet": "http://local" + "host:3000"}],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        surface_path.write_text(json.dumps({"finding_count": 0, "error_count": 0, "warning_count": 0, "findings": []}) + "\n", encoding="utf-8")
        copy_path.write_text(
            json.dumps({"score": 100, "verdict": "publish-ready", "components": []}) + "\n",
            encoding="utf-8",
        )

        self.run_script(
            RENDER_AUDIT,
            "--repo",
            str(repo),
            "--leaks",
            str(leaks_path),
            "--surface",
            str(surface_path),
            "--copy",
            str(copy_path),
            "--out",
            str(out_path),
        )

        audit = out_path.read_text(encoding="utf-8")
        self.assertIn("Recommendation: **Fix findings before publish**", audit)
        self.assertNotIn("Recommendation: **Publish**", audit)

    def test_render_public_audit_respects_not_ready_copy_verdict(self) -> None:
        repo = self.make_repo()
        leaks_path = repo / "leaks.json"
        surface_path = repo / "surface.json"
        copy_path = repo / "copy.json"
        out_path = repo / "audit.md"

        leaks_path.write_text(json.dumps({"finding_count": 0, "error_count": 0, "warning_count": 0, "findings": []}) + "\n", encoding="utf-8")
        surface_path.write_text(json.dumps({"finding_count": 0, "error_count": 0, "warning_count": 0, "findings": []}) + "\n", encoding="utf-8")
        copy_path.write_text(
            json.dumps({"score": 85, "verdict": "not-ready", "components": []}) + "\n",
            encoding="utf-8",
        )

        self.run_script(
            RENDER_AUDIT,
            "--repo",
            str(repo),
            "--leaks",
            str(leaks_path),
            "--surface",
            str(surface_path),
            "--copy",
            str(copy_path),
            "--out",
            str(out_path),
        )

        audit = out_path.read_text(encoding="utf-8")
        self.assertIn("Recommendation: **Do not publish yet**", audit)

    def test_render_public_audit_redacts_repo_path_and_snippets(self) -> None:
        repo = self.make_repo()
        leaks_path = repo / "leaks.json"
        surface_path = repo / "surface.json"
        copy_path = repo / "copy.json"
        out_path = repo / "audit.md"
        repo_path = "/tmp/" + "demo-repo"

        leaks_path.write_text(
            json.dumps(
                {
                    "finding_count": 1,
                    "error_count": 1,
                    "warning_count": 0,
                    "findings": [
                        {
                            "severity": "error",
                            "code": "openai-key",
                            "file": "README.md",
                            "line": 4,
                            "snippet": "token " + "sk-proj-" + "abcdefghijklmnopqrstuvwxyz123456",
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        surface_path.write_text(json.dumps({"finding_count": 0, "error_count": 0, "warning_count": 0, "findings": []}) + "\n", encoding="utf-8")
        copy_path.write_text(json.dumps({"score": 100, "verdict": "publish-ready", "components": []}) + "\n", encoding="utf-8")

        self.run_script(
            RENDER_AUDIT,
            "--repo",
            repo_path,
            "--leaks",
            str(leaks_path),
            "--surface",
            str(surface_path),
            "--copy",
            str(copy_path),
            "--out",
            str(out_path),
        )

        audit = out_path.read_text(encoding="utf-8")
        self.assertIn("- Repo: `demo-repo`", audit)
        self.assertIn("line redacted", audit)
        self.assertNotIn(repo_path, audit)
        self.assertNotIn("sk-proj-", audit)

    def test_scan_leaks_does_not_skip_lines_with_re_compile_calls(self) -> None:
        repo = self.make_repo()
        notes = repo / "notes.txt"
        notes.write_text(
            'secret = "' + "sk-proj-" + 'abcdefghijklmnopqrstuvwxyz123456"; re.compile("x")\n',
            encoding="utf-8",
        )

        out_path = repo / "leaks.json"
        self.run_script(SCAN_LEAKS, "--root", str(repo), "--out", str(out_path))
        payload = self.read_json(out_path)

        codes = {item["code"] for item in payload["findings"]}
        self.assertIn("openai-key", codes)

    def test_public_scope_docs_do_not_overclaim_release_notes_or_social_copy(self) -> None:
        tracked_docs = [
            REPO_ROOT / "skill/publish-guard/agents/openai.yaml",
            REPO_ROOT / "docs/codex/overview.md",
            REPO_ROOT / "README.md",
            REPO_ROOT / "skill/publish-guard/SKILL.md",
        ]

        for path in tracked_docs:
            text = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("social copy", text, path.as_posix())
            self.assertNotIn("release notes", text, path.as_posix())


if __name__ == "__main__":
    unittest.main()
