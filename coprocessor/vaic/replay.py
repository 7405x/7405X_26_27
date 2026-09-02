"""Read WorldState frames back from a log, optionally paced in real time."""
import gzip
import json
import time
from typing import Iterator

from .world import WorldState


def open_log(path: str):
    return gzip.open(path, "rt") if path.endswith(".gz") else open(path)


def read_log(path: str) -> Iterator[WorldState]:
    with open_log(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield WorldState.from_dict(json.loads(line))


def replay(path: str, realtime: bool = False, speed: float = 1.0) -> Iterator[WorldState]:
    """Yield frames; with realtime=True sleep so frames arrive at logged pace."""
    prev_t = None
    for world in read_log(path):
        if realtime and prev_t is not None:
            dt = (world.t - prev_t) / speed
            if dt > 0:
                time.sleep(min(dt, 5.0))
        prev_t = world.t
        yield world
