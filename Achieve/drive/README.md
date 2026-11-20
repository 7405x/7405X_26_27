# 7405X Achieve Drive

V5 C++ project for the VEX VS Code extension. It runs a 6-motor drivetrain (3 motors per side) with split arcade controls, an inertial sensor, a single bar lift and a motor claw.

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
| `src/lift.cpp` | Single bar lift control (R1/R2) and `liftTo()` for autons |
| `include/lift.h` | Lift positions (down / carry / score) to measure and fill in |
| `src/claw.cpp` | Claw control (L2) and `clawOpen()` / `clawClose()` for autons |
| `include/claw.h` | Claw grip strength |
| `include/robot-config.h` | Ports and robot measurements |

## Driver controls
Full driver guide (buttons, buzzes, controller screen, pre-match checklist): [DRIVER.md](DRIVER.md). Port assignments: [WIRING.md](WIRING.md).

| Control | Does |
|---|---|
| Left stick up/down | Drive forward / backward |
| Right stick left/right | Turn |
| R1 (hold) | Lift up |
| R2 (hold) | Lift down |
| L2 | Claw open / close (toggle) |
| L1 | Slow mode on/off (40% speed, for lining up) |
| X | Hold mode on/off (wheels lock when sticks are released, hard to push) |

The controller screen shows battery %, hottest motor temperature (drive, lift or claw), and the current modes. V5 motors lose power above about 55°C.
The controller buzzes 15 seconds before the end of an alliance match. That's the cue to drive back to your alliance loader: a robot touching it when the match ends scores 21 points.
At startup the brain checks that all 8 motors and the IMU are plugged in, and shows a red warning if one isn't.

## Picking an auton
Tap the brain screen to cycle through the options while the robot is disabled (before the match starts). The selected one also shows on the controller. The selection starts on **None**, so the robot stays still if nobody picks one. Taps are ignored while the robot is enabled, so bumping the screen mid-match does nothing.
- **Zone Roller** (Red/Blue, L/R): 15 s alliance auton. The robot drives to your zone's roller on your own wall and presses the toggler into it. This is the half of the autonomous ranking point the robot can do itself.
- **Neutral Roller** (Red/Blue, L/R): 15 s alliance auton. The robot drives along the wall to the nearest neutral roller and flips it to your color. Pick this when your partner will be scoring on that neutral goal.
- "L"/"R" means which loader, as seen standing in **your** driver box.
- **Solo Coding**: 60 s run. For now it runs the same roller path, which scores 0 in solo matches. It's there for practice until the robot can carry pins.
- **Test: Drive / Turn / Square**: for tuning. Square should end where it started; the brain prints where it thinks it ended.
- **Test: Toggler Press**: runs only the push into the roller and the back-off. Start with the front bumper about 3" from a roller.

## Tuning the autons
All auton settings are in the **TUNING** block at the top of `src/autons.cpp`. Set them for red, bottom loader only; the code mirrors them for the other three starting spots.
- `TOGGLER_OFFSET_IN`: how far the toggler sits right (+) or left (−) of the robot's center line. Measure this first. The paths line up the toggler, not the robot's center, with the roller.
- `AUTON_VOLTS`: auton speed. Lower it while trying a new path.
- `PRESS_*` / `BACKOFF_*`: how hard and how far the toggler pushes. Tune these with `Test: Toggler Press`.
- `ZONE_PRESS_Y` / `NEUTRAL_PRESS_X`: where on each roller the toggler hits. The comments next to them explain what limits each one.
- Any spot where the robot makes a big turn must be at least `TURN_CLEARANCE` (13.5") from walls. An 18" robot's corners swing out 12.7" when it turns in place.

## Field coordinates
Autons use field positions in inches, read from Figure 1.2 of the manual. The full map is at the top of `src/autons.cpp`.
- x = 0 at the red wall, 144 at the blue wall
- y = 0 at the bottom of the figure, 144 at the top
- heading 90 = facing the blue wall

Routines are written once for red. Blue reuses the same code mirrored across the field. **These numbers came from a picture.** Measure the real field and fix them before trusting any path.

## Tuning the PID
Run `Test: Drive 24in`. Raise `DRIVE_KP` until the robot slightly overshoots, then raise `DRIVE_KD` until the overshoot stops. Do the same for turning with `Test: Turn 90`, using `TURN_KP` and `TURN_KD`.
