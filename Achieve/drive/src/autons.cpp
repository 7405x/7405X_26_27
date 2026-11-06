#include "autons.h"
#include "drive.h"

// ============================================================================
//  FIELD MAP (inches) - read off Figure 1.2 of the Pinnacle v2.0 manual.
//  These came from a picture, not a tape measure. Measure the real field and
//  fix any that are off. Field pieces can also be +/- 1" from these spots.
//
//  x = 0 at the RED wall, 144 at the BLUE wall
//  y = 0 at the bottom wall of Figure 1.2, 144 at the top wall
//  heading 0 = facing +y, 90 = facing the blue wall (clockwise positive)
//
//  Everything is written for the RED side. Blue routines reuse the same code
//  mirrored across the field (x -> 144 - x).
// ============================================================================
//  Red loaders .............. on the red wall at y ~= 12 and y ~= 132
//  Red goals ................ (24, 48) and (24, 96)
//  Red zone ends at ......... x ~= 48 (white tape line)
//  Neutral goals ............ (72, 24) and (72, 120)
//  Center goal .............. (72, 72)
//  Red-zone roller .......... on the red wall, y ~= 58 to 85
//  Unknown grey circle ...... (24, 72) - check what this is on the real field
// ============================================================================

// Robot is 18" x 18", so its center is 9" from any side.
const double HALF_ROBOT = 9.0;

// Starting spot: back of the robot touching the red loader, facing the blue
// wall. Loader sticks out about 4" from the wall.
const double START_X = 4.0 + HALF_ROBOT;  // 13
const double START_Y = 12.0;              // bottom loader (top is 144 - 12)

// Lane to drive up between the red goals and the zone line.
const double LANE_X = 35.0;
// Height to approach the roller at. Chosen to miss the red goal at y=48
// and the grey circle at y=72. (The top-loader version mirrors this to 83.)
const double ROLLER_Y = 61.0;
// How close the robot's center gets to the red wall before pressing in.
const double ROLLER_STOP_X = 12.0;

// Neutral roller on the bottom wall, x ~= 58 to 85. Approach spot keeps the
// robot left of the neutral goal at (72, 24) and fully on our side of the
// field's center line (x = 72), and far enough off the wall (y = 14) that
// the robot's corners don't hit the wall while it turns.
const double NEUTRAL_X = 58.0;
const double NEUTRAL_Y = 14.0;

// ---------------------------------------------------------------------------
//  Mirroring helpers. Write routines once for red-bottom; these flip them
//  for blue (mirrorX) and for the top loader (mirrorY).
// ---------------------------------------------------------------------------
static bool mirrorX = false;
static bool mirrorY = false;

static double fx(double x) { return mirrorX ? 144.0 - x : x; }
static double fy(double y) { return mirrorY ? 144.0 - y : y; }
static double fh(double h) {
  if (mirrorX) h = -h;
  if (mirrorY) h = 180.0 - h;
  return h;
}

static void startAt(double x, double y, double heading) { setPose(fx(x), fy(y), fh(heading)); }
static void goTo(double x, double y, double maxVolts = 10.0) { driveToPoint(fx(x), fy(y), maxVolts); }
static void face(double heading) { turnToHeading(fh(heading)); }

// ============================================================================
//  Routines
// ============================================================================

// ALLIANCE (15s): drive to our zone's roller and press the toggler into it.
// A drive-only robot can't score pins, so the roller is what we can do:
// it's half of the autonomous ranking point (the other half is 3 cups +
// 4 halfpins on 2 goals, which our partner would have to score), and it
// makes yellow halfpins on our alliance goals worth points.
//
// UNTESTED PATH - walk it on the real field first. The lane between the red
// goal and the slanted pin near (45, 45) is tight, so the robot may brush
// one of them.
// Push the compliant toggler into a roller, then back off so it springs back.
// Low power + short timeout so the motors don't stall against the wall.
// Tune the distance/power once you see how much push the toggler needs.
static void pressToggler() {
  driveDistance(5, 5.0, 800);
  driveDistance(-6, 8.0, 1000);
}

static void rollerRoutine() {
  startAt(START_X, START_Y, 90);   // facing the blue wall, back on the loader

  goTo(LANE_X, START_Y);           // drive out into the zone
  goTo(LANE_X, ROLLER_Y);          // drive up the lane
  goTo(ROLLER_STOP_X, ROLLER_Y);   // drive toward the red wall
  face(270);                       // square up facing the wall
  pressToggler();
}

