# Human-Approved Read-Only Service-State Inventory Plan

Date: 2026-08-23  
Status: design only; no collection, credentials, permission changes, or
integrations are created by this document.

## Purpose and Safety Model

This plan converts the opportunities and access limits in
[LAB_OBSERVABILITY_DISCOVERY.md](LAB_OBSERVABILITY_DISCOVERY.md) into a
least-privilege inventory design. It is for service health and ingestion
readiness, not raw operational telemetry collection.

Every future inventory run must be human-approved, read-only, bounded in
scope, recorded through the Night Shift audit boundary, and redacted before
storage. Outputs are inventory snapshots: JSON or YAML records containing only
the fields listed below, plus collection timestamp, collector identity, and
source classification. No collector may use `shell=True`, persist a credential,
or emit raw logs/events.

## Collection Boundaries

### SAFE WITHOUT ADDITIONAL ACCESS

These sources can be reviewed from the repository and existing local agent
workspace without new host, container, or API permissions:

- Night Shift architecture, content artifacts, and agent-policy documentation.
- Existing agent JSONL receipt inventory metadata: file presence, receipt count,
  date range, result counts, action names, and Git state. Receipt details,
  command output, and targets remain review-required because they can contain
  operational context even after redaction.
- The documented inventory of Ollama, n8n, forwarders, Splunk, and Proxmox.
  Documentation establishes planned scope only; it is never evidence of current
  service state.

Safe output format: a repository-local Markdown or JSON summary marked
`source_classification: documented` or `discovered_local`, with no copied raw
receipt content.

### REQUIRES HUMAN-APPROVED READ-ONLY ACCESS

The following requires a narrowly scoped access path that returns only
allowlisted metadata. Approval must identify the systems, fields, retention,
and reviewer. The preferred local mechanism is a root-owned, read-only command
or API proxy that emits a fixed schema; do **not** add the agent user to the
Docker group or grant unrestricted system-bus access.

- Local systemd unit metadata for Ollama and the two documented forwarders.
- Docker container and image metadata for `ai-pipeline`/n8n.
- Existing, pre-authorized Splunk saved-search aggregates and HEC delivery
  health summaries.
- Existing human-operated Proxmox read-only session or separately approved
  read-only interface.
- Service-specific health metadata for Pi-hole, Tailscale, and Authentik only
  after an owner confirms that each service exists and identifies its host.

Safe output format: one sanitized `service_state` record per service; no raw
journal lines, container logs, search results, user records, tokens, endpoint
URLs, IP addresses, peer names, or configuration payloads.

### DO NOT COLLECT WITHOUT A NEW EXPLICIT DESIGN TASK

- Raw system journals, Ollama requests/responses, prompts, and model logs.
- Docker or n8n logs, workflow definitions, workflow execution payloads,
  environment files, mounts, or container environment variables.
- Splunk raw events, unrestricted searches, HEC configuration, tokens, or
  endpoint configuration.
- Proxmox guest-console output, VM configuration, storage paths, backups, or
  raw host logs.
- Pi-hole DNS query logs, Tailscale peer/device identity data, and Authentik
  users, sessions, authentication events, applications, or provider details.
- Any network scan, credential creation, permission change, scheduling,
  collector, ingestion pipeline, or publishing action.

## Proposed Inventory Categories

