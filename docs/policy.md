# Policy

Codex Guardian is strict by default because it can execute commands automatically.

## Decisions

- `allow`: execute automatically.
- `ask_user`: block unless interactive approval is enabled.
- `decline`: block always.

## Default Automatic Allowlist

Allowed:

- `python -m unittest ...`
- `python -m compileall ...`
- `git status`
- `dir`, `ls`, `pwd`, `Get-Location`
- simple literal `echo ...`
- normal project file reads/searches when reviewed as proposals
- scoped project file edits when reviewed as proposals

Ask user:

- arbitrary shell commands
- dependency installs
- network commands
- git write operations
- absolute paths or parent-directory paths
- secret-looking paths
- unknown action types

Decline:

- broad destructive deletes
- dangerous git cleanup/reset commands
- commands that appear to print secrets or environment variables

## Why Unknown Commands Are Not Auto-Allowed

An unknown command can run arbitrary code. For example:

```powershell
python tools/task.py
```

That may be completely valid, but the automatic gate cannot know that safely from the command string alone. So it returns `ask_user` unless the policy is extended.

## Future Policy Ideas

- Project-specific `guardian-policy.yml`.
- Diff-aware file edit checks.
- Command parser for safer shell analysis.
- Optional AI second opinion for ambiguous actions.
- Signed policy bundles for teams.
