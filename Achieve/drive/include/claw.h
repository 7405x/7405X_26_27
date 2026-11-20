// claw.h - motor claw that grabs pins and cups.
#pragma once
#include "robot-config.h"

// The claw must be fully OPEN when the program starts. That spot becomes 0.

// How hard the claw squeezes, in percent of the motor's max torque.
// Too low = pieces slip out. Too high = the motor overheats while holding.
const double CLAW_GRIP_TORQUE = 40;

// Run one loop of driver control for the claw (L2 = toggle open/closed).
void clawControlStep();

// Auton: grab or let go. If wait is true, the robot waits for the claw to
// finish (or give up after 0.6s) before the next step.
void clawClose(bool wait = true);
void clawOpen(bool wait = true);

// Call once at startup with the claw fully open.
void clawReset();

bool clawIsClosed();
