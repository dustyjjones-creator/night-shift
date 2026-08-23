# Night Shift

Night Shift is a homelab engineering and AI automation project.

## Goals

- Build and maintain AI-assisted automation workflows.
- Integrate Docker services, n8n, Splunk, and local AI infrastructure.
- Develop a controlled engineering agent capable of inspecting, modifying,
  testing, and documenting project infrastructure.
- Maintain a complete audit trail of changes and agent actions.
- Generate daily handoffs summarizing work, results, failures, and next steps.

## Core Principles

1. All meaningful changes should be tracked.
2. Secrets must never be committed.
3. Agent actions should be logged.
4. Changes should be validated before production deployment.
5. Production changes require human approval.
6. Every session should leave a clear handoff for the next one.

## Status

Repository initialized August 23, 2026.

This repository begins as the control center for the existing Night Shift
infrastructure. Existing services will be documented and brought under version
control incrementally to avoid disrupting production systems.
