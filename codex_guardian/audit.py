from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SENSITIVE_KEY_MARKERS = ("key", "token", "secret", "password", "credential")


def append_audit_event(path: str | Path, event: dict[str, Any]) -> None:
    audit_path = Path(path)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **_redact(event),
    }
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True))
        handle.write("\n")


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in SENSITIVE_KEY_MARKERS):
                result[key] = "[REDACTED]"
            else:
                result[key] = _redact(item)
        return result

    if isinstance(value, list):
        return [_redact(item) for item in value]

    return value
