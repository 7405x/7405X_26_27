"""Turn a bearing to an object into field coordinates using the ground plane.

Conventions (match VEX's V5MapPosition.py):
  - field frame: meters, origin at field center, heading is compass style,
    0 deg = +Y, 90 deg = +X
  - robot frame: forward and right, in meters
  - camera angles: tx positive = right of axis, ty positive = above axis (Limelight)
  - mount pitch: negative = tilted down
"""
import math
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class CameraMount:
    forward_m: float = 0.0     # camera position relative to the robot's GPS reference point
    right_m: float = 0.0
    height_m: float = 0.3      # lens height above the tiles
    pitch_deg: float = 0.0     # negative looks down
    yaw_deg: float = 0.0       # positive turned to the right
    hfov_deg: float = 62.5     # Limelight 3 / 3A defaults; check your model
    vfov_deg: float = 48.9
    width: int = 640
    height: int = 480


def pixel_to_angles(px: float, py: float, mount: CameraMount) -> Tuple[float, float]:
    """Bounding-box center in pixels -> (tx, ty) degrees, pinhole model."""
    fx = (mount.width / 2) / math.tan(math.radians(mount.hfov_deg) / 2)
    fy = (mount.height / 2) / math.tan(math.radians(mount.vfov_deg) / 2)
    tx = math.degrees(math.atan((px - mount.width / 2) / fx))
    ty = math.degrees(math.atan((mount.height / 2 - py) / fy))
    return tx, ty


def project_to_robot(tx_deg: float, ty_deg: float, mount: CameraMount,
                     target_height_m: float = 0.0) -> Optional[Tuple[float, float, float]]:
    """(forward, right, range) in meters from the robot reference point, or None if the
    ray does not hit the plane at target_height_m (object above the horizon, or camera
    lower than the target)."""
    ray = math.radians(mount.pitch_deg + ty_deg)
    drop = mount.height_m - target_height_m
    if ray >= -1e-6 or drop <= 0:
        return None
    ground = drop / math.tan(-ray)                 # horizontal distance from the lens
    bearing = math.radians(mount.yaw_deg + tx_deg)
    fwd = mount.forward_m + ground * math.cos(bearing)
    right = mount.right_m + ground * math.sin(bearing)
    return fwd, right, math.hypot(ground, drop)


def robot_to_field(fwd: float, right: float, rx: float, ry: float, heading_deg: float) -> Tuple[float, float]:
    h = math.radians(heading_deg)
    return (rx + fwd * math.sin(h) + right * math.cos(h),
            ry + fwd * math.cos(h) - right * math.sin(h))


def project_to_field(tx_deg: float, ty_deg: float, mount: CameraMount, rx: float, ry: float,
                     heading_deg: float, target_height_m: float = 0.0
                     ) -> Optional[Tuple[float, float, float]]:
    """-> (field_x, field_y, range_m) or None."""
    r = project_to_robot(tx_deg, ty_deg, mount, target_height_m)
    if r is None:
        return None
    fwd, right, rng = r
    x, y = robot_to_field(fwd, right, rx, ry, heading_deg)
    return x, y, rng
