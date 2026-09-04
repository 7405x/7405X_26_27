"""Hand-written WorldState frames for tests. Not a simulator; just enough shape to
exercise logging, replay, strategy, and the web server."""
from vaic.world import Pose, WorldObject, WorldState

T0 = 1_700_000_000.0


def frame(k: int, hz: float = 20.0) -> WorldState:
    """Frame k: robot sits at (0, 0) facing +Y; a red ball at (0, 1) and a blue one at (1, 0)."""
    return WorldState(
        t=T0 + k / hz,
        pose=Pose(x=0.0, y=0.0, heading=0.0, frame=k, status=1),
        objects=[
            WorldObject(1, "BallRed", 0.9, 1.0, 0.0, 1.0, 0.04, (320, 300, 40, 40)),
            WorldObject(0, "BallBlue", 0.8, 1.0, 1.0, 0.0, 0.04, (500, 300, 40, 40)),
        ],
        robot="test",
    )


def frames(n: int, hz: float = 20.0):
    for k in range(n):
        yield frame(k, hz)
