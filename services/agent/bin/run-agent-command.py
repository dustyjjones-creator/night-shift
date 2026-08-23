#!/usr/bin/env python3

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FOR_IMPORTS))

from services.agent.lib.redaction import redact_value


PROJECT_ROOT = Path("/home/dusty/night-shift").resolve()
LOG_DIR = PROJECT_ROOT / "logs" / "agent"


def is_within_project(path):
    """Return whether a path resolves within the Night Shift project."""
    try:
        path.resolve(strict=False).relative_to(PROJECT_ROOT)
        return True
    except (OSError, ValueError):
        return False


def validate_project_path(value, cwd):
    """Validate a filesystem operand, including traversal and symlink checks."""
    path = Path(value)

    if not path.is_absolute():
        path = cwd / path

    if not is_within_project(path):
        return False, f"Path '{value}' resolves outside the project root."

    return True, ""


def validate_paths(values, cwd):
    for value in values:
        valid, reason = validate_project_path(value, cwd)

        if not valid:
            return valid, reason

    return True, ""


def validate_no_options(command, cwd):
    if len(command) != 1:
        return False, f"{command[0]} does not accept arguments in read-only mode."

    return True, ""


def validate_ls(command, cwd):
    allowed_flags = {
        "-a", "-A", "-l", "-h", "-1",
        "-d", "-t", "-r", "-S", "-X",
    }

    paths = []

    for argument in command[1:]:
        if argument.startswith("-"):
            if argument == "--" or argument not in allowed_flags:
                return False, "ls option is not allowed in read-only mode."
        else:
            paths.append(argument)

    return validate_paths(paths, cwd)


def validate_find(command, cwd):
    if len(command) < 2 or command[1].startswith("-"):
        return False, "find requires exactly one project-relative start path."

    valid, reason = validate_project_path(command[1], cwd)

    if not valid:
        return valid, reason

    value_predicates = {
        "-maxdepth", "-mindepth",
        "-name", "-iname",
        "-path", "-ipath",
        "-type", "-mtime",
        "-mmin", "-size",
    }

    no_value_predicates = {
        "-empty", "-print", "-print0",
    }

    index = 2

    while index < len(command):
        argument = command[index]

        if argument in value_predicates:
            if index + 1 >= len(command):
                return False, f"find option '{argument}' requires a value."

            index += 2

        elif argument in no_value_predicates:
            index += 1

        else:
            return False, (
                f"find expression '{argument}' is not allowed "
                "in read-only mode."
            )

    return True, ""


def validate_cat(command, cwd):
    if len(command) < 2 or any(
        value.startswith("-") for value in command[1:]
    ):
        return False, "cat only accepts project file paths in read-only mode."

    return validate_paths(command[1:], cwd)


def validate_head_or_tail(command, cwd):
    paths = []
    index = 1

    while index < len(command):
        argument = command[index]

        if argument in {"-n", "-c", "--lines", "--bytes"}:
            if index + 1 >= len(command):
                return False, (
                    f"{command[0]} option '{argument}' requires a value."
                )

            index += 2

        elif (
            argument.startswith("--lines=")
            or argument.startswith("--bytes=")
        ):
            index += 1

        elif argument in {"-q", "--quiet", "--silent"}:
            index += 1

        elif argument.startswith("-"):
            return False, (
                f"{command[0]} option '{argument}' is not allowed."
            )

        else:
            paths.append(argument)
            index += 1

    if not paths:
        return False, (
            f"{command[0]} requires at least one project file path."
        )

    return validate_paths(paths, cwd)


def validate_grep(command, cwd):
    allowed_flags = {
        "-E", "-F", "-G",
        "-i", "-v", "-n",
        "-H", "-h",
        "-r", "-l", "-L",
        "-c", "-w", "-x",
    }

    index = 1

    while index < len(command) and command[index].startswith("-"):
        argument = command[index]

        if argument not in allowed_flags:
            return False, (
                f"grep option '{argument}' is not allowed "
                "in read-only mode."
            )

        index += 1

    if index >= len(command):
        return False, "grep requires a search pattern."

    index += 1
    paths = command[index:]

    if not paths:
        return False, (
            "grep requires at least one project file path."
        )

    return validate_paths(paths, cwd)


