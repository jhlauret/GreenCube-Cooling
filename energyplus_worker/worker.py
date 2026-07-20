# -*- coding: utf-8 -*-
"""
Standalone EnergyPlus worker (GC-COOLING-15).

Runs as its own OS process, deployed independently of the Odoo server —
see README.md for a systemd unit example. It talks to Odoo ONLY over the
two HTTP routes in controllers/api.py (/energyplus-jobs/claim and
/energyplus-jobs/<id>/complete), authenticated with a shared secret header,
and never opens a database connection, never imports the `odoo` package,
and never reads a PostgreSQL credential. This is what actually satisfies
GC-COOLING-15's "worker separate from the process with direct PostgreSQL
access" requirement — the in-process cron this replaced could not.

Today `run_energyplus_simulation` always raises (see
services/energyplus.py's own docstring: neither honeybee-energy/ladybug nor
an EnergyPlus binary are expected to be present), so this worker will
report every claimed job as unavailable/failed. That is the honest current
end state, not a placeholder pretending otherwise — the isolation
architecture is real and testable independently of whether EnergyPlus
itself is installed anywhere.
"""
import argparse
import json
import logging
import os
import time
import urllib.error
import urllib.request

from addon_bridge import load as load_addon_modules

logger = logging.getLogger("energyplus_worker")


class WorkerConfig:
    def __init__(self, api_base_url, worker_key, poll_interval_s=15, request_timeout_s=30, max_backoff_s=300):
        self.api_base_url = api_base_url.rstrip("/")
        self.worker_key = worker_key
        self.poll_interval_s = poll_interval_s
        self.request_timeout_s = request_timeout_s
        self.max_backoff_s = max_backoff_s

    @classmethod
    def from_env(cls):
        api_base_url = os.environ.get("GC_COOLING_API_BASE_URL")
        worker_key = os.environ.get("GC_COOLING_ENERGYPLUS_WORKER_KEY")
        if not api_base_url or not worker_key:
            raise RuntimeError(
                "GC_COOLING_API_BASE_URL and GC_COOLING_ENERGYPLUS_WORKER_KEY must both be set — "
                "this worker refuses to guess a target server or run without a key."
            )
        return cls(
            api_base_url=api_base_url,
            worker_key=worker_key,
            poll_interval_s=int(os.environ.get("GC_COOLING_WORKER_POLL_INTERVAL_S", "15")),
            request_timeout_s=int(os.environ.get("GC_COOLING_WORKER_REQUEST_TIMEOUT_S", "30")),
            max_backoff_s=int(os.environ.get("GC_COOLING_WORKER_MAX_BACKOFF_S", "300")),
        )


def backoff_seconds(attempt, base_s=2, max_s=300):
    """Exponential backoff for transient HTTP/network failures talking to
    Odoo — distinct from a job legitimately failing, which is reported
    normally via /complete and does not trigger backoff at all."""
    if attempt <= 0:
        return 0
    return min(max_s, base_s * (2 ** (attempt - 1)))


def classify_run_result(exc_or_none, energyplus_module):
    """Maps the outcome of attempting a simulation to the
    energyplus_processing_status the /complete route accepts, plus a human
    detail string. Kept as a pure function so it's unit-testable without a
    real EnergyPlus stack or a live Odoo instance."""
    if exc_or_none is None:
        return "simulation_completed", None
    if isinstance(exc_or_none, energyplus_module.EnergyPlusUnavailableError):
        return "simulation_unavailable", str(exc_or_none)
    if isinstance(exc_or_none, energyplus_module.EnergyPlusSimulationError):
        return "simulation_failed", str(exc_or_none)
    return "simulation_failed", f"Unexpected worker error: {exc_or_none}"


def _http_request(url, method, headers, body_bytes, timeout_s):
    req = urllib.request.Request(url, data=body_bytes, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        status = resp.status
        raw = resp.read()
    return status, raw


def claim_job(config):
    """Returns a claimed job dict, or None if the queue is empty. Raises
    urllib.error.URLError/HTTPError on transient network failure (caller
    applies backoff), and RuntimeError on a definite auth/config problem
    that retrying will not fix."""
    url = f"{config.api_base_url}/api/v1/greencube/cooling/energyplus-jobs/claim"
    headers = {"X-GreenCube-Worker-Key": config.worker_key, "Content-Type": "application/json"}
    try:
        status, raw = _http_request(url, "POST", headers, b"{}", config.request_timeout_s)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 503):
            raise RuntimeError(f"Worker key rejected or endpoint disabled (HTTP {exc.code}): {exc.read()}") from exc
        raise
    if status == 204:
        return None
    payload = json.loads(raw)
    return payload["data"]


def complete_job(config, job_id, status, detail=None, artifacts=None):
    url = f"{config.api_base_url}/api/v1/greencube/cooling/energyplus-jobs/{job_id}/complete"
    headers = {"X-GreenCube-Worker-Key": config.worker_key, "Content-Type": "application/json"}
    body = {"status": status, "detail": detail, "artifacts": artifacts or []}
    _http_request(url, "POST", headers, json.dumps(body).encode("utf-8"), config.request_timeout_s)


def run_one_job(config, addon_modules, job):
    """Builds the MercureInput from the claimed job's frozen snapshot
    payload and attempts the simulation, then reports the outcome back.
    Any artifact the (currently nonexistent, stubbed) simulation stack
    would produce is reported honestly — today that's always none, since
    run_energyplus_simulation always raises before producing output."""
    mercure_input = addon_modules.serialization.mercure_input_from_dict(json.loads(job["payload_json"]))
    exc = None
    try:
        addon_modules.energyplus.run_energyplus_simulation(mercure_input)
    except Exception as caught:  # noqa: BLE001 - classify_run_result narrows this
        exc = caught
    status, detail = classify_run_result(exc, addon_modules.energyplus)
    complete_job(config, job["job_id"], status, detail=detail)
    logger.info("Job %s -> %s (%s)", job["job_id"], status, detail or "ok")
    return status


def run_forever(config, addon_modules, stop_after_n_polls=None):
    attempt = 0
    polls = 0
    while stop_after_n_polls is None or polls < stop_after_n_polls:
        polls += 1
        try:
            job = claim_job(config)
        except RuntimeError:
            logger.exception("Worker misconfigured, stopping.")
            raise
        except (urllib.error.URLError, TimeoutError, OSError):
            attempt += 1
            delay = backoff_seconds(attempt, max_s=config.max_backoff_s)
            logger.warning("Could not reach Odoo, retrying in %ss (attempt %s).", delay, attempt)
            time.sleep(delay)
            continue

        attempt = 0
        if job is None:
            time.sleep(config.poll_interval_s)
            continue

        run_one_job(config, addon_modules, job)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Poll a single time and exit (for cron/systemd-timer deployment).")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(level=args.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    config = WorkerConfig.from_env()
    addon_modules = load_addon_modules()
    logger.info("energyplus_worker starting against %s (poll interval %ss).", config.api_base_url, config.poll_interval_s)
    run_forever(config, addon_modules, stop_after_n_polls=1 if args.once else None)


if __name__ == "__main__":
    main()
