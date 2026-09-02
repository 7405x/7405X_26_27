import os
from typing import List

from . import ROOT

DEFAULT_LABELS = os.path.join(ROOT, "JetsonExample", "labels.txt")


def load_labels(path: str = DEFAULT_LABELS) -> List[str]:
    """One class name per line; index == classID on the wire."""
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]
