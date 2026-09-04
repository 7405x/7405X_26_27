"""build_world() is pure, so the Limelight app's projection path is testable offline."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from vaic.perception import Detection  # noqa: E402
from vaic.world import Pose  # noqa: E402

CFG = json.load(open(os.path.join(os.path.dirname(__file__), "..", "config", "robot_a.example.json")))


class BuildWorldTests(unittest.TestCase):
    def test_build_world_projects_and_labels(self):
        from vaic import app_limelight
        app = app_limelight.LimelightApp.__new__(app_limelight.LimelightApp)
        app.cfg = CFG
        cam = CFG["camera"]; m = cam["mount"]
        from vaic.perception import CameraMount
        app.mount = CameraMount(m["forward_m"], m["right_m"], m["height_m"], m["pitch_deg"], m["yaw_deg"],
                                cam["hfov_deg"], cam["vfov_deg"], cam["width"], cam["height"])
        app.objects = {int(k): v for k, v in CFG["objects"].items()}
        dets = [Detection(1, 0.9, (320, 300, 40, 40), tx=0.0, ty=-10.0),
                Detection(0, 0.9, (320, 100, 40, 40), tx=0.0, ty=+20.0)]   # above horizon -> dropped
        w = app.build_world(dets, Pose(x=0, y=0, heading=0, status=1), t=1.0)
        self.assertEqual(len(w.objects), 1)
        o = w.objects[0]
        self.assertEqual(o.label, "BallRed")
        self.assertGreater(o.y, 0.15)     # in front of the robot along +Y
        self.assertAlmostEqual(o.x, 0.0, places=6)
        self.assertGreater(o.depth, 0)
