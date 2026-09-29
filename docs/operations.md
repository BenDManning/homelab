# Operations and boundaries

## Access is more than DNS

Most web applications follow `browser → internal DNS → Traefik → application`.
DNS resolves a name; it does not provide a firewall. Network reachability, TLS,
and application permissions are separate checks.

Homepage has no application login or special Homepage-only IP gate in this lab.
The wiki allows reading and searching without login within existing network
reachability; editing requires an account. Neither policy is a reason to expose
an internal application on the public internet. The examples bind to loopback by
default and do not create public DNS records, router forwards, or Tailnet ACLs.

Physical Proxmox nodes remain LAN-only. Termix uses stored SSH keys to reach
nodes; installing Tailscale on the hypervisors is not required. AI sharing uses
its own permitted paths, not the core management front door.

## Service ownership

Portainer is the authority for stacks it manages. Use the files here as examples
or recovery references, not as permission to run duplicate stacks alongside an
existing installation. Changing a Compose file here does not update the live lab.

The management VM and Hermes VM have different jobs. Monitoring, Semaphore,
Homepage, and BookStack belong on management; Hermes and its tooling belong on
the Hermes VM. Moving a critical service, taking over an address, or deleting a
workload is a separately planned change.

## Monitoring

Home monitoring observes host metrics, endpoint probes, and alert delivery. The
offsite observer checks selected home paths without relying on the home's DNS
resolver. Its separate ntfy subscription is useful when the home notification
service cannot be reached.

An HTTP health check, successful notification enqueue, and a message appearing
on a phone prove different things. Multi-target loss suggests a home or network
path problem; it does not diagnose an ISP failure or power cut by itself.

Start diagnosis with the scope of the failure:

1. Check whether the client can reach the intended network.
2. Check DNS and TLS identity without bypassing certificate warnings.
3. Compare proxy reachability with application health.
4. Inspect the owning host and service logs before restarting anything.
5. For alerts, distinguish missing metrics, failed probes, and failed delivery.

## Maintenance

Semaphore runs read-only audits separately from manual update/reboot jobs.
Audits inspect host services, cached package candidates, cluster state, and
existing containers; they are not automatic patching or fresh vulnerability
scans. The full private inventory and privileged maintenance runner are not
included here.

Before a disruptive change: agree on targets and a maintenance window, establish
a usable backup and rollback path, check cluster quorum and affected guests,
then change one bounded group and verify the actual applications afterward.
A controller VM running on the node being rebooted is a dependency to plan for,
not a routine unattended operation.

## Backup status

Scheduled backup implementation is deferred until a NAS is available. Existing
copies have not been represented as comprehensive coverage. **NOT PROTECTED**
is the accurate recovery status; no full restore drill is claimed.

Future protection needs to cover application data and external dependencies:

- BookStack: a consistent database backup, uploaded files/config volume, and the
  original application key and database credentials stored outside Git.
- Monitoring: relevant application databases and configuration, with secrets
  recovered through the established secret store.
- Infrastructure: DNS/proxy/network configuration and an independent recovery
  path to the hypervisors and secret store.

Test restoration on an isolated destination before relying on it. BookStack's
**Export → Contained Web File (HTML)** is useful offline reading, not an
application backup. Never rotate `APP_KEY` as a routine BookStack upgrade step.

The original lab temporarily suppresses selected missing/overdue-backup phone
reminders while retaining the rules and a visible unprotected status. This is an
acknowledged gap, not a recommended default for another deployment.
