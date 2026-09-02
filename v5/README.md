# v5/ — team V5 Brain projects

`robot/` is a copy of VEX's `V5Example/ai_demo` with one change: the wire structs in
`include/ai_jetson.h` are replaced by `#include "vaic_protocol.h"`, which is generated
from `protocol/schema.py`. Everything else is VEX's code, so diff against
`V5Example/ai_demo` to see exactly what is ours.

Build/flash with the VEX VS Code extension (open `v5/robot` as the project) or `make`
in that directory with the VEXcode toolchain on PATH. Regenerate the protocol first:

    python protocol/generate.py

For a second robot, copy `robot/` to `robot_b/`, add its header path to
`V5_HEADER_COPIES` in `protocol/generate.py`, and keep robot-specific tuning in
`robot-config.h`.
