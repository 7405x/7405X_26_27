"""RealSense path: run VEX's unmodified pipeline (JetsonExample/pushback.py) and hook
the point where each AI record is handed to the V5 link, so every frame is also
converted to a WorldState, logged, and offered to the strategy."""
import os
import sys
import time

from . import ROOT
from .debugstate import DebugState
from .labels import load_labels
from .logger import WorldLogger
from .strategy import NearestObjectStrategy
from .world import WorldState
from .webui import WebUI

sys.path.insert(0, os.path.join(ROOT, "JetsonExample"))
import pushback  # noqa: E402  (VEX code, needs pyrealsense2 + TensorRT)


class RealSenseApp(pushback.MainApp):
    def __init__(self, cfg: dict):
        super().__init__()
        self.cfg = cfg
        self.labels = load_labels()
        self.logger = WorldLogger(os.path.join(ROOT, cfg.get("log_dir", "logs")),
                                  max_hz=cfg.get("log_hz", 20), compress=cfg.get("log_compress", False))
        s = cfg.get("strategy", {})
        self.strategy = NearestObjectStrategy(s.get("class_ids", [0]), s.get("min_confidence", 0.5))
        self.strategy.reset()
        self._last_print = 0.0
        self.debug = DebugState()
        self.webui = WebUI(self.debug, cfg, port=cfg.get("webui_port", 8080)) if cfg.get("webui", True) else None
        if self.webui:
            self.webui.start()
        print("Logging world state to", self.logger.path)

    def set_v5(self, aiRecord):
        super().set_v5(aiRecord)
        world = WorldState.from_ai_record(aiRecord, self.labels, robot=self.cfg.get("robot", ""))
        self.logger.log(world)
        cmd = self.strategy.update(world)
        self.debug.update(world, cmd, links={"v5": True})
        now = time.time()
        if now - self._last_print > 1.0:
            self._last_print = now
            print(f"[strategy] {cmd.kind} {cmd.target or ''} {cmd.note}")

    def run(self):
        try:
            super().run()
        finally:
            self.logger.close()