// ALLIANCE (15s): flip the neutral roller nearest our loader to our color.
// Shorter than the zone-roller path (~45" then one turn). Note: the other
// alliance can flip it back later, and this does NOT count toward the
// autonomous ranking point (that needs OUR zone's roller).
// UNTESTED - the first move will likely push the pin lying near (24, 20).
static void neutralRollerRoutine() {
  startAt(START_X, START_Y, 90);
  goTo(NEUTRAL_X, NEUTRAL_Y);      // drive along the bottom wall
  face(180);                       // face the bottom wall
  pressToggler();
}

static void setSide(bool blue, bool leftLoader) {
  mirrorX = blue;
  // Red drivers' left = top of Figure 1.2; blue drivers' left = bottom.
  mirrorY = blue ? !leftLoader : leftLoader;
}

static void redLeft()          { setSide(false, true);  rollerRoutine(); }
static void redRight()         { setSide(false, false); rollerRoutine(); }
static void blueLeft()         { setSide(true, true);   rollerRoutine(); }
static void blueRight()        { setSide(true, false);  rollerRoutine(); }
static void redLeftNeutral()   { setSide(false, true);  neutralRollerRoutine(); }
static void redRightNeutral()  { setSide(false, false); neutralRollerRoutine(); }
static void blueLeftNeutral()  { setSide(true, true);   neutralRollerRoutine(); }
static void blueRightNeutral() { setSide(true, false);  neutralRollerRoutine(); }

// SOLO CODING (60s). Rollers alone are worth 0 points in solo matches - they
// only change what yellow halfpins are worth. Until the robot can carry and
// nest pins, this just runs the roller path so you can practice it.
static void soloCoding() {
  mirrorX = false; mirrorY = false;
  rollerRoutine();
}

// Tuning tests (not for matches).
static void testDrive() {
  driveDistance(24);
  wait(500, msec);
  driveDistance(-24);
}

static void testTurn() {
  setPose(0, 0, 0);
  turnToHeading(90);
  wait(500, msec);
  turnToHeading(0);
}

// Drives a 24" square using field points. If odometry is right it ends
// exactly where it started. Check the brain screen for the final x, y.
static void testSquare() {
  setPose(0, 0, 0);
  driveToPoint(0, 24);
  driveToPoint(24, 24);
  driveToPoint(24, 0);
  driveToPoint(0, 0);
  turnToHeading(0);
  Brain.Screen.clearScreen();
  Brain.Screen.setCursor(1, 1);
  Brain.Screen.print("Ended at x=%.1f y=%.1f", poseX(), poseY());
}

static void doNothing() {}

// ============================================================================
//  Selector
//  "Left" / "Right" = which loader, as seen standing in YOUR driver box.
// ============================================================================

struct AutonOption {
  const char* name;
  void (*run)();
};

static AutonOption autons[] = {
  {"Red L: Zone Roller",     redLeft},
  {"Red R: Zone Roller",     redRight},
  {"Blue L: Zone Roller",    blueLeft},
  {"Blue R: Zone Roller",    blueRight},
  {"Red L: Neutral Roller",  redLeftNeutral},
  {"Red R: Neutral Roller",  redRightNeutral},
  {"Blue L: Neutral Roller", blueLeftNeutral},
  {"Blue R: Neutral Roller", blueRightNeutral},
  {"Solo Coding",        soloCoding},
  {"Test: Drive 24in",   testDrive},
  {"Test: Turn 90",      testTurn},
  {"Test: Square",       testSquare},
  {"None",               doNothing},
};
static const int NUM_AUTONS = sizeof(autons) / sizeof(autons[0]);
static int selected = 0;

static void drawSelector() {
  Brain.Screen.clearScreen();
  Brain.Screen.setFont(mono30);
  Brain.Screen.setCursor(1, 1);
  Brain.Screen.print("Auton: %s", autons[selected].name);
  Brain.Screen.setFont(mono20);
  Brain.Screen.setCursor(4, 1);
  Brain.Screen.print("Tap screen to change (%d/%d)", selected + 1, NUM_AUTONS);
  Brain.Screen.setCursor(6, 1);
  Brain.Screen.print("IMU heading: %.1f", IMU.heading(degrees));

  Controller1.Screen.clearScreen();
  Controller1.Screen.setCursor(1, 1);
  Controller1.Screen.print("%s", autons[selected].name);
}

static void onScreenPressed() {
  selected = (selected + 1) % NUM_AUTONS;
  drawSelector();
}

void runAutonSelector() {
  Brain.Screen.pressed(onScreenPressed);
  drawSelector();
}

void runSelectedAuton() {
  autons[selected].run();
}
