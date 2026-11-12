# Operations and recovery boundaries

## Current scope

The [12 November inventory](inventory.md) supersedes the older three-node service
map. Management and core-services VMs are running but due for retirement. Their
retirement is a lifecycle requirement, not a completed migration or permission
to stop them. Replacement placements and the remaining application inventory must
be reconciled before a separate operational cutover.

Repository changes do not update the lab. The public Compose files, monitoring
rules and watchdog templates are selected examples, not authoritative current
runtime configuration. In particular, the former statement that every management
application belongs permanently on one VM no longer describes the intended layout.

## Access is more than DNS

Name resolution, network reachability, TLS identity and application authorization
are separate boundaries. The documented proxy design separates frontend HTTPS,
verified backend TLS and CA passthrough. See [access and identity](services/access-and-identity.md).
Neither a successful HTTP status nor an open TCP port proves authenticated workflows.

The local Compose examples bind to loopback by default and create no public DNS,
router forwards, remote-access ACLs or certificate infrastructure. Their optional
permission policies are historical examples, not freshly verified current lab policy.
For stacks still managed by another deployment owner, a parallel Compose invocation
is not a migration or safe takeover.

## Monitoring is not delivery

Published rules distinguish failed probes, failed scrapes and missing telemetry.
The offsite code distinguishes classes of failed reachability checks. Neither
establishes that the old monitoring stack or offsite observer is still deployed.
No fresh end-to-end alert or phone-delivery test was performed during this revision.

An accepted notification means the server accepted it; it does not prove a phone
rendered it. Routing, overlay and firewall faults can resemble a home power or
ISP outage. Correlated symptoms do not establish the underlying cause.

## Recovery is scoped, not binary

The September publication said scheduled backups awaited a NAS. That blanket
statement is historical and is not carried forward as current status. Maintained
November records describe some local CA/dashboard dump jobs and scoped restoration
checks, plus earlier DNS recovery work. Their raw private receipts are not part of
this public repository, and some checks predate subsequent configuration changes.

| Area | What the available record supports | What it does not establish |
| --- | --- | --- |
| DNS | Dated native backup/isolated-restore work reported | Fresh all-member recovery of the later transport configuration |
| CA/dashboard | Local consumer dumps and selected restore parity reported | Loss-of-site recovery, root custody or complete dependency restoration |
| PostgreSQL | Replication configuration and selected consumer checks documented | Full PostgreSQL/etcd cluster restore or forced-failover acceptance |
| Entire lab | Five nodes online and selected service-manager states observed | Whole-home interruption/reconnection, reboot recovery, offsite automation or agreed RPO/RTO |

Replication, persistent volumes, HTML exports and configuration copies solve
different problems. None is interchangeable with a consistent backup and a tested
restore of current compatible data, identities and dependencies. No verified
whole-lab recovery process is claimed here.

## Changes and rollback

Operational work needs its own target list, current backup source, dependency and
quorum review, rollback boundary and application verification. This revision does
not restart services, migrate workloads, retire VMs or change live DNS/TLS.

For a route fault, a scoped current route preimage is different from a whole-host
snapshot. For CA/database recovery, stale snapshots can discard newer shared state.
For BookStack, the original application key, database and uploaded files belong
together; an HTML export is offline reading, not an application backup.

Unresolved work includes full current-system recovery/failover/reboot acceptance,
delivered monitoring alerts, automatic offsite retention, agreed RPO/RTO and
completion of the management/core-services retirement plan.

[Evidence ledger](verification.md) · [Revision scope](revision-2026-11.md)
