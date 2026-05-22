# Policy

Codex Guardian returns one of three decisions.

## Decisions

- `allow`: The action looks low risk and matches known safe patterns.
- `ask_user`: The action may be valid, but a human should confirm it first.
- `decline`: The action looks unsafe enough that it should not proceed.

## Risk Levels

- `low`: Normal project read, search, or scoped edit.
- `medium`: Environment changes, network access, unknown actions, git writes.
- `high`: Secret-looking paths or paths outside the workspace.
- `critical`: Destructive commands or secret exposure.

## Default Rules

Allowed by default:

- Reading project files.
- Searching project files.
- Editing project files that do not look sensitive.
- Shell commands that do not match risky patterns.

Ask the user:

- Dependency installs.
- Network commands.
- Git write operations.
- Secret-looking paths.
- Absolute paths or parent directory paths.
- Unknown action types.

Decline:

- Broad destructive commands.
- Git commands that can destroy local work.
- Commands that appear to print secrets or environment variables.

## Future Policy Ideas

- Diff-aware review for file edits.
- User-customizable rules in `guardian-policy.yml`.
- Project-specific allowlists.
- Optional AI reviewer for ambiguous actions.
- Stronger sandbox-aware path validation.
