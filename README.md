# anjos/skills

[![skills.sh](https://skills.sh/b/anjos/skills)](https://skills.sh/anjos/skills)

A personal collection of agent skills for Claude Code and Codex, maintained alongside [anjos/dotfiles](https://github.com/anjos/dotfiles).

## Skills

| Skill | Description |
|---|---|
| [add-skill](skills/add-skill/SKILL.md) | Find and install agent skills into a chezmoi dotfiles repo |
| [pixi](skills/pixi/SKILL.md) | Package and environment management with pixi |

## Install all skills

```bash
npx skills add anjos/skills -g --agent codex
```

## Install a specific skill

```bash
npx skills add anjos/skills@add-skill -g --agent codex
```

## List available skills

```bash
npx skills add anjos/skills --list
```
