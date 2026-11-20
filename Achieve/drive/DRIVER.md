# 7405X Driver Controls

## Buttons

| Control | What it does |
|---|---|
| **Left stick** up / down | Drive forward / backward |
| **Right stick** left / right | Turn |
| **R1** (hold) | Lift up |
| **R2** (hold) | Lift down |
| **L2** (tap) | Claw: open ↔ close |
| **L1** (tap) | Slow mode on / off (40% speed, for lining up) |
| **X** (tap) | Hold mode on / off (wheels lock when you let go of the sticks, hard to push) |

- The lift stays where you leave it when you let go of R1 and R2.
- The claw keeps squeezing while it's closed, so pieces don't slip out. Tap L2 again to drop them.
- The sticks are gentle near the middle for fine control and full power at the edge.

## Buzzes

| Buzz | Means |
|---|---|
| One short buzz | Slow mode toggled |
| Two short buzzes | Hold mode toggled |
| Long-short-long-short | **15 seconds left: drive back and touch your loader to park (21 points)** |
| Three long buzzes at startup | A cable is unplugged. Check the brain screen |

## Controller screen

```
Batt 87%  Mtr 41C
FAST COAST
Lift 90  Claw SHUT
```

- **Batt:** battery charge. Swap the battery before a match if it's low.
- **Mtr:** hottest drive motor. Above about 55°C the motors lose power.
- **FAST/SLOW** and **COAST/HOLD:** which modes are on.
- **Lift:** lift angle in degrees. **Claw:** OPEN or SHUT.

## Before every match

1. **Lift all the way down, claw fully open** when you turn the robot on. The code treats that as the starting position.
2. Don't touch the robot for about 2 seconds while the brain says "Calibrating IMU".
3. Tap the brain screen to pick the auton. The name shows on the controller too.
4. Check the controller screen for battery %.
