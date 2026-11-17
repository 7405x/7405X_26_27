// arm.h - the arm that scoops and scores.
#pragma once
#include "robot-config.h"

// ---------------- Arm positions (motor degrees) ----------------
// 0 = arm all the way DOWN, where it rests when the program starts.
// These are placeholders. To find the real numbers: start the program with
// the arm down, move it with R1/R2, and read "Arm:" on the controller screen
// at each position you want.
const double ARM_DOWN_DEG  = 0;    // resting / scooping position
const double ARM_CARRY_DEG = 90;   // lifted enough to carry without dragging
const double ARM_SCORE_DEG = 200;  // high enough to drop onto a goal

// Soft limits stop the driver from slamming the arm into its hard stops.
// Leave OFF until you've measured ARM_SCORE_DEG, then turn on and set MAX.
const bool   ARM_LIMITS_ON = false;
const double ARM_MAX_DEG   = 220;

// Run one loop of driver control for the arm (R1 = up, R2 = down).
void armControlStep();

// Auton: move the arm to a position. If wait is true, the robot waits until
// the arm gets there (or 1.5s passes) before doing the next step.
void armTo(double deg, bool wait = true);

// Call once at startup with the arm resting down. Sets "down" to 0.
void armReset();

double armPosition();
