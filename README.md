# anjos/skills

[![skills.sh](https://skills.sh/b/anjos/skills)](https://skills.sh/anjos/skills)

A personal collection of agent skills for Claude Code and Codex, maintained alongside [anjos/dotfiles](https://github.com/anjos/dotfiles).

## Skills

| Skill | Description |
|---|---|
| [medai-latex-document](skills/medai-latex-document/SKILL.md) | Create and maintain LaTeX documents, papers and theses for the Idiap medai group |
| [medai-latex-letter](skills/medai-latex-letter/SKILL.md) | Create and maintain LaTeX letters with the official Idiap letterhead |
| [medai-latex-poster](skills/medai-latex-poster/SKILL.md) | Create and maintain LaTeX/tikzposter posters for the Idiap medai group |
| [medai-latex-slide-deck](skills/medai-latex-slide-deck/SKILL.md) | Create and maintain reusable LaTeX Beamer slide decks for the Idiap medai group |
| [medai-python-package](skills/medai-python-package/SKILL.md) | Create and manage Python packages for the Idiap medai group using copier |
| [pixi](skills/pixi/SKILL.md) | Comprehensive package and environment management using pixi |

## Install all skills

```bash
npx skills add anjos/skills -g --agent codex
```

## Install a specific skill

```bash
npx skills add anjos/skills@pixi -g --agent codex
```

## List available skills

```bash
npx skills add anjos/skills --list
```
