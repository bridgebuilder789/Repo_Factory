"""
Repo Factory — Fire and Forget Repo Builder
--------------------------------------------
Usage:
    # Build locally into new_repos/ (default)
    python main.py --blueprint repo_assets/blueprints/default_blueprint.yml

    # Build and push to GitHub
    python main.py --blueprint repo_assets/blueprints/default_blueprint.yml --github

    # Build and push to GitHub as a public repo
    python main.py --blueprint repo_assets/blueprints/default_blueprint.yml --github --public
"""

import argparse
import logging
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from config import Config
from repo_builder import RepoBuilder


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        level=level,
    )


ROOT_DIR = Path(__file__).resolve().parent.parent
NEW_REPOS_DIR = ROOT_DIR / "new_repos"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="repo-factory",
        description="Fire-and-forget repo builder from a blueprint file.",
    )
    parser.add_argument(
        "--blueprint", "-b",
        required=True,
        help="Path to the blueprint YAML file.",
    )
    parser.add_argument(
        "--github",
        action="store_true",
        help="Push the new repo to GitHub. Omit to save locally to new_repos/ instead.",
    )
    parser.add_argument(
        "--public",
        action="store_true",
        help="Create the GitHub repo as public (default is private). Only applies with --github.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()


def load_blueprint(path: str) -> dict:
    blueprint_path = Path(path)
    if not blueprint_path.exists():
        raise FileNotFoundError(f"Blueprint not found: {blueprint_path}")
    with blueprint_path.open() as f:
        return yaml.safe_load(f)


def main() -> None:
    load_dotenv()
    args = parse_args()
    setup_logging(args.verbose)

    logger = logging.getLogger(__name__)

    # Load config from env, then apply CLI overrides
    config = Config()
    config.github_push = args.github
    config.github_private = not args.public
    config.output_dir = str(NEW_REPOS_DIR)

    # Ensure new_repos/ exists
    NEW_REPOS_DIR.mkdir(exist_ok=True)

    try:
        config.validate()
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    try:
        blueprint = load_blueprint(args.blueprint)
    except (FileNotFoundError, Exception) as e:
        logger.error(f"Failed to load blueprint: {e}")
        sys.exit(1)

    destination = "GitHub" if args.github else f"new_repos/"
    logger.info(f"Destination: {destination}")

    try:
        builder = RepoBuilder(
            blueprint=blueprint,
            output_dir=Path(config.output_dir),
            config=config,
        )
        repo_path = builder.build()
        logger.info(f"✓ Repo created successfully: {repo_path}")
    except FileExistsError as e:
        logger.error(str(e))
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"Build failed:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()