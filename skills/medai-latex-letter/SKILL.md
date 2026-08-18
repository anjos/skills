---
name: medai-latex-letter
description: Create and maintain LaTeX letters with the official Idiap letterhead using copier and the medai letter template. Use when writing a new Idiap letter, bootstrapping a letter project, building or synchronising an existing medai letter with Overleaf, or updating one to the latest template.
---

# Idiap's MedAI Group LaTeX Letter

Scaffolds Idiap letters from `git@gitlab.idiap.ch:medai/templates/letter`. Creates a git
repository holding a letter typeset with the official Idiap letterhead
(`idiap.sty` plus the bundled Geist faces), built with
[Tectonic](https://tectonic-typesetting.github.io/en-US/) through pixi, with prek QA
hooks, GitLab CI and Overleaf synchronisation.

The letter compiles with **XeLaTeX**, because `idiap.sty` loads `fontspec`. The shipped
`.latexmkrc` forces that on latexmk-based setups; if an Overleaf compile complains about
`fontspec`, set Menu → Settings → Compiler → XeLaTeX.

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

## Create a New Letter

```sh
# Interactive — answer template questions:
copier copy --trust git@gitlab.idiap.ch:medai/templates/letter new-letter

# Non-interactive — accept all defaults:
copier copy --defaults --trust git@gitlab.idiap.ch:medai/templates/letter new-letter

# Template files only — skip post-copy setup tasks:
copier copy --defaults --skip-tasks git@gitlab.idiap.ch:medai/templates/letter new-letter
```

`--trust` is required because the template runs post-copy tasks (see below).

## Template Questions

| Variable | Default | Notes |
|---|---|---|
| `project_description` | `New letter with Idiap letterhead` | Becomes the README title |
| `text_wrap` | `88` | Maximum source line length, written to `tex-fmt.toml` |
| `gitlab_init` | `false` | Create a GitLab project (requires `~/.python-gitlab.cfg`) |
| `gitlab_group` | `medai/letter` | Namespace — only asked when `gitlab_init=true` |
| `overleaf_project_id` | empty | Overleaf project to reset and sync with; empty skips |

Sender, recipient, subject, place and language (english/french) are set inside
`main.tex`, using the commented knobs at the top of the generated file
(`\sendername`, `\senderrole`, `\senderaddress`, `\recipient`, `\subject`, …).

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
| `main.tex` | the letter — yours to edit |
| `idiap.sty` | the letterhead package — vendored, report changes upstream |
| `fonts/` | Geist and Geist Mono, bundled so the letter builds anywhere |
| `pixi.toml`, `pixi.lock` | the pinned toolchain and all tasks |
| `tex-fmt.toml`, `.pre-commit-config.yaml` | formatting and quality-control rules |
| `.scripts/` | Overleaf synchronisation helpers |
| `.gitlab-ci.yml` | quality control, then a build, on every push |

`idiap.sty` and `fonts/` ship inside the repository on purpose: the letter then builds
where the fonts are not installed system-wide (CI containers, Overleaf), and Overleaf's
git integration — which cannot fetch submodules — still sees every file it needs.

## Working on a Letter

```sh
pixi install                # once, after cloning
pixi run install            # once, installs the prek pre-commit hook
pixi run build              # compile main.tex into main.pdf (XeLaTeX, via Tectonic)
pixi run build another.tex  # compile any other file
pixi run clean              # remove the PDF and synctex file of one input
pixi run deep-clean         # remove every untracked file, except .pixi
pixi run qa                 # run all quality-control hooks
pixi run update             # refresh the hook versions
```

Never commit `main.pdf`, `*.synctex.gz` or LaTeX auxiliary files — they are gitignored.

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

Applies template changes — including letterhead fixes in `idiap.sty` — while preserving
your previous answers. All `*.tex` files are excluded from the patch, so an edited letter
is never touched. Letterhead problems belong upstream, in
`project/idiap.sty.jinja` of the template: fix them there and every letter picks them up.