def validate_rg(command, cwd):
    flags_without_values = {
        "--files", "--hidden", "--no-ignore",
        "-n", "-i", "-l", "-c",
        "-F", "-w", "-x",
    }

    flags_with_values = {
        "-g", "--glob", "--type",
    }

    index = 1
    files_mode = False

    while index < len(command) and command[index].startswith("-"):
        argument = command[index]

        if argument in flags_without_values:
            files_mode = files_mode or argument == "--files"
            index += 1

        elif argument in flags_with_values:
            if index + 1 >= len(command):
                return False, (
                    f"rg option '{argument}' requires a value."
                )

            index += 2

        else:
            return False, (
                f"rg option '{argument}' is not allowed "
                "in read-only mode."
            )

    if files_mode:
        return validate_paths(command[index:], cwd)

    if index >= len(command):
        return False, "rg requires a search pattern or --files."

    return validate_paths(command[index + 1:], cwd)


def validate_sed(command, cwd):
    if len(command) < 4 or command[1] != "-n":
        return False, (
            "sed is limited to "
            "'sed -n ADDRESSp FILE...' in read-only mode."
        )

    script = command[2]

    if not re.fullmatch(
        r"(?:[0-9]+(?:,[0-9]+)?|\$)?p",
        script,
    ):
        return False, (
            "sed script is not a permitted print-only expression."
        )

    if any(value.startswith("-") for value in command[3:]):
        return False, (
            "sed options are not allowed after the print-only script."
        )

    return validate_paths(command[3:], cwd)


def validate_git(command, cwd):
    if len(command) < 2:
        return False, "git requires an allowed read-only subcommand."

    subcommand = command[1]
    arguments = command[2:]

    allowed = {
        "status": {
            "--short", "--porcelain",
            "--branch", "--ignored",
        },
        "log": {
            "--oneline", "--stat",
            "--shortstat", "--name-only",
            "--name-status", "--all",
        },
        "diff": {
            "--stat", "--name-only",
            "--name-status", "--cached",
            "--staged",
        },
        "show": {
            "--stat", "--name-only",
            "--name-status", "--oneline",
        },
        "branch": {
            "--show-current", "--all", "--list",
        },
        "remote": {
            "-v",
        },
        "rev-parse": {
            "--short", "--show-toplevel",
            "--is-inside-work-tree",
            "--verify",
        },
    }

    if subcommand not in allowed:
        return False, (
            "Git subcommand is not allowed in read-only mode."
        )

    if subcommand == "branch":
        if any(
            argument not in allowed[subcommand]
            for argument in arguments
        ):
            return False, (
                "git branch only permits listing options "
                "in read-only mode."
            )

        return True, ""

    if subcommand == "remote":
        if not arguments or arguments == ["-v"]:
            return True, ""

        if (
            len(arguments) == 2
            and arguments[0] == "get-url"
            and not arguments[1].startswith("-")
            and "/" not in arguments[1]
        ):
            return True, ""

        return False, (
            "git remote only permits listing or get-url "
            "in read-only mode."
        )

    paths = []
    after_separator = False

    for argument in arguments:
        if argument == "--":
            if after_separator:
                return False, (
                    "Repeated git path separator is not allowed."
                )

            after_separator = True

        elif after_separator:
            paths.append(argument)

        elif (
            argument in allowed[subcommand]
            or argument.startswith("--format=")
            or argument.startswith("--pretty=")
            or argument.startswith("--max-count=")
            or re.fullmatch(r"-[0-9]+", argument)
        ):
            continue

        elif argument.startswith("-"):
            return False, (
                f"git option '{argument}' is not allowed "
                "in read-only mode."
            )

        elif subcommand in {
            "log", "show", "diff", "rev-parse"
        }:
            if "/" in argument or argument in {".", ".."}:
                return False, (
                    "Ambiguous git argument is not allowed "
                    "without '--'."
                )

        else:
            return False, f"git argument '{argument}' is not allowed."

    return validate_paths(paths, cwd)


