# Setup

Read this once end to end. Hardware decision: **Jetson Nano** with an Intel RealSense camera.
The Raspberry Pi 5 path in `JetsonImages/` exists but we do not maintain it.

## Repo layout

| Path | Owner | What |
|---|---|---|
| `JetsonExample/`, `V5Example/`, `JetsonImages/`, `JetsonWebDashboard/` | VEX | Upstream code. Do not edit; pull fixes with `git fetch upstream && git merge upstream/main`. |
| `protocol/` | us | `schema.py` is the wire contract. `generate.py` writes the Python module and C header. |
| `coprocessor/` | us | Python that runs on the Jetson. `main.py` wraps VEX's pipeline and adds logging + strategy. |
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
python3 coprocessor/tools/replay.py --synthetic 200 --verbose
```

Nothing above needs VEX libraries. This is where strategy work happens.

## Jetson Nano

1. Flash the image following `JetsonImages/README.md`.
2. Clone this repo onto the Jetson (same commands as above, plus `git lfs pull`).
3. Copy `coprocessor/config/field.example.json` to `coprocessor/config/field.json` and set `robot`.
4. Set GPS and camera offsets through the web dashboard as VEX documents; they save to
   `JetsonExample/*_offsets.json`, which is gitignored.
5. Run our entrypoint instead of VEX's: edit the `PYTHON_PROGRAM` line in a copy of
   `JetsonExample/Scripts/run.sh` (or the systemd service) to point at `coprocessor/main.py`.
   First launch builds the TensorRT engine and takes several minutes.
6. Logs land in `logs/worldlog_<timestamp>.jsonl`. Copy them to a laptop after each session
   and replay them with `coprocessor/tools/replay.py`.

## V5 Brain

1. Open `v5/robot` in VS Code with the VEX extension, or `make` with the VEXcode toolchain.
2. Always run `python3 protocol/generate.py` first; the header in `v5/robot/include` is generated.
3. Set drivetrain ports in `include/robot-config.h`.

## Changing the wire protocol

1. Edit `protocol/schema.py`. Bump `PROTOCOL_VERSION`; add a new `PACKET_TYPE_*` for a new layout.
2. `python3 protocol/generate.py`, run the tests, rebuild **both** the Jetson and the Brain.
3. Commit the schema and generated files together. CI rejects a stale generated file.

## Day-to-day rules

- `main` is protected. Work on a branch, open a PR, CI must pass.
- Never commit `.trt`/`.engine`, SD images, logs, or `field.json` (all gitignored).
- Model files go under `training/models/` so LFS picks them up.
