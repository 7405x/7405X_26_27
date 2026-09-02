import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from vaic.world import Pose, WorldObject, WorldState  # noqa: E402
import vaic_protocol as P  # noqa: E402


class FakeVexPosition:
    """Shape of JetsonExample/V5Position.Position"""
    def __init__(self):
        self.frameCount, self.status = 5, 1
        self.x, self.y, self.z = 0.5, -0.5, 0.1
        self.azimuth, self.elevation, self.rotation = 45.0, 1.0, 2.0


class FakeVexDetection:
    """Shape of JetsonExample/V5Comm.Detection, typo included"""
    def __init__(self):
        self.classID, self.probability, self.depth = 1, 0.8, float("nan")
        self.screenLocation = type("S", (), dict(x=10, y=20, width=30, height=40))()
        self.mapLocattion = type("M", (), dict(x=1.0, y=2.0, z=0.0))()


class FakeVexRecord:
    def __init__(self):
        self.position = FakeVexPosition()
        self.detections = [FakeVexDetection()]


class WorldTests(unittest.TestCase):
    def test_from_vex_record(self):
        w = WorldState.from_ai_record(FakeVexRecord(), ["A", "B"], t=1.0)
        self.assertEqual(w.pose.heading, 45.0)
        self.assertTrue(w.pose.connected)
        self.assertEqual(w.objects[0].label, "B")
        self.assertEqual(w.objects[0].depth, -1.0)  # NaN sanitized
        self.assertEqual(w.objects[0].bbox, (10, 20, 30, 40))

    def test_roundtrip_wire_and_json(self):
        w = WorldState(t=2.0, pose=Pose(x=1, y=2, heading=90, status=1),
                       objects=[WorldObject(0, "A", 0.9, 1.5, 0.1, 0.2, 0.0, (1, 2, 3, 4))])
        rec = w.to_ai_record()
        back = WorldState.from_ai_record(P.decode_ai_record(P.encode_ai_record(rec)), ["A"], t=2.0)
        self.assertAlmostEqual(back.objects[0].x, 0.1, places=6)
        self.assertEqual(back.pose.heading, 90.0)
        j = WorldState.from_dict(w.to_dict())
        self.assertEqual(j, w)

    def test_nearest(self):
        w = WorldState(pose=Pose(status=1), objects=[
            WorldObject(0, "A", 0.9, x=3, y=0), WorldObject(0, "A", 0.9, x=1, y=0),
            WorldObject(1, "B", 0.9, x=0.1, y=0), WorldObject(0, "A", 0.2, x=0.5, y=0)])
        self.assertEqual(w.nearest(0, min_confidence=0.5).x, 1)
        self.assertIsNone(w.nearest(7))
