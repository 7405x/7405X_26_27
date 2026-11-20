#include "claw.h"

// Speed the claw opens/closes at, in percent.
const double CLAW_SPEED = 100;
// How long auton waits for the claw to open or close.
const int CLAW_WAIT_MS = 600;

static bool closed = false;

void clawReset() {
  claw.resetPosition();
  claw.setStopping(hold);
  closed = false;
}

bool clawIsClosed() {
  return closed;
}

// Closing doesn't aim for a position: the motor keeps squeezing at a
// limited torque, so it grips pieces of any size and doesn't burn out
// when it stalls against one.
static void startClose() {
  claw.setMaxTorque(CLAW_GRIP_TORQUE, percent);
  claw.spin(forward, CLAW_SPEED, percent);
  closed = true;
}

// Opening goes back to the startup position (0) at full torque.
static void startOpen() {
  claw.setMaxTorque(100, percent);
  claw.spinToPosition(0, degrees, CLAW_SPEED, velocityUnits::pct, false);
  closed = false;
}

void clawControlStep() {
  if (Controller1.ButtonL2.PRESSED) {
    if (closed) startOpen();
    else startClose();
  }
}

void clawClose(bool wait) {
  startClose();
  if (wait) vex::wait(CLAW_WAIT_MS, msec);
}

void clawOpen(bool wait) {
  startOpen();
  if (wait) vex::wait(CLAW_WAIT_MS, msec);
}
