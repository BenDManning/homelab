# Verification ledger — 12 November 2026

This ledger distinguishes observations, configuration descriptions and tests.
It is a sanitized summary, not a raw export of private operational evidence.
It does not make the private records independently reproducible by public readers.

## System evidence

| Claim | Source and date | What was actually established |
| --- | --- | --- |
| Five online nodes / quorum | Authenticated Proxmox `/nodes`, `/cluster/status`, 12 November 00:35–00:36 UTC | All five online; cluster quorate at observation time |
| 21 guests, 17 running / four stopped | Authenticated `/cluster/resources` inventory, same interval | Hypervisor placement and states in [inventory](inventory.md) |
| dns1 selected services started | In-guest service-manager status, 12 November | DNS, dnscrypt-proxy, dnsdist, nginx and Keepalived reported started |
| pg1 selected services active | In-guest service-manager status, 12 November | Patroni, HAProxy and Keepalived reported active |
| Management/core retirement | Owner statement, 12 November | Retirement intent, not a completed cutover or approved deletion |
| DNS path and transport | Maintained private configuration records: 5 November configuration / 8 November selected receipts | Dated documented design; no fresh all-member configuration or functional test in this revision |
| PostgreSQL roles/consumers | Maintained private records: 11 November selected native/consumer verification | Reported primary/two replicas and scoped consumer checks, not a new failover drill |
| Proxy/CA/renewal boundaries | Maintained private November records, selected observations through 11 November | Documented routing, identity and dependency design; no fresh application/issuance inspection in this revision |
| Scoped restore work | Maintained private DNS and CA/dashboard records, November | Reported bounded restore work; no current full-system recovery claim |

Fresh runtime evidence is stronger for current guest state than the old public
README. Earlier configuration records are more detailed but remain dated. Source
code and tests demonstrate mechanisms, not their deployment. Private addresses,
keys, endpoints and raw captures are deliberately excluded.

## Repository verification performed

Run on 12 November against this revision, without live targets or notification
services:

| Check | Result | Boundary |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s offsite -v` | **13 tests passed** | Local loopback fixtures, temporary state; includes cross-process failed-publication retry |
| `python3 offsite/watchdog.py --help` | Passed | CLI parsing only; no probes |
| YAML / example JSON parsing | Passed | Syntax/load check, not Compose interpolation or Prometheus semantic validation |
| Relative documentation links and local fragments | Passed | Repository-local paths/anchors, not external site availability |
| SVG XML parsing and HTML diagram rendering | Passed | Chromium desktop render inspected; HTML embeds the same standalone SVG |
| `git diff --check` | Passed | Whitespace/conflict-marker check, not operational acceptance |
| Public-content review | Reviewed | No private domain/address/credential/raw evidence copied; changes limited to this repo |

The watchdog code and Prometheus rule expressions were not changed. Docker,
promtool and amtool were unavailable in the revision environment, so Compose
runtime validation and native monitoring rule/route tests were **not rerun**.
The monitoring reference retains the original publication's versioned commands
and labels its earlier reported validation as historical.

## Not tested here

No operational failover, restart, migration, retirement, backup job, restore,
TLS issuance/renewal, phone delivery or whole-home interruption was performed.
The latest inventory does not establish current watchdog deployment or a working
monitoring stack. Configuration records do not imply every client/VLAN route or
rendered browser workflow is accepted. No full disaster-recovery or RPO/RTO
claim is made.

[Revision scope](revision-2026-11.md) · [Operations](operations.md)
