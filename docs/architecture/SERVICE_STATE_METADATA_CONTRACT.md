# Service-State Metadata Contract

Status: design and static-test contract only. This defines the only permitted
shape for future read-only metadata snapshots of `ollama`,
`ai_server_log_forwarder`, and `n8n_ai_pipeline`. It neither grants access nor
implements a collector.

Machine-readable schema: `services/agent/contracts/service_state_schema.json`.
Static fixtures, validator, and tests are in `services/agent/fixtures/`,
`services/agent/lib/service_state_contract.py`, and `services/agent/tests/`.

## Approved Fields

| Field | Type | Required | Constraints | Sensitivity | Source / meaning | May be absent? |
| --- | --- | --- | --- | --- | --- | --- |
| `schema_version` | string | Yes | Exactly `1.0` | public | Contract version. | No |
| `generated_at` | string | Yes | UTC `YYYY-MM-DDTHH:MM:SSZ` | review_required | Snapshot creation time. | No |
| `service_role` | string | Yes | `ollama`, `ai_server_log_forwarder`, or `n8n_ai_pipeline` | public | Sanitized logical role, not a host identifier. | No |
| `service_name` | string | Yes | Lowercase role-safe name, 1–64 characters, no dots or paths | review_required | Approved local service label. | No |
| `management_type` | string | Yes | `systemd` or `docker_compose` | public | Metadata interface family. | No |
| `observed_state` | string | Yes | `healthy`, `degraded`, `stopped`, `unknown`, or `unavailable` | review_required | State from approved interface. | No |
| `enabled_state` | string | Yes | `enabled`, `disabled`, `unknown`, or `unavailable` | review_required | Enablement summary, not unit configuration. | No |
| `health_summary` | string | Yes | Same values as `observed_state` | review_required | Sanitized health interpretation. | No |
| `restart_count` | integer | No | 0–9999, only when safely exposed | review_required | Restart aggregate; omit rather than infer. | Yes |
| `last_state_change` | string | No | UTC timestamp, only when safely exposed | review_required | Most recent state transition. | Yes |
| `source_interface` | string | Yes | `systemd_metadata_proxy`, `docker_metadata_proxy`, or `unavailable` | public | Fixed interface, never a command or URL. | No |
| `evidence_timestamp` | string | Yes | UTC timestamp | review_required | Time represented by evidence. | No |
| `collection_status` | string | Yes | `success`, `partial`, or `unavailable` | public | Whether contracted metadata was returned. | No |
| `reason_unavailable` | string | Conditional | One line, maximum 160 characters; required only when unavailable | review_required | Short limitation, never raw errors. | Yes, except when unavailable |

Unknown fields are rejected. An unavailable record requires
`collection_status: unavailable`, `source_interface: unavailable`, and a short
reason. A reason is prohibited on success or partial records.

## Role Mapping

| Service role | Management type | Approved future interface | Safe metadata purpose |
| --- | --- | --- | --- |
| `ollama` | `systemd` | Human-approved systemd metadata proxy | Availability and bounded restart/state health. |
| `ai_server_log_forwarder` | `systemd` | Human-approved systemd metadata proxy | Delivery-path reliability without event data. |
| `n8n_ai_pipeline` | `docker_compose` | Human-approved Docker metadata proxy | Automation lifecycle/health without container details. |

## Explicitly Prohibited Fields

The contract must never accept environment variables, command lines or
arguments, raw logs, unit-file contents, credentials, tokens, API keys,
container configuration, identity data, network topology, standard output,
standard error, or arbitrary raw service output. The validator explicitly
rejects `environment_variables`, `command_line`, `raw_logs`,
`unit_file_contents`, `credentials`, `token`, `api_key`,
`container_configuration`, `identity`, `network_topology`, `stdout`, `stderr`,
and `raw_output`.

## Static Fixtures and Tests

Fixtures are fictional and sanitized. They cover healthy Ollama, degraded log
forwarder, stopped n8n/ai-pipeline, and unavailable forwarder scenarios. Tests
accept those fixtures and reject unknown fields, missing required fields,
invalid enums, prohibited sensitive fields, and raw-output fields.

## Live Collection Prerequisite

Before future live collection, a human must approve an exact fixed-field,
read-only metadata proxy. The smallest needed expansion is a systemd metadata
proxy for Ollama and the log forwarder plus a Docker metadata proxy for the
`ai-pipeline` role. Do not grant Docker-group membership, generic sudo,
unrestricted system-bus access, journal access, or credentials as part of this
contract.