def validate_docker(command, cwd):
    if len(command) < 2:
        return False, (
            "docker requires an allowed read-only subcommand."
        )

    subcommand = command[1]
    arguments = command[2:]

    allowed_options = {
        "ps": {
            "-a", "--all",
            "-q", "--quiet",
            "--no-trunc",
        },
        "inspect": set(),
        "logs": {
            "-t", "--timestamps",
        },
        "images": {
            "-a", "--all",
            "-q", "--quiet",
            "--no-trunc",
        },
    }

    if subcommand in allowed_options:
        for argument in arguments:
            if (
                argument in allowed_options[subcommand]
                or argument.startswith("--format=")
                or argument.startswith("--tail=")
                or argument.startswith("--since=")
                or argument.startswith("--until=")
                or not argument.startswith("-")
            ):
                continue

            return False, (
                f"docker {subcommand} option "
                f"'{argument}' is not allowed."
            )

        return True, ""

    if subcommand != "compose" or len(arguments) < 1:
        return False, (
            "Docker subcommand is not allowed in read-only mode."
        )

    compose_command = arguments[0]

    if compose_command not in {"config", "ps", "logs"}:
        return False, (
            "Docker Compose command is not allowed "
            "in read-only mode."
        )

    for argument in arguments[1:]:
        if (
            argument in {
                "-q", "--quiet",
                "-a", "--all",
                "--services",
                "-t", "--timestamps",
            }
            or argument.startswith("--format=")
            or argument.startswith("--tail=")
            or argument.startswith("--since=")
            or argument.startswith("--until=")
            or not argument.startswith("-")
        ):
            continue

        return False, (
            f"docker compose {compose_command} option "
            f"'{argument}' is not allowed."
        )

    return True, ""


def validate_systemctl(command, cwd):
    if len(command) < 2:
        return False, (
            "systemctl requires an allowed read-only subcommand."
        )

    subcommand = command[1]

    if subcommand not in {
        "status", "cat", "show",
        "list-units", "list-unit-files",
    }:
        return False, (
            "systemctl command is not allowed in read-only mode."
        )

    for argument in command[2:]:
        if (
            argument in {"--no-pager", "--all"}
            or argument.startswith("--type=")
            or argument.startswith("--state=")
            or argument.startswith("--property=")
        ):
            continue

        if (
            argument.startswith("-")
            or "/" in argument
            or argument in {".", ".."}
        ):
            return False, (
                "systemctl argument is not allowed "
                "in read-only mode."
            )

    return True, ""


def validate_journalctl(command, cwd):
    flags_without_values = {
        "--no-pager",
        "--reverse", "-r",
        "-k", "--dmesg",
        "-b",
    }

    flags_with_values = {
        "-u", "--unit",
        "--since", "--until",
        "-n", "--lines",
        "-p", "--priority",
        "-o", "--output",
        "-g", "--grep",
    }

    safe_outputs = {
        "short", "short-iso",
        "short-precise", "short-unix",
        "short-full", "verbose",
        "export", "json",
        "json-pretty", "json-sse",
        "cat",
    }

    index = 1

    while index < len(command):
        argument = command[index]

        if argument in flags_without_values:
            index += 1

        elif argument in flags_with_values:
            if index + 1 >= len(command):
                return False, (
                    f"journalctl option '{argument}' requires a value."
                )

            value = command[index + 1]

            if (
                argument in {"-u", "--unit"}
                and ("/" in value or value in {".", ".."})
            ):
                return False, (
                    "journalctl unit must be a unit name, not a path."
                )

            if (
                argument in {"-o", "--output"}
                and value not in safe_outputs
            ):
                return False, (
                    "journalctl output mode is not allowed."
                )

            index += 2

        elif (
            argument.startswith("--lines=")
            or argument.startswith("--since=")
            or argument.startswith("--until=")
            or argument.startswith("--priority=")
            or argument.startswith("--grep=")
        ):
            index += 1

        elif argument.startswith("--output="):
            if argument.split("=", 1)[1] not in safe_outputs:
                return False, (
                    "journalctl output mode is not allowed."
                )

            index += 1

        else:
            return False, (
                f"journalctl option '{argument}' is not allowed "
                "in read-only mode."
            )

    return True, ""


