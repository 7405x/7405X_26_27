#include "drive.h"

// ============================================================================
//  PID tuning constants. These are STARTING values - you will need to tune
//  them on your robot. Tuning order: raise kP until it slightly overshoots,
//  then raise kD until the overshoot goes away, add kI only if it stops short.
// ============================================================================

// Driving straight (error measured in inches, output in volts)
const double DRIVE_KP = 0.6;
const double DRIVE_KI = 0.0;
const double DRIVE_KD = 0.04;     // volts per (inch/second)
const double DRIVE_SETTLE_IN = 0.5;

// Keeping straight while driving (error in degrees)
const double HEADING_KP = 0.15;

// Turning (error measured in degrees, output in volts)
const double TURN_KP = 0.12;
const double TURN_KI = 0.004;
const double TURN_KD = 0.008;     // volts per (degree/second)
const double TURN_SETTLE_DEG = 1.0;
const double TURN_I_START = 10.0; // only build up kI within this many degrees

// How long the robot must stay inside the settle range to count as "done".
const int SETTLE_TIME_MS = 100;
const int LOOP_MS = 10;

// ============================================================================

static double clampD(double value, double lo, double hi) {
  if (value < lo) return lo;
  if (value > hi) return hi;
  return value;
}

// Wrap an angle into the range -180 to 180 so turns take the short way.
static double wrapAngle(double deg) {
  while (deg > 180) deg -= 360;
  while (deg < -180) deg += 360;
  return deg;
}

void setDrive(double leftVolts, double rightVolts) {
  leftDrive.spin(forward, leftVolts, volt);
  rightDrive.spin(forward, rightVolts, volt);
}

void stopDrive(brakeType mode) {
  leftDrive.stop(mode);
  rightDrive.stop(mode);
}

// ---------------------------------------------------------------------------
//  Encoders -> inches
// ---------------------------------------------------------------------------
void resetDriveEncoders() {
  leftDrive.resetPosition();
  rightDrive.resetPosition();
}

double driveInches() {
  // Motor degrees -> wheel degrees -> inches traveled.
  double motorDeg = (leftDrive.position(degrees) + rightDrive.position(degrees)) / 2.0;
  double wheelRevs = (motorDeg / 360.0) * GEAR_RATIO;
  return wheelRevs * M_PI * WHEEL_DIAMETER_IN;
}

// ---------------------------------------------------------------------------
//  Driver control
// ---------------------------------------------------------------------------
static double applyDeadband(int value) {
  if (abs(value) < JOYSTICK_DEADBAND) return 0;
  return value;
}

// Joystick curve: small stick movements give finer control, full stick is
// still full power. CURVE = 0 is linear; higher = more gentle near center.
const double CURVE = 0.5;
static double applyCurve(double pct) {
  double x = pct / 100.0;
  return 100.0 * ((1 - CURVE) * x + CURVE * x * x * x);
}

// Slow mode: toggled with L1. Good for lining up on a loader or goal.
const double SLOW_MODE_SCALE = 0.4;
static bool slowMode = false;
// Hold mode: toggled with X. Wheels lock in place when sticks are released,
// which makes the robot hard to push (useful for defense or staying parked).
static bool holdMode = false;

bool isSlowMode() { return slowMode; }
bool isHoldMode() { return holdMode; }

void driverControlStep() {
  if (Controller1.ButtonL1.PRESSED) {
    slowMode = !slowMode;
    Controller1.rumble(".");
  }
  if (Controller1.ButtonX.PRESSED) {
    holdMode = !holdMode;
    Controller1.rumble("..");
  }

  double left, right;  // percent, -100 to 100

  if (TANK_DRIVE) {
    left  = applyCurve(applyDeadband(Controller1.Axis3.position()));
    right = applyCurve(applyDeadband(Controller1.Axis2.position()));
  } else {
    double fwd  = applyCurve(applyDeadband(Controller1.Axis3.position()));
    double turn = applyCurve(applyDeadband(Controller1.Axis1.position()));
    left  = fwd + turn;
    right = fwd - turn;
  }

  left  = clampD(left,  -100, 100);
  right = clampD(right, -100, 100);
  if (slowMode) {
    left  *= SLOW_MODE_SCALE;
    right *= SLOW_MODE_SCALE;
  }

  // Sticks released -> stop with the chosen brake mode.
  if (left == 0 && right == 0) {
    stopDrive(holdMode ? hold : coast);
    return;
  }

  // Convert percent to volts (12V = 100%). Voltage control gives the
  // driver full power instead of the motor's built-in speed limiter.
  setDrive(left * 0.12, right * 0.12);
}

// ---------------------------------------------------------------------------
//  Health checks
// ---------------------------------------------------------------------------
static motor* allDriveMotors[] = {&leftFront, &leftMiddle, &leftBack,
                                  &rightFront, &rightMiddle, &rightBack};
static const char* allDriveNames[] = {"LF", "LM", "LB", "RF", "RM", "RB"};

int countUnpluggedMotors(char* namesOut, int outSize) {
  int count = 0;
  namesOut[0] = '\0';
  for (int i = 0; i < 6; i++) {
    if (!allDriveMotors[i]->installed()) {
      count++;
      strncat(namesOut, allDriveNames[i], outSize - strlen(namesOut) - 1);
      strncat(namesOut, " ", outSize - strlen(namesOut) - 1);
    }
  }
  return count;
}

