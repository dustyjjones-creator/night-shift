#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path("/home/dusty/night-shift")
LOG_DIR = PROJECT_ROOT / "logs" / "agent"

READ_ONLY_COMMANDS = {
    "pwd",
    "ls",
    "find",
    "cat",
    "head",
    "tail",
    "grep",
    "rg",
    "sed",
    "git",
    "docker",
    "systemctl",
    "journalctl",
    "whoami",
    "hostname",
    "hostnamectl",
}


def git_state():
    try:
        branch = subprocess.check_output(
            ["git", "-C", str(PROJECT_ROOT), "branch", "--show-current"],
            text=True,
        ).strip()

        commit = subprocess.check_output(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "--short", "HEAD"],
            text=True,
        ).strip()

        status = subprocess.check_output(
            ["git", "-C", str(PROJECT_ROOT), "status", "--porcelain"],
            text=True,
        ).strip()

        return {
            "branch": branch,
            "commit": commit,
            "working_tree_clean": not bool(status),
        }

    except Exception as error:
        return {"error": str(error)}


def write_receipt(receipt):
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_file = LOG_DIR / f"{datetime.now(timezone.utc).date()}.jsonl"

    with log_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(receipt) + "\n")


def command_is_allowed(command):
    if not command:
        return False, "No command provided."

    program = command[0]

    if program not in READ_ONLY_COMMANDS:
        return False, (
            f"Program '{program}' is not allowed in read-only mode."
        )

    if program == "git":
        allowed_subcommands = {
            "status",
            "log",
            "diff",
            "show",
            "branch",
            "remote",
            "rev-parse",
        }

        if len(command) < 2 or command[1] not in allowed_subcommands:
            return False, (
                "Git subcommand is not allowed in read-only mode."
            )

    if program == "docker":
        allowed_subcommands = {
            "ps",
            "inspect",
            "logs",
            "images",
            "compose",
        }

        if len(command) < 2 or command[1] not in allowed_subcommands:
            return False, (
                "Docker subcommand is not allowed in read-only mode."
            )

        if command[1] == "compose":
            allowed_compose = {"config", "ps", "logs"}

            if len(command) < 3 or command[2] not in allowed_compose:
                return False, (
                    "Docker Compose command is not allowed in read-only mode."
                )

    if program == "systemctl":
        allowed_subcommands = {
            "status",
            "cat",
            "show",
            "list-units",
            "list-unit-files",
        }

        if len(command) < 2 or command[1] not in allowed_subcommands:
            return False, (
                "systemctl command is not allowed in read-only mode."
            )

    return True, ""


def main():
    parser = argparse.ArgumentParser(
        description="Execute a Night Shift agent command with audit receipts."
    )

    parser.add_argument("--session", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--target", required=True)

    parser.add_argument(
        "--cwd",
        default=str(PROJECT_ROOT),
        help="Working directory for the command",
    )

    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to execute",
    )

    args = parser.parse_args()

    if not args.command:
        print("No command provided.", file=sys.stderr)
        sys.exit(2)

    command = args.command

    if command[0] == "--":
        command = command[1:]

    if not command:
        print("No command provided.", file=sys.stderr)
        sys.exit(2)

    allowed, reason = command_is_allowed(command)

    if not allowed:
        blocked_receipt = {
            "id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session": args.session,
            "action": args.action,
            "target": args.target,
            "phase": "blocked",
            "result": "blocked",
            "command": command,
            "cwd": args.cwd,
            "reason": reason,
            "git": git_state(),
        }

        write_receipt(blocked_receipt)

        print(
            json.dumps(blocked_receipt, indent=2),
            file=sys.stderr,
        )

        sys.exit(126)

    receipt_id = str(uuid4())
    started = datetime.now(timezone.utc)

    write_receipt({
        "id": receipt_id,
        "timestamp": started.isoformat(),
        "session": args.session,
        "action": args.action,
        "target": args.target,
        "phase": "started",
        "command": command,
        "cwd": args.cwd,
        "git": git_state(),
    })

    try:
        result = subprocess.run(
            command,
            cwd=args.cwd,
            text=True,
            capture_output=True,
            timeout=300,
        )

        ended = datetime.now(timezone.utc)

        receipt = {
            "id": str(uuid4()),
            "parent_id": receipt_id,
            "timestamp": ended.isoformat(),
            "session": args.session,
            "action": args.action,
            "target": args.target,
            "phase": "completed",
            "result": (
                "success" if result.returncode == 0 else "failure"
            ),
            "exit_code": result.returncode,
            "command": command,
            "cwd": args.cwd,
            "stdout": result.stdout[-5000:],
            "stderr": result.stderr[-5000:],
            "duration_seconds": round(
                (ended - started).total_seconds(),
                3,
            ),
            "git": git_state(),
        }

        write_receipt(receipt)

        print(json.dumps(receipt, indent=2))

        sys.exit(result.returncode)

    except subprocess.TimeoutExpired as error:
        ended = datetime.now(timezone.utc)

        stdout = error.stdout or ""
        stderr = error.stderr or ""

        if isinstance(stdout, bytes):
            stdout = stdout.decode(errors="replace")

        if isinstance(stderr, bytes):
            stderr = stderr.decode(errors="replace")

        receipt = {
            "id": str(uuid4()),
            "parent_id": receipt_id,
            "timestamp": ended.isoformat(),
            "session": args.session,
            "action": args.action,
            "target": args.target,
            "phase": "completed",
            "result": "timeout",
            "command": command,
            "cwd": args.cwd,
            "duration_seconds": round(
                (ended - started).total_seconds(),
                3,
            ),
            "stdout": stdout[-5000:],
            "stderr": stderr[-5000:],
            "git": git_state(),
        }

        write_receipt(receipt)

        print(json.dumps(receipt, indent=2))
        sys.exit(124)


if __name__ == "__main__":
    main()
