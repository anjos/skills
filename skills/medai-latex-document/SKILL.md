---
name: medai-latex-document
description: Create and maintain LaTeX documents (reports, project proposals, scientific articles, theses) for the Idiap medai group using copier and the medai document template. Use when starting a new LaTeX paper or report, bootstrapping a document project, building or synchronising an existing medai document with Overleaf, or updating one to the latest template.
---

# Idiap's MedAI Group LaTeX Document

Scaffolds Idiap's MedAI Group LaTeX documents — reports, project proposals, scientific
articles, theses — from `git@gitlab.idiap.ch:medai/templates/document`. Creates a git
repository built with [Tectonic](https://tectonic-typesetting.github.io/en-US/) through
pixi, with prek QA hooks, GitLab CI and Overleaf synchronisation. It ships no class or
theme: the document class, packages and structure are yours to choose.

## Prerequisites

Install once globally:

```sh
pixi global install -e copier git copier python-gitlab
```

GitLab SSH access must be configured — follow the
[GitLab SSH guide](https://docs.gitlab.com/user/ssh/) and verify with
`ssh -T git@gitlab.idiap.ch`.

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

## Create a New Document

```sh
# Interactive — answer template questions:
copier copy --trust git@gitlab.idiap.ch:medai/templates/document new-document

# Non-interactive — accept all defaults:
copier copy --defaults --trust git@gitlab.idiap.ch:medai/templates/document new-document

# Template files only — skip post-copy setup tasks:
copier copy --defaults --skip-tasks git@gitlab.idiap.ch:medai/templates/document new-doc
```

`--trust` is required because the template runs post-copy tasks (see below).

## Template Questions

| Variable | Default | Notes |
|---|---|---|
| `project_description` | `New document` | Short description, becomes the README title |
| `text_wrap` | `88` | Maximum source line length, written to `tex-fmt.toml` |
| `main_tex` | `main.tex` | Name of the file compiled by `pixi run build` |
| `gitlab_init` | `false` | Create a GitLab project (requires `~/.python-gitlab.cfg`) |
| `gitlab_group` | `medai/document` | Namespace — only asked when `gitlab_init=true` |
| `overleaf_project_id` | empty | Overleaf project to reset and sync with; empty skips |

For repositories joining the group's shared space, keep the naming convention: lower
case with dashes, and `venue-year-subject` or `venueYY-subject` for articles.

## What `--trust` Does

After generating files, copier runs `create.py` which:

1. Runs `pixi update` and `pixi install` in the new project
2. Initialises a git repository and creates an initial commit
3. Installs prek (pre-commit) hooks, then runs the QA suite and a first build
4. If `gitlab_init=true`: creates a GitLab project under `gitlab_group`, adds it as
   `origin`, and pushes
5. If `overleaf_project_id` was answered: resets that Overleaf project with the new
   repository and wires it as a remote

## Generated Layout

| Path | Purpose |
|---|---|
| `main.tex` (the `main_tex` answer) | the document — an `article` stub to build on |
| `pixi.toml`, `pixi.lock` | the pinned toolchain and all tasks |
| `tex-fmt.toml`, `.pre-commit-config.yaml` | formatting and quality-control rules |
| `.scripts/` | Overleaf synchronisation helpers |
| `.gitlab-ci.yml` | quality control, then a build, on every push |

Split long documents into one `.tex` file per chapter or section and `\input` them from
the main file; keep figures in a subdirectory next to the sources using them, and
references in a `.bib` file typeset with biblatex/biber (both are in the toolchain).

## Working on a Document

```sh
pixi install                # once, after cloning
pixi run install            # once, installs the prek pre-commit hook
pixi run build              # compile the main file into a PDF
pixi run build another.tex  # compile any other file
pixi run clean              # remove the PDF and synctex file of one input
pixi run deep-clean         # remove every untracked file, except .pixi
pixi run qa                 # run all quality-control hooks
pixi run update             # refresh the hook versions
```

Never commit the PDF, `*.synctex.gz` or LaTeX auxiliary files — they are gitignored. Run
`pixi run qa` before proposing changes; when collaborating, use merge requests rather
than pushing to `main`.

To bring in shared material (a common style file, a shared bibliography), vendor it with
[git-subrepo](https://github.com/ingydotnet/git-subrepo), never a git submodule: Overleaf
cannot fetch submodules. A `.gitrepo` file marks such a directory — propose changes to
its own repository rather than editing in place.

## Overleaf Synchronisation

Overleaf can be the only remote, or a second one alongside `origin`. Wire it up at any
point with the project id from Overleaf's Git menu:

```sh
pixi run setup-overleaf <UNIQUE-PROJECT-ID>  # RESETS Overleaf with this repository
pixi run pull-from-overleaf                  # bring in changes made on Overleaf
pixi run push-to-overleaf                    # send local changes to Overleaf
```

Pull first, then push, to reconcile both sides. Both scripts require a clean working
tree. With two remotes, a local `overleaf` branch mirrors Overleaf — never work on it.
Overleaf git integration is a premium feature; an EPFL e-mail address on the account
enables it.

## Update an Existing Project

From inside the project directory:

```sh
copier update --trust --skip-answered
```

Applies template changes (CI config, QA rules, editor settings) while preserving your
previous answers. All `*.tex` files are excluded from the patch, so an edited document is
never touched.
