# Infrastructure designs

These notes follow three paths through the lab:

- [DNS](dns.md): from a client query to private zones or an upstream resolver.
- [PostgreSQL](postgresql.md): from a client endpoint to the elected writer.
- [Certificates and routing](access-and-identity.md): from frontend TLS to backend
  identity, including the CA's database dependency.

The [architecture diagram](../architecture.html) shows their relationships;
[recovery notes](../operations.md) explain what replication leaves unsolved.
