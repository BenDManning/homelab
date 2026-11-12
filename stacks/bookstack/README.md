# BookStack manual

## Publication status — November 2026

Retained new-instance example from the initial release, not a fresh export of
the running wiki or a plan to move it. The management VM is due for retirement;
this publication does not establish BookStack's successor placement. Image pins
are historical example versions, not a current production/support claim.
See [revision scope](../../docs/revision-2026-11.md).

Pinned [LinuxServer BookStack](https://docs.linuxserver.io/images/docker-bookstack/)
and MariaDB Compose example. The database has no published port. Application and
database data use separate named volumes; the initial web binding is loopback
only. This is a new-instance recipe, not an upgrade or import command for the
existing wiki.

## Bootstrap privately

Requirements: Linux Docker host, Docker Compose, OpenSSL, and a password manager.
From this directory:

```sh
cp .env.example .env
chmod 600 .env
```

Fill the empty secret values locally. Generate a new application key using the
pinned image's helper (output is a secret; save it privately):

```sh
docker run --rm --network none --tmpfs /config --entrypoint /bin/bash   lscr.io/linuxserver/bookstack:v26.09-ls285@sha256:5cf80598bb63bb7d475edb391af244f8ec5e9ac86018c197ad73a565e95a0012 appkey
```

Use `openssl rand -hex 32` separately for each database password. Save the key
and both passwords in a password manager as well as the protected local `.env`.
Never commit `.env`. Docker/Portainer administrators can inspect environment
values; these variables are not hidden from administrators.

Set `PUID` and `PGID` for application file ownership. The image's init process
runs as root; those variables do not make the whole container rootless.

```sh
docker compose config --quiet
docker compose up -d
docker compose ps
curl --fail http://127.0.0.1:6875/status
```

Wait for both health checks. Before making the service reachable by other users,
replace the image's default administrator with your own account using the
interactive [admin command](https://www.bookstackapp.com/docs/admin/commands/):

```sh
docker compose exec bookstack php /app/www/artisan bookstack:create-admin --initial
```

Enter a unique password at the prompt, not as a command-line option. Confirm your
new login works and that the default account no longer works. Use the same
loopback address in your browser as `BOOKSTACK_APP_URL`; a remote host can be
accessed with an SSH local forward. Keep registration disabled.

## Configure the real URL and permissions

For private production access, arrange DNS and HTTPS in your existing proxy.
Set `BOOKSTACK_APP_URL` to the exact HTTPS origin,
`BOOKSTACK_SECURE_COOKIE=true`, and `BOOKSTACK_TRUSTED_PROXIES` to only the
verified proxy source addresses. Choose an assigned backend bind address only
when a separate proxy needs it, and restrict that path with Docker-aware
firewall rules. Do not publish the database port or trust every proxy.

Recreate through the deployment owner after changing environment values. If
content already exists, changing `APP_URL` also requires BookStack's
`bookstack:update-url` migration, with a database backup first; follow the
upstream instructions rather than treating it as a harmless hostname edit.

The original example described anonymous read/search and authenticated editing.
That current live permission policy was not rechecked. To choose that policy for
your own instance, enable public viewing in settings and give the Public role view/export
permissions only—no create/update/delete permissions. Check a signed-out browser
can read/search but cannot edit, then save a real edit using the editor account.
This policy is not enabled automatically by Compose. Outbound email and emailed
password resets are not configured by this example.

## Persistence and recovery

An ordinary container restart should retain both named volumes. Verify content,
login, search, and a saved edit after a restart. Do not run `docker compose down
-v` against data you intend to keep: it deletes the volumes.

A restorable backup needs the database, the complete `/config` volume (including
uploads), and the original `APP_KEY` plus credentials. A standalone HTML export
is only an offline document copy. Follow the
[BookStack backup/restore guide](https://www.bookstackapp.com/docs/admin/backup-restore/)
and test a restore separately. This repository does not install a backup job or
claim the lab has completed that test.
