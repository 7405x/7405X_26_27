// drive.h - drivetrain helpers used by driver control and autonomous.
#pragma once
#include "robot-config.h"

// Set both sides directly, in volts (-12 to 12).
void setDrive(double leftVolts, double rightVolts);
void stopDrive(brakeType mode = brake);

// Run one loop of driver control (call this repeatedly).
void driverControlStep();
bool isSlowMode();
bool isHoldMode();

// ---------- Health checks ----------
// Returns how many drive motors aren't detected, and writes their names
// (e.g. "LF RB ") into namesOut.
int countUnpluggedMotors(char* namesOut, int outSize);
// Temperature of the hottest drive motor in Celsius. V5 motors start
// cutting power at 55C.
double hottestDriveMotorC();

// ---------- Autonomous moves ----------
// Drive straight a distance in inches (negative = backward).
// Holds the heading it started at using the IMU.
// maxVolts limits speed (12 = full). timeoutMs gives up if it gets stuck.
void driveDistance(double inches, double maxVolts = 10.0, int timeoutMs = 3000);

// Turn in place to an absolute heading in degrees (0 = where the robot faced
// when the IMU calibrated, positive = clockwise).
void turnToHeading(double degrees, double maxVolts = 10.0, int timeoutMs = 2000);

// Turn in place by a relative amount (positive = clockwise).
void turnBy(double degrees, double maxVolts = 10.0, int timeoutMs = 2000);

// ---------- Field position (odometry) ----------
// See drive.cpp for the coordinate system. Start the task once in pre_auton.
int odometryTask();
// Tell the robot where it is (call at the start of every auton).
void setPose(double x, double y, double headingDeg);
double poseX();
double poseY();
// Turn to face a field point, then drive straight to it.
void driveToPoint(double x, double y, double maxVolts = 10.0, int timeoutMs = 3000);

// Wheel travel in inches since the last resetDriveEncoders().
double driveInches();
void resetDriveEncoders();
