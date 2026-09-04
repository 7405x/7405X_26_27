#!/usr/bin/env python3
"""Team entrypoint on the coprocessor.

    python3 coprocessor/main.py                 # config picked by $VAIC_ROBOT or hostname
    VAIC_ROBOT=robot_b python3 coprocessor/main.py

camera.type in the config selects the pipeline:
    "limelight"  -> vaic/app_limelight.py  (our hardware)
    "realsense"  -> vaic/app_realsense.py  (VEX's stock pipeline, wrapped)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vaic import config as cfg  # noqa: E402


def main():
    c = cfg.load()
    kind = c.get("camera", {}).get("type", "limelight")
    print(f"robot={c.get('robot')} camera={kind} config={cfg.chosen_path}")
    if kind == "limelight":
        from vaic.app_limelight import LimelightApp
        LimelightApp(c).run()
    elif kind == "realsense":
        from vaic.app_realsense import RealSenseApp
        RealSenseApp(c).run()
    else:
        sys.exit(f"unknown camera.type {kind!r}")


if __name__ == "__main__":
    main()
