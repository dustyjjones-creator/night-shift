# Service-State Metadata Proxy Approval Workflow

## Status

Design and static-test workflow only.

This document defines the human approval process required before any future
fixed-field, read-only service-state metadata proxy may be implemented or used.

It does not grant access, change permissions, create a collector, or enable
live collection.

The service-state metadata contract remains the source of truth:

- `docs/architecture/SERVICE_STATE_METADATA_CONTRACT.md`
- `services/agent/contracts/service_state_schema.json`
- `services/agent/lib/service_state_contract.py`

## Approval Principle

Each metadata source requires separate human approval.

Approval must be specific to:

1. The service role.
2. The management interface.
3. The exact fields that may be exposed.
4. The approved metadata purpose.
5. The source owner.
6. The sensitivity classification.
7. The collection boundary.

Approval for one source does not authorize collection from another source.

## Approval Record

Before implementation or live collection, each approved source must have a
human-reviewed approval record containing:

- `approval_id`
- `approved_at`
- `approved_by`
- `source_owner`
- `service_role`
- `management_interface`
- `approved_purpose`
- `approved_fields`
- `sensitivity_classification`
- `collection_boundary`
- `approval_status`

The record must identify the exact source and may not use a blanket approval
such as "systemd access" or "Docker access."

## Systemd Metadata Approval Boundary

A future systemd metadata proxy may expose only human-approved fixed fields.

Potential fields requiring explicit approval:

- unit name
- active state
- sub state
- unit file enabled state
- state change timestamp
- restart count when safely available

The proxy must not expose:

- unit file contents
- environment variables
- command lines
- process arguments
- credentials
- tokens
- API keys
- raw journal entries
- stdout
- stderr
- arbitrary systemd properties

Approval of one unit does not approve metadata access to other units.

## Docker Metadata Approval Boundary

A future Docker metadata proxy may expose only human-approved fixed fields for
a specifically approved container or service role.

Potential fields requiring explicit approval:

- container or service role
- running state
- health state when available
- restart count when safely available
- start or state-change timestamp
- enabled or managed status when represented safely

The proxy must not expose:

- Docker socket access to callers
- container configuration
- environment variables
- mounted secrets
- command lines
- entrypoints
- labels unless individually approved
- network configuration
- port mappings
- volumes
- image history
- raw inspect output
- arbitrary Docker API responses

Approval of one container or role does not approve discovery or enumeration of
other containers.

## Splunk Boundary

The proxy design does not grant direct Splunk access.

Any future Splunk-derived service state must come from a separately approved,
read-only aggregate or saved-search output.

The proxy must not expose:

- credentials
- HEC tokens
- search credentials
- raw events
- arbitrary search capability
- broad index access
- unrestricted query parameters

Each saved-search output requires its own approval and fixed output schema.

## Negative Test Matrix

A future implementation must include negative tests confirming that the proxy
rejects or prevents:

| Attempt | Expected Result |
| --- | --- |
| Request an unapproved service role | Rejected |
| Request an unapproved management interface | Rejected |
| Request a field outside the approved field set | Rejected |
| Request arbitrary systemd properties | Rejected |
| Request unit-file contents | Rejected |
| Request environment variables | Rejected |
| Request command lines or arguments | Rejected |
| Request raw journal output | Rejected |
| Request Docker socket passthrough | Rejected |
| Request arbitrary Docker inspect output | Rejected |
| Request container environment values | Rejected |
| Request network topology | Rejected |
| Request credentials or tokens | Rejected and redacted |
| Request raw stdout or stderr | Rejected |
| Request arbitrary raw output | Rejected |
| Request an expired or revoked approval | Rejected |
| Attempt source substitution | Rejected |
| Attempt path traversal | Rejected |
| Attempt approval-record bypass | Rejected |

## Redaction Fixtures

Future proxy tests must include sanitized fixtures containing representative
secret patterns.

Fixtures should verify that output and audit records redact:

- passwords
- bearer tokens
- Splunk tokens
- API keys
- access keys
- private keys
- OpenAI-style keys
- GitHub tokens
- AWS access-key IDs
- JWTs
- PEM blocks

Fixtures must be fictional and must not contain usable credentials.

A redaction failure must prevent the value from being emitted into:

- proxy output
- audit receipts
- error messages
- test snapshots
- persisted fixtures

## Evidence Format

Each future collection attempt should produce structured evidence containing
only:

- approval identifier
- collection timestamp
- service role
- management type
- approved field names
- collection status
- evidence timestamp
- redaction status
- schema validation result

Evidence must not contain prohibited raw source data.

## Failure Behavior

When metadata cannot be collected safely, the proxy must return an unavailable
or rejected result rather than expanding access.

Failure must not trigger:

- generic sudo
- Docker-group membership
- unrestricted systemd bus access
- journal access
- credential requests
- network scanning
- fallback to arbitrary command execution

The reason for unavailability may be reported only as a sanitized,
non-sensitive summary.

## Implementation Gate

No proxy implementation may begin until:

1. A source-specific approval record exists.
2. The source owner is identified.
3. The exact approved field set is documented.
4. The collection boundary is documented.
5. The metadata contract is compatible with the approved output.
6. Negative tests are defined.
7. Redaction fixtures are defined.
8. A human explicitly approves implementation.

## Current State

No live metadata proxy is implemented by this document.

No permissions, credentials, schedules, services, or collection interfaces are
created or modified.

This workflow exists to ensure that future service-state collection remains
narrow, fixed-field, auditable, and subject to explicit human approval.
