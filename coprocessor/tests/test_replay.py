import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fixtures import frame, frames                    # noqa: E402
from vaic import sim                                  # noqa: E402
from vaic.logger import WorldLogger                   # noqa: E402
from vaic.replay import read_log                      # noqa: E402
from vaic.strategy import Command, NearestObjectStrategy, Strategy  # noqa: E402


class ReplayTests(unittest.TestCase):
    def _write(self, tmp, compress, hz):
        with WorldLogger(tmp, max_hz=hz, compress=compress, name="t") as lg:
            for w in frames(100, hz=20):
                lg.log(w)
            return lg.path

    def test_log_roundtrip_plain_and_gz(self):
        with tempfile.TemporaryDirectory() as tmp:
            for compress in (False, True):
                path = self._write(tmp, compress, hz=0)
                got = list(read_log(path))
                self.assertEqual(len(got), 100)
                self.assertEqual(got[0], frame(0))
                self.assertEqual(got[99], frame(99))

    def test_rate_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, False, hz=10)   # source is 20 Hz
            self.assertEqual(len(list(read_log(path))), 50)

    def test_nearest_strategy_picks_closest_wanted_class(self):
        steps = sim.run(frames(3), NearestObjectStrategy([0, 1]))
        self.assertEqual(sim.summarize(steps)["commands"], {"drive_to": 3})
        self.assertEqual(steps[0].command.target, (0.0, 1.0))     # both at 1 m; red listed first wins ties
        only_blue = sim.run(frames(1), NearestObjectStrategy([0]))
        self.assertEqual(only_blue[0].command.target, (1.0, 0.0))

    def test_no_fix_means_idle(self):
        w = frame(0); w.pose.status = 0
        self.assertEqual(sim.run([w], NearestObjectStrategy([0]))[0].command.kind, "idle")

    def test_custom_strategy_plugs_in(self):
        class Count(Strategy):
            def update(self, world):
                return Command("idle", note=str(len(world.objects)))
        steps = sim.run(frames(5), Count())
        self.assertEqual([s.command.note for s in steps], ["2"] * 5)
