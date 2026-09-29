# Monitoring excerpts

Reusable Prometheus alert rules, behavior tests, and an Alertmanager routing
example—not a deployable stack. No inventory, exporters, backup jobs, credentials,
deployment automation, or notification service is included.

## Integrate

- Load `rules/alerts.yml` through your existing Prometheus `rule_files` list.
  Mount it read-only and use the path visible inside your Prometheus runtime.
  Configure Prometheus-to-Alertmanager delivery separately.
- The file has `infrastructure`, `backup-telemetry`, and `monitoring-health`
  groups. Select groups deliberately for your installation; missing backup
  telemetry is **not** interpreted as successful protection. Review thresholds
  against your own workload and backup schedule before enabling notifications.
- Provide Linux node_exporter CPU, memory, filesystem, and (if used) textfile
  collector metrics. `instance` and `job` identify each scrape source. Filesystem
  series must share `instance`, `job`, `device`, `mountpoint`, and `fstype` labels;
  readonly matching includes `job` to avoid cross-scrape false positives.
  CPU aggregation preserves `instance` and `job`, not custom `host` labels.
- Blackbox rules select exactly `blackbox-http`, `blackbox-tcp`, or `blackbox-dns`
  as the `job` label. Set `instance` to the probed target; optional `service`
  labels survive into alerts. Change both selectors if your job names differ.
  `EndpointDown` means the probe returned zero; `ExporterDown` means a scrape
  failed. A vanished target is not an `up == 0` sample. The empty-inventory rule
  detects only the absence of **all** selected probe jobs, not individual missing
  targets. Remove that rule if endpoint probing is intentionally unused.
- Scrape Prometheus and Alertmanager themselves for evaluation/delivery failure
  counters. A stopped monitoring system cannot reliably report its own outage;
  independent monitoring is still needed.
- Merge `alertmanager.example.yml` into your existing configuration. Replace its
  reserved `.invalid` HTTPS URL with a receiver that accepts Alertmanager webhook
  JSON. Supply any required authentication via your deployment's secret-file
  mechanism, not in this directory. The example sends firing and resolved
  notifications for **all alerts**, including backup alerts. It has no discard
  receiver. The placeholder URL is intentionally unusable; validation does not
  establish notification delivery.

### Backup metric contract and limitations

Supply gauges through your own exporter/textfile emitter:

- `homelab_backup_expected{backup_job="example-backup"} 1`: keep this inventory
  present independently of backup success. Value `0` excludes that job from the
  expected-but-missing rule; it does not suppress other backup rules.
- `homelab_backup_last_success_timestamp_seconds{backup_job="example-backup"}`:
  Unix timestamp in seconds of the last genuinely successful backup. Preserve
  that timestamp between scrapes; never replace it with the current scrape time.
  Emit it only after your own success checks, not just after starting a job.

`backup_job` must be globally unique within this Prometheus rule evaluation
scope. Expected inventory and success series match by that label even when
scraped from different instances. For multiple sites with overlapping job names,
change the matching labels and tests together. Keep clocks synchronized.

The defaults warn on no inventory (15 minutes), a missing expected job (1 hour),
a timestamp over 5 minutes in the future (10-minute hold), or a success older
than 36 hours (15-minute hold). Global absence uses a 1-hour lookback plus a
5-minute hold. On a new Prometheus with no history it can fire after 5 minutes;
it does not wait an extra hour to discover that the history is empty.
`TextfileCollectorError` covers **all** textfile metrics, not only backups.
The failure-counter rules require a positive 5-minute increase to persist for
5 minutes; they are not guaranteed to page on every isolated failure.

A timestamp is an emitter's claim, not proof of restore testing, offsite storage,
or backup integrity. These excerpts neither create backups nor establish that
an installation is protected. In the owner's deployment, scheduled backups are
deferred pending a NAS: **NOT PROTECTED**. That deployment backs off recurring
missing/overdue-backup reminders while retaining alert visibility. This is
context, not a recommendation to disable backup notifications elsewhere, and
that suppression route is deliberately **not** included here.

## Local validation

Requirements: a local Docker daemon and the two exact images below, already
cached. Commands use `--pull never`, no network, read-only mounts, and disposable
native tool entrypoints. Run from this directory. They create no files here,
start no monitoring services, and contact no targets or notification endpoints.

Validated with Prometheus/promtool **3.14.0** and Alertmanager/amtool **0.34.1**:

```sh
PROM_IMAGE='prom/prometheus@sha256:5ce7540c3c00ef4ab0c9d2c995c6a5b9c421f44b4a115d97a2c7af3b1c21cbb0'
AM_IMAGE='prom/alertmanager@sha256:e9733bafb1bdef9b00e25a21f8f99dc26a22224bf16641ad754d1649f4c3357a'

docker --context default run --pull never --rm --network none \
  -v "$PWD:/work:ro" --entrypoint /bin/promtool "$PROM_IMAGE" \
  check rules /work/rules/alerts.yml

docker --context default run --pull never --rm --network none \
  -v "$PWD:/work:ro" -w /work/tests --entrypoint /bin/promtool "$PROM_IMAGE" \
  test rules rules.test.yml

docker --context default run --pull never --rm --network none \
  -v "$PWD:/work:ro" --entrypoint /bin/amtool "$AM_IMAGE" \
  check-config /work/alertmanager.example.yml

docker --context default run --pull never --rm --network none \
  -v "$PWD:/work:ro" --entrypoint /bin/amtool "$AM_IMAGE" \
  config routes test --config.file=/work/alertmanager.example.yml \
  --verify.receivers=webhook alertname=BackupTooOld severity=critical
```

The suite exercises actual rule evaluation: hold times, firing/recovery,
threshold boundaries, absent and expected backups, clock skew, DNS-only probe
inventory, readonly cross-job isolation, ephemeral filesystem exclusion, and
monitoring failure counters. It does not assert production readiness or real
notification delivery. Before deployment, also run `promtool check config`
against **your complete** Prometheus configuration; none is supplied here.

## Grafana

No dashboard is included. Panels depend on your inventory, data source, and
metric emitters; importing this lab's fixed counts would give misleading health
indicators. Keep missing telemetry distinct from a healthy zero when building
your own overview.
