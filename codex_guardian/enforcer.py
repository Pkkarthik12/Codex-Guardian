from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import ActionProposal, Decision
from .policy import review_action


GATE_EXIT_CODES = {"allow": 0, "ask_user": 2, "decline": 3}


@dataclass(frozen=True)
class GateResult:
    decision: Decision
    executed: bool
    approved_by_user: bool
    exit_code: int
    stdout: str = ""
    stderr: str = ""

    def to_dict(self, include_output: bool = True) -> dict[str, Any]:
        result: dict[str, Any] = {
            "decision": self.decision.decision,
            "risk_level": self.decision.risk_level,
            "reasons": list(self.decision.reasons),
            "matched_rules": list(self.decision.matched_rules),
            "executed": self.executed,
            "approved_by_user": self.approved_by_user,
            "exit_code": self.exit_code,
        }
        if include_output:
            result["stdout"] = self.stdout
            result["stderr"] = self.stderr
        return result


def enforce_proposal(
    proposal: ActionProposal,
    *,
    cwd: str | Path | None = None,
    interactive: bool = False,
    dry_run: bool = False,
    capture_output: bool = False,
) -> GateResult:
    decision = review_action(proposal)

    if decision.decision == "decline":
        return GateResult(decision, executed=False, approved_by_user=False, exit_code=GATE_EXIT_CODES["decline"])

    approved_by_user = False
    if decision.decision == "ask_user":
        if not interactive or not _confirm(proposal):
            return GateResult(decision, executed=False, approved_by_user=False, exit_code=GATE_EXIT_CODES["ask_user"])
        approved_by_user = True

    action = proposal.action
    if action.type.lower().strip() != "shell_command":
        return GateResult(
            decision,
            executed=False,
            approved_by_user=approved_by_user,
            exit_code=GATE_EXIT_CODES["allow"],
            stderr="Approved, but this runner only executes shell_command actions.",
        )

    if dry_run:
        return GateResult(decision, executed=False, approved_by_user=approved_by_user, exit_code=GATE_EXIT_CODES["allow"])

    completed = subprocess.run(
        action.command,
        cwd=str(cwd) if cwd else None,
        shell=True,
        text=True,
        capture_output=capture_output,
        check=False,
    )

    return GateResult(
        decision,
        executed=True,
        approved_by_user=approved_by_user,
        exit_code=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
    )


def _confirm(proposal: ActionProposal) -> bool:
    action = proposal.action
    print("Codex Guardian needs user approval before running this action.")
    print(f"Action: {action.description or action.type}")
    if action.command:
        print(f"Command: {action.command}")
    answer = input("Allow this action? [y/N] ").strip().lower()
    return answer in {"y", "yes"}
