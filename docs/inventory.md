# Dated lab inventory

## Observation: 12 November 2026

Authenticated Proxmox API inspection at 00:35–00:36 UTC reported five online
nodes, a quorate cluster and 21 guests (17 running, four stopped). These are
hypervisor states, not application acceptance results. The table preserves the
observed names and distinguishes VM from container (CT); it publishes no addresses.

| Node | Guest | Type | Observed state | Lifecycle / qualification |
| --- | --- | --- | --- | --- |
| pve01 | network-services | VM | stopped | Older network-services guest; not the current three-member DNS pool |
| pve01 | management01 | VM | running | Due for retirement, per owner |
| pve01 | vpn01 | VM | running | Inventory observation only |
| pve01 | ntp01 | CT | running | Inventory observation only |
| pve02 | core-services | VM | running | Due for retirement, per owner |
| pve02 | hermes01 | VM | stopped | No application check performed |
| pve02 | dns1 | CT | running | Selected service-manager check performed |
| pve02 | pg1 | CT | running | Selected service-manager check performed |
| pve02 | ca-offline-disk-restore | VM | stopped | Name is not evidence of a successful restore |
| pve03 | unifi-server-os | VM | running | Inventory observation only |
| pve03 | ai01 | CT | running | Inventory observation only |
| pve03 | media01 | VM | running | Inventory observation only |
| pve03 | openclaw | VM | running | Inventory observation only |
| pve04 | firefly | CT | running | Inventory observation only |
| pve04 | searxng | CT | stopped | No application check performed |
| pve04 | traefik | CT | running | Dedicated proxy guest; not the older core VM placement |
| pve04 | dns2 | CT | running | No fresh in-guest check |
| pve04 | pg2 | CT | running | No fresh in-guest check |
| pve05 | step-ca | VM | running | Inventory observation only |
| pve05 | dns3 | CT | running | No fresh in-guest check |
| pve05 | pg3 | CT | running | No fresh in-guest check |

In dns1, the service manager reported DNS, dnscrypt-proxy, dnsdist, nginx and
Keepalived started. In pg1, Patroni, HAProxy and Keepalived reported active.
Equivalent fresh checks were not performed in dns2/dns3 or pg2/pg3. Process state
alone proves neither correct answers nor replication, TLS, VIP ownership or failover.

## Transition, not a target-state promise

Management and core services still contain running workloads. The owner has marked
both VMs for retirement. No retirement sequence, application migration matrix,
cutover date or deletion is established by this publication. A separate proxy guest
does not mean every former core service has moved. The older three-node map is
superseded as current inventory, not rewritten as if it never existed.

The diagram shows the 17 running guests; the four stopped guests remain in this
table rather than being represented as active service paths. No external observer
was included in the fresh cluster inspection.

See [verification](verification.md), [service designs](services/README.md) and
[recovery boundaries](operations.md).
