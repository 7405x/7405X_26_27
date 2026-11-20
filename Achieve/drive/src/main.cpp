// 7405X - RECF Achieve (Pinnacle) drivetrain code
// 6-motor drive (3 per side) + inertial sensor + single bar lift + claw.

#include "vex.h"
#include "robot-config.h"
#include "drive.h"
#include "autons.h"
#include "lift.h"
#include "claw.h"

// Runs once when the program starts, before the match begins.
void pre_auton() {
  // Warn if a cable is loose before the match instead of finding out mid-match.
  char missing[32];
  int unplugged = countUnpluggedMotors(missing, sizeof(missing));
  if (unplugged > 0 || !IMU.installed() || !lift.installed() || !claw.installed()) {
    Brain.Screen.clearScreen();
    Brain.Screen.setPenColor(red);
    Brain.Screen.setCursor(1, 1);
    Brain.Screen.print("CHECK CABLES!");
    Brain.Screen.setCursor(2, 1);
    if (unplugged > 0) Brain.Screen.print("Motors not found: %s", missing);
    Brain.Screen.setCursor(3, 1);
    if (!IMU.installed()) Brain.Screen.print("IMU not found - auton turns won't work");
    Brain.Screen.setCursor(4, 1);
    if (!lift.installed()) Brain.Screen.print("Lift motor (port 16) not found");
    Brain.Screen.setCursor(5, 1);
    if (!claw.installed()) Brain.Screen.print("Claw motor (port 17) not found");
    Brain.Screen.setPenColor(white);
    Controller1.rumble("---");
    wait(3, sec);
  }

  // Calibrate the IMU. The robot must NOT move during this (~2 seconds).
  Brain.Screen.clearScreen();
  Brain.Screen.setCursor(1, 1);
  Brain.Screen.print("Calibrating IMU... don't touch the robot");
  IMU.calibrate();
  waitUntil(!IMU.isCalibrating());

  resetDriveEncoders();
  liftReset();  // the lift must be resting DOWN when the program starts
  clawReset();  // the claw must be fully OPEN when the program starts
  static task odom(odometryTask);
  runAutonSelector();
}

// Driver period of an alliance match is 105 seconds. Parking (touching your
// own alliance loader at the end) is worth 21 points, so warn the driver.
const int DRIVER_PERIOD_SEC = 105;
const int PARK_WARNING_SEC = 15;  // seconds left when the controller buzzes

// Shows status on the controller screen during driver control.
int controllerDisplayTask() {
  while (true) {
    Controller1.Screen.clearScreen();
    Controller1.Screen.setCursor(1, 1);
    Controller1.Screen.print("Batt %d%%  Mtr %.0fC", Brain.Battery.capacity(),
                             hottestDriveMotorC());
    Controller1.Screen.setCursor(2, 1);
    Controller1.Screen.print("%s %s", isSlowMode() ? "SLOW" : "FAST",
                             isHoldMode() ? "HOLD" : "COAST");
    Controller1.Screen.setCursor(3, 1);
    Controller1.Screen.print("Lift %.0f  Claw %s", liftPosition(),
                             clawIsClosed() ? "SHUT" : "OPEN");
    // The controller screen is slow; updating too often causes lag.
    wait(500, msec);
  }
  return 0;
}

// Runs during the autonomous period (15s alliance, or the full 60s
// Solo Coding match). Field control / timed run decides how long.
void autonomous() {
  leftDrive.setStopping(brake);
  rightDrive.setStopping(brake);
  runSelectedAuton();
}

// Runs during driver control (Solo Driving and alliance matches).
void usercontrol() {
  // Coast feels smoother for drivers; switch to brake if you prefer.
  leftDrive.setStopping(coast);
  rightDrive.setStopping(coast);

  // Start the display task only once, even if driver control restarts.
  static task display(controllerDisplayTask);
  timer matchTimer;
  bool warned = false;

  while (true) {
    driverControlStep();
    liftControlStep();
    clawControlStep();

    // Buzz once when it's time to head back to the loader to park.
    // (In Solo Driving there is no parking bonus - just ignore the buzz.)
    if (!warned && matchTimer.time(sec) > DRIVER_PERIOD_SEC - PARK_WARNING_SEC) {
      Controller1.rumble("-.-.");
      warned = true;
    }

    wait(20, msec);
  }
}

int main() {
  Competition.autonomous(autonomous);
  Competition.drivercontrol(usercontrol);

  pre_auton();

  while (true) {
    wait(100, msec);
  }
}
