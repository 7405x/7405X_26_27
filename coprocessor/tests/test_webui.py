import http.client
import json
import os
import socket
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fixtures import frame, frames                    # noqa: E402
from vaic.debugstate import DebugState               # noqa: E402
from vaic.logger import WorldLogger                  # noqa: E402
from vaic.strategy import Command                    # noqa: E402
from vaic.webui import WebUI                         # noqa: E402


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


class WebUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        with WorldLogger(cls.tmp.name, max_hz=0, name="t") as lg:
            for w in frames(30):
                lg.log(w)
        cls.state = DebugState()
        w = frame(0)
        cls.state.update(w, Command("drive_to", (0.5, 0.5)), links={"limelight": False, "v5": True}, timing={"fetch": 0.01})
        cls.state.log_event("hello")
        cfg = {"robot": "test", "camera": {"host": "127.0.0.1", "port": 1, "stream_port": 1}, "objects": {}}
        cls.port = free_port()
        cls.ui = WebUI(cls.state, cfg, port=cls.port, log_dir=cls.tmp.name)
        cls.ui.start()

    @classmethod
    def tearDownClass(cls):
        cls.ui.stop(); cls.tmp.cleanup()

    def get(self, path, method="GET"):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        c.request(method, path); r = c.getresponse(); body = r.read(); c.close()
        return r.status, r.getheader("Content-Type", ""), body

    def test_index(self):
        st, ct, body = self.get("/")
        self.assertEqual(st, 200); self.assertIn("text/html", ct); self.assertIn(b"VAIC Debug", body)

    def test_state(self):
        st, _, body = self.get("/api/state"); s = json.loads(body)
        self.assertEqual(st, 200)
        self.assertEqual(s["command"]["kind"], "drive_to")
        self.assertEqual(s["links"]["v5"], True)
        self.assertEqual(s["world"]["robot"], "test")
        self.assertEqual(s["events"][0][1], "hello")
        self.assertEqual(len(s["trail"]), 1)

    def test_config_and_system(self):
        self.assertEqual(json.loads(self.get("/api/config")[2])["robot"], "test")
        self.assertIn("cpus", json.loads(self.get("/api/system")[2]))

    def test_logs_list_and_read(self):
        logs = json.loads(self.get("/api/logs")[2])
        self.assertEqual(logs[0]["name"], "t.jsonl")
        r = json.loads(self.get("/api/logs/t.jsonl?from=10&count=5")[2])
        self.assertEqual((r["total"], len(r["frames"]), r["frames"][0]["pose"]["frame"]), (30, 5, 10))
        self.assertIn("error", json.loads(self.get("/api/logs/../x")[2]))

    def test_limelight_unreachable_is_reported_not_crashed(self):
        r = json.loads(self.get("/api/limelight/status")[2])
        self.assertFalse(r["ok"])
        r = json.loads(self.get("/api/limelight/pipeline?index=1", "POST")[2])
        self.assertFalse(r["ok"])
        self.assertEqual(self.get("/camera/stream")[0], 502)

    def test_404(self):
        self.assertEqual(self.get("/nope")[0], 404)
