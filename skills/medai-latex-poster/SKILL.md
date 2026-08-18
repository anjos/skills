---
name: medai-latex-poster
description: Create and maintain LaTeX posters for the Idiap medai group using copier and the medai poster template. Use when creating a new poster, bootstrapping a conference poster project, building or synchronising an existing medai poster with Overleaf, or updating one to the latest template.
---

# Idiap's MedAI Group LaTeX Poster

Scaffolds Idiap's MedAI Group posters from `git@gitlab.idiap.ch:medai/templates/poster`.
Creates a git repository holding a [tikzposter](https://ctan.org/pkg/tikzposter) document
built with [Tectonic](https://tectonic-typesetting.github.io/en-US/) through pixi, prek
QA hooks, GitLab CI, Overleaf synchronisation, and the Idiap poster theme vendored with
git-subrepo.

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

## Create a New Poster

```sh
# Interactive — answer template questions:
copier copy --trust git@gitlab.idiap.ch:medai/templates/poster new-poster

# Non-interactive — accept all defaults:
copier copy --defaults --trust git@gitlab.idiap.ch:medai/templates/poster new-poster

# Template files only — skip post-copy setup tasks:
copier copy --defaults --skip-tasks git@gitlab.idiap.ch:medai/templates/poster new-poster
```

`--trust` is required because the template runs post-copy tasks (see below).

## Template Questions

| Variable | Default | Notes |
|---|---|---|
| `project_description` | `New poster` | Short description, becomes the README title |
| `layout` | `portrait-2col` | Also `portrait-3col`, `landscape-3col`, `landscape-4col` |
| `language` | `english` | Also `french`; sets hyphenation, dates, logotype variant |
| `text_wrap` | `88` | Maximum source line length, written to `tex-fmt.toml` |
| `gitlab_init` | `false` | Create a GitLab project (requires `~/.python-gitlab.cfg`) |
| `gitlab_group` | `medai/poster` | Namespace — only asked when `gitlab_init=true` |
| `overleaf_project_id` | empty | Overleaf project to reset and sync with; empty skips |

`layout` and `language` only seed `main.tex`: it and `references.bib` belong to the
generated project from then on, and `copier update` never patches them.

## What `--trust` Does

After generating files, copier runs `create.py` which:

1. Runs `pixi update` and `pixi install` in the new project
2. Initialises a git repository and creates an initial commit
3. Vendors the Idiap poster theme into `theme/` with git-subrepo
4. Installs prek (pre-commit) hooks, then runs the QA suite and a first build
5. If `gitlab_init=true`: creates a GitLab project under `gitlab_group`, adds it as
   `origin`, and pushes
6. If `overleaf_project_id` was answered: resets that Overleaf project with the new
   repository and wires it as a remote

## Generated Layout

| Path | Purpose |
|---|---|
| `main.tex`, `references.bib` | the poster and its bibliography — yours to edit |
| `theme/` | Idiap style package (`idiap.sty`, fonts, graphics), vendored |
| `pixi.toml`, `pixi.lock` | the pinned toolchain and all tasks |
| `tex-fmt.toml`, `.pre-commit-config.yaml` | formatting and quality-control rules |
| `.scripts/` | Overleaf synchronisation helpers |
| `.gitlab-ci.yml` | quality control, then a build, on every push |

`theme/` is a style package **only** — the poster body never lives there. Its graphics
are referenced as `theme/graphics/<name>.<ext>`, extension included. A `.gitrepo` file
marks it as vendored: never edit inside, report changes upstream instead.

## Working on a Poster

```sh
pixi install                # once, after cloning
pixi run install            # once, installs the prek pre-commit hook
pixi run build              # compile main.tex into main.pdf (XeLaTeX, via Tectonic)
pixi run build another.tex  # compile any other file
pixi run clean              # remove the PDF and synctex file of one input
pixi run deep-clean         # remove every untracked file, except .pixi
pixi run qa                 # run all quality-control hooks
pixi run update             # refresh hook versions and pull the vendored theme
```

Never commit `main.pdf`, `*.synctex.gz` or LaTeX auxiliary files — they are gitignored.
Run `pixi run qa` before proposing changes; when collaborating, use merge requests rather
than pushing to `main`.

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
Overleaf git integration is a premium feature (an EPFL e-mail address enables it), and it
cannot fetch git submodules: that is why vendoring uses git-subrepo.

## Update an Existing Project

From inside the project directory:

```sh
copier update --trust --skip-answered
```

Applies template changes (CI config, QA rules, editor settings) while preserving your
previous answers. `main.tex` and `references.bib` are excluded from the patch, so an
edited poster is never touched.
