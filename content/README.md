# Night Shift Content Intelligence Pipeline

## Purpose

This directory defines a design-only pipeline for turning safe, educational
observations from the Night Shift lab into human-reviewed LinkedIn post
suggestions. It contains no live integrations, credentials, schedules, or
publishing capability.

The intended flow is:

```text
sources → normalize → findings → candidate generation → scoring and ranking
        → human review → approved content archive
```

## Repository Layout

```text
content/
├── sources/
│   ├── splunk/
│   ├── cyber_news/
│   └── lab_notes/
├── findings/
│   ├── pending/
│   └── processed/
├── candidates/
│   ├── pending/
│   ├── approved/
│   └── rejected/
├── templates/
└── archive/
```

Directories are placeholders for future, version-controlled and sanitized
artifacts. Runtime data, credentials, raw operational exports, and automated
collection are outside this design.

## Source Model

The pipeline has three initial source categories:

- **Splunk and home-lab findings:** narrowly scoped, sanitized findings from
  approved saved searches or manually exported summaries; never unrestricted
  operational data access.
- **Curated cybersecurity news and advisories:** a small, reviewable source
  list that favors authoritative primary sources such as vendor advisories and
  government security agencies.
- **Manual lab notes and project milestones:** operator-authored summaries of
  experiments, lessons, and completed work.

Future Splunk work must consume only narrowly scoped findings or saved-search
outputs. Future news ingestion begins with the curated list and must not fetch
sources or use credentials until separately approved.

## Finding Model

Each normalized observation may be represented as a sanitized JSON or YAML
record with this shape:

```yaml
id: finding-YYYYMMDD-unique-id
timestamp: "2026-08-23T00:00:00Z"
source: lab_notes | splunk | cyber_news
source_reference: sanitized-human-readable-reference
category: detection | incident_lesson | advisory | lab_milestone
title: concise-finding-title
summary: plain-language-summary
evidence: sanitized-supporting-observations
educational_angle: lesson-a-reader-can-apply
security_relevance: why-this-matters
sensitivity: public | review_required | restricted
status: pending | processed | excluded
```

Before a finding is stored or used for drafting, operational identifiers,
credentials, private addresses, internal host details, and any other sensitive
evidence must be redacted or the finding must be marked `restricted` and
excluded. `source_reference` must identify provenance without embedding raw
credentials, queries, or sensitive event data.

## Content Candidate Model

Candidate records connect one or more approved findings to a proposed,
educational post. A proposed format is:

```yaml
id: candidate-YYYYMMDD-unique-id
finding_references:
  - finding-YYYYMMDD-unique-id
content_type: lab_finding | news_connection | educational | lab_journal
proposed_hook: opening-idea
core_lesson: concise-takeaway
draft: human-review-required-draft
audience: security-practitioners | career-transitioners | general-technical
confidence: 0.0
originality: 0.0
educational_value: 0.0
timeliness: 0.0
overall_score: 0.0
status: pending | approved | rejected
```

Scores are decision support, not an authorization to publish. Candidate drafts
must preserve the source finding's sensitivity constraints.

## Daily Content Board

The intended daily board ranks three suggestions for a human reviewer:

1. **Primary recommendation** — the strongest timely or broadly useful idea.
2. **Educational suggestion** — a clear concept, technique, or lesson.
3. **Short lab or career-journey suggestion** — a concise reflection on a lab
   milestone or learning process.

Each suggestion includes its candidate ID, linked findings, proposed hook,
audience, score summary, and a short explanation of why it was recommended.
The board is a review artifact, not a publishing queue.

## Human Approval Boundary

Night Shift may collect approved inputs in the future, normalize and correlate
them, create findings, draft and rank candidates, and prepare a review board.
It may not publish to LinkedIn automatically. A human must review and approve
both the content and its sensitivity before any external publication. Approval
is represented by moving a candidate to `candidates/approved/`; publication is
outside this repository and this pipeline design.

## Future Implementation Guardrails

- Add no live Splunk, news, or LinkedIn integration without separate approval.
- Keep source permissions least-privileged and scoped to the required finding.
- Preserve source provenance and human review decisions for auditability.
- Treat all lab-derived content as review-required until sanitized.
