#!/usr/bin/env python3
"""Write a synthetic world log so the replay tooling can be tried without a robot."""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from vaic.logger import WorldLogger              # noqa: E402
from vaic.synthetic import synthetic_frames      # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out-dir", default="logs")
ap.add_argument("--frames", type=int, default=400)
a = ap.parse_args()
with WorldLogger(a.out_dir, max_hz=0, name="synthetic") as lg:
    for w in synthetic_frames(a.frames):
        lg.log(w)
print("wrote", lg.path, lg.frames, "frames")
