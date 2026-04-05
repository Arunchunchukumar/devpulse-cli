"""Rich terminal formatters for DevPulse output.

Provides beautiful tables, panels, and status badges for PR dashboards,
CI status monitors, and velocity summaries.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def _review_badge(state: str) -> str:
    """Color-coded review status badge."""
    badges = {
        "APPROVED": "[bold green]APPROVED[/]",
        "CHANGES_REQUESTED": "[bold red]CHANGES REQ[/]",
        "REVIEW_REQUIRED": "[bold yellow]NEEDS REVIEW[/]",
        "PENDING": "[dim]PENDING[/]",
    }
    return badges.get(state, f"[dim]{state}[/]")


def _ci_badge(status: str) -> str:
    """Color-coded CI status badge."""
    badges = {
        "passing": "[bold green]PASS[/]",
        "failing": "[bold red]FAIL[/]",
        "running": "[bold blue]RUNNING[/]",
        "none": "[dim]NONE[/]",
    }
    return badges.get(status, f"[dim]{status}[/]")


def _stale_indicator(days: int, threshold: int = 7) -> str:
    """Visual staleness indicator."""
    if days >= threshold * 2:
        return f"[bold red]{days}d[/]"
    elif days >= threshold:
        return f"[yellow]{days}d[/]"
    elif days >= 3:
        return f"[dim]{days}d[/]"
    return f"[green]{days}d[/]"


def render_pr_table(console: Console, prs: list[dict], settings: dict) -> None:
    """Render a table of open pull requests."""
    stale_days = settings.get("stale_days", 7)

    table = Table(
        title="Open Pull Requests",
        title_style="bold",
        show_lines=True,
        padding=(0, 1),
    )

    table.add_column("Repo", style="cyan", max_width=30)
    table.add_column("#", style="dim", justify="right")
    table.add_column("Title", max_width=50)
    table.add_column("Author", style="magenta")
    table.add_column("Age", justify="center")
    table.add_column("Review", justify="center")
    table.add_column("CI", justify="center")
    table.add_column("+/-", justify="right")

    for pr in sorted(prs, key=lambda p: p["days_inactive"], reverse=True):
        title = pr["title"]
        if pr.get("draft"):
            title = f"[dim]DRAFT: {title}[/]"
        if len(title) > 50:
            title = title[:47] + "..."

        diff = f"[green]+{pr.get('additions', 0)}[/] [red]-{pr.get('deletions', 0)}[/]"

        table.add_row(
            pr["repo"],
            str(pr["number"]),
            title,
            pr["author"],
            _stale_indicator(pr["days_inactive"], stale_days),
            _review_badge(pr["review_state"]),
            _ci_badge(pr["ci_status"]),
            diff,
        )

    console.print(table)
    console.print(f"\n[dim]{len(prs)} open pull request(s)[/]")


def render_ci_table(console: Console, repos_checks: list[dict]) -> None:
    """Render CI pipeline status for each repo."""
    table = Table(
        title="CI Pipeline Status",
        title_style="bold",
        show_lines=True,
    )

    table.add_column("Repo", style="cyan")
    table.add_column("Check", max_width=40)
    table.add_column("Status", justify="center")
    table.add_column("Conclusion", justify="center")
    table.add_column("Duration", justify="right")

    for entry in repos_checks:
        repo = entry["repo"]
        checks = entry["checks"]

        if not checks:
            table.add_row(repo, "[dim]No checks found[/]", "", "", "")
            continue

        for check in checks:
            conclusion = check.get("conclusion") or "-"
            conclusion_style = {
                "success": "[green]success[/]",
                "failure": "[bold red]FAILURE[/]",
                "cancelled": "[yellow]cancelled[/]",
                "skipped": "[dim]skipped[/]",
            }.get(conclusion, f"[dim]{conclusion}[/]")

            # Calculate duration if timestamps available
            duration = "-"
            if check.get("started_at") and check.get("completed_at"):
                from datetime import datetime
                start = datetime.fromisoformat(check["started_at"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(check["completed_at"].replace("Z", "+00:00"))
                secs = int((end - start).total_seconds())
                duration = f"{secs // 60}m {secs % 60}s"

            table.add_row(repo, check["name"], check["status"], conclusion_style, duration)

    console.print(table)


def render_summary_panel(console: Console, metrics: dict, period: str) -> None:
    """Render a velocity summary panel."""
    for repo, data in metrics.items():
        panel_content = (
            f"[bold]Merged PRs:[/] {data['merged_count']}\n"
            f"[bold]Open PRs:[/] {data['open_count']}\n"
            f"[bold]Avg Cycle Time:[/] {data['avg_cycle_time_hours']}h\n"
            f"[bold]Lines Changed:[/] "
            f"[green]+{data['total_additions']}[/] / "
            f"[red]-{data['total_deletions']}[/]"
        )

        console.print(Panel(
            panel_content,
            title=f"{repo} ({period})",
            border_style="blue",
            padding=(1, 2),
        ))
