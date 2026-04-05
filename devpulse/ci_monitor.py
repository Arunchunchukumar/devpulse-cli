"""CI pipeline monitoring and analysis.

Aggregates workflow runs across repositories and computes
reliability metrics, average durations, and failure patterns.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from devpulse.github_client import GitHubClient, WorkflowRun


@dataclass
class CIStats:
    """Aggregated CI statistics for a repository."""
    repo: str
    total_runs: int = 0
    successful: int = 0
    failed: int = 0
    in_progress: int = 0
    cancelled: int = 0
    avg_duration_minutes: Optional[float] = None
    failure_rate: float = 0.0
    most_failing_workflow: Optional[str] = None
    last_failure: Optional[datetime] = None
    runs: list[WorkflowRun] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        completed = self.successful + self.failed
        return (self.successful / completed * 100) if completed > 0 else 0.0

    @property
    def health_emoji(self) -> str:
        rate = self.success_rate
        if rate >= 95:
            return "[green]HEALTHY[/green]"
        if rate >= 80:
            return "[yellow]DEGRADED[/yellow]"
        return "[red]FAILING[/red]"


class CIMonitor:
    """Monitors CI pipelines across multiple repositories."""

    def __init__(self, client: GitHubClient):
        self._client = client

    async def get_stats(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
        lookback_hours: int = 24,
    ) -> CIStats:
        """Compute CI statistics for a repository within the lookback window."""
        runs = await self._client.get_workflow_runs(owner, repo, branch, per_page=100)

        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        recent = [r for r in runs if r.created_at >= cutoff]

        stats = CIStats(repo=f"{owner}/{repo}", runs=recent, total_runs=len(recent))

        failure_counts: dict[str, int] = defaultdict(int)

        for run in recent:
            if run.conclusion == "success":
                stats.successful += 1
            elif run.conclusion == "failure":
                stats.failed += 1
                failure_counts[run.name] += 1
                if stats.last_failure is None or run.created_at > stats.last_failure:
                    stats.last_failure = run.created_at
            elif run.conclusion == "cancelled":
                stats.cancelled += 1
            elif run.status in ("queued", "in_progress"):
                stats.in_progress += 1

        completed = stats.successful + stats.failed
        if completed > 0:
            stats.failure_rate = stats.failed / completed * 100

        if failure_counts:
            stats.most_failing_workflow = max(failure_counts, key=failure_counts.get)

        return stats

    async def get_failing_checks(
        self, owner: str, repo: str, ref: str
    ) -> list[dict[str, str]]:
        """Get details on failing checks for a specific commit."""
        checks = await self._client.get_check_runs(owner, repo, ref)
        return [
            {
                "name": c.name,
                "status": c.status,
                "conclusion": c.conclusion or "pending",
                "url": c.url,
            }
            for c in checks
            if c.conclusion in ("failure", "timed_out", None)
        ]
