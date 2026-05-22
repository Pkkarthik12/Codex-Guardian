from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repo_root))

    from codex_guardian.mcp_server import main as run_server

    return run_server()


if __name__ == "__main__":
    raise SystemExit(main())
