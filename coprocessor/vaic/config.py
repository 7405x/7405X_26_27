"""Per-robot / per-field settings. field.json is gitignored; field.example.json is not."""
import json
import os
import sys

from . import ROOT

CONFIG_DIR = os.path.join(ROOT, "coprocessor", "config")
LOCAL = os.path.join(CONFIG_DIR, "field.json")
EXAMPLE = os.path.join(CONFIG_DIR, "field.example.json")


def load(path: str = LOCAL) -> dict:
    if not os.path.exists(path):
        print(f"[vaic.config] {os.path.relpath(path, ROOT)} not found, using example config", file=sys.stderr)
        path = EXAMPLE
    with open(path) as f:
        return json.load(f)
