"""PR tracking logic — staleness detection, SLA checks, and sorting.

This module takes raw PullRequest objects from the GitHub client and
enriches them with actionable insights (stale flags, SLA breaches, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from devpulse.config import Settings
from devpulse.github_client import PullRequest


@dataclass
class PRInsight:
    """A PR enriched with actionable flags."""

    pr: PullRequest
    is_stale: bool
    sla_breached: bool
    urgency: str  # "critical", "warning", "ok"

    @property
    def urgency_rank(self) -> int:
        """Numeric rank for sorting (lower = more urgent)."""
        return {"critical": 0, "warning": 1, "ok": 2}[self.urgency]


def analyze_prs(prs: List[PullRequest], settings: Settings) -> List[PRInsight]:
    """Analyze a list of PRs and return enriched insights, sorted by urgency."""
    insights: List[PRInsight] = []

    for pr in prs:
        is_stale = pr.idle_hours > (settings.stale_days * 24)
        sla_breached = (
            pr.review_status == "pending"
            and pr.age_hours > settings.review_sla_hours
        )

        # Determine urgency level
        if pr.ci_status == "failure":
            urgency = "critical"
        elif is_stale or sla_breached:
            urgency = "warning"
        else:
            urgency = "ok"

        insights.append(
            PRInsight(
                pr=pr,
                is_stale=is_stale,
                sla_breached=sla_breached,
                urgency=urgency,
            )
        )

    # Sort: critical first, then warning, then ok; within each group by age desc
    insights.sort(key=lambda i: (i.urgency_rank, -i.pr.age_hours))
    return insights


def filter_stale(insights: List[PRInsight]) -> List[PRInsight]:
    """Return only stale PRs."""
    return [i for i in insights if i.is_stale]


def compute_velocity(merged_prs: list, days: int) -> dict:
    """Compute team velocity metrics from merged PR data.

    Returns a dict with:
      - total_merged: number of PRs merged
      - avg_time_to_merge_hours: mean time from open to merge
      - daily_throughput: average PRs merged per day
      - fastest_merge_hours: quickest PR turnaround
      - slowest_merge_hours: longest PR turnaround
    """
    if not merged_prs:
        return {
            "total_merged": 0,
            "avg_time_to_merge_hours": 0.0,
            "daily_throughput": 0.0,
            "fastest_merge_hours": 0.0,
            "slowest_merge_hours": 0.0,
        }

    times = [pr["time_to_merge_hours"] for pr in merged_prs]
    return {
        "total_merged": len(merged_prs),
        "avg_time_to_merge_hours": round(sum(times) / len(times), 1),
        "daily_throughput": round(len(merged_prs) / max(days, 1), 1),
        "fastest_merge_hours": round(min(times), 1),
        "slowest_merge_hours": round(max(times), 1),
    }
