from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

from .models import ActionProposal
from .policy import review_action


EXIT_CODES = {"allow": 0, "ask_user": 2, "decline": 3}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="codex-guardian")
    subparsers = parser.add_subparsers(dest="command", required=True)

    review_parser = subparsers.add_parser("review", help="Review an action proposal.")
    review_parser.add_argument("proposal", nargs="?", help="Path to a JSON proposal. Reads stdin when omitted.")
    review_parser.add_argument("--audit-log", help="Optional JSONL audit log path.")
    review_parser.add_argument("--pretty", action="store_true", help="Pretty-print the decision JSON.")

    args = parser.parse_args(argv)

    if args.command == "review":
        proposal_data = _read_json(args.proposal, sys.stdin)
        proposal = ActionProposal.from_mapping(proposal_data)
        decision = review_action(proposal)
        result = decision.to_dict()

        if args.audit_log:
            _append_audit_log(Path(args.audit_log), proposal_data, result)

        indent = 2 if args.pretty else None
        print(json.dumps(result, indent=indent, sort_keys=True))
        return EXIT_CODES.get(decision.decision, 2)

    return 1


def _read_json(path: str | None, stdin: TextIO) -> dict[str, Any]:
    if path:
        raw = Path(path).read_text(encoding="utf-8")
    else:
        raw = stdin.read()

    value = json.loads(raw)
    if not isinstance(value, dict):
        raise SystemExit("Proposal JSON must be an object.")
    return value


def _append_audit_log(path: Path, proposal: dict[str, Any], decision: dict[str, Any]) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "proposal": _redact(proposal),
        "decision": decision,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True))
        handle.write("\n")


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in ("key", "token", "secret", "password")):
                result[key] = "[REDACTED]"
            else:
                result[key] = _redact(item)
        return result

    if isinstance(value, list):
        return [_redact(item) for item in value]

    return value
