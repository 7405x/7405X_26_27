#!/usr/bin/env python3
"""Team entrypoint on the coprocessor.

Runs VEX's unmodified pipeline (JetsonExample/pushback.py) and hooks the point
where each AI record is handed to the V5 link, so every frame is also:
  - converted to a WorldState
  - appended to a JSONL log (replayable with tools/replay.py)
  - offered to the strategy (result currently printed; sending commands to the
    Brain needs a v2 packet type in protocol/schema.py)

Run exactly like VEX's script:  python3 coprocessor/main.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "JetsonExample"))

from vaic import config as cfg                      # noqa: E402
from vaic.labels import load_labels                  # noqa: E402
from vaic.logger import WorldLogger                  # noqa: E402
from vaic.strategy import NearestObjectStrategy      # noqa: E402
from vaic.world import WorldState                    # noqa: E402

import pushback                                      # noqa: E402  (VEX code, needs Jetson libs)


class TeamApp(pushback.MainApp):
    def __init__(self):
        super().__init__()
        self.cfg = cfg.load()
        self.labels = load_labels()
        self.logger = WorldLogger(os.path.join(ROOT, self.cfg.get("log_dir", "logs")),
                                  max_hz=self.cfg.get("log_hz", 20),
                                  compress=self.cfg.get("log_compress", False))
        s = self.cfg.get("strategy", {})
        self.strategy = NearestObjectStrategy(s.get("class_ids", [0]), s.get("min_confidence", 0.5))
        self.strategy.reset()
        self._last_print = 0.0
        print("Logging world state to", self.logger.path)

    def set_v5(self, aiRecord):
        super().set_v5(aiRecord)          # unchanged VEX behaviour: send to Brain
        world = WorldState.from_ai_record(aiRecord, self.labels, robot=self.cfg.get("robot", ""))
        self.logger.log(world)
        cmd = self.strategy.update(world)
        now = time.time()
        if now - self._last_print > 1.0:
            self._last_print = now
            print(f"[strategy] {cmd.kind} {cmd.target or ''} {cmd.note}")

    def run(self):
        try:
            super().run()
        finally:
            self.logger.close()


if __name__ == "__main__":
    TeamApp().run()
