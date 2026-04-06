import os
from dataclasses import dataclass, field


@dataclass
class Config:
    """Runtime configuration loaded from environment variables."""

    # GitHub
    github_token: str = field(default_factory=lambda: os.getenv("GITHUB_TOKEN", ""))
    github_org: str = field(default_factory=lambda: os.getenv("GITHUB_ORG", ""))
    github_push: bool = field(default_factory=lambda: os.getenv("GITHUB_PUSH", "true").lower() == "true")
    github_private: bool = field(default_factory=lambda: os.getenv("GITHUB_PRIVATE", "true").lower() == "true")

    # Paths
    output_dir: str = field(default_factory=lambda: os.getenv("OUTPUT_DIR", "./output"))
    blueprints_dir: str = field(default_factory=lambda: os.getenv("BLUEPRINTS_DIR", "repo_assets/blueprints"))

    def validate(self) -> None:
        """Raise ValueError for any missing required config."""
        if self.github_push and not self.github_token:
            raise ValueError(
                "GITHUB_TOKEN is required when GITHUB_PUSH is enabled.\n"
                "Set it in your .env file or export it in your shell."
            )