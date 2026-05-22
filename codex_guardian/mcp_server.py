from __future__ import annotations

import json
import sys
from typing import Any

from .models import ActionProposal
from .policy import review_action


SERVER_INFO = {"name": "codex-guardian", "version": "0.1.0"}


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            response = handle_request(request)
        except Exception as exc:  # MCP servers should return JSON-RPC errors, not crash.
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(exc)},
            }

        if response is not None:
            sys.stdout.write(json.dumps(response))
            sys.stdout.write("\n")
            sys.stdout.flush()

    return 0


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")

    if method == "initialize":
        return _result(
            request_id,
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            },
        )

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return _result(
            request_id,
            {
                "tools": [
                    {
                        "name": "review_action",
                        "description": "Review a proposed Codex action and return allow, ask_user, or decline.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "user_request": {"type": "string"},
                                "action": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"type": "string"},
                                        "description": {"type": "string"},
                                        "command": {"type": "string"},
                                        "paths": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                    },
                                    "required": ["type"],
                                },
                                "context": {"type": "object"},
                            },
                            "required": ["user_request", "action"],
                        },
                    }
                ]
            },
        )

    if method == "tools/call":
        params = request.get("params", {})
        if params.get("name") != "review_action":
            return _error(request_id, -32602, "Unknown tool.")

        arguments = params.get("arguments", {})
        proposal = ActionProposal.from_mapping(arguments)
        decision = review_action(proposal).to_dict()
        return _result(
            request_id,
            {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(decision, indent=2, sort_keys=True),
                    }
                ],
                "isError": False,
            },
        )

    return _error(request_id, -32601, f"Unsupported method: {method}")


def _result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


if __name__ == "__main__":
    raise SystemExit(main())
