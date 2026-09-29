# Offsite watchdog

A Linux/Python reachability observer with a durable SQLite notification outbox.
Run it outside the home's power and network failure domain. Requires Python 3.10+
with its standard library; systemd is optional. No packages or ntfy server are included.

## Local checks

From this directory, without live targets or credentials:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 watchdog.py --help
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v
```

Tests bind loopback HTTP/TCP fixtures and use temporary state outside this directory
(`TMPDIR` can select the location). They exercise debounce, persistence, failed
publication/retry across CLI processes, and HTTP/configuration safety boundaries.

## Setup

1. Copy `config.example.json` to a **private runtime location**. Replace every
   documentation address and `management.example.net`; these are not working targets.
   Keep the six role names. Choose home witnesses in useful failure domains and
   two independent external services that permit your checks.
2. HTTP(S) health requires status 200 and a JSON object containing `"healthy": true`.
   HTTPS connects to literal `ip` but uses `hostname` for SNI, certificate validation
   and the Host header, without resolving it. Install the appropriate trusted CA;
   there is no insecure TLS option. Plain HTTP probes are loopback-only.
3. Provision ntfy separately using its [installation](https://docs.ntfy.sh/install/)
   and [authentication](https://docs.ntfy.sh/config/) documentation. Require default-deny
   auth, a non-admin **write-only publisher** and separate **read-only subscriber**
   on your topic. Verify anonymous access, publisher reads and subscriber writes fail.
   Configure persistent ntfy storage and retention independently.
4. `publish_url` is the JSON publishing endpoint, normally the server root, not a
   topic URL. The example expects ntfy bound to `127.0.0.1:2586`; expose a separately
   secured HTTPS endpoint for subscribers. Remote publishing requires trusted HTTPS
   and system DNS independent of home. URL credentials, queries, fragments, redirects
   and environment proxies are not supported.
5. Create a private runtime credential file. Its JSON format is
   `{"username":"PUBLISHER_USER","password":"REPLACE_WITH_RUNTIME_SECRET"}`:
   nonsecret placeholders, not supplied credentials. Use mode `0600`, a protected
   state directory (`0700`), and ownership suitable for the service account.
   Never put passwords in source control, URLs or command arguments.
6. Add the server/topic/subscriber to your [phone client](https://docs.ntfy.sh/subscribe/phone/).
   Check background permissions and independently test delivery over cellular.
   An ntfy receipt is server acceptance, **not proof of phone delivery**.

After provisioning and reviewing targets, a real invocation is:

```sh
python3 watchdog.py --config /etc/offsite-watchdog/config.json \
  --credentials /etc/offsite-watchdog/publisher.json \
  --state /var/lib/offsite-watchdog/state.db
```

This **probes and may publish**. `--test` is not a dry run: it requires loopback
probes/publisher, a `TEST` label and non-default state. Use fresh isolated state
and fixture credentials; the guard cannot recognize every custom production path.

### Optional systemd templates

Create a non-login `offsite-watchdog` user/group. Place the runtime at
`/opt/offsite-watchdog/watchdog.py` and root-owned, mode-`0600` configuration and
publisher files under `/etc/offsite-watchdog/`. The service uses `LoadCredential`
and `%d`; use a systemd version supporting both. `StateDirectory` creates private
state under `/var/lib/offsite-watchdog/`.

Review the `.service`/`.timer` paths, limits and network access before installing
under `/etc/systemd/system/`. Add ordering for your own ntfy/overlay service names
as needed. Enable the timer only when ready to notify. It runs every minute;
missed runs produce one catch-up observation, not historical samples. Its 45-second
service deadline may interrupt slow batches; unacknowledged events remain queued.

## Behavior and limitations

Classification is ordered:

| Condition | Observation |
|---|---|
| `HEALTHY` | Management health succeeds, regardless of other probes |
| `MONITORING_ONLY_LOSS` | Health fails; management TCP responds |
| `MANAGEMENT_HOST_LOSS` | Both management checks fail; core or network responds |
| `HOME_MULTI_TARGET_LOSS` | All home checks fail; an external witness responds |
| `OFFSITE_CONNECTIVITY_LOSS` | All six fail |

Defaults: three consecutive same-class failures, two healthy samples for recovery,
30-minute reminders, five-second per-socket-operation timeouts. Probes run concurrently;
the standalone CLI has no overall deadline. A gap over 150 seconds or backward clock
step resets debounce. Pending messages suppress reminders. TCP does not test application
health, and `HEALTHY` does not mean every witness is healthy.

State changes and queued events commit together. Publication retries oldest first,
at most 20 per run, stopping on failure. **At-least-once** delivery can duplicate
server-accepted messages if the process crashes before recording the receipt;
stable event UUIDs support correlation. Old alerts can arrive after recovery.
Health and receipt responses are capped at 4096 bytes. Only nonblank receipt IDs
acknowledge publication. Exit 0 means no error in the attempted delivery batch,
not healthy targets or an empty queue; invalid config exits 2, other errors nonzero.

Acknowledged rows outside the newest 2000 outbox rows are pruned; pending events
are never silently removed. The database has a 16384-page ceiling (journal files
are additional); disk exhaustion fails the run. One state path is locked against
concurrent CLI runs. Use one scheduler, protected state and stable configuration:
there is no state migration, config-change reset or self-monitoring. Deleting state
loses queued events and starts debounce again.

Reachability symptoms are **not proof of power loss or an ISP outage**. Routing,
firewall or overlay failures can look identical; offsite-host/ntfy failure can
prevent immediate alerts. Local tests do not verify real ntfy auth, deployed TLS,
phone delivery, reboot behavior or whole-home outage performance. Those require
separately authorized operational tests.