def git_state():
    try:
        branch = subprocess.check_output(
            [
                "git",
                "-C",
                str(PROJECT_ROOT),
                "branch",
                "--show-current",
            ],
            text=True,
        ).strip()

        commit = subprocess.check_output(
            [
                "git",
                "-C",
                str(PROJECT_ROOT),
                "rev-parse",
                "--short",
                "HEAD",
            ],
            text=True,
        ).strip()

        status = subprocess.check_output(
            [
                "git",
                "-C",
                str(PROJECT_ROOT),
                "status",
                "--porcelain",
            ],
            text=True,
        ).strip()

        return {
            "branch": branch,
            "commit": commit,
            "working_tree_clean": not bool(status),
        }

    except Exception as error:
        return {
            "error": str(error),
        }


def write_receipt(receipt):
    """Redact sensitive values and append the receipt to the JSONL audit log."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    safe_receipt = redact_value(receipt)

    log_file = (
        LOG_DIR
        / f"{datetime.now(timezone.utc).date()}.jsonl"
    )

    with log_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(safe_receipt) + "\n")

    return safe_receipt


def command_is_allowed(command, cwd):
    if not command:
        return False, "No command provided."

    validators = {
        "pwd": validate_no_options,
        "ls": validate_ls,
        "find": validate_find,
        "cat": validate_cat,
        "head": validate_head_or_tail,
        "tail": validate_head_or_tail,
        "grep": validate_grep,
        "rg": validate_rg,
        "sed": validate_sed,
        "git": validate_git,
        "docker": validate_docker,
        "systemctl": validate_systemctl,
        "journalctl": validate_journalctl,
        "whoami": validate_no_options,
        "hostname": validate_no_options,
        "hostnamectl": validate_no_options,
    }

    validator = validators.get(command[0])

    if validator is None:
        return False, (
            f"Program '{command[0]}' is not allowed "
            "in read-only mode."
        )

    return validator(command, cwd)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Execute a Night Shift agent command "
            "with redacted audit receipts."
        )
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

    try:
        cwd = Path(args.cwd).resolve(strict=False)

    except OSError as error:
        cwd = None
        cwd_reason = (
            f"Unable to resolve working directory: {error}"
        )

    else:
        if not cwd.is_dir():
            cwd_reason = (
                "Working directory must be an existing directory."
            )

        elif not is_within_project(cwd):
            cwd_reason = (
                "Working directory resolves outside the project root."
            )

        else:
            cwd_reason = ""

    if cwd_reason:
        allowed = False
        reason = cwd_reason
        receipt_cwd = args.cwd

    else:
        allowed, reason = command_is_allowed(command, cwd)
        receipt_cwd = str(cwd)

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
            "cwd": receipt_cwd,
            "reason": reason,
            "git": git_state(),
        }

        safe_receipt = write_receipt(blocked_receipt)

        print(
            json.dumps(safe_receipt, indent=2),
            file=sys.stderr,
        )

        sys.exit(126)

    receipt_id = str(uuid4())
    started = datetime.now(timezone.utc)

    write_receipt(
        {
            "id": receipt_id,
            "timestamp": started.isoformat(),
            "session": args.session,
            "action": args.action,
            "target": args.target,
            "phase": "started",
            "command": command,
            "cwd": receipt_cwd,
            "git": git_state(),
        }
    )

    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
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
                "success"
                if result.returncode == 0
                else "failure"
            ),
            "exit_code": result.returncode,
            "command": command,
            "cwd": receipt_cwd,
            "stdout": result.stdout[-5000:],
            "stderr": result.stderr[-5000:],
            "duration_seconds": round(
                (ended - started).total_seconds(),
                3,
            ),
            "git": git_state(),
        }

        safe_receipt = write_receipt(receipt)

        print(json.dumps(safe_receipt, indent=2))

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
            "cwd": receipt_cwd,
            "duration_seconds": round(
                (ended - started).total_seconds(),
                3,
            ),
            "stdout": stdout[-5000:],
            "stderr": stderr[-5000:],
            "git": git_state(),
        }

        safe_receipt = write_receipt(receipt)

        print(json.dumps(safe_receipt, indent=2))
        sys.exit(124)


if __name__ == "__main__":
    main()
