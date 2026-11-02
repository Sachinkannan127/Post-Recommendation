"""
Multi-Objective Ranking Engine.
Scores candidate posts through a multi-factor ranking function:
Score = w_social * S_social + w_content * S_content + w_commerce * S_commerce + w_quality * S_quality * R(t) - P_fatigue
Provides full transparent factor attribution and explainability.
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from datetime import datetime, timezone
import math

from backend.app.core.user_profile import UserProfile
from backend.app.core.candidate_generator import CandidatePost


class RankingWeights:
    def __init__(
        self,
        w_social: float = 0.28,
        w_content: float = 0.27,
        w_commerce: float = 0.25,
        w_quality: float = 0.20,
        recency_half_life_days: float = 7.0,
        fatigue_penalty: float = 0.35
    ):
        self.w_social = w_social
        self.w_content = w_content
        self.w_commerce = w_commerce
        self.w_quality = w_quality
        self.recency_half_life_days = recency_half_life_days
        self.fatigue_penalty = fatigue_penalty


class ScoredPost:
    def __init__(
        self,
        candidate: CandidatePost,
        total_score: float,
        subscores: Dict[str, float],
        explanations: List[str]
    ):
        self.candidate = candidate
        self.total_score = total_score
        self.subscores = subscores
        self.explanations = explanations

    def to_dict(self) -> Dict[str, Any]:
        p = self.candidate.post_doc
        s = self.candidate.seller
        prod = self.candidate.pinned_product
        m = self.candidate.metrics

        return {
            "post_id": self.candidate.post_id,
            "total_score": round(self.total_score, 4),
            "subscores": {k: round(v, 4) for k, v in self.subscores.items()},
            "explanations": self.explanations,
            "retrieval_channel": self.candidate.channel,
            "post": {
                "id": p.get("_id"),
                "caption": p.get("caption"),
                "category_id": p.get("category_id"),
                "media_url": p.get("media_url"),
                "media_type": p.get("media_type", "video"),
                "created_at": p.get("created_at")
            },
            "seller": {
                "id": s.get("_id"),
                "name": s.get("name"),
                "handle": s.get("handle"),
                "avatar": s.get("avatar"),
                "rating": s.get("rating", 4.8)
            },
            "pinned_product": {
                "id": prod.get("_id"),
                "title": prod.get("title"),
                "price": prod.get("price"),
                "rating": prod.get("rating")
            } if prod else None,
            "metrics": {
                "likes": m.get("total_likes", 0),
                "comments": m.get("total_comments", 0),
                "shares": m.get("total_shares", 0),
                "saves": m.get("total_saves", 0),
                "views": m.get("total_views", 0),
                "avg_watch_time": m.get("avg_watch_time", 0.0)
            }
        }


class Ranker:
    def __init__(self, weights: Optional[RankingWeights] = None):
        self.weights = weights or RankingWeights()

    def rank(
        self,
        profile: UserProfile,
        candidates: List[CandidatePost],
        weights_override: Optional[RankingWeights] = None
    ) -> List[ScoredPost]:
        w = weights_override or self.weights
        scored: List[ScoredPost] = []
        now = datetime.now(timezone.utc)

        for cand in candidates:
            p_doc = cand.post_doc
            m = cand.metrics
            seller_id = p_doc.get("seller_id", "")
            cat_id = p_doc.get("category_id", "")
            prod_id = p_doc.get("pinned_product_id")

            subscores: Dict[str, float] = {}
            explanations: List[str] = []

            # 1. Social Affinity Score
            # High boost if user follows this creator
            is_followed = seller_id in profile.followed_sellers
            seller_rating = cand.seller.get("rating", 4.5) if cand.seller else 4.5
            s_social = 1.0 if is_followed else (seller_rating / 5.0 * 0.4)
            subscores["social"] = s_social
            if is_followed:
                handle = cand.seller.get("handle", seller_id)
                explanations.append(f"Following creator {handle}")

            # 2. Content Semantic Similarity Score
            s_content = 0.5  # Neutral default for cold start
            if profile.user_vector is not None and cand.embedding is not None:
                sim = float(np.dot(profile.user_vector, cand.embedding))
                s_content = max(0.0, min(1.0, (sim + 1.0) / 2.0))
                if sim > 0.45:
                    explanations.append(f"Matches your taste profile ({int(sim * 100)}% match)")
            elif cat_id in profile.category_affinities:
                aff = profile.category_affinities[cat_id]
                s_content = 0.5 + (aff * 0.5)
                if aff > 0.3:
                    explanations.append(f"High affinity for {cat_id.replace('cat_', '').title()}")
            subscores["content"] = s_content

            # 3. Commerce Intent Score
            s_commerce = 0.2
            if prod_id and prod_id in profile.cart_product_ids:
                s_commerce = 1.0
                prod_title = cand.pinned_product.get("title", "item") if cand.pinned_product else "item"
                explanations.append(f"Pinned item '{prod_title[:25]}...' is currently in your cart")
            elif prod_id and prod_id in profile.ordered_product_ids:
                s_commerce = 0.85
                explanations.append("Related to past purchase")
            elif cat_id in profile.category_affinities:
                s_commerce = 0.3 + (profile.category_affinities[cat_id] * 0.6)
            subscores["commerce"] = s_commerce

            # 4. Engagement Quality Score (Bayesian smoothed)
            views = max(1, m.get("total_views", 100))
            likes = m.get("total_likes", 5)
            comments = m.get("total_comments", 1)
            shares = m.get("total_shares", 1)
            saves = m.get("total_saves", 2)
            avg_watch = m.get("avg_watch_time", 0.5)

            # Smoothed engagement rate
            smoothed_eng = (likes + 1.5 * comments + 2.5 * shares + 2.0 * saves + 10) / (views + 100)
            s_quality = min(1.0, (smoothed_eng * 5.0 * 0.6) + (avg_watch * 0.4))
            subscores["quality"] = s_quality

            if avg_watch >= 0.85:
                explanations.append(f"High completion rate ({int(avg_watch * 100)}% watched)")
            elif likes > 2000:
                explanations.append(f"Trending community favorite ({likes:,} likes)")

            # 5. Recency Decay
            days_old = 1.0
            if "created_at" in p_doc:
                try:
                    dt = datetime.fromisoformat(p_doc["created_at"].replace("Z", "+00:00"))
                    days_old = max(0.1, (now - dt).total_seconds() / 86400.0)
                except Exception:
                    days_old = 3.0
            decay_rate = math.log(2) / max(0.5, w.recency_half_life_days)
            recency_mult = math.exp(-decay_rate * days_old)
            subscores["recency"] = recency_mult

            # 6. Fatigue Penalty
            # Check if user already engaged with this post
            fatigue = 0.0
            if cand.post_id in profile.engaged_post_ids:
                fatigue = w.fatigue_penalty
            subscores["fatigue_penalty"] = fatigue

            # Compute Final Composite Score
            # If cold-start, shift weight toward trending quality & recency
            if profile.is_cold_start:
                total_score = (0.55 * s_quality * recency_mult) + (0.25 * s_commerce) + (0.20 * s_social)
                if not explanations:
                    explanations.append("Fresh viral post across platform")
            else:
                base_score = (
                    w.w_social * s_social +
                    w.w_content * s_content +
                    w.w_commerce * s_commerce +
                    w.w_quality * s_quality * recency_mult
                )
                total_score = max(0.01, base_score - fatigue)

            scored.append(ScoredPost(
                candidate=cand,
                total_score=total_score,
                subscores=subscores,
                explanations=explanations[:3]  # Top 3 clear reasons
            ))

        # Sort descending by total score
        scored.sort(key=lambda x: x.total_score, reverse=True)
        return scored
