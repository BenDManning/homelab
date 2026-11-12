# Access, certificates and shared dependencies

## Proxy placement is no longer the old core-services layout

The 12 November inventory places a dedicated Traefik container on pve04 and a
step-ca VM on pve05. The old core-services VM remains running on pve02 and is due
for retirement; this does not imply all of its applications have moved.

Maintained November records describe manual DNS records and Traefik's native
watched File provider, not automatic Docker/Proxmox service discovery. Three
routing cases must remain distinct:

| Route type | TLS boundary | Why it matters |
| --- | --- | --- |
| Application frontend | Browser HTTPS terminates at Traefik | Frontend reachability is not authenticated app acceptance |
| Selected private backends | A separate TLS connection verifies backend name and root | A frontend certificate does not verify the backend identity |
| Certificate authority | Exact-SNI TCP passthrough; CA terminates TLS/mTLS | HTTP termination is not interchangeable with preserving client mTLS |

The documented administration API is loopback-only. Public example links do not
create DNS records, trust roots, proxy routes, permissions or remote-access rules.
A current working application cannot be inferred from a Homepage card.

## CA and database depend on one another

Maintained 11 November records describe step-ca using PostgreSQL for authoritative
state and hardware-backed intermediate signing. The dashboard has a scoped CA
administration identity, a SELECT-only CA-state SQL role and a separate app-state
writer; it is not the operator's root or Super Admin identity.

The CA needs the database to start, while database certificate renewal needs the
CA. Recovery therefore requires more than restarting guests in arbitrary order:
certificate validity, independent signing recovery, protected keys and compatible
database state are separate dependencies. A rehearsed break-glass substep does
not demonstrate full CA/database disaster recovery.

A separate OpenClaw guest is present on pve03. Maintained records describe its
HTTPS/WSS publication and renewal lifecycle; its presence does not prove every
browser, mobile path or renewal is healthy today. Broader identity-provider,
SSH-CA and Wi-Fi identity work remains planning, not an implemented capability.

## Evidence boundary

Fresh 12 November inspection establishes guest placement/running state, not
proxy configuration, certificate issuance or rendered browser behavior. Design
statements above summarize dated private records. Private endpoints, key custody,
credential references and live configuration are intentionally not reproduced.

[Verification](../verification.md) · [Recovery](../operations.md)
