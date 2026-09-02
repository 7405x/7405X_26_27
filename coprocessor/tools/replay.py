#!/usr/bin/env python3
"""Replay a world-state log through a strategy on a laptop.

  python coprocessor/tools/replay.py logs/worldlog_x.jsonl
  python coprocessor/tools/replay.py logs/worldlog_x.jsonl --classes 1 --verbose
  python coprocessor/tools/replay.py --synthetic 300            # no log needed
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from vaic import sim                                 # noqa: E402
from vaic.replay import read_log                     # noqa: E402
from vaic.strategy import NearestObjectStrategy      # noqa: E402
from vaic.synthetic import synthetic_frames          # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log", nargs="?", help="worldlog .jsonl or .jsonl.gz")
    ap.add_argument("--synthetic", type=int, metavar="N", help="use N generated frames instead of a log")
    ap.add_argument("--classes", default="0,1", help="comma-separated class ids to chase")
    ap.add_argument("--min-conf", type=float, default=0.5)
    ap.add_argument("--verbose", action="store_true", help="print every command")
    a = ap.parse_args()
    if not a.log and a.synthetic is None:
        ap.error("give a log path or --synthetic N")
    frames = synthetic_frames(a.synthetic) if a.synthetic is not None else read_log(a.log)
    strategy = NearestObjectStrategy([int(c) for c in a.classes.split(",")], a.min_conf)
    steps = sim.run(frames, strategy)
    if a.verbose:
        for s in steps:
            print(f"{s.t:.3f} pose=({s.world.pose.x:+.2f},{s.world.pose.y:+.2f}) "
                  f"objs={len(s.world.objects)} -> {s.command.kind} {s.command.target or ''} {s.command.note}")
    print(sim.summarize(steps))


if __name__ == "__main__":
    main()
