"""World state: the typed boundary between perception and everything above it.

Perception produces a WorldState per frame. Logging, replay, and strategy only
ever see WorldState, never raw detections or serial packets.
"""
from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence

import vaic_protocol as P

SCHEMA_VERSION = 1  # bump when WorldState's JSON shape changes


@dataclass
class Pose:
    x: float = 0.0            # meters, field center origin
    y: float = 0.0
    z: float = 0.0
    heading: float = 0.0      # degrees
    pitch: float = 0.0
    roll: float = 0.0
    frame: int = 0
    status: int = 0

    @property
    def connected(self) -> bool:
        return bool(self.status & P.POS_STATUS_CONNECTED)

    def distance_to(self, x: float, y: float) -> float:
        return math.hypot(x - self.x, y - self.y)


@dataclass
class WorldObject:
    class_id: int
    label: str = ""
    confidence: float = 0.0
    depth: float = 0.0        # meters from camera
    x: float = 0.0            # field coordinates, meters
    y: float = 0.0
    z: float = 0.0
    bbox: Sequence[int] = (0, 0, 0, 0)   # image center x, center y, w, h


@dataclass
class WorldState:
    t: float = 0.0            # unix seconds when the frame was captured
    pose: Pose = field(default_factory=Pose)
    objects: List[WorldObject] = field(default_factory=list)
    robot: str = ""           # robot id from config, e.g. "robot_a"

    # ---- conversions to/from the wire record ----
    @classmethod
    def from_ai_record(cls, rec: Any, labels: Optional[List[str]] = None,
                       t: Optional[float] = None, robot: str = "") -> "WorldState":
        """Accepts either the generated AI_RECORD or VEX's V5Comm.AIRecord (duck typed)."""
        labels = labels or []
        pos = getattr(rec, "pos", None) or rec.position
        pose = Pose(
            x=pos.x, y=pos.y, z=pos.z,
            heading=getattr(pos, "az", getattr(pos, "azimuth", 0.0)),
            pitch=getattr(pos, "el", getattr(pos, "elevation", 0.0)),
            roll=getattr(pos, "rot", getattr(pos, "rotation", 0.0)),
            frame=getattr(pos, "framecnt", getattr(pos, "frameCount", 0)),
            status=pos.status,
        )
        objs = []
        for d in rec.detections:
            # VEX's class has a typo: mapLocattion
            mp = getattr(d, "mapLocation", None) or getattr(d, "mapLocattion")
            sl = d.screenLocation
            cid = int(d.classID)
            objs.append(WorldObject(
                class_id=cid,
                label=labels[cid] if 0 <= cid < len(labels) else str(cid),
                confidence=float(d.probability),
                depth=float(d.depth) if d.depth == d.depth else -1.0,  # NaN -> -1
                x=float(mp.x), y=float(mp.y), z=float(mp.z),
                bbox=(int(sl.x), int(sl.y), int(sl.width), int(sl.height)),
            ))
        return cls(t=time.time() if t is None else t, pose=pose, objects=objs, robot=robot)

    def to_ai_record(self) -> P.AI_RECORD:
        rec = P.AI_RECORD(pos=P.POS_RECORD(
            framecnt=self.pose.frame, status=self.pose.status,
            x=self.pose.x, y=self.pose.y, z=self.pose.z,
            az=self.pose.heading, el=self.pose.pitch, rot=self.pose.roll))
        for o in self.objects:
            rec.detections.append(P.DETECTION_OBJECT(
                classID=o.class_id, probability=o.confidence, depth=o.depth,
                screenLocation=P.IMAGE_DETECTION(*o.bbox),
                mapLocation=P.MAP_DETECTION(o.x, o.y, o.z)))
        rec.detectionCount = len(rec.detections)
        return rec

    # ---- JSON for logs ----
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["v"] = SCHEMA_VERSION
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "WorldState":
        pose = Pose(**d.get("pose", {}))
        objs = [WorldObject(**{**o, "bbox": tuple(o.get("bbox", (0, 0, 0, 0)))}) for o in d.get("objects", [])]
        return cls(t=d.get("t", 0.0), pose=pose, objects=objs, robot=d.get("robot", ""))

    # ---- queries strategy code will want ----
    def objects_of(self, *class_ids: int, min_confidence: float = 0.0) -> List[WorldObject]:
        return [o for o in self.objects if o.class_id in class_ids and o.confidence >= min_confidence]

    def nearest(self, *class_ids: int, min_confidence: float = 0.0) -> Optional[WorldObject]:
        cands = self.objects_of(*class_ids, min_confidence=min_confidence)
        if not cands:
            return None
        return min(cands, key=lambda o: self.pose.distance_to(o.x, o.y))
