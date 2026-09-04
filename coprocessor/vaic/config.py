"""Per-robot settings.

Lookup order (first that exists):
  coprocessor/config/$VAIC_ROBOT.json
  coprocessor/config/<hostname>.json
  coprocessor/config/robot.json
  coprocessor/config/robot_a.example.json   (with a warning)
Real files are gitignored; commit only *.example.json.
"""
import json
import os
import socket
import sys

from . import ROOT

CONFIG_DIR = os.path.join(ROOT, "coprocessor", "config")
chosen_path = None


def candidates():
    names = []
    if os.environ.get("VAIC_ROBOT"):
        names.append(os.environ["VAIC_ROBOT"])
    names.append(socket.gethostname().split(".")[0])
    names.append("robot")
    return [os.path.join(CONFIG_DIR, n + ".json") for n in names]


def load() -> dict:
    global chosen_path
    for path in candidates():
        if os.path.exists(path):
            chosen_path = path
            break
    else:
        chosen_path = os.path.join(CONFIG_DIR, "robot_a.example.json")
        print(f"[vaic.config] no robot config found, using {os.path.basename(chosen_path)}", file=sys.stderr)
    with open(chosen_path) as f:
        return json.load(f)
