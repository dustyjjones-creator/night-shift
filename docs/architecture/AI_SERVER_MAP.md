AI Server Infrastructure Map

Last mapped: 2026-08-23
Status: Initial infrastructure inventory

Overview

The ai-server is a Debian virtual machine running under QEMU/Proxmox. It hosts AI-related services, automation infrastructure, and telemetry forwarders.

Proxmox Host
└── QEMU Virtual Machine: ai-server
    ├── Debian GNU/Linux 13
    │
    ├── Ollama
    │   └── systemd journal
    │       └── ollama-forwarder.py
    │           └── Splunk HEC
    │
    ├── Docker Compose: ai-pipeline
    │   └── n8n
    │       └── Docker JSON logs
    │           └── n8n-forwarder.py
    │               └── Splunk HEC
    │
    └── Night Shift
        ├── Git repository
        ├── GitHub remote
        └── Future agent control and audit system
Host
Component	Current State
Hostname	ai-server
Operating system	Debian GNU/Linux 13 (trixie)
Virtualization	QEMU virtual machine
Architecture	x86-64
Primary user	dusty
n8n Automation

The n8n instance is managed through Docker Compose.

Item	Location / Value
Compose project	ai-pipeline
Compose directory	/home/dusty/ai-pipeline
Compose file	/home/dusty/ai-pipeline/compose.yml
Container	n8n
Persistent storage	Docker volume n8n_data
Internal service port	5678

The live n8n workflow data is stored in the Docker-managed volume and is not currently tracked directly in Git. Workflow export and backup will be added as part of the Night Shift project.

AI and Telemetry
Ollama to Splunk

The ai-ollama-forwarder.service is enabled and running.

Python application: /opt/ai-splunk-forwarder/ollama-forwarder.py
Input: Ollama systemd journal events
Output: Splunk HTTP Event Collector
Destination index: ai_server
Sourcetype: ai:ollama
Reliability mechanism: systemd journal cursor tracking

The forwarder only advances its journal cursor after a successful event send.

n8n to Splunk

The ai-splunk-forwarder.service is enabled and running.

Python application: /opt/ai-splunk-forwarder/n8n-forwarder.py
Input: Docker JSON logs from the n8n container
Output: Splunk HTTP Event Collector
Destination index: ai_server
Sourcetype: ai:n8n
Reliability mechanism: file-position tracking

The forwarder tracks its position in the Docker log stream and checks for log file changes.

Secrets

Splunk HEC credentials are supplied through an environment file and are not stored in this repository.

The following paths are treated as sensitive or runtime-only and should not be committed:

Environment files containing credentials
API tokens
Certificates and private keys
Runtime logs
Docker volumes
Agent backups
Night Shift

/home/dusty/night-shift is the Git-tracked control center for the project.

Its long-term role is to provide:

Infrastructure documentation
Version-controlled configuration and code
Agent workspace and guardrails
Structured action logging
Change tracking through Git
Splunk observability for agent activity
Daily handoffs and workflow summaries
Known Future Work
Export and version-control n8n workflow definitions safely.
Bring forwarder source code into the Night Shift repository.
Document systemd service definitions without exposing secrets.
Add infrastructure change logging.
Build a read-only agent inspection mode.
Add controlled editing and testing.
Generate daily handoffs from actual agent action logs.
