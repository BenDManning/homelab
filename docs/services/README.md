# Service design index

These public summaries describe the current documented direction without exporting
private deployment files. They separate the 12 November runtime observation from
earlier maintained configuration records. They are not deployment recipes.

| Subsystem | Design question | Public summary |
| --- | --- | --- |
| DNS | How does one client endpoint use three resolver guests? | [DNS pool](dns.md) |
| PostgreSQL | How do leadership, client routing and consumers differ? | [Single-writer database cluster](postgresql.md) |
| Routing and identity | Where does TLS terminate, and what depends on the CA? | [Access and certificates](access-and-identity.md) |

[Inventory](../inventory.md) owns dated guest placement; [verification](../verification.md)
owns evidence limits. Actual addresses, trust material, native configurations,
application data and operational credentials remain private.
