"""Limelight as a detection source.

The Limelight runs its own neural detector and serves results as JSON over HTTP
on port 5807 (`/results`). It has no depth sensor, so distance is computed in
projection.py from the mount geometry. Works over Ethernet or the USB network
interface; set `camera.host` in the robot config (default limelight.local).

Docs: https://docs.limelightvision.io  (JSON dump spec, REST API)
"""
import json
import time
import urllib.request
from typing import Any, Dict, List, Optional

from .base import Detection, DetectionSource


def parse_results(doc: Dict[str, Any]) -> List[Detection]:
    """Accepts both the flat (2024+) and the older {"Results": {...}} layouts."""
    r = doc.get("Results", doc)
    out = []
    for d in r.get("Detector", []) or []:
        pts = d.get("pts") or []
        if len(pts) >= 4:
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            w, h = max(xs) - min(xs), max(ys) - min(ys)
        else:
            cx, cy = d.get("txp", 0.0), d.get("typ", 0.0)
            w = h = 0.0
        out.append(Detection(
            class_id=int(d.get("classID", -1)),
            confidence=float(d.get("conf", 0.0)),
            bbox=(int(cx), int(cy), int(w), int(h)),
            tx=float(d["tx"]) if "tx" in d else None,
            ty=float(d["ty"]) if "ty" in d else None,
            label=str(d.get("class", "")),
        ))
    return out


class LimelightSource(DetectionSource):
    def __init__(self, host: str = "limelight.local", port: int = 5807, timeout: float = 0.2):
        self.url = f"http://{host}:{port}/results"
        self.timeout = timeout
        self.last_ok = 0.0
        self.errors = 0
        self._last_ts: Optional[float] = None

    def fetch(self) -> List[Detection]:
        try:
            with urllib.request.urlopen(self.url, timeout=self.timeout) as resp:
                doc = json.loads(resp.read().decode())
        except Exception:
            self.errors += 1
            return []
        self.last_ok = time.time()
        r = doc.get("Results", doc)
        ts = r.get("ts")
        if ts is not None and ts == self._last_ts:
            return []          # same frame as last poll
        self._last_ts = ts
        return parse_results(doc)

    @property
    def connected(self) -> bool:
        return time.time() - self.last_ok < 1.0
