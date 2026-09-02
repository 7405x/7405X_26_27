"""Drive to the nearest object of the wanted classes. Same idea as findTarget()
in VEX's ai_functions.cpp, but testable offline."""
from typing import Sequence

from ..world import WorldState
from .base import Command, Strategy


class NearestObjectStrategy(Strategy):
    def __init__(self, class_ids: Sequence[int], min_confidence: float = 0.5):
        self.class_ids = tuple(class_ids)
        self.min_confidence = min_confidence

    def update(self, world: WorldState) -> Command:
        if not world.pose.connected:
            return Command("idle", note="no GPS fix")
        obj = world.nearest(*self.class_ids, min_confidence=self.min_confidence)
        if obj is None:
            return Command("idle", note="no target")
        return Command("drive_to", target=(obj.x, obj.y), class_id=obj.class_id, note=obj.label)
