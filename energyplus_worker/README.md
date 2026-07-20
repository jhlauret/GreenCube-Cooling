# energyplus_worker

Standalone process for GC-COOLING-15's EnergyPlus job execution. This is
deliberately **not** part of the `greencube_cooling` Odoo addon: it must
run outside the Odoo web/cron process, with no PostgreSQL access, so that
a long-running or crashing EnergyPlus invocation can never take down or
compromise the Odoo application server or its database.

## What it replaces

Earlier versions of this module ran EnergyPlus jobs from an Odoo `ir.cron`
(`_cron_process_pending_energyplus_jobs`), inside the same process that has
full ORM/DB access — which is exactly what GC-COOLING-15 forbids. That
cron has been removed (see `migrations/18.0.3.0.0/post-migrate.py` in the
addon). This worker is the replacement.

## How it talks to Odoo

Only over two HTTP routes (`controllers/api.py`), authenticated with a
shared-secret header — never a database connection, never an Odoo session:

- `POST /api/v1/greencube/cooling/energyplus-jobs/claim` — claims the
  oldest queued job and returns its frozen MERCURE snapshot payload.
- `POST /api/v1/greencube/cooling/energyplus-jobs/<job_id>/complete` —
  reports the outcome (`simulation_completed` / `simulation_unavailable` /
  `simulation_failed`) plus any artifacts.

The shared secret is an Odoo `ir.config_parameter`,
`greencube_cooling.energyplus_worker_key`. It must be set explicitly (e.g.
via `odoo-bin shell` or the Settings > Technical > System Parameters UI) —
if it is unset, the two routes return `503` unconditionally rather than
accepting unauthenticated requests.

## Running it

```bash
export GC_COOLING_API_BASE_URL="https://your-odoo-host"
export GC_COOLING_ENERGYPLUS_WORKER_KEY="<same value as the ir.config_parameter>"
export GC_COOLING_WORKER_POLL_INTERVAL_S=15   # optional, default 15
python3 energyplus_worker/worker.py
```

`--once` polls a single time and exits — useful for a systemd timer /
cron-on-the-worker-host deployment instead of a long-lived daemon:

```bash
python3 energyplus_worker/worker.py --once
```

### Suggested systemd unit (long-lived daemon, non-root)

```ini
[Unit]
Description=GreenCube Cooling EnergyPlus worker
After=network.target

[Service]
Type=simple
User=greencube-worker
Group=greencube-worker
Environment=GC_COOLING_API_BASE_URL=https://your-odoo-host
Environment=GC_COOLING_ENERGYPLUS_WORKER_KEY=change-me
WorkingDirectory=/opt/greencube_cooling
ExecStart=/usr/bin/python3 energyplus_worker/worker.py
Restart=on-failure
RestartSec=5
# No database credentials anywhere in this unit — the worker never needs any.

[Install]
WantedBy=multi-user.target
```

`greencube-worker` should be a dedicated, unprivileged system user with no
access to Odoo's filesystem, config, or PostgreSQL role — its only
capability is the shared worker key, itself scoped to exactly these two
routes server-side.

## What is honestly NOT built here

- No real EnergyPlus/Honeybee execution: `services/energyplus.py` always
  raises `EnergyPlusUnavailableError`/`EnergyPlusSimulationError` today
  (see its own docstring) — neither honeybee-energy/ladybug nor an actual
  EnergyPlus binary are expected to be installed anywhere in this MVP's
  target environment. This worker faithfully reports that, it does not
  fabricate a result.
- No durable queue (Redis/RQ/Celery/...): the "queue" is just the
  `queued_for_worker` rows in `greencube.cooling.calculation.job`, claimed
  one at a time over HTTP. There is no dead-letter mechanism beyond the
  job staying `simulation_failed`/`simulation_unavailable` — an operator
  has to notice and re-queue manually today.
- No per-job execution timeout around `run_energyplus_simulation` itself
  (only the outer HTTP calls have a timeout). Irrelevant while that
  function always raises immediately, but would need a real subprocess
  timeout (e.g. `subprocess.run(..., timeout=...)`) once an actual
  EnergyPlus binary is wired in.
- No sandboxing beyond "runs as an unprivileged OS user with no DB
  credentials" — no container/seccomp/network-namespace isolation.

## Tests

```bash
python3 -m unittest energyplus_worker.test_worker -v
```

Pure Python, no Odoo, no network — genuinely executable in any environment
with this repo checked out. It verifies the addon-bridge actually loads
`services/energyplus.py` and `services/mercure/*.py` (proving this worker
is really running the same logic the Odoo addon ships, not a fork of it),
plus the backoff/classification pure functions. It does **not** verify the
two HTTP routes themselves or the systemd deployment — that would need a
live Odoo instance, which (as with the rest of this module, see
`docs/cooling_v2_traceability_matrix.md`) has never been available in the
environment these changes were written in.
