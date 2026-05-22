from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, TextIO

from .audit import append_audit_event
from .enforcer import GATE_EXIT_CODES, enforce_proposal
from .models import ActionProposal
from .policy import review_action


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="codex-guardian")
    subparsers = parser.add_subparsers(dest="command", required=True)

    review_parser = subparsers.add_parser("review", help="Review an action proposal without executing it.")
    review_parser.add_argument("proposal", nargs="?", help="Path to a JSON proposal. Reads stdin when omitted.")
    review_parser.add_argument("--audit-log", help="Optional JSONL audit log path.")
    review_parser.add_argument("--pretty", action="store_true", help="Pretty-print the decision JSON.")

    enforce_parser = subparsers.add_parser("enforce", help="Review a proposal and execute allowed shell actions.")
    enforce_parser.add_argument("proposal", help="Path to a JSON action proposal.")
    enforce_parser.add_argument("--audit-log", help="Optional JSONL audit log path.")
    enforce_parser.add_argument("--cwd", help="Working directory for command execution.")
    enforce_parser.add_argument("--dry-run", action="store_true", help="Review but do not execute.")
    enforce_parser.add_argument("--interactive", action="store_true", help="Ask before running ask_user actions.")
    enforce_parser.add_argument("--json", action="store_true", help="Print a JSON gate result.")

    run_parser = subparsers.add_parser("run", help="Automatically gate and run a shell command.")
    run_parser.add_argument("--user-request", default="Run a guarded shell command.")
    run_parser.add_argument("--audit-log", help="Optional JSONL audit log path.")
    run_parser.add_argument("--cwd", help="Working directory for command execution.")
    run_parser.add_argument("--dry-run", action="store_true", help="Review but do not execute.")
    run_parser.add_argument("--interactive", action="store_true", help="Ask before running ask_user commands.")
    run_parser.add_argument("--json", action="store_true", help="Print a JSON gate result.")
    run_parser.add_argument("shell_command", nargs=argparse.REMAINDER, help="Command to run after --.")

    args = parser.parse_args(argv)

    if args.command == "review":
        proposal_data = _read_json(args.proposal, sys.stdin)
        proposal = ActionProposal.from_mapping(proposal_data)
        decision = review_action(proposal)
        result = decision.to_dict()

        if args.audit_log:
            append_audit_event(args.audit_log, {"proposal": proposal_data, "decision": result})

        indent = 2 if args.pretty else None
        print(json.dumps(result, indent=indent, sort_keys=True))
        return GATE_EXIT_CODES.get(decision.decision, 2)

    if args.command == "enforce":
        proposal_data = _read_json(args.proposal, sys.stdin)
        proposal = ActionProposal.from_mapping(proposal_data)
        result = enforce_proposal(
            proposal,
            cwd=args.cwd,
            interactive=args.interactive,
            dry_run=args.dry_run,
            capture_output=args.json,
        )
        if args.audit_log:
            append_audit_event(args.audit_log, {"proposal": proposal_data, "gate_result": result.to_dict()})
        _print_gate_result(result, as_json=args.json)
        return result.exit_code

    if args.command == "run":
        command = _join_remainder(args.shell_command)
        if not command:
            raise SystemExit("Provide a command after --, for example: codex-guardian run -- git status")
        proposal = ActionProposal.from_mapping(
            {
                "user_request": args.user_request,
                "action": {
                    "type": "shell_command",
                    "description": f"Run guarded command: {command}",
                    "command": command,
                },
            }
        )
        result = enforce_proposal(
            proposal,
            cwd=args.cwd,
            interactive=args.interactive,
            dry_run=args.dry_run,
            capture_output=args.json,
        )
        if args.audit_log:
            append_audit_event(args.audit_log, {"proposal": proposal.to_dict(), "gate_result": result.to_dict()})
        _print_gate_result(result, as_json=args.json)
        return result.exit_code

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


def _join_remainder(parts: list[str]) -> str:
    if parts and parts[0] == "--":
        parts = parts[1:]
    return " ".join(parts).strip()


def _print_gate_result(result: Any, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return

    decision = result.decision.decision
    if result.executed:
        print(f"Codex Guardian: allowed and executed. Exit code: {result.exit_code}")
    elif decision == "allow":
        print("Codex Guardian: allowed. No shell command was executed.")
    elif decision == "ask_user":
        print("Codex Guardian: blocked until user approval.")
    else:
        print("Codex Guardian: declined.")

    for reason in result.decision.reasons:
        print(f"- {reason}")
