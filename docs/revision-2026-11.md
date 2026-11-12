# November 2026 repository revision

## Why this is more than a new opening paragraph

The initial public release described a 28 September three-node layout. The
12 November authenticated inventory has five nodes, distributed DNS/PostgreSQL,
a dedicated proxy, a CA and OpenClaw. Management and core-services are due for
retirement, not stable target-state anchors.

This revision reconciles the root overview, inventory, service explanations,
standalone SVG, HTML diagram page, operations/recovery statements and component
status labels. The Homepage example gains five node links and illustrative current
service categories. It does not export the running dashboard or private configurations.

## Publication status by area

| Material | Status in this revision |
| --- | --- |
| Root overview / inventory / diagram | 12 November topology observation plus owner-supplied retirement intent |
| DNS / database / access summaries | Public synthesis of dated November private records; not deployable configurations |
| Homepage Compose / BookStack Compose | Retained examples from the original release, not revalidated production exports |
| Homepage links | Sanitized illustrative directory updated for the five-node map; links are not liveness evidence |
| Monitoring | Retained rules/fixtures/receiver example; deployment and delivered alerts unverified |
| Offsite | Retained source/templates and local fixtures; current deployment unverified; old management/core probe roles need redesign before retirement |

No automatic discovery, new IdP, migration, VM deletion, failover drill or lab
configuration change is implied. No private operating manual or raw evidence was
copied into the public tree. Historical example versions remain pinned rather than
being upgraded without deployment-specific compatibility work.

## Deferred engineering, not missing publication polish

- Reconcile each application before retiring management/core services.
- Redesign the watchdog's management/core assumptions for the successor layout.
- Establish current all-member DNS/PostgreSQL functional and failover acceptance.
- Establish delivered monitoring alerts and complete recovery/offsite coverage.

[Verification ledger](verification.md) records what was actually checked.
