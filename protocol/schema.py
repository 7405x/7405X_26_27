"""Single source of truth for the coprocessor <-> V5 Brain wire protocol.

Edit this file, then run `python protocol/generate.py` to regenerate:
  protocol/generated/vaic_protocol.py   (used by coprocessor/)
  protocol/generated/vaic_protocol.h    (copied into v5/*/include/)

Version 1 is byte-for-byte identical to VEX's ai_jetson.h / V5Comm.py layout so
the stock ai_demo V5 project keeps working. When you change a struct:
  1. bump PROTOCOL_VERSION
  2. add a new PACKET_TYPE_* value and keep the old one for the old layout
  3. regenerate and rebuild BOTH sides before flashing either
The generator embeds a layout hash in both outputs; tests fail if they drift.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

PROTOCOL_VERSION = 2
MAX_DETECTIONS = 50
SYNC_BYTES = (0xAA, 0x55, 0xCC, 0x33)
BAUD = 115200
# The V5 Brain sends this ASCII line to request one packet.
REQUEST_LINE = "AA55CC3301"
CRC32_POLY = 0x04C11DB7  # non-reflected, init 0, no final xor (matches VEX)

# Packet types (16-bit `type` field in the header). Never reuse a value.
PACKET_TYPES = {
    "PACKET_TYPE_AI_RECORD": (0x0001, "Jetson -> Brain: AI_RECORD payload, layout v1"),
    "PACKET_TYPE_ODOM":      (0x0002, "Brain -> Jetson: ODOM_RECORD from encoder odometry"),
}

# Scalar types: name -> (C type, struct format char, size)
SCALARS = {
    "i32": ("int32_t", "i", 4),
    "u32": ("uint32_t", "I", 4),
    "f32": ("float", "f", 4),
}


@dataclass
class Field:
    name: str
    type: str                      # scalar key or struct name
    comment: str = ""
    array: Optional[int] = None    # fixed-size array length, or None


@dataclass
class Struct:
    name: str
    fields: List[Field]
    comment: str = ""
    # Name of an i32 field that says how many trailing array entries are
    # actually sent on the wire (variable-length payload), or None.
    count_field: Optional[str] = None


POS_RECORD = Struct("POS_RECORD", [
    Field("framecnt", "i32", "Increments each GPS frame"),
    Field("status", "i32", "0 = good; see POS_STATUS_* flags"),
    Field("x", "f32", "Field X in meters, 0 at field center"),
    Field("y", "f32", "Field Y in meters, 0 at field center"),
    Field("z", "f32", "Height above tiles in meters"),
    Field("az", "f32", "Heading in degrees"),
    Field("el", "f32", "Pitch in degrees"),
    Field("rot", "f32", "Roll in degrees"),
], "Robot pose from the V5 GPS sensor, offsets already applied")

IMAGE_DETECTION = Struct("IMAGE_DETECTION", [
    Field("x", "i32", "Bounding box center X in pixels, 0 at top-left"),
    Field("y", "i32", "Bounding box center Y in pixels"),
    Field("width", "i32", "Bounding box width in pixels"),
    Field("height", "i32", "Bounding box height in pixels"),
], "Detection in camera image coordinates")

MAP_DETECTION = Struct("MAP_DETECTION", [
    Field("x", "f32", "Field X in meters"),
    Field("y", "f32", "Field Y in meters"),
    Field("z", "f32", "Height above tiles in meters"),
], "Detection in field coordinates")

DETECTION_OBJECT = Struct("DETECTION_OBJECT", [
    Field("classID", "i32", "Index into labels.txt"),
    Field("probability", "f32", "Confidence, 1.0 == 100%"),
    Field("depth", "f32", "Distance from camera in meters"),
    Field("screenLocation", "IMAGE_DETECTION"),
    Field("mapLocation", "MAP_DETECTION"),
], "One detected object")

AI_RECORD = Struct("AI_RECORD", [
    Field("detectionCount", "i32", "Number of valid entries in detections[]"),
    Field("pos", "POS_RECORD"),
    Field("detections", "DETECTION_OBJECT", array=MAX_DETECTIONS),
], "Everything the coprocessor sends per frame", count_field="detectionCount")

ODOM_RECORD = Struct("ODOM_RECORD", [
    Field("t_ms", "u32", "Brain uptime in ms when the estimate was made"),
    Field("x", "f32", "Field X in meters (same frame as POS_RECORD)"),
    Field("y", "f32", "Field Y in meters"),
    Field("heading", "f32", "Compass heading in degrees, 0 = +Y, 90 = +X"),
    Field("status", "i32", "0 = ok; ODOM_STATUS_* flags"),
], "Brain-side pose from motor encoders, used when the GPS has no fix")

STRUCTS: List[Struct] = [POS_RECORD, IMAGE_DETECTION, MAP_DETECTION, DETECTION_OBJECT, AI_RECORD, ODOM_RECORD]

# GPS status flags (POS_RECORD.status), copied from VEX's V5Position.py
POS_STATUS_FLAGS = {
    "POS_STATUS_CONNECTED":  0x00000001,
    "POS_STATUS_NODOTS":     0x00000002,
    "POS_STATUS_NORAWBITS":  0x00000004,
    "POS_STATUS_NOGROUPS":   0x00000008,
    "POS_STATUS_NOBITS":     0x00000010,
    "POS_STATUS_PIXELERROR": 0x00000020,
    "POS_STATUS_SOLVER":     0x00000040,
    "POS_STATUS_ANGLEJUMP":  0x00000080,
    "POS_STATUS_POSJUMP":    0x00000100,
    "POS_STATUS_NOSOLUTION": 0x00000200,
    "POS_STATUS_KALMAN_EST": 0x00100000,
}


ODOM_STATUS_FLAGS = {
    "ODOM_STATUS_VALID":  0x00000001,
    "ODOM_STATUS_RESET":  0x00000002,  # pose was just re-seeded from GPS
}


def struct_by_name(name: str) -> Struct:
    for s in STRUCTS:
        if s.name == name:
            return s
    raise KeyError(name)


def size_of(type_name: str) -> int:
    if type_name in SCALARS:
        return SCALARS[type_name][2]
    return sum(size_of(f.type) * (f.array or 1) for f in struct_by_name(type_name).fields)


def canonical_layout() -> str:
    """Stable text description of the layout, hashed into both outputs."""
    lines = [f"version={PROTOCOL_VERSION}", f"max_detections={MAX_DETECTIONS}"]
    for s in STRUCTS:
        for f in s.fields:
            lines.append(f"{s.name}.{f.name}:{f.type}[{f.array or 1}]")
    for k, (v, _) in PACKET_TYPES.items():
        lines.append(f"{k}={v}")
    return "\n".join(lines)