double hottestDriveMotorC() {
  double hottest = 0;
  for (int i = 0; i < 6; i++) {
    double t = allDriveMotors[i]->temperature(celsius);
    if (t > hottest) hottest = t;
  }
  return hottest;
}

// ---------------------------------------------------------------------------
//  Autonomous: drive straight with PID
// ---------------------------------------------------------------------------
void driveDistance(double inches, double maxVolts, int timeoutMs) {
  // Measure from where we are now (don't reset encoders - odometry uses them).
  double startInches = driveInches();
  double targetHeading = IMU.rotation(degrees);

  double prevError = inches;
  double integral = 0;
  int settledMs = 0;
  int elapsedMs = 0;

  while (elapsedMs < timeoutMs) {
    double error = inches - (driveInches() - startInches);

    integral += error * (LOOP_MS / 1000.0);
    double derivative = (error - prevError) / (LOOP_MS / 1000.0);
    prevError = error;

    double power = DRIVE_KP * error + DRIVE_KI * integral + DRIVE_KD * derivative;
    power = clampD(power, -maxVolts, maxVolts);

    // If the robot drifts off its heading, slow one side to steer back.
    double headingError = wrapAngle(targetHeading - IMU.rotation(degrees));
    double correction = HEADING_KP * headingError;

    setDrive(power + correction, power - correction);

    if (fabs(error) < DRIVE_SETTLE_IN) {
      settledMs += LOOP_MS;
      if (settledMs >= SETTLE_TIME_MS) break;
    } else {
      settledMs = 0;
    }

    wait(LOOP_MS, msec);
    elapsedMs += LOOP_MS;
  }
  stopDrive(brake);
}

// ---------------------------------------------------------------------------
//  Autonomous: turn with PID
// ---------------------------------------------------------------------------
void turnToHeading(double degreesTarget, double maxVolts, int timeoutMs) {
  double prevError = wrapAngle(degreesTarget - IMU.rotation(degrees));
  double integral = 0;
  int settledMs = 0;
  int elapsedMs = 0;

  while (elapsedMs < timeoutMs) {
    double error = wrapAngle(degreesTarget - IMU.rotation(degrees));

    // Only use the integral near the target, and reset it if we cross over,
    // so it doesn't wind up and cause a big overshoot.
    if (fabs(error) < TURN_I_START) integral += error * (LOOP_MS / 1000.0);
    else integral = 0;
    if ((error > 0) != (prevError > 0)) integral = 0;

    double derivative = (error - prevError) / (LOOP_MS / 1000.0);
    prevError = error;

    double power = TURN_KP * error + TURN_KI * integral + TURN_KD * derivative;
    power = clampD(power, -maxVolts, maxVolts);

    // Positive power = turn clockwise (left forward, right backward).
    setDrive(power, -power);

    if (fabs(error) < TURN_SETTLE_DEG) {
      settledMs += LOOP_MS;
      if (settledMs >= SETTLE_TIME_MS) break;
    } else {
      settledMs = 0;
    }

    wait(LOOP_MS, msec);
    elapsedMs += LOOP_MS;
  }
  stopDrive(brake);
}

void turnBy(double deg, double maxVolts, int timeoutMs) {
  turnToHeading(IMU.rotation(degrees) + deg, maxVolts, timeoutMs);
}

// ---------------------------------------------------------------------------
//  Odometry: keeps track of where the robot is on the field.
//
//  Field coordinates (inches), looking at Figure 1.2 in the game manual:
//    x = 0 at the RED wall, 144 at the BLUE wall
//    y = 0 at the bottom wall, 144 at the top wall
//    heading 0 = facing +y (up in the figure), 90 = facing +x (toward blue),
//    clockwise positive, same as the IMU.
//
//  Every 10ms it reads how far the wheels moved and which way the IMU says
//  the robot is facing, and adds that little step to x and y.
// ---------------------------------------------------------------------------
static double odomX = 0, odomY = 0;
static double lastInches = 0;

int odometryTask() {
  lastInches = driveInches();
  while (true) {
    double now = driveInches();
    double step = now - lastInches;
    lastInches = now;

    double headingRad = IMU.rotation(degrees) * M_PI / 180.0;
    odomX += step * sin(headingRad);
    odomY += step * cos(headingRad);

    wait(10, msec);
  }
  return 0;
}

void setPose(double x, double y, double headingDeg) {
  odomX = x;
  odomY = y;
  lastInches = driveInches();
  IMU.setRotation(headingDeg, degrees);
  IMU.setHeading(fmod(fmod(headingDeg, 360) + 360, 360), degrees);
}

double poseX() { return odomX; }
double poseY() { return odomY; }

void driveToPoint(double x, double y, double maxVolts, int timeoutMs) {
  double dx = x - odomX;
  double dy = y - odomY;
  double dist = sqrt(dx * dx + dy * dy);
  if (dist < 0.5) return;

  double heading = atan2(dx, dy) * 180.0 / M_PI;
  turnToHeading(heading, maxVolts);
  driveDistance(dist, maxVolts, timeoutMs);
}
