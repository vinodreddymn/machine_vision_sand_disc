from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx


@dataclass(slots=True)
class Sample:
    ts: float
    ok: bool
    latency_ms: float
    payload: dict[str, Any] | None
    error: str | None


def _get(url: str, timeout_s: float = 2.0) -> Sample:
    started = time.perf_counter()
    try:
        r = httpx.get(url, timeout=timeout_s)
        latency = (time.perf_counter() - started) * 1000.0
        r.raise_for_status()
        return Sample(ts=time.time(), ok=True, latency_ms=latency, payload=r.json(), error=None)
    except Exception as e:
        latency = (time.perf_counter() - started) * 1000.0
        return Sample(ts=time.time(), ok=False, latency_ms=latency, payload=None, error=str(e))


def main() -> int:
    host = "127.0.0.1"
    port = 8010
    duration_s = int(float(Path("config").joinpath("health_thresholds.json").exists() and 60))  # default 60s
    interval_s = 5.0

    # Allow overrides
    import os

    host = os.getenv("DISK_VISION_TEST_HOST", host)
    port = int(os.getenv("DISK_VISION_TEST_PORT", str(port)))
    duration_s = int(float(os.getenv("DISK_VISION_TEST_DURATION_S", str(duration_s))))
    interval_s = float(os.getenv("DISK_VISION_TEST_INTERVAL_S", str(interval_s)))

    base = f"http://{host}:{port}"
    endpoints = {
        "system_health": f"{base}/api/system/health",
        "status": f"{base}/api/status",
        "station1": f"{base}/api/station1",
        "metrics": f"{base}/api/metrics",
        "devices": f"{base}/api/system/devices",
        "services": f"{base}/api/system/services",
    }

    start = time.time()
    samples: dict[str, list[Sample]] = {k: [] for k in endpoints}
    errors: list[dict[str, Any]] = []

    while time.time() - start < duration_s:
        for name, url in endpoints.items():
            s = _get(url)
            samples[name].append(s)
            if not s.ok:
                errors.append({"endpoint": name, "ts": s.ts, "error": s.error})
        time.sleep(interval_s)

    report = _summarize(samples, errors, duration_s, interval_s, endpoints)
    out_path = Path("RELIABILITY_REPORT.md")
    out_path.write_text(report, encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


def _summarize(samples: dict[str, list[Sample]], errors: list[dict[str, Any]], duration_s: int, interval_s: float, endpoints: dict[str, str]) -> str:
    now = datetime.now(timezone.utc).isoformat()
    lines: list[str] = []
    lines.append("# Reliability Report (Soak Test)")
    lines.append("")
    lines.append(f"Generated: {now}")
    lines.append(f"Duration: {duration_s}s, Interval: {interval_s}s")
    lines.append("")
    lines.append("## Endpoints")
    lines.append("")
    for k, v in endpoints.items():
        lines.append(f"- `{k}`: `{v}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    for name, runs in samples.items():
        if not runs:
            continue
        ok_count = sum(1 for r in runs if r.ok)
        total = len(runs)
        latencies = [r.latency_ms for r in runs if r.ok]
        p95 = _percentile(latencies, 95) if latencies else None
        lines.append(f"- `{name}`: ok={ok_count}/{total}, p95_ms={p95:.1f}" if p95 is not None else f"- `{name}`: ok={ok_count}/{total}")
    lines.append("")
    lines.append("## Errors")
    lines.append("")
    if not errors:
        lines.append("No errors recorded.")
    else:
        lines.append("```json")
        lines.append(json.dumps(errors[:200], indent=2))
        lines.append("```")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- This is a baseline soak runner (Phase 16 foundation).")
    lines.append("- Next improvements: fault injection (camera/network/db), memory trend alerts, multi-hour runs.")
    lines.append("")
    return "\n".join(lines)


def _percentile(values: list[float], pct: int) -> float:
    if not values:
        return 0.0
    values_sorted = sorted(values)
    k = (len(values_sorted) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(values_sorted) - 1)
    if f == c:
        return float(values_sorted[f])
    d0 = values_sorted[f] * (c - k)
    d1 = values_sorted[c] * (k - f)
    return float(d0 + d1)


if __name__ == "__main__":
    raise SystemExit(main())

