# Codex Integration

Codex Guardian now has an enforcement path, not just a review path.

## Direct CLI Gate

Use this when you want Codex or a script to run commands through Guardian:

```powershell
python -m codex_guardian run -- echo guardian-ok
```

Behavior:

- `allow`: command runs automatically.
- `ask_user`: command is blocked by default.
- `decline`: command is blocked always.

For interactive approval of `ask_user` commands:

```powershell
python -m codex_guardian run --interactive -- python tools/task.py
```

## Proposal Gate

Codex can write an action proposal JSON and ask Guardian to enforce it:

```powershell
python -m codex_guardian enforce action.json --json
```

Only `shell_command` actions are executed by the built-in runner. File edits, reads, and searches are reviewed so the caller can enforce the decision.

## MCP Tool

The package includes a small stdio MCP server:

```powershell
python -m codex_guardian.mcp_server
```

The plugin scaffold at `plugins/codex-guardian` exposes two tools:

- `review_action`
- `guarded_shell_command`

`guarded_shell_command` is the automatic gate. It executes only when policy returns `allow`.

## Important Limit

Codex Guardian can enforce commands that are routed through it. It cannot magically intercept commands that bypass it.

Use one of these patterns:

- Ask Codex to use `codex-guardian run -- <command>` for shell commands.
- Configure Codex/plugin workflows to call `guarded_shell_command`.
- Keep Codex's normal approval settings enabled for actions that are not routed through Guardian.
