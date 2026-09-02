import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from vaic import sim                                  # noqa: E402
from vaic.logger import WorldLogger                   # noqa: E402
from vaic.replay import read_log                      # noqa: E402
from vaic.strategy import Command, NearestObjectStrategy, Strategy  # noqa: E402
from vaic.synthetic import synthetic_frames           # noqa: E402


class ReplayTests(unittest.TestCase):
    def _write(self, tmp, compress, hz):
        with WorldLogger(tmp, max_hz=hz, compress=compress, name="t") as lg:
            for w in synthetic_frames(100, hz=20):
                lg.log(w)
            return lg.path

    def test_log_roundtrip_plain_and_gz(self):
        with tempfile.TemporaryDirectory() as tmp:
            for compress in (False, True):
                path = self._write(tmp, compress, hz=0)
                frames = list(read_log(path))
                self.assertEqual(len(frames), 100)
                self.assertEqual(frames[0], next(synthetic_frames(1)))

    def test_rate_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, False, hz=10)   # source is 20 Hz
            self.assertEqual(len(list(read_log(path))), 50)

    def test_strategy_over_synthetic(self):
        steps = sim.run(synthetic_frames(200), NearestObjectStrategy([0, 1]))
        summary = sim.summarize(steps)
        self.assertEqual(summary["frames"], 200)
        self.assertIn("drive_to", summary["commands"])
        for s in steps:
            if s.command.kind == "drive_to":
                self.assertIsNotNone(s.command.target)

    def test_strategy_is_deterministic(self):
        a = sim.run(synthetic_frames(50), NearestObjectStrategy([0]))
        b = sim.run(synthetic_frames(50), NearestObjectStrategy([0]))
        self.assertEqual([s.command for s in a], [s.command for s in b])

    def test_custom_strategy_plugs_in(self):
        class Count(Strategy):
            def update(self, world):
                return Command("idle", note=str(len(world.objects)))
        steps = sim.run(synthetic_frames(5), Count())
        self.assertEqual(len(steps), 5)
