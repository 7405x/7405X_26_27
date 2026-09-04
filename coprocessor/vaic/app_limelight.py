"""Limelight path: poll the Limelight for detections, take the robot pose from the
VEX GPS (via VEX's V5GPS class) or from Brain odometry packets, project detections
onto the field, then log, run strategy, and serve AI_RECORDs to the Brain."""
import os
import sys
import time
from typing import Optional

import vaic_protocol as P

from . import ROOT
from .debugstate import DebugState
from .logger import WorldLogger
from .perception import CameraMount, LimelightSource, pixel_to_angles, project_to_field
from .strategy import NearestObjectStrategy
from .v5link import V5Link
from .world import Pose, WorldObject, WorldState
from .webui import WebUI


class PoseSource:
    """GPS when it has a fix, otherwise the latest Brain odometry."""

    def __init__(self, use_gps: bool, odom_fallback: bool):
        self.gps = None
        self.odom: Optional[P.ODOM_RECORD] = None
        self.odom_fallback = odom_fallback
        if use_gps:
            sys.path.insert(0, os.path.join(ROOT, "JetsonExample"))
            try:
                from V5Position import V5GPS   # VEX code: pyserial + numpy
                self.gps = V5GPS()
                self.gps.start()
            except Exception as e:
                print("[pose] GPS unavailable:", e)

    def on_odom(self, rec: P.ODOM_RECORD) -> None:
        self.odom = rec

    def current(self) -> Pose:
        if self.gps is not None:
            p = self.gps.getPosition()
            if p.status & P.POS_STATUS_CONNECTED:
                return Pose(p.x, p.y, p.z, p.azimuth, p.elevation, p.rotation, p.frameCount, p.status)
        if self.odom_fallback and self.odom is not None and self.odom.status & P.ODOM_STATUS_VALID:
            o = self.odom
            return Pose(o.x, o.y, 0.0, o.heading, 0.0, 0.0, o.t_ms, P.POS_STATUS_CONNECTED | P.POS_STATUS_KALMAN_EST)
        return Pose()


class LimelightApp:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        cam = cfg["camera"]
        m = cam.get("mount", {})
        self.mount = CameraMount(
            forward_m=m.get("forward_m", 0.0), right_m=m.get("right_m", 0.0), height_m=m.get("height_m", 0.3),
            pitch_deg=m.get("pitch_deg", 0.0), yaw_deg=m.get("yaw_deg", 0.0),
            hfov_deg=cam.get("hfov_deg", 62.5), vfov_deg=cam.get("vfov_deg", 48.9),
            width=cam.get("width", 640), height=cam.get("height", 480))
        self.source = LimelightSource(cam.get("host", "limelight.local"), cam.get("port", 5807))
        self.period = 1.0 / cam.get("poll_hz", 30)
        self.objects = {int(k): v for k, v in cfg.get("objects", {}).items()}
        loc = cfg.get("localization", {})
        self.pose_source = PoseSource(loc.get("gps", True), loc.get("odom_fallback", True))
        self.link = V5Link(on_odom=self.pose_source.on_odom)
        self.logger = WorldLogger(os.path.join(ROOT, cfg.get("log_dir", "logs")),
                                  max_hz=cfg.get("log_hz", 20), compress=cfg.get("log_compress", False))
        s = cfg.get("strategy", {})
        self.strategy = NearestObjectStrategy(s.get("class_ids", [0]), s.get("min_confidence", 0.5))
        self.strategy.reset()
        self.debug = DebugState()
        self.webui = WebUI(self.debug, cfg, port=cfg.get("webui_port", 8080)) if cfg.get("webui", True) else None

    def build_world(self, dets, pose: Pose, t: float) -> WorldState:
        objs = []
        for d in dets:
            tx, ty = (d.tx, d.ty) if d.tx is not None and d.ty is not None else pixel_to_angles(d.bbox[0], d.bbox[1], self.mount)
            meta = self.objects.get(d.class_id, {})
            r = project_to_field(tx, ty, self.mount, pose.x, pose.y, pose.heading, meta.get("height_m", 0.0))
            if r is None:
                continue
            x, y, rng = r
            objs.append(WorldObject(d.class_id, meta.get("label", d.label), d.confidence, rng,
                                    x, y, meta.get("height_m", 0.0), d.bbox))
        return WorldState(t=t, pose=pose, objects=objs, robot=self.cfg.get("robot", ""))

    def run(self) -> None:
        self.link.start()
        if self.webui:
            self.webui.start()
        print("Logging world state to", self.logger.path)
        last_print = 0.0
        try:
            while True:
                t0 = time.time()
                dets = self.source.fetch()
                t1 = time.time()
                pose = self.pose_source.current()
                world = self.build_world(dets, pose, t0)
                self.logger.log(world)
                self.link.set_record(world.to_ai_record())
                cmd = self.strategy.update(world)
                self.debug.update(world, cmd, [d.__dict__ for d in dets],
                                  links={"limelight": self.source.connected, "v5": self.link.connected,
                                         "v5_requests": self.link.requests, "odom_packets": self.link.odom_packets,
                                         "limelight_errors": self.source.errors},
                                  timing={"fetch": t1 - t0, "process": time.time() - t1})
                if t0 - last_print > 1.0:
                    last_print = t0
                    print(f"[ll {'ok' if self.source.connected else 'DOWN'}] [v5 {'ok' if self.link.connected else 'DOWN'}] "
                          f"pose=({pose.x:+.2f},{pose.y:+.2f},{pose.heading:.0f}) objs={len(world.objects)} "
                          f"-> {cmd.kind} {cmd.target or ''} {cmd.note}")
                dt = self.period - (time.time() - t0)
                if dt > 0:
                    time.sleep(dt)
        finally:
            self.link.stop()
            if self.webui:
                self.webui.stop()
            self.logger.close()
