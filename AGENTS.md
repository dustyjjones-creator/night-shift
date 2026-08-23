# Night Shift Agent Instructions

## Mission

Night Shift is an AI-assisted homelab automation and observability project.

The agent's job is to help inspect, document, improve, and build the
Night Shift environment while preserving an auditable history of work.

## Project Root

/home/dusty/night-shift

Do not treat files outside this project as part of the Night Shift
repository unless explicitly instructed by the user.

## Safety Model

Start with inspection and understanding.

Prefer read-only operations before making changes.

Do not use destructive commands unless explicitly authorized.

Do not delete files, containers, volumes, services, or Git history.

Do not modify system configuration outside the project repository without
explicit authorization.

Do not expose, print, commit, or log secrets, tokens, passwords, API keys,
or credential files.

## Audit Requirements

Important actions should be recorded using:

services/agent/bin/log-action.py

Shell commands that inspect the project should use:

services/agent/bin/run-agent-command.py

The command wrapper is intentionally read-only. Do not bypass it for
inspection commands when the wrapper can be used.

If a change is required, explain the proposed change and preserve enough
information for the user to review what changed.

## Git Requirements

Before making repository changes:

1. Inspect `git status`.
2. Inspect relevant existing files.
3. Make the smallest reasonable change.
4. Review the resulting diff.
5. Do not commit unless explicitly instructed by the user.

Never force-push.

Never rewrite shared Git history.

## Documentation

Keep architecture, decisions, and handoffs understandable to a human.

Prefer updating existing documentation over creating duplicate documents.

Important architectural decisions belong in:

docs/decisions/

## Daily Workflow Goal

At the end of a work session, Night Shift should eventually be able to
produce:

- A summary of actions performed
- Changes made
- Commands executed
- Blocked actions
- Git commits
- Current system state
- Remaining work
- A simple workflow schematic

## Current Phase

The current implementation phase is building the agent control and audit
layer.

Existing components include:

- Structured JSONL action logging
- Audited command receipts
- Read-only command allowlisting
- Git/GitHub project history
- Initial AI server architecture documentation

Prioritize strengthening these foundations before expanding agent
permissions.
