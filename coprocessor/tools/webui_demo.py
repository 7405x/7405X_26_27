#!/usr/bin/env python3
"""Serve the debug dashboard on a laptop from a recorded log (no robot needed).

    python coprocessor/tools/webui_demo.py logs/worldlog_x.jsonl [--port 8080]
Then open http://localhost:8080/ . The log loops; the replay panel can scrub any log in logs/.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from vaic import config as cfg                      # noqa: E402
from vaic.debugstate import DebugState              # noqa: E402
from vaic.replay import read_log                    # noqa: E402
from vaic.strategy import NearestObjectStrategy     # noqa: E402
from vaic.webui import WebUI                        # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("log", help="worldlog .jsonl or .jsonl.gz recorded by coprocessor/main.py")
ap.add_argument("--port", type=int, default=8080)
a = ap.parse_args()

c = cfg.load()
state = DebugState()
state.mode = "log " + os.path.basename(a.log)
ui = WebUI(state, c, port=a.port, log_dir=os.path.dirname(os.path.abspath(a.log)))
ui.start()
strategy = NearestObjectStrategy(c["strategy"]["class_ids"], c["strategy"]["min_confidence"])
print(f"open http://localhost:{a.port}/  (ctrl-c to stop)")
try:
    while True:
        prev = None
        for w in read_log(a.log):
            if prev is not None:
                time.sleep(min(1.0, max(0.0, w.t - prev)))
            prev = w.t
            state.update(w, strategy.update(w), links={"limelight": None, "v5": None})
except KeyboardInterrupt:
    pass
finally:
    ui.stop()
