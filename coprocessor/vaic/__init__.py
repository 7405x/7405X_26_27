"""Team code that runs on the coprocessor (Jetson Nano) beside VEX's JetsonExample."""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_GEN = os.path.join(ROOT, "protocol", "generated")
if _GEN not in sys.path:
    sys.path.insert(0, _GEN)
