# Homelab

I use a five-node Proxmox lab to work on the infrastructure behind everyday
services: DNS, databases, certificates and monitoring. This repo collects a few
of those designs, along with code and configuration examples.

The interesting parts are the boundaries: which component chooses a database
writer, where TLS ends, and how an alert survives a failed delivery.

![Selected infrastructure relationships](docs/architecture.svg)

## Infrastructure designs

- **[DNS](docs/services/dns.md)** — my DNS kept breaking, so I built a
  three-resolver cluster to make it more resilient.
- **[PostgreSQL](docs/services/postgresql.md)** — a curiosity project that got
  more complicated than I expected, ending up with Patroni, etcd and HAProxy.
- **[Certificates and routing](docs/services/access-and-identity.md)** — frontend
  HTTPS, backend identity checks and a CA whose database dependency complicates
  recovery.
- **[Recovery](docs/operations.md)** — the state and dependencies that have to
  survive together, rather than just keeping a VM running.

## Code and examples

| Project | Engineering focus |
| --- | --- |
| [Offsite watchdog](offsite/README.md) | SQLite outbox, debounce and notification retry across process runs |
| [Prometheus alerts](monitoring/README.md) | Distinguishing failed checks from missing telemetry, with rule fixtures |
| [Homepage directory](stacks/homepage/README.md) | A links-only dashboard without Docker socket access or integration credentials |
| [BookStack](stacks/bookstack/README.md) | Application/database isolation and the state needed for recovery |

The watchdog includes local Python tests; the alert rules include Prometheus test
fixtures. The service write-ups explain the design, not a measured failover or
whole-site recovery result. Examples use reserved addresses and placeholder
secrets. The service inventory and deployment configuration stay private.

## License

[MIT](LICENSE) for this repository's code, documentation and configuration.
Third-party applications retain their own licenses.
