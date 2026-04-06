import os
import shutil
import subprocess
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from config import Config

logger = logging.getLogger(__name__)


class RepoBuilder:
    """
    Fire-and-forget repo builder.
    Reads a blueprint, renders templates, creates the directory structure
    locally, initializes a git repo, and pushes to GitHub.
    """

    def __init__(self, blueprint: dict, output_dir: Path, config: Config):
        self.blueprint = blueprint
        self.project_name = blueprint["project_name"]
        self.variables = blueprint.get("variables", {})
        self.structure = blueprint.get("structure", [])
        self.templates_dir = Path(blueprint.get("templates_dir", "repo_assets/templates"))
        self.output_dir = output_dir / self.project_name
        self.config = config

        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            keep_trailing_newline=True,
        )

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def build(self) -> Path:
        """Run the full build pipeline. Returns the path of the created repo."""
        logger.info(f"Building repo '{self.project_name}' → {self.output_dir}")

        self._prepare_output_dir()
        self._render_structure(self.structure, self.output_dir)
        self._git_init()

        if self.config.github_push:
            self._github_create_and_push()

        logger.info(f"Done. Repo ready at: {self.output_dir}")
        return self.output_dir

    # ------------------------------------------------------------------
    # Directory + template rendering
    # ------------------------------------------------------------------

    def _prepare_output_dir(self) -> None:
        if self.output_dir.exists():
            raise FileExistsError(
                f"Output directory already exists: {self.output_dir}\n"
                "Delete it or choose a different project name."
            )
        self.output_dir.mkdir(parents=True)
        logger.debug(f"Created output directory: {self.output_dir}")

    def _render_structure(self, nodes: list, parent: Path) -> None:
        for node in nodes:
            node_path = parent / node["path"]

            if "children" in node:
                node_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {node_path}")
                self._render_structure(node["children"], node_path)
            else:
                self._render_file(node, node_path)

    def _render_file(self, node: dict, dest: Path) -> None:
        template_name = node.get("template")
        context = {
            "project_name": self.project_name,
            **self.variables,
        }

        if template_name:
            try:
                template = self.env.get_template(template_name)
                content = template.render(**context)
            except TemplateNotFound:
                logger.warning(f"Template '{template_name}' not found — creating empty file.")
                content = ""
        else:
            content = ""

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)
        logger.debug(f"Wrote file: {dest}")

    # ------------------------------------------------------------------
    # Git
    # ------------------------------------------------------------------

    def _git_init(self) -> None:
        logger.info("Initializing git repo...")
        self._run(["git", "init", "-b", "main"], cwd=self.output_dir)
        self._run(["git", "add", "."], cwd=self.output_dir)
        self._run(
            ["git", "commit", "-m", "chore: initial commit from Repo Factory"],
            cwd=self.output_dir,
        )

    def _github_create_and_push(self) -> None:
        logger.info(f"Creating GitHub repo '{self.project_name}'...")

        private_flag = "--private" if self.config.github_private else "--public"

        self._run([
            "gh", "repo", "create", self.project_name,
            private_flag,
            "--source", str(self.output_dir),
            "--remote", "origin",
            "--push",
        ])

        logger.info(f"Pushed to GitHub: {self.config.github_org or 'personal'}/{self.project_name}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _run(self, cmd: list[str], cwd: Path = None) -> None:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Command failed: {' '.join(cmd)}\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )
        if result.stdout:
            logger.debug(result.stdout.strip())