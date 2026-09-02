"""Headless harness: feed a log through a Strategy with no hardware attached."""
from dataclasses import dataclass
from typing import Iterable, List

from .replay import read_log
from .strategy.base import Command, Strategy
from .world import WorldState


@dataclass
class Step:
    t: float
    world: WorldState
    command: Command


def run(frames: Iterable[WorldState], strategy: Strategy) -> List[Step]:
    strategy.reset()
    return [Step(w.t, w, strategy.update(w)) for w in frames]


def run_log(path: str, strategy: Strategy) -> List[Step]:
    return run(read_log(path), strategy)


def summarize(steps: List[Step]) -> dict:
    kinds = {}
    for s in steps:
        kinds[s.command.kind] = kinds.get(s.command.kind, 0) + 1
    duration = steps[-1].t - steps[0].t if len(steps) > 1 else 0.0
    return {"frames": len(steps), "seconds": round(duration, 2), "commands": kinds}
