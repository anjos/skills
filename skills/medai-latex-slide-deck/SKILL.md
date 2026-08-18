---
name: medai-latex-slide-deck
description: Create and maintain reusable LaTeX Beamer slide decks for the Idiap medai group using copier and the medai slides template. Use when creating a new slide deck or presentation, composing a talk from several decks, vendoring one deck into another, building or synchronising an existing medai deck with Overleaf, or updating one to the latest template.
---

# Idiap's MedAI Group LaTeX Slide Deck

Scaffolds Idiap's MedAI Group slide decks from
`git@gitlab.idiap.ch:medai/templates/slides`. Creates a git repository holding a Beamer
deck built with [Tectonic](https://tectonic-typesetting.github.io/en-US/) through pixi,
prek QA hooks, GitLab CI, Overleaf synchronisation, and the medai Beamer theme vendored
with git-subrepo.

A deck is an arbitrarily long, self-contained set of Beamer frames. A conference talk is
usually one deck; a lecture or group presentation is assembled from several, and decks
may be nested. Keeping decks reusable is the point of the conventions below.

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

## Create a New Deck

```sh
# Interactive — answer template questions:
copier copy --trust git@gitlab.idiap.ch:medai/templates/slides new-slides

# Non-interactive — accept all defaults:
copier copy --defaults --trust git@gitlab.idiap.ch:medai/templates/slides new-slides

# Template files only — skip post-copy setup tasks:
copier copy --defaults --skip-tasks git@gitlab.idiap.ch:medai/templates/slides new-slides
```

`--trust` is required because the template runs post-copy tasks (see below). Create one
repository per logically self-contained deck: that is what makes decks reusable.

## Template Questions

| Variable | Default | Notes |
|---|---|---|
| `project_description` | `New slides` | Short description, becomes the README title |
| `beamer_theme_url` | `git@gitlab.idiap.ch:medai/slides/theme` | Theme vendored into `theme/` |
| `text_wrap` | `88` | Maximum source line length, written to `tex-fmt.toml` |
| `main_tex` | `test.tex` | The build driver compiled by `pixi run build` |
| `gitlab_init` | `false` | Create a GitLab project (requires `~/.python-gitlab.cfg`) |
| `gitlab_group` | `medai/slides` | Namespace — only asked when `gitlab_init=true` |
| `overleaf_project_id` | empty | Overleaf project to reset and sync with; empty skips |

## What `--trust` Does

After generating files, copier runs `create.py` which:

1. Runs `pixi update` and `pixi install` in the new project
2. Initialises a git repository and creates an initial commit
3. Vendors the Beamer theme from `beamer_theme_url` into `theme/` with git-subrepo
4. Installs prek (pre-commit) hooks, then runs the QA suite and a first build
5. If `gitlab_init=true`: creates a GitLab project under `gitlab_group`, adds it as
   `origin`, and pushes
6. If `overleaf_project_id` was answered: resets that Overleaf project with the new
   repository and wires it as a remote

## Deck Layout and Conventions

| Path | Purpose |
|---|---|
| `test.tex` (the `main_tex` answer) | build driver: title, preamble, includes `all.tex` |
| `all.tex` | the deck: the ordered list of slide files it is made of |
| `intro.tex` | a slide file; add as many as needed |
| `preamble.tex` | packages and configuration this deck requires |
| `authors.tex` | presenter names, read by the theme for the title page |
| `theme/` | Beamer theme, vendored with git-subrepo — do not edit |

Rules that keep a deck reusable:

- Slide files contain **frames only** — no `\section`, no `\title`, no formatting. The
  presentation including the deck decides sectioning; the theme decides layout.
- `all.tex` lists the deck contents and normally declares no frames itself.
- Packages a deck needs go in `preamble.tex`, not in the build driver, so any
  presentation including the deck can reproduce a working environment.
- Every deck, nested ones included, must build standalone.
- Graphics live next to the deck that uses them, so they travel with it.

Two theme-provided commands compose decks, inserting them under a
section/subsection/subsubsection heading chosen from the depth of inclusion:

- `\inputslidedeck[Optional Heading]{file}` — deck in the **same** directory.
- `\importslidedeck[Optional Heading]{dir/}{file}` — deck in **another** directory; the
  imported deck's own paths resolve relative to `dir/`, which is what makes nesting work.

## Reusing Another Deck

Vendor it with [git-subrepo](https://github.com/ingydotnet/git-subrepo) — never a git
submodule, which Overleaf's git integration cannot fetch:

```sh
git subrepo clone git@gitlab.idiap.ch:<group>/<deck> <deck> -b main
```

Then, in `preamble.tex`, `\input{<deck>/preamble}`, and in `all.tex`,
`\importslidedeck[Optional Heading]{<deck>/}{all}`. Refresh every vendored deck later
with `pixi run update`. A `.gitrepo` file marks a vendored directory: propose changes to
its own repository, never edit in place. To repurpose one figure from a vendored deck,
symlink it next to your own graphics rather than copying it.

## Working on a Deck

```sh
pixi install                # once, after cloning
pixi run install            # once, installs the prek pre-commit hook
pixi run build              # compile the build driver into a PDF
pixi run build <deck>/test.tex  # compile a nested deck standalone
pixi run clean              # remove the PDF and synctex file of one input
pixi run deep-clean         # remove every untracked file, except .pixi
pixi run qa                 # run all quality-control hooks
pixi run update             # refresh hook versions and pull every vendored subrepo
```

Never commit the PDF, `*.synctex.gz` or LaTeX auxiliary files — they are gitignored. Run
`pixi run qa` before proposing changes; when collaborating, use merge requests rather
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
previous answers. All `*.tex` files are excluded from the patch, so edited slides are
never touched.

## Structuring a Presentation

When in doubt, follow the scientific method: state the problem and research questions;
review the state of the art and your hypotheses; describe data, methods, splits, measures
and baselines; describe your solution with technical depth; analyse results; close with
take-away messages and links to data and software. Avoid "Thank you" slides — the last
slide should carry the take-aways and contact information.
