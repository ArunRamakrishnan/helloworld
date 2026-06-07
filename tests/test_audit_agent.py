"""Unit tests for AuditAgent — prompt versioning and changelog recording."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.agents.audit_agent import AuditAgent, _get_git_commit_hash


class TestGetGitCommitHash:
    def test_returns_string(self):
        result = _get_git_commit_hash()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_unknown_on_failure(self):
        with patch("subprocess.run", side_effect=Exception("no git")):
            result = _get_git_commit_hash()
        assert result == "unknown"


class TestAuditAgent:
    def setup_method(self):
        self.agent = AuditAgent()

    def test_record_change_creates_prompt_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.agents.audit_agent.PROMPTS_DIR", tmp_path / "prompt_versions")
        monkeypatch.setattr("src.agents.audit_agent.CHANGELOG_PATH", tmp_path / "CHANGELOG.md")

        result = self.agent.record_change(
            changed_files=["src/agents/moat_agent.py"],
            reason="Added moat scoring",
            unit_test_result="passed",
        )

        assert result["version"].startswith("v")
        assert result["changelog_updated"] is True
        prompt_file = Path(result["prompt_file"])
        assert prompt_file.exists()

    def test_record_change_content_includes_reason(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.agents.audit_agent.PROMPTS_DIR", tmp_path / "prompt_versions")
        monkeypatch.setattr("src.agents.audit_agent.CHANGELOG_PATH", tmp_path / "CHANGELOG.md")

        result = self.agent.record_change(
            changed_files=["src/agents/risk_agent.py"],
            reason="Fixed debt ratio threshold",
            unit_test_result="passed",
        )

        content = Path(result["prompt_file"]).read_text()
        assert "Fixed debt ratio threshold" in content

    def test_record_change_increments_version(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.agents.audit_agent.PROMPTS_DIR", tmp_path / "prompt_versions")
        monkeypatch.setattr("src.agents.audit_agent.CHANGELOG_PATH", tmp_path / "CHANGELOG.md")

        r1 = self.agent.record_change(["file1.py"], "First change", "passed")
        r2 = self.agent.record_change(["file2.py"], "Second change", "passed")

        v1 = int(r1["version"].lstrip("v"))
        v2 = int(r2["version"].lstrip("v"))
        assert v2 == v1 + 1

    def test_changelog_is_updated(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.agents.audit_agent.PROMPTS_DIR", tmp_path / "prompt_versions")
        changelog = tmp_path / "CHANGELOG.md"
        monkeypatch.setattr("src.agents.audit_agent.CHANGELOG_PATH", changelog)

        self.agent.record_change(["src/api/routes.py"], "New endpoint", "passed")

        assert changelog.exists()
        content = changelog.read_text()
        assert "New endpoint" in content

    def test_changed_files_listed_in_prompt(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.agents.audit_agent.PROMPTS_DIR", tmp_path / "prompt_versions")
        monkeypatch.setattr("src.agents.audit_agent.CHANGELOG_PATH", tmp_path / "CHANGELOG.md")

        files = ["src/agents/risk_agent.py", "tests/test_risk_agent.py"]
        result = self.agent.record_change(files, "Risk scoring update", "passed")

        content = Path(result["prompt_file"]).read_text()
        assert "src/agents/risk_agent.py" in content
        assert "tests/test_risk_agent.py" in content

    def test_backtest_result_included_when_provided(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.agents.audit_agent.PROMPTS_DIR", tmp_path / "prompt_versions")
        monkeypatch.setattr("src.agents.audit_agent.CHANGELOG_PATH", tmp_path / "CHANGELOG.md")

        result = self.agent.record_change(
            ["src/strategies.py"], "Backtest run", "passed",
            backtest_result="Nifty 50 backtest: CAGR 14.2%"
        )
        content = Path(result["prompt_file"]).read_text()
        assert "Nifty 50 backtest" in content
