# Codex Guardian

Codex Guardian is an open-source starter project for reviewing proposed Codex actions before they happen.

It is designed around a simple safety loop:

```text
Codex proposes an action
Codex Guardian reviews the action
Guardian returns allow, ask_user, or decline
Codex continues only when the decision is safe
```

This first version is intentionally small and auditable. The core decision engine uses deterministic rules, because hard safety boundaries should not depend only on another AI model. An AI reviewer can be added later as a second opinion for explanations and edge cases.

## What It Can Do

- Review file reads, file edits, shell commands, git operations, network actions, and dependency installs.
- Detect risky patterns like secret access, destructive commands, project-wide deletes, network downloads, and git history rewriting.
- Return machine-readable JSON decisions.
- Write an audit log for every reviewed action.
- Expose a small MCP-style stdio server with a `review_action` tool for Codex workflows.
- Provide a Codex plugin scaffold under `plugins/codex-guardian`.

## Quick Start

```powershell
python -m codex_guardian review examples/safe-file-edit.json
python -m codex_guardian review examples/destructive-command.json
python -m codex_guardian review examples/install-dependency.json --audit-log .guardian-audit.jsonl
```

You should see a JSON response like:

```json
{
  "decision": "ask_user",
  "risk_level": "medium",
  "reasons": [
    "Dependency installation can change the environment and may reach the network."
  ],
  "matched_rules": [
    "dependency_install_requires_user"
  ]
}
```

## Action Proposal Format

```json
{
  "user_request": "Fix the login validation bug",
  "action": {
    "type": "file_edit",
    "description": "Update validation in src/auth/login.py",
    "paths": ["src/auth/login.py"]
  }
}
```

Supported action types:

- `file_read`
- `file_edit`
- `search`
- `shell_command`
- `git`
- `network`
- `dependency_install`
- `unknown`

## CLI Exit Codes

- `0`: allowed
- `2`: ask the user before continuing
- `3`: declined

## Codex Integration

There are two practical integration paths:

1. Use the CLI from a Codex workflow:

```powershell
python -m codex_guardian review action.json
```

2. Install or adapt the plugin scaffold in `plugins/codex-guardian`, which exposes a `review_action` tool through the included MCP server.

Important: this prototype can help Codex ask for review, but true automatic interception of every Codex action depends on host-level Codex support. Until then, use Codex's built-in approval modes for enforcement and Guardian as a reviewer/policy layer.

See [docs/codex-integration.md](docs/codex-integration.md) for details.

## Project Layout

```text
codex_guardian/           Python package
examples/                 Sample action proposals
tests/                    Unit tests
docs/                     Integration and policy notes
plugins/codex-guardian/   Codex plugin scaffold
prompts/                  Optional AI reviewer prompt
```

## Development

```powershell
python -m unittest discover -s tests
python -m codex_guardian review examples/safe-file-edit.json
```

No third-party Python dependencies are required for the MVP.

## License

MIT. See [LICENSE](LICENSE).
