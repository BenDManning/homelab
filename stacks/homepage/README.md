# Homepage directory

## Publication status — November 2026

The Compose image/settings remain a retained example from the initial release;
the service links have been refreshed as a sanitized five-node illustration.
Neither is a current production export. All URLs are placeholders, including
links for services whose application health was not checked. A directory entry
is not a deployment or liveness assertion. Management/core retirement does not
happen through this example. See [revision scope](../../docs/revision-2026-11.md).

A links-only [Homepage](https://gethomepage.dev/) configuration with service
search, descriptions, and a mobile search button. It contains no integration
credentials or Docker socket mount. All destinations are examples.

## Local preview

Use a separate copy on a Linux Docker host with Compose. From this directory:

```sh
cp .env.example .env
id -u
id -g
```

Set `PUID` and `PGID` in `.env` to the IDs that own `config/`. The application
needs to write this directory, so do not mount it read-only. Do not recursively
change ownership outside this copy.

```sh
docker compose config --quiet
docker compose up -d
docker compose ps
curl --fail http://127.0.0.1:3002/api/healthcheck
```

Open `http://localhost:3002` on that host. For a remote host, use an SSH local
forward instead of opening the backend to every interface. The backend binds
only to loopback unless you deliberately change `BIND_IP`.

Edit `config/services.yaml` for your own links. The sample AI names stand in for
your own private access paths; they are not real Tailnet names. The Proxmox
addresses are documentation-only, not usable node addresses.

On first startup, use Homepage's bottom-right refresh control once to apply the
bundled title, layout, and search settings. Repeat after changing settings or
recreating the image if old settings remain. Confirm the browser displays the
current cards and that a search opens the intended link.

## Behind an existing proxy

Set `HOMEPAGE_ALLOWED_HOSTS` to the exact requested hostname (including port for
nonstandard ports). If the proxy is on another host, choose a specific assigned
backend address and restrict backend reachability using your Docker-aware
firewall. Do not use `0.0.0.0` simply to avoid understanding the route.

Supply DNS, TLS, and the proxy route through your existing infrastructure. This
example creates none of them. Homepage itself has no login; keep its reachability
appropriate to the directory's contents. Other services retain their own login
and network restrictions.

For a temporary preview, `docker compose down` stops and removes its containers
and network. The files in `config/` remain. Do not apply this command to the live
Portainer-owned stack.
