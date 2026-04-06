# Commands & Workflow — Repo Factory

## Overview

Repo Factory is a CLI tool that generates standardized project repositories from blueprint YAML files and Jinja2 templates. You can build repos locally or push them directly to GitHub in a single command.

---

## Prerequisites

Before running the project, ensure you have the following installed:

- Python 3.10+
- `git`
- GitHub CLI (`gh`) — only required if pushing to GitHub

Install Python dependencies:

```bash
pip install -r requirements.txt
```

The project depends on at minimum:

- `pyyaml` — for parsing blueprint files
- `jinja2` — for rendering templates
- `python-dotenv` — for loading `.env` config

---

## Environment Setup

Create a `.env` file in the project root. The following variables are supported:

```env
# Required only when pushing to GitHub
GITHUB_TOKEN=your_personal_access_token

# Optional: your GitHub org name (leave blank for personal account)
GITHUB_ORG=your_org_name

# Whether to push to GitHub (overridden by --github CLI flag)
GITHUB_PUSH=false

# Whether to create private repos (overridden by --public CLI flag)
GITHUB_PRIVATE=true

# Where built repos are saved locally (default: ./new_repos)
OUTPUT_DIR=./new_repos

# Directory containing blueprint YAML files
BLUEPRINTS_DIR=repo_assets/blueprints
```

> `GITHUB_TOKEN` is only required when using the `--github` flag. For local-only builds, you can leave it unset.

---

## Project Structure

```
repo-factory/
├── src/
│   ├── main.py              # CLI entry point
│   ├── config.py            # Environment config loader
│   └── repo_builder.py      # Core build logic
├── repo_assets/
│   ├── blueprints/
│   │   └── default_blueprint.yml   # Example blueprint
│   └── templates/                  # Jinja2 file templates
├── new_repos/               # Output directory (auto-created)
├── docs/
│   └── README.md
├── .env                     # Local environment variables (not committed)
└── requirements.txt
```

---

## Running the Tool

All commands are run from the **project root**, targeting `src/main.py`.

### Build a repo locally (no GitHub push)

```bash
python src/main.py --blueprint repo_assets/blueprints/default_blueprint.yml
```

The generated repo will be saved to `new_repos/<project_name>/`.

---

### Build and push to GitHub (private repo)

```bash
python src/main.py --blueprint repo_assets/blueprints/default_blueprint.yml --github
```

Requires `GITHUB_TOKEN` to be set in your `.env` file and the `gh` CLI to be authenticated.

---

### Build and push to GitHub (public repo)

```bash
python src/main.py --blueprint repo_assets/blueprints/default_blueprint.yml --github --public
```

---

### Enable verbose/debug logging

Add `-v` or `--verbose` to any command:

```bash
python src/main.py --blueprint repo_assets/blueprints/default_blueprint.yml -v
```

---

## CLI Reference

| Flag | Short | Description |
|---|---|---|
| `--blueprint PATH` | `-b` | **(Required)** Path to the blueprint YAML file |
| `--github` | | Push the new repo to GitHub after building |
| `--public` | | Make the GitHub repo public (default is private) |
| `--verbose` | `-v` | Enable debug-level logging output |

---

## Blueprint Format

Blueprints are YAML files that define the project name, template directory, variables, and directory/file structure. Example (`default_blueprint.yml`):

```yaml
project_name: my_new_project
templates_dir: repo_assets/templates

variables:
  author: "Your Name"
  description: "A short project description"
  version: 1.0

structure:
  - path: src/
    children:
      - path: __init__.py
        template: template__init__.py
      - path: main.py
        template: template_main.py

  - path: docs/
    children:
      - path: README.md
        template: template_readme.md

  - path: requirements.txt
    template: template_requirements.txt

  - path: .gitignore
    template: template_gitignore
```

- `project_name` — name of the generated repo directory and GitHub repo
- `templates_dir` — path to the folder containing Jinja2 template files
- `variables` — key/value pairs injected into every template at render time
- `structure` — nested list of directories (`children`) and files (`template`)

> If a referenced template file is not found, an empty file is created in its place and a warning is logged.

---

## Build Workflow

When you run `main.py`, the following steps occur in order:

1. **Load `.env`** — environment variables are read via `python-dotenv`
2. **Parse CLI args** — flags override any env-based config
3. **Validate config** — raises an error if `GITHUB_TOKEN` is missing when `--github` is set
4. **Load blueprint** — the YAML file is parsed into a Python dict
5. **Prepare output directory** — creates `new_repos/<project_name>/`; exits if it already exists
6. **Render structure** — directories and files are created; Jinja2 templates are rendered with blueprint variables
7. **Git init** — runs `git init -b main`, `git add .`, and an initial commit
8. **GitHub push** *(if `--github`)* — runs `gh repo create` with the appropriate visibility flag and pushes

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `GITHUB_TOKEN is required...` | `--github` used without a token set | Add `GITHUB_TOKEN` to `.env` |
| `Output directory already exists` | A repo with that `project_name` was already built | Delete `new_repos/<project_name>/` or rename the project in the blueprint |
| `Blueprint not found` | Invalid path passed to `--blueprint` | Check the file path is correct relative to the project root |
| `Template not found` (warning) | A template listed in the blueprint doesn't exist in `templates_dir` | Add the missing template file or remove the reference from the blueprint |
| `Command failed: gh repo create` | `gh` CLI not installed or not authenticated | Run `gh auth login` or install the GitHub CLI |