| System | Metadata worth collecting | Why it matters | Minimum access / access type | Sensitivity and redaction | Safe evidence format |
| --- | --- | --- | --- | --- | --- |
| Ollama | Unit load/active/sub state, enabled state, process exit status, restart count, last transition time, model-service port *presence only* | Establishes availability and reliability without observing requests. | Approved local systemd metadata proxy. | `review_required`; omit command lines, paths, logs, model names, ports, and endpoint details. | `service_state` with boolean/enumerated health fields and timestamps rounded to the minute. |
| n8n / ai-pipeline | Container existence, image digest or version label, lifecycle/health status, restart count, creation/start time, compose project label, volume *count* | Validates that the documented automation stack exists and indicates reliability trends. | Approved Docker metadata proxy limited to list/inspect fields; no Docker group membership. | `review_required`; omit container IDs, names if identifying, mounts, networks, env, labels except approved project label, and logs. | `container_state` with sanitized service role, state, health, restart count, version label, and timestamp. |
| Splunk forwarders | Unit state, enabled state, exit status, restart count, last transition time, delivery-health aggregate: last successful send time and failure count | Confirms that documented Ollama/n8n telemetry paths are healthy before new work is considered. | Approved local systemd metadata proxy; optionally an existing approved saved-search aggregate. | `review_required`; omit forwarder paths, HEC URL, tokens, payloads, and raw errors. | `service_state` plus `delivery_health` counts and coarse time window. |
| Splunk / HEC | Saved-search identity, search completion state, time window, aggregate event counts by approved sourcetype, latest-event age, aggregate delivery failures | Produces the smallest useful evidence of ingest freshness and content-worthy patterns. | Existing, owner-approved read-only saved-search interface; no new token. API-based or existing UI export. | `restricted` until output is sanitized; exclude raw events, queries, indexes beyond approved labels, host/user fields, IPs, URLs, and HEC credentials. | `saved_search_summary` with approved source label, count, time window, freshness bucket, and redaction status. |
| Docker containers and metadata | Daemon reachability, container count, approved service-role state, health, restart count, image version/digest | Supports stack discovery and container health without accessing workloads. | Same approved Docker metadata proxy as n8n. | `review_required`; exclude all configuration, environment, mount, network, and log fields. | Aggregate `docker_inventory` plus per-approved-role `container_state`. |
| Proxmox / QEMU context | Host/guest availability, guest power state, guest agent availability, allocated CPU/RAM/disk *buckets*, backup age *bucket*, hypervisor version | Adds capacity and lifecycle context for the documented `ai-server` VM. | Existing human-operated read-only Proxmox session or separately approved read-only interface. API-based or UI-export-based. | `restricted`; exclude host names beyond approved roles, node addresses, VM IDs, storage names, task logs, console data, and configuration. | `virtualization_state` with sanitized role, availability, resource buckets, and time-age buckets. |
| Pi-hole | Service existence, version, DNS service health, aggregate blocked/allowed query counts, block-rate percentage, upstream health count | Can provide privacy-aware DNS security and learning signals. | Service owner confirms existence, then a service-specific read-only metadata interface. Local or API-based. | `restricted`; never collect query logs, domains, client identifiers, upstream addresses, API credentials, or lists. | `dns_health_summary` using aggregate counts and time windows only. |
| Tailscale | Service existence, client version, backend connection state, peer-count bucket, DERP/relay health category, last-sync age bucket | Offers remote-access availability context without exposing the network graph. | Service owner confirms existence, then an approved local status summary or existing read-only API scope. | `restricted`; exclude device names, users, tailnet name, node keys, IPs, peer identities, routes, and exit-node data. | `remote_access_health` with enums and count/age buckets. |
| Authentik | Service existence, version, service health, aggregate authentication success/failure counts, provider/application *counts*, last-event age bucket | Potential identity observability source after ownership and retention controls are defined. | Service owner confirms existence, then a narrowly scoped read-only aggregate interface. Local/container/API-based. | `restricted`; exclude users, groups, sessions, applications, providers, events, tokens, cookies, endpoints, and client IPs. | `identity_health_summary` containing only aggregate counters and freshness buckets. |

## Minimum Access Expansion

The first expansion should be a human-approved, root-owned read-only metadata
interface on `ai-server` with a fixed allowlist for:

1. `systemctl show` of `ollama`, `ai-ollama-forwarder`, and
   `ai-splunk-forwarder`, returning only approved state/restart fields.
2. Docker list/inspect metadata for the approved `ai-pipeline` service role,
   returning only approved lifecycle and health fields.

This is smaller and safer than Docker socket access, Docker-group membership,
generic sudo, shell access, or unrestricted system-bus access. It does not
need journal content, container logs, environment data, or credentials.

No Splunk, Proxmox, Pi-hole, Tailscale, or Authentik access should be expanded
in this first step. Those systems require an owner-confirmed source inventory
and a separate field-level design before any access request.

## Proposed Ingestion Priority Order

1. **Agent audit-receipt summaries** — already local and structured; first
   define retention and daily-handoff summaries without external ingestion.
2. **Ollama and forwarder service-state metadata** — validates documented
   telemetry paths with minimal systemd-only metadata.
3. **n8n / ai-pipeline container-state metadata** — validates automation stack
   presence and reliability using a restricted Docker metadata proxy.
4. **Sanitized Splunk saved-search summaries** — only after the first three
   sources are understood and an owner approves exact aggregates.
5. **Proxmox/QEMU resource and lifecycle summaries** — valuable operational
   context, but needs a separate approved interface.
6. **Pi-hole, Tailscale, and Authentik aggregates** — defer until existence,
   ownership, and sensitivity controls are established.

## Approval and Evidence Requirements

Before implementing any category marked as requiring approval, the approver
must specify:

- named system roles and exact allowed fields;
- access mechanism and identity; no reusable secrets in this repository;
- collection frequency and retention duration;
- redaction test cases and sample sanitized output;
- output destination, human reviewer, and rollback/disable path.

Each inventory snapshot should include `schema_version`, `collected_at`,
`source_role`, `access_class`, `redaction_status`, and `human_approval_ref`.
The value of `human_approval_ref` is a review identifier, not a credential or
an implementation authorization.

## Recommended Next Task

Design and test a fixed-schema, read-only **service-state metadata contract**
for the three local systemd units and the `ai-pipeline` service role. The task
should define allowed fields, sanitization fixtures, negative tests for
disallowed fields, and approval workflow—but must not yet grant access, change
permissions, or implement collection.
