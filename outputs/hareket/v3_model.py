"""Locations of the original V3 grasp data and its repaired collision model."""

from pathlib import Path
import sys
import numpy as np
import mujoco as mj

H = Path(__file__).resolve().parent
HERE = H.parent / "ikinci-tur"
OLD = H.parent / "deneyler"
sys.path.insert(0, str(OLD))
from hand import Hand
