# Lab Observability and Ingestion Discovery

Date: 2026-08-23  
Scope: read-only discovery from the Night Shift repository and the current
local session. This is a recommendation record, not a statement that any
documented service is currently running.

## 1. Executive Summary

The strongest directly observed opportunity is the Night Shift agent audit log:
the local repository contains structured JSONL action receipts. This is already
an auditable record of permitted agent activity and can support operational
handoffs and educational material about safe automation.

The architecture also documents a promising future telemetry path from Ollama
and n8n through purpose-built forwarders to Splunk. It should be investigated
through a narrowly scoped, human-approved service-state and saved-search review
before it is treated as available. Docker and systemd state could not be read
from this session, and journal access returned no visible entries.

## 2. Evidence and Classification Rules

- **DISCOVERED:** directly observed through a permitted command in this session.
- **DOCUMENTED:** present in repository documentation but not directly observed.
- **UNKNOWN:** insufficient evidence to determine availability.
- **UNAVAILABLE:** a known read-only inspection path was blocked by access or
  outside the task boundary.

## 3. Environment Inventory

| System or source | Classification | Evidence | Current state known from this task |
| --- | --- | --- | --- |
| Local host `ai-server` | DISCOVERED | `hostname` returned `ai-server`. | Host identity only; platform details were not accessible. |
| Night Shift agent audit receipts | DISCOVERED | `logs/agent/2026-08-23.jsonl` was directly listed. | Local structured receipt log exists. |
| systemd service state | UNAVAILABLE | `systemctl show` for documented and candidate units failed because the session cannot connect to the system bus. | Unit existence and running state not verified. |
| system journal data | UNAVAILABLE | `journalctl --no-pager -n 0` succeeded but returned no visible entries and reported limited journal access. | Journal interface exists; useful system entries are not accessible. |
| Docker daemon/container metadata | UNAVAILABLE | `docker ps` and `docker images` failed to connect to `/var/run/docker.sock` due to permission denial. | Docker installation, daemon state, containers, and images not verified. |
| Ollama | DOCUMENTED | AI server map names Ollama and an Ollama forwarder. | Not directly observed; service state unavailable. |
| `ai-ollama-forwarder.service` | DOCUMENTED | Architecture describes journal-to-Splunk forwarding. | Not directly observed; systemd access unavailable. |
| n8n / `ai-pipeline` Docker Compose project | DOCUMENTED | Architecture describes the compose project, n8n, and Docker JSON logs. | Not directly observed; Docker access unavailable. |
| `ai-splunk-forwarder.service` | DOCUMENTED | Architecture describes n8n-log forwarding to Splunk. | Not directly observed; systemd access unavailable. |
| Splunk HEC / `ai_server` index | DOCUMENTED | Architecture identifies the destination and sourcetypes. | Endpoint, credentials, connectivity, and ingest state were not inspected. |
| Proxmox host / QEMU virtualization | DOCUMENTED | Architecture maps `ai-server` as a QEMU VM under Proxmox. | Host telemetry is outside this local session and was not accessed. |
| Pi-hole | UNKNOWN | No repository evidence; named only as a discovery consideration. | The unit probe could not reach systemd, so absence cannot be inferred. |
| Tailscale | UNKNOWN | No repository evidence; named only as a discovery consideration. | The unit probe could not reach systemd, so absence cannot be inferred. |
| Authentik | UNKNOWN | No repository evidence; named only as a discovery consideration. | The unit probe could not reach systemd, so absence cannot be inferred. |

## 4. Potential Ingestion Points

### Agent audit receipts

- **Classification:** DISCOVERED
- **Evidence:** `logs/agent/2026-08-23.jsonl` was directly listed. The command
  wrapper and architecture also describe structured, redacted audit receipts.
- **Likely data:** session, action, target, command metadata, result, timing,
  Git state, and blocked-command records.
- **Current ingestion status:** local JSONL receipt generation is observed;
  downstream ingestion or retention is not verified.
- **Observability value:** high for agent accountability, command-failure
  analysis, and daily handoffs.
- **Cybersecurity learning value:** high for least privilege, audit trails,
  command policy enforcement, and secret redaction.
- **Educational content value:** high; it can support a safe-automation lab
  journal without exposing workload telemetry.
- **Implementation effort:** low for a future schema and retention review;
  unknown for any external aggregation.
- **Recommended next investigation:** review a sanitized sample receipt schema
  and retention requirements without adding an ingestion path.
- **Human approval requirement:** required before exporting, aggregating, or
  using receipts outside the local audit workflow.

### Ollama system journal and documented forwarder

- **Classification:** DOCUMENTED; journal data is UNAVAILABLE in this session.
- **Evidence:** architecture maps Ollama journal events through
  `ai-ollama-forwarder.service` to Splunk; systemd state could not be queried.
- **Likely data:** service health, model-serving lifecycle events, and
  forwarder delivery outcomes. Request content must be treated as sensitive
  unless proven otherwise.
- **Current ingestion status:** documented as forwarded to Splunk; not verified.
- **Observability value:** medium to high for AI-service reliability.
- **Cybersecurity learning value:** medium for telemetry hygiene and safe AI
  operations.
