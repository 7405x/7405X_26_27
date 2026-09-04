# Setup

Read this once end to end. Hardware: **OKdo Nano C100 (Jetson Nano) + Limelight camera + V5 GPS**,
one set per robot; the NVIDIA dev kit is the bench board. See [HARDWARE.md](HARDWARE.md).
The Raspberry Pi 5 and RealSense paths exist in VEX's code but we do not maintain them.

## Repo layout

| Path | Owner | What |
|---|---|---|
| `JetsonExample/`, `V5Example/`, `JetsonImages/`, `JetsonWebDashboard/` | VEX | Upstream code. Do not edit; pull fixes with `git fetch upstream && git merge upstream/main`. |
| `protocol/` | us | `schema.py` is the wire contract. `generate.py` writes the Python module and C header. |
| `coprocessor/` | us | Python that runs on the Jetson. `main.py` polls the Limelight, reads GPS/odometry, projects to the field, logs, runs strategy, serves the Brain. |
| `v5/robot/` | us | Copy of `ai_demo` that includes the generated header. Build with VEXcode. |
| `training/` | us | Dataset pin, export script, LFS-tracked model files. |
| `docs/` | us | This file and design notes. |

## Laptop (any OS, Python 3.9+)

```bash
git clone git@github.com:7405x/VAIC_25_26.git && cd VAIC_25_26
git remote add upstream https://github.com/VEX-Robotics/VAIC_25_26.git
git lfs install
python3 protocol/generate.py --check                 # should print nothing
python3 -m unittest discover -s protocol/tests
python3 -m unittest discover -s coprocessor/tests
python3 coprocessor/tools/replay.py logs/<a recorded log>.jsonl --verbose
```

Nothing above needs VEX libraries. Strategy work happens here, against logs recorded on the robot.

## Jetson Nano

1. Flash the image following `JetsonImages/README.md`.
2. Clone this repo onto the Jetson (same commands as above, plus `git lfs pull`).
3. Set the hostname to `robot_a` or `robot_b`, then copy `coprocessor/config/robot_a.example.json`
   to `coprocessor/config/robot_a.json` (or `robot_b`) and measure in the camera mount values.
4. Connect the Limelight and confirm `curl http://limelight.local:5807/results` returns JSON.
   Configure the Limelight's detector pipeline in its web UI.
5. Run `python3 coprocessor/main.py`. The status line shows Limelight and Brain link state once a
   second, and the debug dashboard is at `http://<jetson-ip>:8080/` ([DEBUG_UI.md](DEBUG_UI.md)). To start on boot, adapt `JetsonExample/Scripts/service.sh` to point at this command.
6. Logs land in `logs/worldlog_<timestamp>.jsonl`. Copy them to a laptop after each session
   and replay them with `coprocessor/tools/replay.py`.

## V5 Brain

1. Open `v5/robot` in VS Code with the VEX extension, or `make` with the VEXcode toolchain.
2. Always run `python3 protocol/generate.py` first; the header in `v5/robot/include` is generated.
3. Set drivetrain ports in `include/robot-config.h`.

## Sending Brain odometry to the Jetson

Once the Brain has an encoder-based pose, set `VAIC_SEND_ODOM` to 1 in `v5/robot/src/main.cpp`
and feed your estimate to `vaic::send_odom()`. The Jetson falls back to it when the GPS has no fix.

## Changing the wire protocol

1. Edit `protocol/schema.py`. Bump `PROTOCOL_VERSION`; add a new `PACKET_TYPE_*` for a new layout.
2. `python3 protocol/generate.py`, run the tests, rebuild **both** the Jetson and the Brain.
3. Commit the schema and generated files together. CI rejects a stale generated file.

## Day-to-day rules

- `main` is protected. Work on a branch, open a PR, CI must pass.
- Never commit `.trt`/`.engine`, SD images, logs, or `field.json` (all gitignored).
- Model files go under `training/models/` so LFS picks them up.
