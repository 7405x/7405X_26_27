"""Append WorldState frames to a JSONL file at a bounded rate."""
import gzip
import json
import os
import time
from typing import IO, Optional

from .world import WorldState


class WorldLogger:
    def __init__(self, directory: str, max_hz: float = 20.0, compress: bool = False, name: Optional[str] = None):
        os.makedirs(directory, exist_ok=True)
        stamp = name or time.strftime("worldlog_%Y%m%d_%H%M%S")
        ext = ".jsonl.gz" if compress else ".jsonl"
        self.path = os.path.join(directory, stamp + ext)
        self._fh: IO = gzip.open(self.path, "at") if compress else open(self.path, "a")
        self._min_dt = 1.0 / max_hz if max_hz > 0 else 0.0
        self._last = -1e9
        self.frames = 0

    def log(self, world: WorldState) -> bool:
        """Write the frame unless it arrives sooner than 1/max_hz after the last one."""
        if world.t - self._last < self._min_dt * 0.999:  # tolerance for float drift
            return False
        self._last = world.t
        self._fh.write(json.dumps(world.to_dict(), separators=(",", ":")) + "\n")
        self.frames += 1
        return True

    def flush(self) -> None:
        self._fh.flush()

    def close(self) -> None:
        if not self._fh.closed:
            self._fh.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
