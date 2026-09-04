# VAIC 25/26 — team fork (7405X)

Fork of VEX's VAIC system with team code beside it. **Start at [docs/SETUP.md](docs/SETUP.md).**

- `protocol/` — versioned Jetson ⇄ V5 wire schema; generates both the Python and C sides
- `coprocessor/` — Jetson code: Limelight perception, GPS/odometry pose, world-state logging, offline replay, strategy
- `v5/robot/` — Brain project derived from `ai_demo`, using the generated header
- `training/` — dataset pin and model export
- Debug dashboard on the Jetson at port 8080, see [docs/DEBUG_UI.md](docs/DEBUG_UI.md)
- Hardware: OKdo Nano C100 + Limelight camera + V5 GPS per robot. See [docs/HARDWARE.md](docs/HARDWARE.md).

VEX's original README follows.

---

# The VEX AI Competition (VAIC) System

## [JetsonExample](./JetsonExample/README.md)

JetsonExample contains the default code that powers the VEX AI system, from processing image data and running the AI model to detect objects for the VEX V5 Brain.

## [JetsonImages](./JetsonImages/README.md)

JetsonImages is where you will find how to get the most up-to-date image of the NVIDIA Jetson Nano and Raspberry Pi 5 and instructions on how to install the SD card image and or building from source.

## [JetsonWebDashboard](./JetsonWebDashboard/README.md)

JetsonWebDashboard is where you will find the source code for the VEX AI Web Dashboard that runs on the Jetson Nano/Raspberry Pi.

## [V5Example](./V5Example/ai_demo/README.md)

V5Example contains the `ai_demo` V5 Project which has examples on how to connect with the Jetson Nano/Raspberry Pi and how to interpret and process the data from the board on the V5 Brain
