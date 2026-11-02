"""
Unified Post Feed Recommendation Engine.
Orchestrates User Profile Building -> Candidate Generation -> Multi-Objective Ranking -> Diversity Re-ranking.
"""
from typing import Dict, List, Any, Optional
import time

from backend.app.core.user_profile import build_user_profile, UserProfile
from backend.app.core.candidate_generator import CandidateGenerator
from backend.app.core.ranker import Ranker, RankingWeights, ScoredPost
from backend.app.core.reranker import Reranker


class FeedRecommender:
    def __init__(self, db: Any):
        self.db = db
        self.candidate_gen = CandidateGenerator(db)
        self.ranker = Ranker()
        self.reranker = Reranker()

    def get_feed(
        self,
        user_id: str,
        limit: int = 20,
        weights_override: Optional[RankingWeights] = None,
        enable_exploration: bool = True
    ) -> Dict[str, Any]:
        """Generates a personalized post feed for a given user with performance metrics."""
        t0 = time.perf_counter()

        # Step 1: User Profile Extraction
        profile = build_user_profile(user_id, self.db)
        t_profile = time.perf_counter()

        # Step 2: Multi-Channel Candidate Retrieval
        candidates = self.candidate_gen.generate_candidates(profile, max_candidates=100)
        t_candidates = time.perf_counter()

        # Step 3: Multi-Objective Scoring & Explainability
        scored = self.ranker.rank(profile, candidates, weights_override=weights_override)
        t_ranking = time.perf_counter()

        # Step 4: Diversity & Business Rule Re-ranking
        final_feed = self.reranker.rerank(scored, limit=limit, enable_exploration=enable_exploration)
        t_rerank = time.perf_counter()

        total_latency_ms = round((t_rerank - t0) * 1000, 2)

        return {
            "user_id": user_id,
            "is_cold_start": profile.is_cold_start,
            "user_profile": profile.to_dict(),
            "feed_count": len(final_feed),
            "feed": [item.to_dict() for item in final_feed],
            "diagnostics": {
                "total_latency_ms": total_latency_ms,
                "profile_latency_ms": round((t_profile - t0) * 1000, 2),
                "retrieval_latency_ms": round((t_candidates - t_profile) * 1000, 2),
                "ranking_latency_ms": round((t_ranking - t_candidates) * 1000, 2),
                "rerank_latency_ms": round((t_rerank - t_ranking) * 1000, 2),
                "candidates_retrieved": len(candidates),
                "candidates_scored": len(scored)
            }
        }

    def log_interaction(
        self,
        user_id: str,
        post_id: str,
        interaction_type: str,
        value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Logs real-time user feedback (views, likes, bookmarks, carts, shares)
        to dynamically update user signals and post metrics.
        """
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).isoformat()

        if interaction_type in ["like", "comment", "bookmark", "share"]:
            self.db.postengagements.insert_one({
                "user_id": user_id,
                "post_id": post_id,
                "action": interaction_type,
                "timestamp": now_iso
            })
            # Increment metric
            metric_field = f"total_{interaction_type}s"
            self.db.postmetrics.update_one(
                {"post_id": post_id},
                {"$inc": {metric_field: 1}},
                upsert=True
            )
        elif interaction_type == "view":
            watch_pct = value if value is not None else 0.85
            self.db.views.insert_one({
                "user_id": user_id,
                "post_id": post_id,
                "watch_percentage": watch_pct,
                "duration_seconds": int(watch_pct * 30),
                "timestamp": now_iso
            })
            self.db.postmetrics.update_one(
                {"post_id": post_id},
                {"$inc": {"total_views": 1}},
                upsert=True
            )
        elif interaction_type == "cart":
            post = self.db.posts.find_one({"_id": post_id})
            if post and post.get("pinned_product_id"):
                prod_id = post["pinned_product_id"]
                self.db.carts.insert_one({
                    "user_id": user_id,
                    "product_id": prod_id,
                    "quantity": 1,
                    "timestamp": now_iso
                })
        elif interaction_type == "order":
            post = self.db.posts.find_one({"_id": post_id})
            if post and post.get("pinned_product_id"):
                prod_id = post["pinned_product_id"]
                prod = self.db.products.find_one({"_id": prod_id})
                price = prod.get("price", 50.0) if prod else 50.0
                self.db.orders.insert_one({
                    "user_id": user_id,
                    "items": [{"product_id": prod_id, "quantity": 1, "price": price}],
                    "total_amount": price,
                    "status": "completed",
                    "timestamp": now_iso
                })

        return {"status": "success", "interaction": interaction_type, "post_id": post_id}
