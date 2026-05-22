# Contributing

Thanks for helping improve Codex Guardian.

## Principles

- Keep safety rules easy to read and easy to test.
- Prefer deterministic blocking rules for destructive or privacy-sensitive actions.
- Use AI review as a second opinion, not as the automatic approval mechanism.
- Remember that `run` and `enforce` can execute allowed commands.
- Add tests for every new policy rule.
- Keep the default install dependency-free when possible.

## Local Checks

```powershell
python -m unittest discover -s tests
python -m codex_guardian run -- echo guardian-ok
```

## Pull Request Checklist

- Explain the safety behavior you changed.
- Add or update examples if the input/output shape changed.
- Add tests for new allow, ask_user, or decline behavior.
- Avoid logging secrets or full environment dumps.
