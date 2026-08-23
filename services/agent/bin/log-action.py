#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path("/home/dusty/night-shift")
LOG_DIR = PROJECT_ROOT / "logs" / "agent"


def git_state():
    try:
        branch = subprocess.check_output(
            ["git", "-C", str(PROJECT_ROOT), "branch", "--show-current"],
            text=True
        ).strip()

        commit = subprocess.check_output(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "--short", "HEAD"],
            text=True
        ).strip()

        status = subprocess.check_output(
            ["git", "-C", str(PROJECT_ROOT), "status", "--porcelain"],
            text=True
        ).strip()

        return {
            "branch": branch,
            "commit": commit,
            "working_tree_clean": not bool(status)
        }

    except Exception as error:
        return {
            "error": str(error)
        }


def main():
    parser = argparse.ArgumentParser(
        description="Write a structured Night Shift agent action receipt."
    )

    parser.add_argument("--session", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--details", default="")

    args = parser.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)

    receipt = {
        "id": str(uuid4()),
        "timestamp": now.isoformat(),
        "session": args.session,
        "action": args.action,
        "target": args.target,
        "result": args.result,
        "details": args.details,
        "git": git_state()
    }

    log_file = LOG_DIR / f"{now.date().isoformat()}.jsonl"

    with log_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(receipt) + "\n")

    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
