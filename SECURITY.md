# Security Policy

Codex Guardian is a policy layer. Treat it as one layer in a larger safety system.

## Current Security Model

- Deterministic rules decide whether an action is allowed, declined, or needs the user.
- High-risk operations should never be silently approved by AI alone.
- Audit logs should not include secret values.
- The CLI and MCP server do not execute proposed commands. They only review action proposals.

## Reporting Issues

If you find a bypass or unsafe default, please open a private security report in your fork or repository host. If private reporting is not available yet, open a public issue without including real secrets or exploit payloads.

## Known Limits

- Codex Guardian cannot intercept every Codex action unless the Codex host is configured to route proposals through it.
- The MVP does not inspect file diffs deeply yet.
- Path checks are conservative string checks, not a full sandbox.
