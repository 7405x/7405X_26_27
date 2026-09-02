"""Strategy interface. A Strategy sees only WorldState and returns a Command.

Keep strategies pure (no I/O, no sleeping) so they run identically on the robot
and in the replay harness.
"""
from dataclasses import dataclass
from typing import Optional, Tuple

from ..world import WorldState


@dataclass
class Command:
    kind: str = "idle"                        # "idle" | "drive_to" | "collect" | "score" ...
    target: Optional[Tuple[float, float]] = None
    class_id: Optional[int] = None
    note: str = ""


class Strategy:
    def reset(self) -> None:
        """Called once before a run or replay."""

    def update(self, world: WorldState) -> Command:
        raise NotImplementedError
