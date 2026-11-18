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
//  Everything is written for the RED side, BOTTOM loader. The other three
//  starting spots reuse the same code, mirrored (see "Mirroring" below).
// ============================================================================
//  Red loaders .............. on the red wall at y ~= 12 and y ~= 132
//  Red goals ................ (24, 48) and (24, 96)
//  Red zone ends at ......... x ~= 48 (white tape line)
//  Neutral goals ............ (72, 24) and (72, 120)
//  Center goal .............. (72, 72)
//  Red-zone roller .......... on the red wall, y ~= 58 to 85
//  Neutral roller (bottom) .. on the bottom wall, x ~= 58 to 85
//  Unknown grey circle ...... (24, 72) - check what this is on the real field
// ============================================================================

// ============================================================================
//  TUNING - everything you should need to change is in this block.
//  All positions are for RED, BOTTOM loader; the code mirrors them for the
//  other starting spots, so tune them once.
// ============================================================================

// ---- Robot ----------------------------------------------------------------
// Robot is 18" x 18", so its center is 9" from any side.
const double HALF_ROBOT = 9.0;

// Where the toggler is, measured sideways from the robot's center line, in
// inches. 0 = dead center of the front. Positive = toggler is to the robot's
// RIGHT (as if you're standing behind the robot), negative = to its left.
// The routines use this to line the TOGGLER (not the robot's center) up with
// the roller, so measure it on the real robot.
const double TOGGLER_OFFSET_IN = 0.0;

// ---- Speed ----------------------------------------------------------------
// Max volts for auton driving and turning (12 = full power). Lower = slower
// but more accurate. Start low while testing a new path, raise it once the
// path works.
const double AUTON_VOLTS = 10.0;

// ---- Pressing the toggler into a roller -----------------------------------
// The robot is SUPPOSED to push against the wall here. The timeout is what
// ends the push, so the motors don't stall against the wall for long.
const double PRESS_IN       = 5.0;  // how far to push forward (inches)
const double PRESS_VOLTS    = 5.0;  // gentle - just enough to flip the roller
const int    PRESS_MS       = 800;  // give up pushing after this long
const double BACKOFF_IN     = 6.0;  // how far to back away afterwards
const double BACKOFF_VOLTS  = 8.0;

// ---- Turning clearance ----------------------------------------------------
// When the robot spins in place, its corners swing out in a circle of radius
// sqrt(9^2 + 9^2) ~= 12.7". So the robot's CENTER must be at least that far
// from a wall (or anything else) before it does a big turn, or a corner will
// hit it. Every spot where a routine turns more than a few degrees is at
// least this far from the walls.
const double TURN_CLEARANCE = 13.5;  // 12.7" + a little margin

// ---- Starting spot --------------------------------------------------------
// Back of the robot touching the red loader, facing the blue wall.
// The loader sticks out about 4" from the wall.
const double START_X = 4.0 + HALF_ROBOT;  // 13
const double START_Y = 12.0;              // bottom loader (top is 144 - 12)

// ---- Zone Roller path -----------------------------------------------------
// Lane to drive up between the red goals and the zone line.
const double LANE_X = 35.0;
// Height of the first waypoint out in the lane. The robot turns 90 here, so
// it has to be TURN_CLEARANCE off the bottom wall (START_Y = 12 is too close:
// the corners would scrape the wall). Getting there from the start is only a
// ~4 degree turn, which is small enough to do right next to the loader.
const double LANE_START_Y = TURN_CLEARANCE;
// Where on the zone roller (y) the TOGGLER should hit. The roller runs from
// y ~= 58 to 85. The robot drives across the field at this height (adjusted
// for TOGGLER_OFFSET_IN), so its 18" body covers y +/- 9 on the way. 61 was
// chosen to miss the red goal at y = 48 and the grey circle at y = 72.
// That's only ~3" inside the roller's end - check it on the real field.
const double ZONE_PRESS_Y = 61.0;
// How close the robot's center gets to the red wall before pressing in.
// (Center at 12 = front bumper ~3" from the wall.)
const double ROLLER_STOP_X = 12.0;

// ---- Neutral Roller path --------------------------------------------------
// Where on the neutral roller (x) the TOGGLER should hit. The roller runs from
// x ~= 58 to 85. This is a trade-off - check BOTH on the real field:
//   * Too small (toward 58): the toggler hits the roller's end, or misses it.
//   * Too big: the robot's top-right corner, at (x + 9, NEUTRAL_Y + 9), gets
//     close to the neutral goal at (72, 24). At 60 the corner is at
//     (69, 22.5), ~3.4" from the goal's center. If the goal's base is wider
//     than that, lower this.
// The robot's right edge also has to stay on our side of the center line
// (x = 72), so with the toggler centered this can't go above 63.
const double NEUTRAL_PRESS_X = 60.0;
// Robot's distance from the bottom wall when it turns to face the roller.
const double NEUTRAL_Y = TURN_CLEARANCE;

