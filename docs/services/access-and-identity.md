# Certificates and routing

Traefik handles application routing using its watched File provider. DNS records
and routes are explicit rather than discovered through a Docker socket.

Three connection types need different handling:

| Connection | TLS boundary | Reason |
| --- | --- | --- |
| Browser to application frontend | HTTPS terminates at Traefik | Presents the frontend certificate and routes HTTP |
| Proxy to selected backend | A separate TLS connection verifies the backend name and root | Protects the backend hop as well as the frontend |
| Client to certificate authority | Exact-SNI TCP passthrough; the CA terminates TLS/mTLS | Preserves client-certificate authentication |

A frontend certificate says nothing about whether the proxy verifies its backend.
Likewise, turning a CA route into ordinary HTTP termination would change who
receives and verifies a client's certificate.

## The CA/database dependency cycle

The step-ca design stores authoritative state in PostgreSQL and uses
hardware-backed intermediate signing. Its administration application has a
scoped CA identity, a read-only CA-state database role and a separate writer for
its own application data.

The CA needs the database to start, but database certificate renewal needs the
CA. That creates a recovery cycle: restarting everything in an arbitrary order
is not enough if the database certificate has expired. Certificate validity,
recoverable signing material and compatible database state all matter.

Hardware-backed signing protects a key; it does not by itself make the service
recoverable. These notes explain the dependencies, not a completed disaster
recovery exercise.

[Database design](postgresql.md) · [Recovery](../operations.md)
