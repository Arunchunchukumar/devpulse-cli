"""Async GitHub REST API client.

Wraps the GitHub REST API with typed return values for PRs,
check runs, and repository metrics used by the CLI commands.
"""

from __future__ import annotations

import httpx
from datetime import datetime, timedelta, timezone
from typing import Any


class GitHubClient:
    """Lightweight async client for the GitHub REST API v3."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str) -> None:
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _get(self, path: str, params: dict | None = None) -> Any:
        """Make an authenticated GET request to the GitHub API."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}{path}",
                headers=self._headers,
                params=params or {},
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # Pull Requests
    # ------------------------------------------------------------------

    async def get_open_prs(self, owner: str, repo: str) -> list[dict]:
        """Fetch open PRs with review status and staleness info."""
        raw_prs = await self._get(
            f"/repos/{owner}/{repo}/pulls",
            {"state": "open", "per_page": 100, "sort": "updated", "direction": "desc"},
        )

        results = []
        now = datetime.now(timezone.utc)

        for pr in raw_prs:
            updated_at = datetime.fromisoformat(pr["updated_at"].replace("Z", "+00:00"))
            days_inactive = (now - updated_at).days

            # Determine review state from the latest reviews
            reviews = await self._get(
                f"/repos/{owner}/{repo}/pulls/{pr['number']}/reviews",
                {"per_page": 10},
            )

            review_state = "REVIEW_REQUIRED"
            if reviews:
                latest = reviews[-1]
                review_state = latest.get("state", "PENDING")

            # Check CI status
            check_runs = await self._get(
                f"/repos/{owner}/{repo}/commits/{pr['head']['sha']}/check-runs",
                {"per_page": 50},
            )
            checks = check_runs.get("check_runs", [])
            ci_status = "passing"
            if any(c["conclusion"] == "failure" for c in checks if c.get("conclusion")):
                ci_status = "failing"
            elif any(c["status"] == "in_progress" for c in checks):
                ci_status = "running"
            elif not checks:
                ci_status = "none"

            results.append({
                "repo": f"{owner}/{repo}",
                "number": pr["number"],
                "title": pr["title"],
                "author": pr["user"]["login"],
                "created_at": pr["created_at"],
                "updated_at": pr["updated_at"],
                "days_inactive": days_inactive,
                "review_state": review_state,
                "ci_status": ci_status,
                "draft": pr.get("draft", False),
                "url": pr["html_url"],
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
            })

        return results

    # ------------------------------------------------------------------
    # CI / Check Runs
    # ------------------------------------------------------------------

    async def get_check_runs(self, owner: str, repo: str, branch: str = "main") -> list[dict]:
        """Fetch the latest check runs for a branch."""
        data = await self._get(
            f"/repos/{owner}/{repo}/commits/{branch}/check-runs",
            {"per_page": 50, "filter": "latest"},
        )

        return [
            {
                "name": c["name"],
                "status": c["status"],
                "conclusion": c.get("conclusion"),
                "started_at": c.get("started_at"),
                "completed_at": c.get("completed_at"),
                "url": c.get("html_url"),
            }
            for c in data.get("check_runs", [])
        ]

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    async def get_repo_metrics(self, owner: str, repo: str, period: str = "weekly") -> dict:
        """Calculate velocity metrics for a repository over a time period."""
        days_map = {"daily": 1, "weekly": 7, "monthly": 30}
        days = days_map.get(period, 7)
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        # Get merged PRs in the period
        closed_prs = await self._get(
            f"/repos/{owner}/{repo}/pulls",
            {"state": "closed", "per_page": 100, "sort": "updated", "direction": "desc"},
        )

        since_dt = datetime.fromisoformat(since)
        merged_prs = [
            pr for pr in closed_prs
            if pr.get("merged_at")
            and datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00")) >= since_dt
        ]

        # Calculate review turnaround times
        turnaround_hours = []
        for pr in merged_prs:
            created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
            merged = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
            turnaround_hours.append((merged - created).total_seconds() / 3600)

        avg_turnaround = (
            sum(turnaround_hours) / len(turnaround_hours) if turnaround_hours else 0
        )

        open_prs = await self._get(
            f"/repos/{owner}/{repo}/pulls",
            {"state": "open", "per_page": 100},
        )

        return {
            "period": period,
            "merged_count": len(merged_prs),
            "open_count": len(open_prs),
            "avg_cycle_time_hours": round(avg_turnaround, 1),
            "total_additions": sum(pr.get("additions", 0) for pr in merged_prs),
            "total_deletions": sum(pr.get("deletions", 0) for pr in merged_prs),
        }
