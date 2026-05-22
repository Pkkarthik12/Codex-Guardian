from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePath

from .models import ActionProposal, Decision


RISK_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}
DECISION_ORDER = {"allow": 1, "ask_user": 2, "decline": 3}

SECRET_PATH_MARKERS = (
    ".env",
    ".npmrc",
    ".pypirc",
    ".netrc",
    ".ssh",
    "id_rsa",
    "id_dsa",
    "credentials",
    "credential",
    "private_key",
    "secret",
    "secrets",
    "token",
)

DESTRUCTIVE_COMMAND_PATTERNS = (
    r"\brm\s+(-[^\n]*r|-[^\n]*f|/[sq])",
    r"\bremove-item\b[^\n]*(?:-recurse|-force)",
    r"\brmdir\b[^\n]*(?:/s|-r)",
    r"\brd\b[^\n]*/s",
    r"\bdel\b[^\n]*/s",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\b[^\n]*(?:-f|-x|-d)",
    r"\bformat\b\s+[a-z]:",
    r"\bmkfs(?:\.[a-z0-9]+)?\b",
)

DEPENDENCY_OR_NETWORK_PATTERNS = (
    r"\bnpm\s+(?:install|i|add)\b",
    r"\byarn\s+(?:add|install)\b",
    r"\bpnpm\s+(?:add|install)\b",
    r"\bpip(?:x|3)?\s+install\b",
    r"\bpoetry\s+add\b",
    r"\buv\s+add\b",
    r"\bcargo\s+install\b",
    r"\bgo\s+get\b",
    r"\bcurl\b",
    r"\bwget\b",
    r"\binvoke-webrequest\b",
    r"\binvoke-restmethod\b",
    r"\birm\b",
    r"\biwr\b",
    r"\bdocker\s+pull\b",
)

GIT_WRITE_PATTERNS = (
    r"\bgit\s+commit\b",
    r"\bgit\s+push\b",
    r"\bgit\s+tag\b",
    r"\bgit\s+merge\b",
    r"\bgit\s+rebase\b",
    r"\bgit\s+checkout\b",
    r"\bgit\s+switch\b",
)

SECRET_EXPOSURE_PATTERNS = (
    r"\b(?:cat|type|get-content)\b[^\n]*(?:\.env|id_rsa|credentials|secret|token)",
    r"\b(?:printenv|set)\b",
    r"\becho\s+\$env:",
    r"\becho\s+\$[A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD)",
)


@dataclass
class RuleHit:
    decision: str
    risk_level: str
    reason: str
    rule: str


def review_action(proposal: ActionProposal) -> Decision:
    hits: list[RuleHit] = []
    action = proposal.action
    action_type = action.type.lower().strip() or "unknown"
    command = _normalize_command(action.command)
    all_text = " ".join([proposal.user_request, action.description, action.command])

    if any(_path_looks_secret(path) for path in action.paths):
        hits.append(
            RuleHit(
                "ask_user",
                "high",
                "The action touches a path that looks like it may contain secrets.",
                "secret_path_requires_user",
            )
        )

    if any(_path_escapes_workspace(path) for path in action.paths):
        hits.append(
            RuleHit(
                "ask_user",
                "high",
                "The action references a parent or absolute path, so the user should confirm the scope.",
                "workspace_escape_requires_user",
            )
        )

    if action_type in {"file_read", "search"}:
        hits.append(
            RuleHit(
                "allow",
                "low",
                "Reading or searching project files is normally safe.",
                "project_read_allowed",
            )
        )

    elif action_type == "file_edit":
        hits.append(
            RuleHit(
                "allow",
                "low",
                "The action is a file edit inside the project proposal.",
                "project_file_edit_allowed",
            )
        )

    elif action_type == "dependency_install":
        hits.append(
            RuleHit(
                "ask_user",
                "medium",
                "Dependency installation can change the environment and may reach the network.",
                "dependency_install_requires_user",
            )
        )

    elif action_type == "network":
        hits.append(
            RuleHit(
                "ask_user",
                "medium",
                "Network access can send or receive data outside the project.",
                "network_requires_user",
            )
        )

    elif action_type == "git":
        hits.append(_review_git_command(command))

    elif action_type == "shell_command":
        hits.extend(_review_shell_command(command))

    else:
        hits.append(
            RuleHit(
                "ask_user",
                "medium",
                "Unknown action types should be reviewed by the user.",
                "unknown_action_requires_user",
            )
        )

    if _matches_any(all_text.lower(), SECRET_EXPOSURE_PATTERNS):
        hits.append(
            RuleHit(
                "decline",
                "critical",
                "The action appears to expose secrets or environment variables.",
                "secret_exposure_declined",
            )
        )

    return _combine_hits(hits)


def _review_shell_command(command: str) -> list[RuleHit]:
    if not command:
        return [
            RuleHit(
                "ask_user",
                "medium",
                "Shell commands without a command string need user review.",
                "empty_shell_command_requires_user",
            )
        ]

    hits: list[RuleHit] = []

    if _matches_any(command, DESTRUCTIVE_COMMAND_PATTERNS):
        hits.append(
            RuleHit(
                "decline",
                "critical",
                "The shell command looks destructive or can delete many files.",
                "destructive_shell_command_declined",
            )
        )

    if _matches_any(command, DEPENDENCY_OR_NETWORK_PATTERNS):
        hits.append(
            RuleHit(
                "ask_user",
                "medium",
                "The shell command can install dependencies or access the network.",
                "network_or_dependency_shell_requires_user",
            )
        )

    if _matches_any(command, GIT_WRITE_PATTERNS):
        hits.append(_review_git_command(command))

    if not hits:
        hits.append(
            RuleHit(
                "allow",
                "low",
                "The shell command does not match known risky patterns.",
                "safe_shell_command_allowed",
            )
        )

    return hits


def _review_git_command(command: str) -> RuleHit:
    if re.search(r"\bgit\s+(?:reset\s+--hard|clean\b)", command):
        return RuleHit(
            "decline",
            "critical",
            "The git command can destroy local work or rewrite the working tree.",
            "destructive_git_declined",
        )

    return RuleHit(
        "ask_user",
        "medium",
        "Git write operations should be confirmed by the user.",
        "git_write_requires_user",
    )


def _combine_hits(hits: list[RuleHit]) -> Decision:
    if not hits:
        hits = [
            RuleHit(
                "ask_user",
                "medium",
                "No policy rule matched, so the user should decide.",
                "no_rule_requires_user",
            )
        ]

    decision = max((hit.decision for hit in hits), key=lambda item: DECISION_ORDER[item])
    risk_level = max((hit.risk_level for hit in hits), key=lambda item: RISK_ORDER[item])

    return Decision(
        decision=decision,
        risk_level=risk_level,
        reasons=tuple(dict.fromkeys(hit.reason for hit in hits)),
        matched_rules=tuple(dict.fromkeys(hit.rule for hit in hits)),
    )


def _normalize_command(command: str) -> str:
    return " ".join(command.lower().strip().split())


def _matches_any(value: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, value, flags=re.IGNORECASE) for pattern in patterns)


def _path_looks_secret(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return any(marker in normalized for marker in SECRET_PATH_MARKERS)


def _path_escapes_workspace(path: str) -> bool:
    if not path:
        return False

    normalized = path.replace("\\", "/")
    pure_path = PurePath(normalized)
    return pure_path.is_absolute() or ".." in pure_path.parts
