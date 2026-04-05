"""Configuration management for DevPulse CLI.

Reads settings from ~/.devpulse.yml or environment variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


CONFIG_PATH = Path.home() / ".devpulse.yml"


@dataclass
class Settings:
    """Tuneable thresholds and defaults."""

    stale_days: int = 7
    review_sla_hours: int = 24
    default_branch: str = "main"


@dataclass
class DevPulseConfig:
    """Top-level configuration."""

    github_token: str = ""
    repos: List[str] = field(default_factory=list)
    settings: Settings = field(default_factory=Settings)

    # ------------------------------------------------------------------
    # Loaders
    # ------------------------------------------------------------------

    @classmethod
    def load(cls) -> "DevPulseConfig":
        """Load config from file, falling back to env vars."""
        cfg = cls()

        # Try YAML file first
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as fh:
                raw = yaml.safe_load(fh) or {}

            cfg.github_token = raw.get("github_token", "")
            cfg.repos = raw.get("repos", [])

            if "settings" in raw:
                s = raw["settings"]
                cfg.settings = Settings(
                    stale_days=s.get("stale_days", 7),
                    review_sla_hours=s.get("review_sla_hours", 24),
                    default_branch=s.get("default_branch", "main"),
                )

        # Environment overrides
        env_token = os.environ.get("GITHUB_TOKEN", "")
        if env_token:
            cfg.github_token = env_token

        env_repos = os.environ.get("DEVPULSE_REPOS", "")
        if env_repos:
            cfg.repos = [r.strip() for r in env_repos.split(",") if r.strip()]

        return cfg

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Write current config to ~/.devpulse.yml."""
        data = {
            "github_token": self.github_token,
            "repos": self.repos,
            "settings": {
                "stale_days": self.settings.stale_days,
                "review_sla_hours": self.settings.review_sla_hours,
                "default_branch": self.settings.default_branch,
            },
        }
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as fh:
            yaml.dump(data, fh, default_flow_style=False, sort_keys=False)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> Optional[str]:
        """Return an error message if config is incomplete, else None."""
        if not self.github_token:
            return "GitHub token not configured. Run `devpulse config init` or set GITHUB_TOKEN."
        if not self.repos:
            return "No repositories configured. Run `devpulse config init`."
        return None
