# devpulse-cli

[![PyPI](https://img.shields.io/badge/pypi-v0.3.0-blue?logo=pypi)](https://pypi.org/project/devpulse-cli/)
[![Python](https://img.shields.io/badge/python-3.10+-3776AB?logo=python)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen?logo=pytest)](https://github.com/Arunchunchukumar/devpulse-cli/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

A developer productivity CLI that monitors **GitHub PR activity**, **CI pipeline status**, and **team velocity** from your terminal. Built with Click and Rich for a beautiful developer experience.

## Features

- **PR Dashboard** - See all open PRs across repos with review status, CI checks, and staleness indicators
- **CI Monitor** - Track pipeline health with pass/fail rates and failure alerts
- **Team Velocity** - Weekly/monthly metrics on merge frequency, review turnaround, and cycle time
- **Multi-Repo** - Monitor multiple repositories from a single config file
- **Rich Output** - Beautiful terminal tables, progress bars, and color-coded status

## Installation

```bash
pip install devpulse-cli
```

Or install from source:

```bash
git clone https://github.com/Arunchunchukumar/devpulse-cli.git
cd devpulse-cli
pip install -e ".[dev]"
```

## Quick Start

```bash
# Configure your GitHub token
devpulse config set-token ghp_xxxxxxxxxxxxx

# Add repositories to monitor
devpulse config add-repo owner/repo-name

# View PR dashboard
devpulse prs

# Check CI pipeline status
devpulse ci

# Weekly summary
devpulse summary --period weekly
```

## Usage Examples

```bash
# Show all stale PRs (no activity for 7+ days)
devpulse prs --stale

# Filter PRs needing your review
devpulse prs --needs-review

# CI status for a specific repo
devpulse ci --repo owner/my-repo

# Export summary as JSON
devpulse summary --format json > report.json
```

## Configuration

DevPulse stores config in `~/.devpulse/config.yaml`:

```yaml
github_token: ghp_xxxxxxxxxxxxx
repos:
  - owner/frontend
  - owner/backend
  - owner/infrastructure
settings:
  stale_days: 7
  review_sla_hours: 24
  ci_lookback_hours: 48
```

## Architecture

```
devpulse/
  cli.py             # Click command group & entry point
  github_client.py   # Async GitHub REST API client
  formatters.py      # Rich table/panel formatters
  config.py          # YAML config management
tests/
  test_cli.py        # CLI integration tests
```

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy devpulse/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Run tests (`pytest`)
4. Submit a Pull Request

## License

MIT License - see [LICENSE](./LICENSE) for details.
