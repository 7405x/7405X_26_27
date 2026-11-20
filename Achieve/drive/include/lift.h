// lift.h - single bar lift (one motor on port 16 swings the bar up/down).
#pragma once
#include "robot-config.h"

// ---------------- Lift positions (motor degrees) ----------------
// 0 = lift all the way DOWN, where it rests when the program starts.
// These are placeholders. To find the real numbers: start the program with
// the lift down, move it with R1/R2, and read "Lift:" on the controller screen
// at each position you want.
const double LIFT_DOWN_DEG  = 0;    // resting / scooping position
const double LIFT_CARRY_DEG = 90;   // high enough to carry without dragging
const double LIFT_SCORE_DEG = 200;  // high enough to drop onto a goal

// Soft limits stop the driver from slamming the lift into its hard stops.
// Leave OFF until you've measured LIFT_SCORE_DEG, then turn on and set MAX.
const bool   LIFT_LIMITS_ON = false;
const double LIFT_MAX_DEG   = 220;

// Run one loop of driver control for the lift (R1 = up, R2 = down).
void liftControlStep();

// Auton: move the lift to a position. If wait is true, the robot waits until
// the lift gets there (or 1.5s passes) before doing the next step.
void liftTo(double deg, bool wait = true);

// Call once at startup with the lift resting down. Sets "down" to 0.
void liftReset();

double liftPosition();
