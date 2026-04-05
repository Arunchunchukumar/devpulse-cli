"""DevPulse CLI - main entry point.

Provides commands for monitoring GitHub PR activity, CI pipeline status,
and generating team velocity summaries.
"""

import click
import asyncio
from rich.console import Console

from devpulse import __version__
from devpulse.github_client import GitHubClient
from devpulse.formatters import (
    render_pr_table,
    render_ci_table,
    render_summary_panel,
)

console = Console()


def _load_config():
    """Load configuration from ~/.devpulse/config.yaml."""
    import yaml
    from pathlib import Path

    config_path = Path.home() / ".devpulse" / "config.yaml"
    if not config_path.exists():
        console.print("[yellow]No config found. Run 'devpulse config set-token <token>' first.[/]")
        raise SystemExit(1)

    with open(config_path) as f:
        return yaml.safe_load(f)


@click.group()
@click.version_option(version=__version__, prog_name="devpulse")
def main():
    """DevPulse - Developer productivity CLI for GitHub."""
    pass


# ---------------------------------------------------------------------------
# PR Dashboard
# ---------------------------------------------------------------------------

@main.command()
@click.option("--repo", "-r", help="Filter to a specific repo (owner/name)")
@click.option("--stale", is_flag=True, help="Show only stale PRs (no activity for 7+ days)")
@click.option("--needs-review", is_flag=True, help="Show PRs that need your review")
def prs(repo, stale, needs_review):
    """Show open pull requests across all monitored repos."""
    config = _load_config()
    client = GitHubClient(config["github_token"])
    repos = [repo] if repo else config.get("repos", [])
    settings = config.get("settings", {})

    all_prs = []
    with console.status("Fetching pull requests..."):
        for r in repos:
            owner, name = r.split("/")
            prs_data = asyncio.run(client.get_open_prs(owner, name))
            all_prs.extend(prs_data)

    # Apply filters
    if stale:
        stale_days = settings.get("stale_days", 7)
        all_prs = [p for p in all_prs if p.get("days_inactive", 0) >= stale_days]
    if needs_review:
        all_prs = [p for p in all_prs if p.get("review_state") == "REVIEW_REQUIRED"]

    if not all_prs:
        console.print("[green]No matching pull requests found.[/]")
        return

    render_pr_table(console, all_prs, settings)


# ---------------------------------------------------------------------------
# CI Monitor
# ---------------------------------------------------------------------------

@main.command()
@click.option("--repo", "-r", help="Filter to a specific repo (owner/name)")
@click.option("--branch", "-b", default="main", help="Branch to check (default: main)")
def ci(repo, branch):
    """Show CI pipeline status for monitored repos."""
    config = _load_config()
    client = GitHubClient(config["github_token"])
    repos = [repo] if repo else config.get("repos", [])

    all_checks = []
    with console.status("Fetching CI status..."):
        for r in repos:
            owner, name = r.split("/")
            checks = asyncio.run(client.get_check_runs(owner, name, branch))
            all_checks.append({"repo": r, "checks": checks})

    render_ci_table(console, all_checks)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

@main.command()
@click.option("--period", type=click.Choice(["daily", "weekly", "monthly"]), default="weekly")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table")
def summary(period, output_format):
    """Generate a velocity summary for the team."""
    import json

    config = _load_config()
    client = GitHubClient(config["github_token"])
    repos = config.get("repos", [])

    metrics = {}
    with console.status(f"Generating {period} summary..."):
        for r in repos:
            owner, name = r.split("/")
            repo_metrics = asyncio.run(client.get_repo_metrics(owner, name, period))
            metrics[r] = repo_metrics

    if output_format == "json":
        click.echo(json.dumps(metrics, indent=2, default=str))
    else:
        render_summary_panel(console, metrics, period)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@main.group()
def config():
    """Manage DevPulse configuration."""
    pass


@config.command("set-token")
@click.argument("token")
def set_token(token):
    """Set your GitHub personal access token."""
    import yaml
    from pathlib import Path

    config_dir = Path.home() / ".devpulse"
    config_dir.mkdir(exist_ok=True)
    config_path = config_dir / "config.yaml"

    data = {}
    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

    data["github_token"] = token

    with open(config_path, "w") as f:
        yaml.dump(data, f)

    console.print("[green]GitHub token saved.[/]")


@config.command("add-repo")
@click.argument("repo")
def add_repo(repo):
    """Add a repository to monitor (format: owner/name)."""
    import yaml
    from pathlib import Path

    if "/" not in repo:
        console.print("[red]Invalid format. Use owner/repo-name.[/]")
        raise SystemExit(1)

    config_path = Path.home() / ".devpulse" / "config.yaml"
    data = {}
    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

    repos = data.get("repos", [])
    if repo not in repos:
        repos.append(repo)
        data["repos"] = repos

        with open(config_path, "w") as f:
            yaml.dump(data, f)

        console.print(f"[green]Added {repo} to monitored repos.[/]")
    else:
        console.print(f"[yellow]{repo} is already being monitored.[/]")


if __name__ == "__main__":
    main()
