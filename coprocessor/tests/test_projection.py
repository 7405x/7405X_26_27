import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from vaic.perception import CameraMount, pixel_to_angles, project_to_field, project_to_robot  # noqa: E402
from vaic.perception.projection import robot_to_field  # noqa: E402


class ProjectionTests(unittest.TestCase):
    def test_straight_down_45(self):
        m = CameraMount(height_m=1.0, pitch_deg=-45.0)
        fwd, right, rng = project_to_robot(0.0, 0.0, m)
        self.assertAlmostEqual(fwd, 1.0, places=6)
        self.assertAlmostEqual(right, 0.0, places=6)
        self.assertAlmostEqual(rng, math.sqrt(2), places=6)

    def test_ty_and_target_height(self):
        m = CameraMount(height_m=0.5, pitch_deg=-30.0)
        # ty = +30 puts the ray on the horizon -> no ground hit
        self.assertIsNone(project_to_robot(0.0, 30.0, m))
        # object center 0.1 m up, ray at -45 -> distance 0.4
        fwd, _, _ = project_to_robot(0.0, -15.0, m, target_height_m=0.1)
        self.assertAlmostEqual(fwd, 0.4, places=6)

    def test_tx_right_positive_and_mount_offsets(self):
        m = CameraMount(forward_m=0.2, right_m=-0.1, height_m=1.0, pitch_deg=-45.0)
        fwd, right, _ = project_to_robot(30.0, 0.0, m)
        self.assertAlmostEqual(fwd, 0.2 + math.cos(math.radians(30)), places=6)
        self.assertAlmostEqual(right, -0.1 + math.sin(math.radians(30)), places=6)

    def test_compass_heading_convention(self):
        # heading 0 -> forward is +Y ; heading 90 -> forward is +X ; right at heading 0 is +X
        self.assertEqual(tuple(round(v, 6) for v in robot_to_field(1, 0, 0, 0, 0)), (0.0, 1.0))
        self.assertEqual(tuple(round(v, 6) for v in robot_to_field(1, 0, 0, 0, 90)), (1.0, 0.0))
        self.assertEqual(tuple(round(v, 6) for v in robot_to_field(0, 1, 0, 0, 0)), (1.0, 0.0))

    def test_project_to_field_end_to_end(self):
        m = CameraMount(height_m=1.0, pitch_deg=-45.0)
        x, y, _ = project_to_field(0.0, 0.0, m, rx=0.5, ry=0.5, heading_deg=180.0)
        self.assertAlmostEqual(x, 0.5, places=6)
        self.assertAlmostEqual(y, -0.5, places=6)

    def test_pixel_to_angles_center_and_edges(self):
        m = CameraMount(hfov_deg=60, vfov_deg=40, width=640, height=480)
        self.assertEqual(pixel_to_angles(320, 240, m), (0.0, 0.0))
        tx, ty = pixel_to_angles(640, 0, m)
        self.assertAlmostEqual(tx, 30.0, places=6)
        self.assertAlmostEqual(ty, 20.0, places=6)
