# 7405X Wiring Guide

Plug each device into the port number listed. These match `include/robot-config.h`. If you have to use a different port, change it there too.

"Front" means the side the robot drives toward when you push the left stick forward.

## Ports

| Port | Device | Where on the robot | Reversed in code? |
|---|---|---|---|
| 1 | Motor: left front | Left side, front | No |
| 2 | Motor: left middle | Left side, middle | No |
| 3 | Motor: left back | Left side, back | No |
| 4 | Motor: right front | Right side, front | Yes |
| 5 | Motor: right middle | Right side, middle | Yes |
| 6 | Motor: right back | Right side, back | Yes |
| 10 | Inertial sensor (IMU) | See below | - |
| Any free port | Radio | See below | - |

Ports 7–9 and 11–21 are free.

## Inertial sensor (IMU)
- Mount it **flat** (level with the floor) and as close to the middle of the robot as you can.
- Screw it to something solid, not something that shakes or flexes. Vibration makes auton turns drift.
- Any rotation works: the code only cares about which way the robot turns, not how the sensor faces.

## Radio
- The radio isn't set in the code, so any free port works.
- Mount it high and in the open, not buried under metal. Metal blocks the signal.

## Battery
- 1100mAh V5 battery only (the rules require it).
- Mount it where you can reach it quickly. The rules say the robot must be easy to power off.

## After wiring: check motor directions
1. Put the robot on blocks so the wheels are off the ground.
2. Download the code and start it with **driver control**.
3. Push the **left stick forward**. Every wheel should spin forward. Then push the **right stick right**: the left wheels should spin forward and the right wheels backward, so the robot turns right.
4. If one wheel spins **backward**, open `src/robot-config.cpp` and flip that motor's `true`/`false`.
5. If one wheel **doesn't spin at all**, check its cable. The brain also shows a red "CHECK CABLES" warning at startup for any motor it can't find.

## Also check in `include/robot-config.h`
These numbers are guesses. Change them to match the robot:

| Setting | Current guess | How to find it |
|---|---|---|
| `DRIVE_CARTRIDGE` | `ratio6_1` (blue, 600 rpm) | Color of the cartridge cap on the motor: blue = `ratio6_1`, green = `ratio18_1`, red = `ratio36_1` |
| `WHEEL_DIAMETER_IN` | 3.25 | Printed on the wheel (common sizes: 2.75, 3.25, 4) |
| `GEAR_RATIO` | 0.75 | Teeth on the motor's gear ÷ teeth on the wheel's gear. Use 1.0 if the motor drives the wheel directly |

## Cable tips
- Push every cable in until it clicks, and pull gently to check it's latched.
- Zip-tie cables so they can't catch on wheels, field objects or the toggler.
- Leave some slack at each motor so cables don't pull out when the robot bumps something.
