"""Tests for DevPulse CLI commands."""

import pytest
from unittest.mock import patch, AsyncMock
from click.testing import CliRunner

from devpulse.cli import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_config(tmp_path):
    """Create a temporary config file for testing."""
    config_dir = tmp_path / ".devpulse"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text(
        "github_token: ghp_test_token_12345\n"
        "repos:\n"
        "  - testowner/testrepo\n"
        "settings:\n"
        "  stale_days: 7\n"
        "  review_sla_hours: 24\n"
    )
    return config_file


class TestVersion:
    def test_version_flag(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "devpulse" in result.output
        assert "0.3.0" in result.output


class TestConfig:
    def test_set_token(self, runner, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = runner.invoke(main, ["config", "set-token", "ghp_test123"])
            assert result.exit_code == 0
            assert "saved" in result.output.lower()

    def test_add_repo(self, runner, tmp_path, mock_config):
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = runner.invoke(main, ["config", "add-repo", "owner/new-repo"])
            assert result.exit_code == 0
            assert "Added" in result.output or "already" in result.output

    def test_add_repo_invalid_format(self, runner, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = runner.invoke(main, ["config", "add-repo", "invalid-format"])
            assert result.exit_code != 0


class TestPRCommand:
    @patch("devpulse.cli._load_config")
    @patch("devpulse.cli.GitHubClient")
    def test_prs_empty(self, mock_client_cls, mock_config_fn, runner):
        mock_config_fn.return_value = {
            "github_token": "test",
            "repos": ["owner/repo"],
            "settings": {"stale_days": 7},
        }
        mock_client = mock_client_cls.return_value
        mock_client.get_open_prs = AsyncMock(return_value=[])

        result = runner.invoke(main, ["prs"])
        assert result.exit_code == 0
        assert "No matching" in result.output

    @patch("devpulse.cli._load_config")
    @patch("devpulse.cli.GitHubClient")
    def test_prs_with_results(self, mock_client_cls, mock_config_fn, runner):
        mock_config_fn.return_value = {
            "github_token": "test",
            "repos": ["owner/repo"],
            "settings": {"stale_days": 7},
        }
        mock_client = mock_client_cls.return_value
        mock_client.get_open_prs = AsyncMock(return_value=[
            {
                "repo": "owner/repo",
                "number": 42,
                "title": "Fix login bug",
                "author": "dev1",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-10T00:00:00Z",
                "days_inactive": 3,
                "review_state": "APPROVED",
                "ci_status": "passing",
                "draft": False,
                "url": "https://github.com/owner/repo/pull/42",
                "additions": 50,
                "deletions": 10,
            }
        ])

        result = runner.invoke(main, ["prs"])
        assert result.exit_code == 0


class TestCICommand:
    @patch("devpulse.cli._load_config")
    @patch("devpulse.cli.GitHubClient")
    def test_ci_status(self, mock_client_cls, mock_config_fn, runner):
        mock_config_fn.return_value = {
            "github_token": "test",
            "repos": ["owner/repo"],
        }
        mock_client = mock_client_cls.return_value
        mock_client.get_check_runs = AsyncMock(return_value=[
            {
                "name": "build",
                "status": "completed",
                "conclusion": "success",
                "started_at": "2024-01-10T10:00:00Z",
                "completed_at": "2024-01-10T10:05:00Z",
                "url": "https://github.com/owner/repo/actions",
            }
        ])

        result = runner.invoke(main, ["ci"])
        assert result.exit_code == 0
