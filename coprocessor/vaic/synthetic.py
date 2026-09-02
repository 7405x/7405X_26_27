"""Fake world states for tests and for trying the harness before hardware exists."""
import math
import random
from typing import Iterator, List

from .world import Pose, WorldObject, WorldState


def synthetic_frames(n: int = 200, hz: float = 20.0, labels: List[str] = ("BallBlue", "BallRed"),
                     seed: int = 0, t0: float = 1_700_000_000.0) -> Iterator[WorldState]:
    """Robot drives a circle; a few objects sit on the field; detections jitter."""
    rng = random.Random(seed)
    objects = [(i % len(labels), rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5)) for i in range(6)]
    for k in range(n):
        t = t0 + k / hz
        a = 2 * math.pi * k / n
        pose = Pose(x=math.cos(a), y=math.sin(a), heading=math.degrees(a) % 360, frame=k, status=1)
        seen = []
        for cid, ox, oy in objects:
            if pose.distance_to(ox, oy) < 2.0 and rng.random() < 0.9:
                seen.append(WorldObject(cid, labels[cid], rng.uniform(0.6, 0.99), pose.distance_to(ox, oy),
                                        ox + rng.gauss(0, 0.02), oy + rng.gauss(0, 0.02), 0.0,
                                        (rng.randint(0, 640), rng.randint(0, 480), 40, 40)))
        yield WorldState(t=t, pose=pose, objects=seen, robot="sim")
