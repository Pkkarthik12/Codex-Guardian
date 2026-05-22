from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DecisionValue = str
RiskLevel = str


@dataclass(frozen=True)
class Action:
    type: str = "unknown"
    description: str = ""
    command: str = ""
    paths: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "Action":
        paths_value = value.get("paths", ())
        if isinstance(paths_value, str):
            paths = (paths_value,)
        elif isinstance(paths_value, list):
            paths = tuple(str(item) for item in paths_value)
        else:
            paths = ()

        known = {"type", "description", "command", "paths"}
        metadata = {key: item for key, item in value.items() if key not in known}

        return cls(
            type=str(value.get("type", "unknown")),
            description=str(value.get("description", "")),
            command=str(value.get("command", "")),
            paths=paths,
            metadata=metadata,
        )


@dataclass(frozen=True)
class ActionProposal:
    user_request: str
    action: Action
    context: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "ActionProposal":
        action_value = value.get("action", {})
        if not isinstance(action_value, dict):
            action_value = {"description": str(action_value)}

        context_value = value.get("context", {})
        if not isinstance(context_value, dict):
            context_value = {}

        return cls(
            user_request=str(value.get("user_request", "")),
            action=Action.from_mapping(action_value),
            context=context_value,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_request": self.user_request,
            "action": {
                "type": self.action.type,
                "description": self.action.description,
                "command": self.action.command,
                "paths": list(self.action.paths),
                **self.action.metadata,
            },
            "context": self.context,
        }


@dataclass(frozen=True)
class Decision:
    decision: DecisionValue
    risk_level: RiskLevel
    reasons: tuple[str, ...]
    matched_rules: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "risk_level": self.risk_level,
            "reasons": list(self.reasons),
            "matched_rules": list(self.matched_rules),
        }
