#include "arm.h"

// Driver arm speed in percent. Lower = more control, higher = faster.
const double ARM_DRIVER_SPEED = 80;
// Auton arm speed in percent.
const double ARM_AUTON_SPEED = 60;

void armReset() {
  arm.resetPosition();
  // Hold keeps the arm where it is when no button is pressed, so it doesn't
  // fall under the weight of a pin/cup.
  arm.setStopping(hold);
}

double armPosition() {
  return arm.position(degrees);
}

void armControlStep() {
  bool up = Controller1.ButtonR1.pressing();
  bool down = Controller1.ButtonR2.pressing();

  if (ARM_LIMITS_ON) {
    if (up && armPosition() >= ARM_MAX_DEG) up = false;
    if (down && armPosition() <= ARM_DOWN_DEG) down = false;
  }

  if (up && !down) {
    arm.spin(forward, ARM_DRIVER_SPEED, percent);
  } else if (down && !up) {
    arm.spin(reverse, ARM_DRIVER_SPEED, percent);
  } else {
    arm.stop(hold);
  }
}

void armTo(double deg, bool wait) {
  // Give up after 1.5s so a jammed arm can't freeze the whole auton.
  arm.setTimeout(1500, msec);
  arm.spinToPosition(deg, degrees, ARM_AUTON_SPEED, velocityUnits::pct, wait);
}
