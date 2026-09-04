# Hardware

Inventory (from team chat, 2026-09-03) and how each piece is used.

| Item | Qty | Role |
|---|---|---|
| OKdo Nano C100 (Jetson Nano module carrier) | 2 | One per competition robot. Runs `coprocessor/main.py`. |
| NVIDIA Jetson Nano Developer Kit | 1 | Bench / spare board. Same software; use it for TensorRT engine builds and testing off-robot. |
| Limelight camera | 1 (need 2) | Detection source. Runs its own neural detector; we read JSON results over HTTP. **One per robot is required.** |
| VEX V5 Brain | per robot | Runs `v5/robot`. Talks to the Jetson over USB serial. |
| VEX GPS sensor | per robot | Field position. Plugs into the Brain; the Jetson reads it over USB serial like VEX's example does. |
| Jetson battery packs | 2+ | Power for the Jetson. The Brain's USB port cannot supply the Nano's 5 V / 4 A. Confirm the pack holds up for a full match plus queueing. |

## Data flow on a robot

```
Limelight --HTTP JSON (5807)--> Jetson <--USB serial--> V5 Brain
GPS sensor --USB serial------> Jetson
Jetson --> logs/worldlog_*.jsonl (replay on a laptop)
```

The Jetson answers the Brain's request line with an `AI_RECORD` (VEX format, `protocol/`).
The Brain can optionally send `ODOM_RECORD` packets with an encoder-based pose, which the
Jetson uses when the GPS has no fix (see `v5/robot/include/vaic_odom.h`).

## Differences from VEX's stock setup

- VEX's example assumes an Intel RealSense D435 with depth. The Limelight has no depth sensor,
  so distance comes from the ground-plane projection in `coprocessor/vaic/perception/projection.py`.
  Camera mount height and pitch in the robot config must be measured accurately, and every object
  class needs its center height in `objects`.
- The Limelight must be running a detector pipeline trained on this season's objects; the Jetson
  does no inference on the Limelight path. Class IDs in the Limelight pipeline must match the
  `objects` table in the robot config and `labels.txt`.
- If we ever go back to RealSense, set `camera.type` to `realsense`; that path wraps VEX's code.

## Board naming

Set each board's hostname to `robot_a` / `robot_b` (`sudo hostnamectl set-hostname robot_a`) so
`coprocessor/vaic/config.py` picks `config/robot_a.json` automatically. The dev kit can be `bench`.

## Limelight networking

Over Ethernet the Limelight advertises itself as `limelight.local`. Over USB it appears as a USB
network adapter; check the Limelight web UI for the address it assigns and put it in `camera.host`.
Verify with `curl http://<host>:5807/results` from the Jetson before anything else.
