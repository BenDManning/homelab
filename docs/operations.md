# Recovery: preserve the right state

A running replica and a restorable backup solve different failures. Replication
can keep a service available after member loss, but it can also copy an accidental
deletion to every member. Recovery needs data from before the mistake and the
identities and configuration required to use it.

## Recover applications, not just disks

| Component | State that belongs together |
| --- | --- |
| BookStack example | Database, uploaded files, application key and credentials |
| Certificate authority | CA database, signing material and the trust configuration needed by clients |
| PostgreSQL cluster | Database data, coordination state and a compatible cluster configuration |
| DNS | Authoritative zones and the configuration for ingress, recursion and trust |

A BookStack HTML export is useful for offline reading, but it cannot replace its
application database and uploads. Similarly, a SQL dump of a CA consumer is not a
backup of the entire PostgreSQL cluster.

## Availability has dependencies

The [CA/database cycle](services/access-and-identity.md#the-cadatabase-dependency-cycle)
is a concrete example: certificates may be needed before the service that renews
them can start. Recovery planning has to account for validity periods and a
separate path to recover signing capability.

DNS and database replicas share physical hosts. Their guest counts therefore
cannot be added together as independent failure domains. Loss of the site is a
different case from loss of one member.

## Measure the outcome

A service-manager status checks a process; a successful connection checks a path.
Neither proves that a restored application can read its data, authenticate a user
and accept a new write. Recovery timing needs to include those application checks.

The examples here do not implement whole-site recovery or establish an RPO/RTO.
The [watchdog](../offsite/README.md) and [alert rules](../monitoring/README.md)
address detection and notification, not restoration.
