---
name: codex-guardian
description: Review proposed Codex actions with a local policy tool before running risky commands, editing sensitive files, installing dependencies, using network access, or changing git state.
---

# Codex Guardian

Use this skill when a proposed Codex action may need policy review before it runs.

## When To Review

Call the `review_action` MCP tool before:

- Running shell commands that can change files or system state.
- Installing dependencies.
- Accessing the network.
- Editing secret-looking files such as `.env`, credentials, tokens, or SSH keys.
- Running git write operations like commit, push, reset, clean, merge, rebase, checkout, or switch.
- Editing files outside the current project scope.
- Performing any action that feels ambiguous or higher risk.

## Proposal Shape

Send the tool a JSON object:

```json
{
  "user_request": "Fix the login bug",
  "action": {
    "type": "shell_command",
    "description": "Run the test suite",
    "command": "python -m unittest",
    "paths": ["tests"]
  },
  "context": {
    "cwd": "project root"
  }
}
```

Action types:

- `file_read`
- `file_edit`
- `search`
- `shell_command`
- `git`
- `network`
- `dependency_install`
- `unknown`

## Decision Handling

- `allow`: proceed normally.
- `ask_user`: ask the user for approval before continuing.
- `decline`: do not perform the action. Explain the reason briefly and offer a safer alternative.

Never bypass a `decline` decision.
