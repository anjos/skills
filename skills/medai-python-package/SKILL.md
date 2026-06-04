---
name: medai-python-package
description: Create and manage Python packages for the Idiap medai group using copier and the medai Python template. Use when creating a new medai Python package, bootstrapping a medai project, or updating an existing medai Python project to the latest template.
---

# Idiap's MedAI Group Python Package

Scaffolds Idiap's MedAI Group Python packages from `git@gitlab.idiap.ch:medai/templates/python`. Creates a `src/`-layout package with Hatchling builds, pixi environments, prek QA hooks, optional Sphinx docs, and optional GitLab project initialization.

## Prerequisites

Install once globally:

```sh
pixi global install -e copier git copier python-gitlab
```

GitLab SSH access must be configured — follow the [GitLab SSH guide](https://docs.gitlab.com/user/ssh/) and verify with `ssh -T git@gitlab.idiap.ch`.

For GitLab project initialization (`gitlab_init=true`), create `~/.python-gitlab.cfg`:

```ini
[global]
default = idiap
ssl_verify = true
timeout = 15

[idiap]
url = https://gitlab.idiap.ch
private_token = <your-token>
api_version = 4
```

Set permissions: `chmod 600 ~/.python-gitlab.cfg`

## Create a New Package

```sh
# Interactive — answer template questions:
copier copy --trust git@gitlab.idiap.ch:medai/templates/python new-package

# Non-interactive — accept all defaults:
copier copy --defaults --trust git@gitlab.idiap.ch:medai/templates/python new-package

# Template files only — skip post-copy setup tasks:
copier copy --defaults --skip-tasks git@gitlab.idiap.ch:medai/templates/python new-package
```

`--trust` is required because the template runs post-copy tasks (see below).

## Template Questions

| Variable | Default | Notes |
|---|---|---|
| `project_name` | destination folder name | Distribution name: lower-case with dashes (`my-package`) |
| `project_slug` | derived from `project_name` | Import name: lower-case with underscores (`my_package`) |
| `project_description` | `Python package for <name>` | Short metadata/README summary |
| `author_name` | `First Last` | Main author |
| `author_email` | `first.last@idiap.ch` | Derived from `author_name` |
| `text_wrap` | `88` | Max source line length |
| `requires_python` | `3.11` | Choices: `3.11`, `3.12`, `3.13`, `3.14` |
| `software_license` | `GPL-3.0-or-later` | Choices: `GPL-3.0-or-later`, `BSD-3-Clause`, `Closed-source` |
| `has_doc` | `false` | Include Sphinx documentation scaffold |
| `gitlab_init` | `false` | Create GitLab project (requires `~/.python-gitlab.cfg`) |
| `gitlab_group` | `medai/software` | GitLab namespace — only asked when `gitlab_init=true` |

## What `--trust` Does

After generating files, copier runs `create.py` which:

1. Initialises a git repository and creates an initial commit
2. Runs `pixi install` to set up the managed environment
3. Installs prek (pre-commit) hooks and runs the full QA suite
4. Commits any lock-file or config changes produced by the above
5. If `gitlab_init=true`: creates a GitLab project under `gitlab_group`, adds it as `origin`, and pushes

## Update an Existing Project

From inside the project directory:

```sh
copier update --trust --skip-answered
```

Applies template changes (CI config, QA rules, etc.) while preserving your previous answers.
