"""
Scoring and Similarity Calculation Utilities.
Includes vector cosine similarity, exponential time decay, and weighted combination.
"""
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence
import numpy as np


def cosine_similarity(
    vec1: Sequence[float],
    vec2: Sequence[float]
) -> float:
    """
    Compute cosine similarity between two numeric vectors.
    Returns a score mapped to [0.0, 1.0].
    """
    if not vec1 or not vec2:
        return 0.0
    
    a = np.array(vec1, dtype=np.float32)
    b = np.array(vec2, dtype=np.float32)
    
    if len(a) != len(b):
        min_len = min(len(a), len(b))
        a = a[:min_len]
        b = b[:min_len]
        
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    raw_sim = float(np.dot(a, b) / (norm_a * norm_b))
    # Normalize from [-1.0, 1.0] to [0.0, 1.0]
    normalized = (raw_sim + 1.0) / 2.0
    return float(np.clip(normalized, 0.0, 1.0))


def compute_freshness_decay(
    created_at: Optional[datetime],
    half_life_days: float = 7.0,
    reference_time: Optional[datetime] = None
) -> float:
    """
    Compute exponential freshness decay score in [0.0, 1.0].
    Score = 2^(-delta_days / half_life_days)
    """
    if not created_at:
        return 0.5
        
    now = reference_time or datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
        
    delta_seconds = max(0.0, (now - created_at).total_seconds())
    delta_days = delta_seconds / 86400.0
    
    # Exponential decay
    decay = math.pow(2.0, -delta_days / max(0.1, half_life_days))
    return float(np.clip(decay, 0.0, 1.0))


def combine_hybrid_scores(
    content_sim: float,
    user_engagement: float,
    social_rel: float,
    commerce_rel: float,
    popularity: float,
    freshness: float,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculates the configurable hybrid recommendation score:
    Final Score = (w_content * Content) + (w_eng * Engagement) + (w_soc * Social)
                + (w_comm * Commerce) + (w_pop * Popularity) + (w_fresh * Freshness)
    All components and final score are bounded in [0.0, 1.0].
    """
    w = weights or {
        "content": 0.30,
        "engagement": 0.20,
        "social": 0.15,
        "commerce": 0.15,
        "popularity": 0.10,
        "freshness": 0.10
    }
    
    total_w = sum(w.values()) or 1.0
    
    raw = (
        (w.get("content", 0.30) * content_sim) +
        (w.get("engagement", 0.20) * user_engagement) +
        (w.get("social", 0.15) * social_rel) +
        (w.get("commerce", 0.15) * commerce_rel) +
        (w.get("popularity", 0.10) * popularity) +
        (w.get("freshness", 0.10) * freshness)
    ) / total_w
    
    return float(np.clip(raw, 0.0, 1.0))
