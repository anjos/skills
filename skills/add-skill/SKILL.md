---
name: add-skill
description: Add a new agent skill to this chezmoi dotfiles repo. Use when the user wants to find, install, or add a skill for Claude Code or Codex.
metadata:
  short-description: Find and add an agent skill to chezmoi
---

# Add Skill

@../find-skills/SKILL.md

## Installing from a GitHub Path or URL

If given a short path like `github/awesome-copilot/git-commit` or a full URL like
`https://github.com/github/awesome-copilot/tree/main/skills/git-commit` or
`https://www.skills.sh/github/awesome-copilot/git-commit`, derive the
install command as follows:

| Input | `owner/repo` | `skill-name` |
|---|---|---|
| `github/awesome-copilot/git-commit` | `github/awesome-copilot` | `git-commit` |
| `https://github.com/github/awesome-copilot/tree/main/skills/git-commit` | `github/awesome-copilot` | `git-commit` |
| `https://www.skills.sh/github/awesome-copilot/git-commit` | `github/awesome-copilot` | `git-commit` |

For the short path, `owner/repo` is the first two segments and `skill-name` is the third.
For a full URL, `owner/repo` comes after `github.com/` and `skill-name` is the last path segment.

Then run:

```fish
npx skills add <owner/repo>@<skill-name> --skill <skill-name> -g --agent codex
```

## Chezmoi Integration

`~/.agents/skills` is a symlink to the chezmoi source directory:

```
~/.local/share/chezmoi/dot_agents/the-skills/
```

This means `npx skills add` writes directly into the git-tracked source — no copy step needed.

**Always use this install command:**

```fish
npx skills add <skill-url> --skill <skill-name> -g --agent codex
```

**After any install or update, commit** using the git-commit skill:

```
/git-commit dot_agents/the-skills/<skill-name>/
```

Skills committed to git are available to both agents on all machines after `chezmoi update`.
