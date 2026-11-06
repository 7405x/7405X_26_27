// robot-config.h - every hardware setting lives here.
// CHANGE THESE to match your robot before you run anything.
#pragma once
#include "vex.h"

// ---------------- Ports ----------------
// Left side motors. If a motor spins the wrong way, flip its "true/false"
// in robot-config.cpp (that's the "reversed" flag).
#define LEFT_FRONT_PORT  PORT1
#define LEFT_MIDDLE_PORT PORT2
#define LEFT_BACK_PORT   PORT3

#define RIGHT_FRONT_PORT  PORT4
#define RIGHT_MIDDLE_PORT PORT5
#define RIGHT_BACK_PORT   PORT6

#define IMU_PORT PORT10

// ---------------- Drive geometry ----------------
// Cartridge inside the motors: ratio6_1 = blue (600rpm),
// ratio18_1 = green (200rpm), ratio36_1 = red (100rpm).
#define DRIVE_CARTRIDGE ratio6_1

// Wheel diameter in inches (common: 2.75, 3.25, 4.0).
const double WHEEL_DIAMETER_IN = 3.25;

// External gear ratio = motor gear teeth / wheel gear teeth.
// Direct drive = 1.0. Example: 36T on motor driving 48T on wheel = 36/48 = 0.75.
const double GEAR_RATIO = 0.75;

// ---------------- Driver settings ----------------
// false = split arcade (left stick up/down drives forward/back,
//         right stick left/right turns)
// true  = tank (left stick drives left side, right stick drives right side)
const bool TANK_DRIVE = false;

// Stick values under this (out of 100) are ignored so the robot doesn't creep.
const int JOYSTICK_DEADBAND = 5;

// ---------------- Devices (defined in robot-config.cpp) ----------------
extern brain Brain;
extern controller Controller1;
extern competition Competition;

extern motor leftFront, leftMiddle, leftBack;
extern motor rightFront, rightMiddle, rightBack;
extern motor_group leftDrive;
extern motor_group rightDrive;
extern inertial IMU;
