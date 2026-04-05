"""Tests for the GitHub API client."""

from datetime import datetime, timezone
from devpulse.github_client import PullRequest, CheckRun


class TestPullRequest:
    def test_age_display_minutes(self):
        pr = PullRequest(
            number=1, title="Test", author="user", state="open",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            url="https://github.com/test/test/pull/1",
        )
        assert "m" in pr.age_display

    def test_age_display_hours(self):
        from datetime import timedelta
        pr = PullRequest(
            number=2, title="Old PR", author="user", state="open",
            created_at=datetime.now(timezone.utc) - timedelta(hours=5),
            updated_at=datetime.now(timezone.utc),
            url="https://github.com/test/test/pull/2",
        )
        assert "h" in pr.age_display

    def test_age_display_days(self):
        from datetime import timedelta
        pr = PullRequest(
            number=3, title="Stale PR", author="user", state="open",
            created_at=datetime.now(timezone.utc) - timedelta(days=10),
            updated_at=datetime.now(timezone.utc),
            url="https://github.com/test/test/pull/3",
        )
        assert "d" in pr.age_display


class TestCheckRun:
    def test_duration(self):
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        check = CheckRun(
            name="build", status="completed", conclusion="success",
            started_at=now - timedelta(minutes=5), completed_at=now,
        )
        assert check.duration_seconds is not None
        assert 299 <= check.duration_seconds <= 301

    def test_no_duration_when_pending(self):
        check = CheckRun(name="lint", status="queued")
        assert check.duration_seconds is None
