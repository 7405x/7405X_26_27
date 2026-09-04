"""Latest-state snapshot shared between the robot loop and the web UI."""
import collections
import threading
import time
from typing import Any, Dict, List, Optional

from .strategy.base import Command
from .world import WorldState


class DebugState:
    def __init__(self, history: int = 600):
        self._lock = threading.Lock()
        self.world: Optional[WorldState] = None
        self.command: Optional[Command] = None
        self.raw_detections: List[Dict[str, Any]] = []
        self.links: Dict[str, Any] = {}
        self.timing: Dict[str, float] = {}
        self.started = time.time()
        self.frames = 0
        self.history = collections.deque(maxlen=history)   # (t, x, y, heading)
        self.events = collections.deque(maxlen=200)         # (t, text)
        self.mode = "live"

    def update(self, world: WorldState, command: Optional[Command] = None, raw_detections=None,
               links: Optional[Dict[str, Any]] = None, timing: Optional[Dict[str, float]] = None) -> None:
        with self._lock:
            self.world = world
            self.command = command
            self.raw_detections = raw_detections or []
            if links:
                self.links.update(links)
            if timing:
                self.timing.update(timing)
            self.frames += 1
            self.history.append((world.t, world.pose.x, world.pose.y, world.pose.heading))

    def log_event(self, text: str) -> None:
        with self._lock:
            self.events.append((time.time(), text))

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            w = self.world
            c = self.command
            return {
                "now": time.time(),
                "uptime": time.time() - self.started,
                "frames": self.frames,
                "mode": self.mode,
                "world": w.to_dict() if w else None,
                "command": c.__dict__ if c else None,
                "raw_detections": list(self.raw_detections),
                "links": dict(self.links),
                "timing": dict(self.timing),
                "trail": list(self.history)[-300:],
                "events": list(self.events)[-50:],
            }