- **Educational content value:** medium after sanitization; focus on delivery
  guarantees and observability design rather than prompts or user data.
- **Implementation effort:** medium, pending access and a data-classification
  review.
- **Recommended next investigation:** obtain human-approved read-only service
  status and a sanitized saved-search summary, not raw journal access.
- **Human approval requirement:** required before viewing broader logs or
  connecting this data to any new destination.

### n8n Docker logs and documented forwarder

- **Classification:** DOCUMENTED; Docker inspection is UNAVAILABLE in this
  session.
- **Evidence:** architecture maps Docker JSON logs from n8n through
  `ai-splunk-forwarder.service` to Splunk; Docker socket access was denied.
- **Likely data:** workflow execution health, error trends, throughput, and
  delivery status. Workflow inputs and outputs may be sensitive.
- **Current ingestion status:** documented as forwarded to Splunk; not verified.
- **Observability value:** high for automation reliability.
- **Cybersecurity learning value:** medium to high for workflow assurance,
  error handling, and least-privilege telemetry design.
- **Educational content value:** medium after strict sanitization, especially
  around resilient automation patterns.
- **Implementation effort:** medium, pending read-only Docker or saved-search
  access.
- **Recommended next investigation:** request a human-approved container state
  check and sanitized execution-failure aggregate.
- **Human approval requirement:** required before reading container logs,
  exporting workflow data, or adding ingestion.

### Splunk saved-search findings

- **Classification:** DOCUMENTED; direct access is UNAVAILABLE within this
  task because no approved credentials or scoped query interface was provided.
- **Evidence:** architecture records Splunk HEC destinations and the content
  design requires future narrow saved-search findings.
- **Likely data:** sanitized trends, delivery errors, authentication patterns,
  and lab detection hypotheses.
- **Current ingestion status:** HEC ingestion is documented, but query access
  and data availability are not verified.
- **Observability value:** high, if outputs are limited to approved aggregates.
- **Cybersecurity learning value:** high for detection engineering and incident
  investigation methodology.
- **Educational content value:** high when findings are manually sanitized and
  human-reviewed.
- **Implementation effort:** medium for saved-search design; high if broad
  access controls and data classification are unresolved.
- **Recommended next investigation:** design a minimal set of sanitized,
  read-only saved-search outputs with owner approval.
- **Human approval requirement:** required before any access grant, export, or
  downstream use.

### Proxmox, Pi-hole, Tailscale, and Authentik telemetry

- **Classification:** Proxmox is DOCUMENTED; Pi-hole, Tailscale, and Authentik
  are UNKNOWN. Direct local inspection is UNAVAILABLE for unit state.
- **Evidence:** Proxmox is in the architecture map; no repository evidence
  identifies the other three services. Systemd probing was access-limited.
- **Likely data:** virtualization lifecycle and capacity events; DNS security
  signals; secure-network access events; and identity/authentication events.
- **Current ingestion status:** unknown.
- **Observability value:** potentially high, especially DNS and identity data,
  but not established by this discovery.
- **Cybersecurity learning value:** potentially high for access, identity, and
  network-defense topics.
- **Educational content value:** medium to high only after source ownership,
  sensitivity, and aggregation boundaries are defined.
- **Implementation effort:** unknown.
- **Recommended next investigation:** inventory service ownership and request
  service-specific, read-only metadata checks; do not scan the network.
- **Human approval requirement:** required before any credential use, log
  access, or ingestion design.

## 5. Priority Recommendations

1. **Agent audit receipts:** directly observed, local, structured, and already
   designed for safe review. Start with a schema/retention and daily-handoff
   design rather than a new collector.
2. **Narrow Splunk saved-search summaries:** documented integration paths make
   this the strongest future technical source, but use only approved aggregate
   findings and avoid unrestricted operational data access.
3. **n8n and Ollama delivery-health summaries:** documented forwarders suggest
   useful reliability lessons; validate service state and sanitized aggregates
   before treating either source as live.
4. **Identity, DNS, and remote-access telemetry inventory:** potentially high
   security value, but Pi-hole, Tailscale, and Authentik are unverified and
   should not be assumed present.

## 6. Known Gaps and Uncertainty

- No Docker daemon access was available, so n8n container presence, images,
  and logs were not verified.
- No system-bus access was available, so neither documented services nor
  candidate services can be represented as running or installed.
- The journal command itself was available, but no readable entries were
  returned; broader journal access would require approval outside this task.
- Splunk connectivity, ingest health, saved searches, and credentials were not
  inspected.
- Proxmox, Pi-hole, Tailscale, and Authentik availability remain unverified.
- No network collection, external scanning, or credentialed inspection was
  attempted.

## 7. Proposed Next Actions

1. Request approval for a read-only, sanitized service-state inventory that can
   access the system bus and Docker metadata without exposing logs or secrets.
2. Design a minimal Splunk saved-search contract containing only sanitized
   aggregates and provenance fields needed for findings.
3. Define retention, access control, and redaction review for agent receipts
   before any aggregation or content use.
4. Inventory ownership and sensitivity classifications for any Pi-hole,
   Tailscale, Authentik, or Proxmox sources before proposing collection.

None of these actions are implemented by this discovery document.
