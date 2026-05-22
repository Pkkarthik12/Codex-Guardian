from __future__ import annotations

import json
import sys
from typing import Any

from .enforcer import enforce_proposal
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
                        "description": "Review a proposed Codex action without executing it.",
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
                    },
                    {
                        "name": "guarded_shell_command",
                        "description": "Review a shell command and automatically execute it only when Codex Guardian allows it.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "user_request": {"type": "string"},
                                "command": {"type": "string"},
                                "cwd": {"type": "string"},
                            },
                            "required": ["user_request", "command"],
                        },
                    },
                ]
            },
        )

    if method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")

        if tool_name == "review_action":
            arguments = params.get("arguments", {})
            proposal = ActionProposal.from_mapping(arguments)
            decision = review_action(proposal).to_dict()
            return _tool_text_result(request_id, decision, is_error=False)

        if tool_name == "guarded_shell_command":
            arguments = params.get("arguments", {})
            proposal = ActionProposal.from_mapping(
                {
                    "user_request": arguments.get("user_request", ""),
                    "action": {
                        "type": "shell_command",
                        "description": f"Run guarded command: {arguments.get('command', '')}",
                        "command": arguments.get("command", ""),
                    },
                }
            )
            result = enforce_proposal(proposal, cwd=arguments.get("cwd") or None, capture_output=True)
            payload = result.to_dict()
            return _tool_text_result(request_id, payload, is_error=result.decision.decision == "decline")

        return _error(request_id, -32602, "Unknown tool.")

    return _error(request_id, -32601, f"Unsupported method: {method}")


def _result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _tool_text_result(request_id: Any, payload: dict[str, Any], *, is_error: bool) -> dict[str, Any]:
    return _result(
        request_id,
        {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(payload, indent=2, sort_keys=True),
                }
            ],
            "isError": is_error,
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
