# 7405X Achieve Drive

V5 C++ project for the VEX VS Code extension. It runs a 6-motor tank drive (3 motors per side) with an inertial sensor.

## Before the first run
1. Open `include/robot-config.h` and set the motor ports, IMU port, cartridge, wheel size and gear ratio.
2. Put the robot on blocks, push both sticks forward, and check that every wheel spins forward. If one spins backward, flip its `true`/`false` in `src/robot-config.cpp`.
3. Keep the robot still while the IMU calibrates at startup (about 2 seconds).

## Files
| File | What it does |
|---|---|
| `src/main.cpp` | Competition setup: pre-auton, autonomous and driver control |
| `src/drive.cpp` | Driver control plus PID `driveDistance` / `turnToHeading` |
| `src/autons.cpp` | Auton routines and the brain-screen selector |
| `include/robot-config.h` | Ports and robot measurements |

## Driver controls
| Control | Does |
|---|---|
| Left / right stick | Tank drive (set `TANK_DRIVE = false` for arcade) |
| L1 | Slow mode on/off (40% speed, for lining up) |
| X | Hold mode on/off (wheels lock when sticks are released, hard to push) |

The controller screen shows battery %, hottest drive motor temperature, and the current modes. V5 motors lose power above about 55°C.
The controller buzzes 15 seconds before the end of an alliance match. That's the cue to drive back to your alliance loader: a robot touching it when the match ends scores 21 points.
At startup the brain checks that all 6 motors and the IMU are plugged in, and shows a red warning if one isn't.

## Picking an auton
During pre-auton, tap the brain screen to cycle through the options. The selected one also shows on the controller.
- **Zone Roller** (Red/Blue, L/R): 15 s alliance auton. The robot drives to your zone's roller on your own wall and presses the toggler into it. This is the half of the autonomous ranking point the robot can do itself.
- **Neutral Roller** (Red/Blue, L/R): 15 s alliance auton. The robot drives along the wall to the nearest neutral roller and flips it to your color. Pick this when your partner will be scoring on that neutral goal.
- "L"/"R" means which loader, as seen standing in **your** driver box.
- **Solo Coding**: 60 s run. For now it runs the same roller path, which scores 0 in solo matches. It's there for practice until the robot can carry pins.
- **Test: Drive / Turn / Square**: for tuning. Square should end where it started; the brain prints where it thinks it ended.

## Field coordinates
Autons use field positions in inches, read from Figure 1.2 of the manual. The full map is at the top of `src/autons.cpp`.
- x = 0 at the red wall, 144 at the blue wall
- y = 0 at the bottom of the figure, 144 at the top
- heading 90 = facing the blue wall

Routines are written once for red. Blue reuses the same code mirrored across the field. **These numbers came from a picture.** Measure the real field and fix them before trusting any path.

## Tuning the PID
Run `Test: Drive 24in`. Raise `DRIVE_KP` until the robot slightly overshoots, then raise `DRIVE_KD` until the overshoot stops. Do the same for turning with `Test: Turn 90`, using `TURN_KP` and `TURN_KD`.
