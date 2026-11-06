#include "robot-config.h"

brain Brain;
controller Controller1 = controller(primary);
competition Competition;

// motor(port, cartridge, reversed)
// Usually one side is reversed because the motors face opposite directions.
// Test each motor: if pushing the stick forward makes it spin backward, flip it.
motor leftFront  = motor(LEFT_FRONT_PORT,  DRIVE_CARTRIDGE, false);
motor leftMiddle = motor(LEFT_MIDDLE_PORT, DRIVE_CARTRIDGE, false);
motor leftBack   = motor(LEFT_BACK_PORT,   DRIVE_CARTRIDGE, false);

motor rightFront  = motor(RIGHT_FRONT_PORT,  DRIVE_CARTRIDGE, true);
motor rightMiddle = motor(RIGHT_MIDDLE_PORT, DRIVE_CARTRIDGE, true);
motor rightBack   = motor(RIGHT_BACK_PORT,   DRIVE_CARTRIDGE, true);

motor_group leftDrive  = motor_group(leftFront, leftMiddle, leftBack);
motor_group rightDrive = motor_group(rightFront, rightMiddle, rightBack);

inertial IMU = inertial(IMU_PORT);
