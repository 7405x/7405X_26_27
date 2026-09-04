"""Debug dashboard served from the Jetson. Standard library only.

    GET  /                      the page
    GET  /api/state             latest world state, command, links, timing, trail
    GET  /api/config            active robot config
    GET  /api/system            Jetson temp / load / memory
    GET  /api/limelight/status  proxied Limelight /status (pipeline, fps, temps, hw)
    GET  /api/limelight/results proxied raw Limelight /results JSON
    POST /api/limelight/pipeline?index=N   switch pipeline
    POST /api/limelight/snapshot?name=X    save a snapshot on the Limelight (training data)
    GET  /camera/stream         MJPEG proxy of the Limelight stream (port 5800)
    GET  /api/logs              list of world logs
    GET  /api/logs/<name>?from=I&count=N   frames from a log for replay
"""
import json
import os
import socketserver
import threading
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

from .. import ROOT
from ..debugstate import DebugState

HERE = os.path.dirname(os.path.abspath(__file__))


class ThreadingServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class WebUI:
    def __init__(self, state: DebugState, cfg: dict, port: int = 8080, log_dir: Optional[str] = None):
        self.state = state
        self.cfg = cfg
        self.port = port
        self.log_dir = log_dir or os.path.join(ROOT, cfg.get("log_dir", "logs"))
        cam = cfg.get("camera", {})
        self.ll_host = cam.get("host", "limelight.local")
        self.ll_api = f"http://{self.ll_host}:{cam.get('port', 5807)}"
        self.ll_stream = f"http://{self.ll_host}:{cam.get('stream_port', 5800)}/stream.mjpg"
        self._server: Optional[ThreadingServer] = None

    # ---- lifecycle ----
    def start(self) -> None:
        ui = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):  # quiet
                pass

            def do_GET(self):
                ui.route(self, "GET")

            def do_POST(self):
                ui.route(self, "POST")

        self._server = ThreadingServer(("0.0.0.0", self.port), Handler)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        print(f"[webui] http://0.0.0.0:{self.port}/")

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()

    # ---- routing ----
    def route(self, h: BaseHTTPRequestHandler, method: str) -> None:
        url = urllib.parse.urlsplit(h.path)
        path, q = url.path, dict(urllib.parse.parse_qsl(url.query))
        try:
            if path == "/" and method == "GET":
                return self.send_file(h, os.path.join(HERE, "index.html"), "text/html; charset=utf-8")
            if path == "/api/state":
                return self.send_json(h, self.state.snapshot())
            if path == "/api/config":
                return self.send_json(h, self.cfg)
            if path == "/api/system":
                return self.send_json(h, system_stats())
            if path == "/api/limelight/status":
                return self.send_json(h, self.ll_get("/status"))
            if path == "/api/limelight/results":
                return self.send_json(h, self.ll_get("/results"))
            if path == "/api/limelight/pipeline" and method == "POST":
                idx = int(q.get("index", 0))
                self.state.log_event(f"pipeline -> {idx}")
                return self.send_json(h, self.ll_post(f"/pipeline-switch?index={idx}"))
            if path == "/api/limelight/snapshot" and method == "POST":
                name = urllib.parse.quote(q.get("name", "snap"))
                self.state.log_event(f"snapshot {name}")
                return self.send_json(h, self.ll_post(f"/capture-snapshot?snapname={name}"))
            if path == "/camera/stream":
                return self.proxy_stream(h)
            if path == "/api/logs":
                return self.send_json(h, self.list_logs())
            if path.startswith("/api/logs/"):
                return self.send_json(h, self.read_log(path[len("/api/logs/"):], int(q.get("from", 0)), int(q.get("count", 200))))
            h.send_error(404)
        except ConnectionError:
            pass
        except Exception as e:  # never let a handler kill the server
            try:
                self.send_json(h, {"error": str(e)}, 500)
            except Exception:
                pass

    # ---- responses ----
    @staticmethod
    def send_json(h, obj, code=200):
        body = json.dumps(obj).encode()
        h.send_response(code)
        h.send_header("Content-Type", "application/json")
        h.send_header("Content-Length", str(len(body)))
        h.send_header("Cache-Control", "no-store")
        h.end_headers()
        h.wfile.write(body)

    @staticmethod
    def send_file(h, path, ctype):
        with open(path, "rb") as f:
            body = f.read()
        h.send_response(200)
        h.send_header("Content-Type", ctype)
        h.send_header("Content-Length", str(len(body)))
        h.end_headers()
        h.wfile.write(body)

    # ---- limelight ----
    def ll_get(self, path):
        try:
            with urllib.request.urlopen(self.ll_api + path, timeout=1.0) as r:
                return {"ok": True, "data": json.loads(r.read().decode() or "null")}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def ll_post(self, path):
        try:
            req = urllib.request.Request(self.ll_api + path, method="POST", data=b"")
            with urllib.request.urlopen(req, timeout=2.0) as r:
                return {"ok": True, "status": r.status}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def proxy_stream(self, h):
        """Relay the Limelight MJPEG stream so laptops only need to reach the Jetson."""
        try:
            src = urllib.request.urlopen(self.ll_stream, timeout=3.0)
        except Exception as e:
            h.send_error(502, f"limelight stream unavailable: {e}")
            return
        h.send_response(200)
        h.send_header("Content-Type", src.headers.get("Content-Type", "multipart/x-mixed-replace"))
        h.send_header("Cache-Control", "no-store")
        h.end_headers()
        try:
            while True:
                chunk = src.read(16384)
                if not chunk:
                    break
                h.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            src.close()

    # ---- logs ----
    def list_logs(self):
        if not os.path.isdir(self.log_dir):
            return []
        out = []
        for name in sorted(os.listdir(self.log_dir), reverse=True):
            if name.endswith(".jsonl") or name.endswith(".jsonl.gz"):
                p = os.path.join(self.log_dir, name)
                out.append({"name": name, "bytes": os.path.getsize(p), "mtime": os.path.getmtime(p)})
        return out

    def read_log(self, name, start, count):
        if "/" in name or ".." in name:
            return {"error": "bad name"}
        from ..replay import open_log
        p = os.path.join(self.log_dir, name)
        frames, total = [], 0
        with open_log(p) as fh:
            for i, line in enumerate(fh):
                total += 1
                if start <= i < start + count and line.strip():
                    frames.append(json.loads(line))
        return {"name": name, "from": start, "total": total, "frames": frames}


def _read(path, default=None):
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return default


def system_stats():
    import glob
    temps = {}
    for z in glob.glob("/sys/devices/virtual/thermal/thermal_zone*"):
        t, kind = _read(z + "/temp"), _read(z + "/type", "?")
        if t:
            temps[kind] = round(int(t) / 1000, 1)
    mem = {}
    for line in (_read("/proc/meminfo", "") or "").splitlines():
        k, _, v = line.partition(":")
        if k in ("MemTotal", "MemAvailable"):
            mem[k] = int(v.split()[0]) // 1024
    load = None
    try:
        load = os.getloadavg()
    except Exception:
        pass
    return {"temps": temps, "mem_mb": mem, "load": load, "cpus": os.cpu_count()}
