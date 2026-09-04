import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from vaic.perception import parse_results  # noqa: E402

FLAT = {"pID": 0, "ts": 12.5, "v": 1, "Detector": [
    {"class": "BallRed", "classID": 1, "conf": 0.91, "tx": 4.5, "ty": -8.0, "txp": 350, "typ": 300,
     "pts": [[330, 280], [370, 280], [370, 320], [330, 320]], "ta": 0.5}],
    "Fiducial": []}
NESTED = {"Results": FLAT}


class LimelightParseTests(unittest.TestCase):
    def test_flat_and_nested(self):
        for doc in (FLAT, NESTED):
            d = parse_results(doc)
            self.assertEqual(len(d), 1)
            self.assertEqual(d[0].class_id, 1)
            self.assertEqual(d[0].label, "BallRed")
            self.assertEqual(d[0].bbox, (350, 300, 40, 40))
            self.assertEqual((d[0].tx, d[0].ty), (4.5, -8.0))

    def test_empty(self):
        self.assertEqual(parse_results({"Detector": []}), [])
        self.assertEqual(parse_results({}), [])
