# Codex Guardian

Codex Guardian is an open-source automatic approval gate for coding agents.

It does not only review actions. It can sit in front of a command, decide whether the action is safe, and automatically run only the actions that pass policy.

```text
Codex proposes a command
Codex Guardian checks policy
allow      -> command runs automatically
ask_user   -> command is blocked unless interactive approval is enabled
decline    -> command never runs
```

The core is deterministic and dependency-free. AI review can be added later, but the first safety boundary is plain code that anyone can audit.

## What It Does Now

- Automatically executes allowlisted low-risk shell commands.
- Blocks destructive commands like recursive deletes and dangerous git cleanup.
- Blocks uncertain commands unless the user explicitly approves them in interactive mode.
- Detects dependency installs, network calls, secret-looking paths, and secret exposure patterns.
- Writes JSON audit logs.
- Exposes an MCP-style `guarded_shell_command` tool for Codex/plugin workflows.

## Quick Start

Review only:

```powershell
python -m codex_guardian review examples/auto-allowed-command.json --pretty
```

Automatically gate and run a command:

```powershell
python -m codex_guardian run -- echo guardian-ok
```

Run from a proposal file:

```powershell
python -m codex_guardian enforce examples/auto-allowed-command.json --json
```

Block dangerous commands:

```powershell
python -m codex_guardian enforce examples/declined-command.json --json
```

## Decisions

- `allow`: safe enough to run automatically.
- `ask_user`: not automatically allowed; blocked by default.
- `decline`: unsafe; never run.

Exit codes:

- `0`: allowed, or allowed command finished with exit code 0.
- `2`: user approval required and not granted.
- `3`: declined by policy.
- Any other code: the allowed command ran and returned that process exit code.

## Proposal Format

```json
{
  "user_request": "Run the test suite",
  "action": {
    "type": "shell_command",
    "description": "Run unit tests",
    "command": "python -m unittest discover -s tests",
    "paths": ["tests"]
  }
}
```

Supported action types:

- `shell_command`
- `file_read`
- `file_edit`
- `search`
- `git`
- `network`
- `dependency_install`
- `unknown`

Only `shell_command` actions can be executed by the built-in runner. Other action types are reviewed and returned as decisions for Codex or another wrapper to enforce.

## Automatic Allowlist

The default automatic runner is conservative. It auto-runs commands like:

- `python -m unittest ...`
- `python -m compileall ...`
- `git status`
- `dir`, `ls`, `pwd`, `Get-Location`
- simple literal `echo ...`

It does not auto-run arbitrary scripts, dependency installs, network commands, git writes, or destructive commands.

## Codex Integration

The plugin scaffold is in:

```text
plugins/codex-guardian
```

It exposes:

- `review_action`: decision only.
- `guarded_shell_command`: decision plus automatic execution only when policy returns `allow`.

This gives Codex a real gate to call instead of running a command directly. Full host-level interception still depends on how Codex is configured, so the safest pattern is: route risky commands through `codex-guardian run` or the MCP `guarded_shell_command` tool.

## Development

```powershell
python -m unittest discover -s tests
python -m codex_guardian run -- echo guardian-ok
```

No third-party Python dependencies are required.

## Project Layout

```text
codex_guardian/           Policy engine, CLI, enforcer, MCP server
examples/                 Sample action proposals
tests/                    Unit tests
docs/                     Integration and policy notes
plugins/codex-guardian/   Codex plugin scaffold
```

## License

MIT. See [LICENSE](LICENSE).
