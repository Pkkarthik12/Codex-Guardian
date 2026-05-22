---
name: codex-guardian
description: Gate proposed Codex shell commands with a local policy tool that automatically executes allowed commands and blocks unsafe commands.
---

# Codex Guardian

Use this skill when Codex is about to run a shell command or perform a risky action.

## Preferred Tool

Use `guarded_shell_command` instead of running shell commands directly.

Input:

```json
{
  "user_request": "Run the tests",
  "command": "python -m unittest discover -s tests",
  "cwd": "project root"
}
```

Behavior:

- `allow`: the tool executes the command automatically.
- `ask_user`: the tool blocks by default.
- `decline`: the tool blocks always.

## Review Only

Use `review_action` when Codex only needs a decision and another system will enforce it.

## When To Gate

Call Guardian before:

- Running shell commands.
- Installing dependencies.
- Accessing the network.
- Editing secret-looking files such as `.env`, credentials, tokens, or SSH keys.
- Running git write operations like commit, push, reset, clean, merge, rebase, checkout, or switch.
- Editing files outside the current project scope.

Never bypass a `decline` decision.
