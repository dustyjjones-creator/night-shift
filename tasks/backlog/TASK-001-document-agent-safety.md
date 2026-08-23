# Task: Document Agent Safety System

## ID
TASK-001

## Status
backlog

## Objective

Update the Night Shift architecture documentation to accurately describe the implemented agent inspection and audit safety system.

## Scope

### Allowed
- docs/architecture/
- README.md
- AGENTS.md
- services/agent/
- tasks/

### Forbidden
- Host system configuration
- Docker configuration
- Splunk configuration
- Proxmox configuration
- Credentials or secrets
- Any files outside the Night Shift repository

## Required Documentation

Document the following implemented capabilities:

- Read-only agent command wrapper
- Project-root path boundaries
- Per-command argument validation
- Blocked dangerous command forms
- Structured JSONL audit receipts
- Command execution metadata
- Parent/child receipt linking
- Secret redaction before audit logging
- Automated policy regression tests
- Automated redaction regression tests

## Acceptance Criteria

- [ ] Architecture documentation reflects the current implementation
- [ ] Future-work references are updated where functionality is now implemented
- [ ] No secrets are added to documentation
- [ ] Existing documentation is not unnecessarily rewritten
- [ ] Relevant tests pass
- [ ] Git diff is reviewed
- [ ] A final summary is provided

## Verification

Run:

python3 services/agent/tests/test-policy.py

python3 services/agent/tests/test-redaction.py

git diff --check

## Notes

Do not commit or push changes.

Stop after completing the task and provide a summary of:
- files changed
- tests run
- tests passed or failed
- remaining concerns
