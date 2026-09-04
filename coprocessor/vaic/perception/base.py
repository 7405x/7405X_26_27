"""Camera-independent detection. Sources (Limelight, RealSense, replay) all emit this."""
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class Detection:
    class_id: int
    confidence: float
    bbox: Tuple[int, int, int, int]      # center x, center y, width, height in pixels
    tx: Optional[float] = None           # degrees right of camera axis, if the camera gives it
    ty: Optional[float] = None           # degrees above camera axis
    depth: float = -1.0                  # meters from camera if known, else -1
    label: str = ""


class DetectionSource:
    def start(self) -> None: ...
    def stop(self) -> None: ...

    def fetch(self) -> List[Detection]:
        """Latest frame's detections. Non-blocking; may return [] if nothing new."""
        raise NotImplementedError
