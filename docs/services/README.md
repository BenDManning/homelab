# Infrastructure designs

These are a few things I have built in the lab, for different reasons:

- [DNS](dns.md): my old setup kept breaking, so I built a cluster to make it more
  resilient.
- [PostgreSQL](postgresql.md): I was bored, started watching a cluster-building
  series, and discovered how involved it was. I ended up using Patroni.
- [Certificates and routing](access-and-identity.md): from frontend TLS to backend
  identity, including the CA's database dependency.

The [architecture diagram](../architecture.html) shows their relationships;
[recovery notes](../operations.md) explain what replication leaves unsolved.
