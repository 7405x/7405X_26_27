#include "lift.h"

// Driver lift speed in percent. Lower = more control, higher = faster.
const double LIFT_DRIVER_SPEED = 80;
// Auton lift speed in percent.
const double LIFT_AUTON_SPEED = 60;

void liftReset() {
  lift.resetPosition();
  // Hold keeps the lift where it is when no button is pressed, so it doesn't
  // fall under the weight of a pin/cup.
  lift.setStopping(hold);
}

double liftPosition() {
  return lift.position(degrees);
}

void liftControlStep() {
  bool up = Controller1.ButtonR1.pressing();
  bool down = Controller1.ButtonR2.pressing();

  if (LIFT_LIMITS_ON) {
    if (up && liftPosition() >= LIFT_MAX_DEG) up = false;
    if (down && liftPosition() <= LIFT_DOWN_DEG) down = false;
  }

  if (up && !down) {
    lift.spin(forward, LIFT_DRIVER_SPEED, percent);
  } else if (down && !up) {
    lift.spin(reverse, LIFT_DRIVER_SPEED, percent);
  } else {
    lift.stop(hold);
  }
}

void liftTo(double deg, bool wait) {
  // Give up after 1.5s so a jammed lift can't freeze the whole auton.
  lift.setTimeout(1500, msec);
  lift.spinToPosition(deg, degrees, LIFT_AUTON_SPEED, velocityUnits::pct, wait);
}
