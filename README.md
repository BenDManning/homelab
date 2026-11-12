# Homelab

My five-node Proxmox lab runs distributed DNS and PostgreSQL alongside local AI,
media, networking, a certificate authority and OpenClaw. The older management and
core-services VMs remain running but are due for retirement; they are transitional,
not the intended long-term service layout.

This repository is a public account of the system's design and selected engineering
work, not a copy of the private operating manual or a complete deployment bundle.

![Five-node lab placement](docs/architecture.svg)

## The running system

An authenticated inspection on **12 November 2026** found all five Proxmox nodes
online, cluster quorum, and **21 guests: 17 running, four stopped**.

| Host | Observed workloads |
| --- | --- |
| pve01 | Management (due for retirement), VPN and NTP |
| pve02 | Core services (due for retirement), DNS member 1 and PostgreSQL member 1 |
| pve03 | UniFi, AI, media and OpenClaw |
| pve04 | Firefly, Traefik, DNS member 2 and PostgreSQL member 2 |
| pve05 | step-ca, DNS member 3 and PostgreSQL member 3 |

The [inventory](docs/inventory.md) includes stopped guests and the inspection's
limits. Placement is an observation, not proof of application health or failover.
Retirement has not happened, and no replacement destination or date is claimed.

## Shared infrastructure, separate responsibilities

**DNS has a frontend and a resolver pool.** Three guests on different hosts form
the documented DNS design: a Keepalived client address, dnsdist ingress,
Technitium authoritative/recursive service and DNSCrypt upstreams. The internal
forwarding leg is plaintext, even when the client and recursive upstream legs
are encrypted. [DNS design and evidence](docs/services/dns.md).

**PostgreSQL is single-writer, not three writable databases.** Patroni, HAProxy
and Keepalived separate member leadership from the client endpoint. Replica
routing can lag; replication is not a backup. DNS query logging and CA state
introduce shared dependencies. [Database design](docs/services/postgresql.md).

**Routing and certificate identity are different layers.** A dedicated Traefik
guest now appears on pve04, outside the older core-services VM. The documented
routes distinguish HTTP termination, verified backend TLS and CA TLS passthrough.
The CA depends on PostgreSQL; database TLS renewal also depends on the CA.
[Access, certificates and recovery dependencies](docs/services/access-and-identity.md).

## Selected engineering work

**A directory without a Docker control path.** The published
[Homepage example](stacks/homepage/README.md) links to services without a Docker
socket or integration credentials. The [BookStack example](stacks/bookstack/README.md)
publishes application/database configuration without reproducing the private manual.
Neither example is a live export or the retirement migration plan.

**Notifications that survive a failed publish.** The [Python watchdog](offsite/README.md)
commits state transitions and queued events together in SQLite, then retries across
runs. This accepts duplicate or delayed notifications in exchange for persistence.
Its local tests include a failed publication retried by a second CLI process.
The code is published; its current offsite deployment is not established.

**Missing evidence is not a healthy zero.** The [Prometheus rules](monitoring/README.md)
distinguish unsuccessful endpoint probes, failed exporter scrapes and absent backup
telemetry. Fixtures cover missing reports, future timestamps and cross-source
matching. A reported backup timestamp still does not prove a restore works.

## What is established—and what is not

The [verification ledger](docs/verification.md) separates fresh hypervisor and
selected guest observations, dated private configuration records, public source,
and local test results. Historical deployment statements are not current status.

The latest inspection did **not** demonstrate DNS/PostgreSQL failover, full-cluster
restoration, end-to-end phone alerts or recovery after a whole-home interruption.
Some scoped backup/restore work exists in the maintained records; that is not full
lab recovery coverage. The old blanket “all scheduled backups await a NAS” statement
is no longer an adequate description of the system.

[Operations and recovery boundaries](docs/operations.md) ·
[Revision scope and example status](docs/revision-2026-11.md)

## Published material

| Area | What is included |
| --- | --- |
| [System map](docs/inventory.md) | Dated five-node inventory and lifecycle status |
| [Service designs](docs/services/README.md) | DNS, PostgreSQL, routing and CA dependency explanations |
| [Homepage](stacks/homepage/README.md) | Links-only five-node directory example |
| [BookStack](stacks/bookstack/README.md) | Isolated new-instance Compose example |
| [Monitoring](monitoring/README.md) | Rules, fixtures and receiver placeholder |
| [Offsite observer](offsite/README.md) | Watchdog source, local tests and optional systemd templates |

Examples use reserved domains and documentation IP ranges. Image pins describe
published artifacts, not current production versions or an update recommendation.
Private inventories, accounts, addresses, keys, databases and manual contents are
not published here.

## License

The configuration examples, documentation and code are licensed under the
[MIT License](LICENSE). Third-party applications retain their own licenses.