// ============================================================================
//  Mirroring helpers. Routines are written once for red-bottom; these flip
//  them for blue (mirrorX) and for the top loader (mirrorY).
// ============================================================================
static bool mirrorX = false;  // true = blue side (flip left/right in Fig 1.2)
static bool mirrorY = false;  // true = top loader (flip up/down in Fig 1.2)

// Flip a red-bottom x / y / heading to whichever side we're actually on.
static double fx(double x) { return mirrorX ? 144.0 - x : x; }
static double fy(double y) { return mirrorY ? 144.0 - y : y; }
static double fh(double h) {
  // Heading 0 = +y, clockwise positive. A heading points along
  // (sin h, cos h): flipping x negates sin -> -h; flipping y negates
  // cos -> 180 - h.
  if (mirrorX) h = -h;
  if (mirrorY) h = 180.0 - h;
  return h;
}

// The toggler's sideways offset, as it looks in the red-bottom picture the
// routines are written in. A mirror image swaps left and right, so when the
// field is flipped exactly once (blue-bottom or red-top) a toggler on the
// robot's right shows up on its left in the picture. Flipped twice
// (blue-top) it's back to normal.
static double togglerOffset() {
  return (mirrorX != mirrorY) ? -TOGGLER_OFFSET_IN : TOGGLER_OFFSET_IN;
}

// Always use these in routines (not setPose/driveToPoint/turnToHeading
// directly) so the mirroring is applied. Write coordinates for RED, BOTTOM.
static void startAt(double x, double y, double heading) { setPose(fx(x), fy(y), fh(heading)); }
static void goTo(double x, double y) { driveToPoint(fx(x), fy(y), AUTON_VOLTS); }
static void face(double heading) { turnToHeading(fh(heading), AUTON_VOLTS); }

// ============================================================================
//  Routines
// ============================================================================

// Push the compliant toggler into a roller, then back off so it springs back.
// Values are in the TUNING block. Tune them once you see how much push the
// toggler needs to flip a roller.
static void pressToggler() {
  driveDistance(PRESS_IN, PRESS_VOLTS, PRESS_MS);
  driveDistance(-BACKOFF_IN, BACKOFF_VOLTS);
}

// ALLIANCE (15s): drive to our zone's roller and press the toggler into it.
// The robot can't score pins in auton yet, so the roller is what we can do:
// it's half of the autonomous ranking point (the other half is 3 cups +
// 4 halfpins on 2 goals, which our partner would have to score), and it
// makes yellow halfpins on our alliance goals worth points.
//
// The arm isn't used here: it should be resting down at the start (that's
// where armReset() zeroes it) and it stays there. If it ever needs to be
// tucked or raised in auton, add an armTo(...) at the top of the routine.
//
// UNTESTED PATH - walk it on the real field first. The lane between the red
// goal and the slanted pin near (45, 45) is tight, so the robot may brush
// one of them.
//
// Path (red, bottom loader, toggler centered), robot center:
//   (13, 12) start -> (35, 13.5) -> (35, 61) -> (12, 61), face red wall, press
static void rollerRoutine() {
  // Facing the red wall (heading 270), the robot's right is +y. To put the
  // toggler at ZONE_PRESS_Y, the robot's center goes the other way.
  double rollerY = ZONE_PRESS_Y - togglerOffset();

  startAt(START_X, START_Y, 90);    // facing the blue wall, back on the loader

  goTo(LANE_X, LANE_START_Y);       // out into the zone, far enough off the
                                    // wall to turn safely
  goTo(LANE_X, rollerY);            // turn left ~90, drive up the lane
  goTo(ROLLER_STOP_X, rollerY);     // turn left 90, drive toward the red wall
  face(270);                        // fix any drift so we hit the roller
                                    // square (only a few degrees, so it's OK
                                    // this close to the wall)
  pressToggler();
}

// ALLIANCE (15s): flip the neutral roller nearest our loader to our color.
// Shorter than the zone-roller path (~47" then one turn). Note: the other
// alliance can flip it back later, and this does NOT count toward the
// autonomous ranking point (that needs OUR zone's roller).
// UNTESTED - the first move will likely push the pin lying near (24, 20).
//
// Path (red, bottom loader, toggler centered), robot center:
//   (13, 12) start -> (60, 13.5) -> turn right to face bottom wall, press
static void neutralRollerRoutine() {
  // Facing the bottom wall (heading 180), the robot's right is -x. To put
  // the toggler at NEUTRAL_PRESS_X, the robot's center goes the other way.
  double neutralX = NEUTRAL_PRESS_X + togglerOffset();

  startAt(START_X, START_Y, 90);
  goTo(neutralX, NEUTRAL_Y);        // drive along the bottom wall
  face(180);                        // turn right ~90 to face the bottom wall
  pressToggler();
}

