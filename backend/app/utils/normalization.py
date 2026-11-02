"""
Normalization Utilities for Recommendation Scoring Components.
Ensures all scoring signals are normalized strictly to the [0.0, 1.0] interval.
"""
import math
from typing import List, Union, Sequence
import numpy as np


def min_max_normalize(
    val: float,
    min_val: float,
    max_val: float,
    clip_default: float = 0.5
) -> float:
    """Normalize a value to [0.0, 1.0] via min-max scaling with edge-case handling."""
    if math.isclose(max_val, min_val, abs_tol=1e-9):
        return clip_default
    scaled = (val - min_val) / (max_val - min_val)
    return float(np.clip(scaled, 0.0, 1.0))


def sigmoid_normalize(
    val: float,
    center: float = 0.0,
    temperature: float = 1.0
) -> float:
    """Normalize unbounded real numbers using a tunable sigmoid function."""
    try:
        z = (val - center) / max(temperature, 1e-6)
        # Avoid overflow
        z = np.clip(z, -30.0, 30.0)
        return float(1.0 / (1.0 + math.exp(-z)))
    except Exception:
        return 0.5


def log_scale_normalize(val: float, max_expected: float = 1000.0) -> float:
    """Log-transform heavy-tailed count signals (views, likes, comments) into [0.0, 1.0]."""
    safe_val = max(0.0, float(val))
    scaled = math.log1p(safe_val) / math.log1p(max(1.0, float(max_expected)))
    return float(np.clip(scaled, 0.0, 1.0))


def z_score_normalize(
    values: Sequence[float],
    clip_std: float = 3.0
) -> List[float]:
    """Z-score normalization with standard deviation clipping scaled to [0, 1]."""
    arr = np.array(values, dtype=np.float64)
    if len(arr) == 0:
        return []
    mean = float(np.mean(arr))
    std = float(np.std(arr))
    if math.isclose(std, 0.0, abs_tol=1e-9):
        return [0.5] * len(arr)
    
    z = (arr - mean) / std
    z_clipped = np.clip(z, -clip_std, clip_std)
    # Rescale [-clip_std, +clip_std] to [0.0, 1.0]
    rescaled = (z_clipped + clip_std) / (2.0 * clip_std)
    return [float(x) for x in rescaled]


def clip_score(score: float) -> float:
    """Safety clamp for component recommendation scores."""
    if math.isnan(score) or math.isinf(score):
        return 0.0
    return float(max(0.0, min(1.0, score)))
