# Codex Integration

Codex Guardian can be attached to Codex in stages.

## Stage 1: CLI Review

Create an action proposal JSON file and ask Guardian to review it:

```powershell
python -m codex_guardian review action.json --pretty
```

Codex can use this pattern before running a risky command or editing sensitive files.

## Stage 2: MCP Tool

The package includes a minimal stdio MCP server:

```powershell
python -m codex_guardian.mcp_server
```

The included plugin scaffold points at that server from:

```text
plugins/codex-guardian/.mcp.json
```

The exposed tool is:

```text
review_action
```

It accepts the same proposal shape as the CLI and returns a JSON decision.

## Stage 3: Codex Plugin

The plugin scaffold lives at:

```text
plugins/codex-guardian
```

It contains:

- `.codex-plugin/plugin.json`
- `.mcp.json`
- `skills/codex-guardian/SKILL.md`

The skill teaches Codex to call `review_action` before risky actions.

## Important Limit

This project does not magically intercept every Codex operation by itself. It gives Codex a reviewer and policy tool. Hard enforcement still requires one of these:

- Codex running in a restrictive built-in approval mode.
- A host-level Codex hook that routes proposed actions through Guardian.
- A wrapper that refuses to execute actions unless Guardian returns `allow`.

Use Codex's built-in approval modes for real enforcement while this project grows.