// Pick which quarter of the field we're in before running a routine.
// "Left"/"right" = which loader, as seen standing in OUR driver box.
static void setSide(bool blue, bool leftLoader) {
  mirrorX = blue;
  // Red drivers stand at x = 0 looking toward +x, so their left is +y (top
  // of Figure 1.2). Blue drivers stand at x = 144 looking toward -x, so
  // their left is -y (bottom).
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
  setSide(false, false);  // red, right loader (= bottom of Figure 1.2)
  rollerRoutine();
}

// Tuning tests (not for matches). See "Tuning the PID" in README.md.
// These use full default speed so the PID is tuned for real match moves.

// Drives 24" forward and back. Measure how far it actually went: if it's
// consistently off, check WHEEL_DIAMETER_IN and GEAR_RATIO first, then PID.
static void testDrive() {
  driveDistance(24);
  wait(500, msec);
  driveDistance(-24);
}

// Turns 90 right and back. Should stop square both times without wobbling.
static void testTurn() {
  setPose(0, 0, 0);
  turnToHeading(90);
  wait(500, msec);
  turnToHeading(0);
}

// Drives a 24" square using field points. If odometry is right it ends
// exactly where it started. Check the brain screen for the final x, y.
// Needs about 4 feet of open floor.
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

// Tests ONLY the toggler press, using the PRESS_ / BACKOFF_ values above.
// Put the robot with its front bumper ~3" from a wall (or a roller) and run
// it. Adjust the PRESS_ values until the roller flips reliably.
static void testPress() {
  pressToggler();
}

static void doNothing() {}

// ============================================================================
//  Selector
//  "Left" / "Right" = which loader, as seen standing in YOUR driver box.
// ============================================================================

struct AutonOption {
  const char* name;  // shown on the brain and controller screens
  void (*run)();     // the routine to run when autonomous starts
};

// "None" is FIRST so it's the default. If nobody picks an auton, the robot
// sits still instead of running a red path on the blue side (or vice versa).
// To add a routine: write it above, then add a line here.
static AutonOption autons[] = {
  {"None",                   doNothing},
  {"Red L: Zone Roller",     redLeft},
  {"Red R: Zone Roller",     redRight},
  {"Blue L: Zone Roller",    blueLeft},
  {"Blue R: Zone Roller",    blueRight},
  {"Red L: Neutral Roller",  redLeftNeutral},
  {"Red R: Neutral Roller",  redRightNeutral},
  {"Blue L: Neutral Roller", blueLeftNeutral},
  {"Blue R: Neutral Roller", blueRightNeutral},
  {"Solo Coding",            soloCoding},
  {"Test: Drive 24in",       testDrive},
  {"Test: Turn 90",          testTurn},
  {"Test: Square",           testSquare},
  {"Test: Toggler Press",    testPress},
};
static const int NUM_AUTONS = sizeof(autons) / sizeof(autons[0]);
static int selected = 0;  // index into autons[]; 0 = "None"

static void drawSelector() {
  Brain.Screen.clearScreen();
  Brain.Screen.setFont(mono30);
  Brain.Screen.setCursor(1, 1);
  Brain.Screen.print("Auton: %s", autons[selected].name);
  Brain.Screen.setFont(mono20);
  Brain.Screen.setCursor(4, 1);
  Brain.Screen.print("Tap screen to change (%d/%d)", selected + 1, NUM_AUTONS);
  // Note: this is the heading at the moment the screen was drawn (it only
  // redraws on a tap), not a live reading.
  Brain.Screen.setCursor(6, 1);
  Brain.Screen.print("IMU heading: %.1f", IMU.heading(degrees));

  Controller1.Screen.clearScreen();
  Controller1.Screen.setCursor(1, 1);
  Controller1.Screen.print("%s", autons[selected].name);
}

static void onScreenPressed() {
  // Only allow changing the auton while the robot is disabled (before the
  // match). Otherwise a bump to the brain screen mid-match would change the
  // selection and wipe whatever else is on the screen.
  // With no field control or competition switch plugged in, the brain counts
  // as "enabled" the whole time, so taps do nothing. That's fine: auton can
  // only run with field control / a competition switch / the controller's
  // timed run, and all of those start out disabled.
  if (Competition.isEnabled()) return;
  selected = (selected + 1) % NUM_AUTONS;
  drawSelector();
}

// Called once from pre_auton(): hooks up the screen tap and draws the menu.
void runAutonSelector() {
  Brain.Screen.pressed(onScreenPressed);
  drawSelector();
}

// Called from autonomous(): runs whatever was picked on the screen.
void runSelectedAuton() {
  autons[selected].run();
}
