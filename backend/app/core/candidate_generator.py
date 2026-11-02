"""
Multi-Channel Candidate Generation Engine.
Retrieves diverse candidate posts across 5 distinct channels:
1. Social Graph (creators user follows)
2. Content Vector Similarity (cosine similarity against postembeddings)
3. Commerce Intent (pinned products matching cart/orders/category affinities)
4. Collaborative Behavioral Signals (posts engaged by users with overlapping taste)
5. Trending & Viral Velocity (recency-decayed engagement rate for discovery & cold start)
"""
from typing import Dict, List, Any, Set, Tuple, Optional
import numpy as np
from datetime import datetime, timezone
import math

from backend.app.core.user_profile import UserProfile


class CandidatePost:
    def __init__(
        self,
        post_id: str,
        channel: str,
        channel_score: float,
        post_doc: Dict[str, Any],
        embedding: Optional[np.ndarray] = None,
        metrics: Optional[Dict[str, Any]] = None,
        seller: Optional[Dict[str, Any]] = None,
        pinned_product: Optional[Dict[str, Any]] = None
    ):
        self.post_id = post_id
        self.channel = channel
        self.channel_score = channel_score
        self.post_doc = post_doc
        self.embedding = embedding
        self.metrics = metrics or {}
        self.seller = seller or {}
        self.pinned_product = pinned_product


class CandidateGenerator:
    def __init__(self, db: Any):
        self.db = db

    def generate_candidates(self, profile: UserProfile, max_candidates: int = 150) -> List[CandidatePost]:
        """Runs all 5 retrieval channels and combines deduplicated candidate posts."""
        candidates_map: Dict[str, CandidatePost] = {}

        # 1. Trending / Viral Channel (Runs for all users; primary channel for Cold-Start)
        trending_candidates = self._retrieve_trending(limit=30)
        for cand in trending_candidates:
            self._merge_candidate(candidates_map, cand)

        if not profile.is_cold_start:
            # 2. Social Graph Channel
            social_candidates = self._retrieve_social_graph(profile, limit=35)
            for cand in social_candidates:
                self._merge_candidate(candidates_map, cand)

            # 3. Content Vector Similarity Channel
            if profile.user_vector is not None:
                vector_candidates = self._retrieve_vector_similarity(profile, limit=35)
                for cand in vector_candidates:
                    self._merge_candidate(candidates_map, cand)

            # 4. Commerce Intent Channel
            commerce_candidates = self._retrieve_commerce_intent(profile, limit=30)
            for cand in commerce_candidates:
                self._merge_candidate(candidates_map, cand)

            # 5. Collaborative Behavioral Channel
            collab_candidates = self._retrieve_collaborative(profile, limit=25)
            for cand in collab_candidates:
                self._merge_candidate(candidates_map, cand)

        # Hydrate all candidate posts with embeddings, metrics, seller, and product details
        hydrated = self._hydrate_candidates(list(candidates_map.values()))
        return hydrated[:max_candidates]

    def _merge_candidate(self, cand_map: Dict[str, CandidatePost], cand: CandidatePost):
        if cand.post_id not in cand_map:
            cand_map[cand.post_id] = cand
        else:
            # Keep highest channel score or combine channel tags
            existing = cand_map[cand.post_id]
            if cand.channel_score > existing.channel_score:
                existing.channel = f"{existing.channel}+{cand.channel}"
                existing.channel_score = max(existing.channel_score, cand.channel_score)

    def _retrieve_social_graph(self, profile: UserProfile, limit: int = 35) -> List[CandidatePost]:
        if not profile.followed_sellers:
            return []
        posts = list(self.db.posts.find({
            "seller_id": {"$in": list(profile.followed_sellers)},
            "status": "active"
        }))
        results = []
        for p in posts:
            results.append(CandidatePost(
                post_id=p["_id"],
                channel="social_graph",
                channel_score=1.0,
                post_doc=p
            ))
        return results[:limit]

    def _retrieve_vector_similarity(self, profile: UserProfile, limit: int = 35) -> List[CandidatePost]:
        if profile.user_vector is None:
            return []
        
        all_embeddings = list(self.db.postembeddings.find({}))
        if not all_embeddings:
            return []

        post_ids = [e["post_id"] for e in all_embeddings]
        vectors = np.array([e["embedding"] for e in all_embeddings], dtype=float)

        # Dot product with normalized user vector gives cosine similarity
        sims = np.dot(vectors, profile.user_vector)
        top_indices = np.argsort(sims)[::-1][:limit]

        posts_lookup = {p["_id"]: p for p in self.db.posts.find({"_id": {"$in": [post_ids[i] for i in top_indices]}})}

        results = []
        for idx in top_indices:
            p_id = post_ids[idx]
            sim = float(sims[idx])
            p_doc = posts_lookup.get(p_id)
            if p_doc and p_doc.get("status") == "active":
                results.append(CandidatePost(
                    post_id=p_id,
                    channel="vector_similarity",
                    channel_score=sim,
                    post_doc=p_doc,
                    embedding=vectors[idx]
                ))
        return results

    def _retrieve_commerce_intent(self, profile: UserProfile, limit: int = 30) -> List[CandidatePost]:
        results = []
        # Target products in cart or matching top categories
        target_product_ids = set(profile.cart_product_ids)
        top_categories = [cat for cat, _ in sorted(profile.category_affinities.items(), key=lambda x: x[1], reverse=True)[:2]]

        query: Dict[str, Any] = {"status": "active"}
        conditions = []
        if target_product_ids:
            conditions.append({"pinned_product_id": {"$in": list(target_product_ids)}})
        if top_categories:
            conditions.append({"category_id": {"$in": top_categories}})

        if conditions:
            query["$or"] = conditions
            matched_posts = list(self.db.posts.find(query))
            for p in matched_posts:
                score = 0.9 if p.get("pinned_product_id") in target_product_ids else 0.75
                results.append(CandidatePost(
                    post_id=p["_id"],
                    channel="commerce_intent",
                    channel_score=score,
                    post_doc=p
                ))
        return results[:limit]

    def _retrieve_collaborative(self, profile: UserProfile, limit: int = 25) -> List[CandidatePost]:
        """Finds posts engaged by users who engaged with similar posts (User-to-User CF)."""
        if not profile.engaged_post_ids:
            return []

        # Find other users who engaged with the same posts
        other_engagements = list(self.db.postengagements.find({
            "post_id": {"$in": list(profile.engaged_post_ids)},
            "user_id": {"$ne": profile.user_id}
        }))
        similar_users = {e["user_id"] for e in other_engagements}
        if not similar_users:
            return []

        # What other posts did these users engage with?
        co_engagements = list(self.db.postengagements.find({
            "user_id": {"$in": list(similar_users)},
            "post_id": {"$nin": list(profile.engaged_post_ids)}
        }))

        post_counts: Dict[str, int] = {}
        for ce in co_engagements:
            p_id = ce["post_id"]
            post_counts[p_id] = post_counts.get(p_id, 0) + 1

        sorted_posts = sorted(post_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        if not sorted_posts:
            return []

        post_ids = [p[0] for p in sorted_posts]
        posts = {p["_id"]: p for p in self.db.posts.find({"_id": {"$in": post_ids}, "status": "active"})}

        results = []
        for p_id, count in sorted_posts:
            if p_id in posts:
                results.append(CandidatePost(
                    post_id=p_id,
                    channel="collaborative_filtering",
                    channel_score=min(1.0, count / 3.0),
                    post_doc=posts[p_id]
                ))
        return results

    def _retrieve_trending(self, limit: int = 30) -> List[CandidatePost]:
        """Ranks posts by recency-decayed viral engagement rate from postmetrics."""
        metrics_docs = list(self.db.postmetrics.find({}))
        posts = {p["_id"]: p for p in self.db.posts.find({"status": "active"})}

        now = datetime.now(timezone.utc)
        scored_posts = []

        for m in metrics_docs:
            p_id = m.get("post_id")
            post = posts.get(p_id)
            if not post:
                continue

            views = max(1, m.get("total_views", 1))
            likes = m.get("total_likes", 0)
            comments = m.get("total_comments", 0)
            shares = m.get("total_shares", 0)
            saves = m.get("total_saves", 0)
            avg_watch = m.get("avg_watch_time", 0.5)

            # Weighted engagement rate
            engagement_weight = (likes * 1.0 + comments * 1.5 + shares * 2.5 + saves * 2.0)
            eng_rate = engagement_weight / views

            # Recency decay: half-life of 7 days
            days_old = 1.0
            if "created_at" in post:
                try:
                    dt = datetime.fromisoformat(post["created_at"].replace("Z", "+00:00"))
                    days_old = max(0.1, (now - dt).total_seconds() / 86400.0)
                except Exception:
                    days_old = 3.0
            decay = math.exp(-0.099 * days_old)  # ln(2)/7 ~ 0.099

            trending_score = (eng_rate * 0.7 + avg_watch * 0.3) * decay
            scored_posts.append((trending_score, post, m))

        scored_posts.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, post, metric in scored_posts[:limit]:
            results.append(CandidatePost(
                post_id=post["_id"],
                channel="trending_viral",
                channel_score=round(score, 4),
                post_doc=post,
                metrics=metric
            ))
        return results

    def _hydrate_candidates(self, candidates: List[CandidatePost]) -> List[CandidatePost]:
        """Batched hydration of postembeddings, metrics, sellers, and products."""
        if not candidates:
            return []

        post_ids = [c.post_id for c in candidates]
        seller_ids = list({c.post_doc.get("seller_id") for c in candidates if c.post_doc.get("seller_id")})
        prod_ids = list({c.post_doc.get("pinned_product_id") for c in candidates if c.post_doc.get("pinned_product_id")})

        embeddings = {e["post_id"]: np.array(e["embedding"], dtype=float) for e in self.db.postembeddings.find({"post_id": {"$in": post_ids}})}
        metrics = {m["post_id"]: m for m in self.db.postmetrics.find({"post_id": {"$in": post_ids}})}
        sellers = {s["_id"]: s for s in self.db.sellerdetails.find({"_id": {"$in": seller_ids}})}
        products = {p["_id"]: p for p in self.db.products.find({"_id": {"$in": prod_ids}})}

        for c in candidates:
            if c.post_id in embeddings and c.embedding is None:
                c.embedding = embeddings[c.post_id]
            if c.post_id in metrics and not c.metrics:
                c.metrics = metrics[c.post_id]
            seller_id = c.post_doc.get("seller_id")
            if seller_id in sellers:
                c.seller = sellers[seller_id]
            pinned_prod_id = c.post_doc.get("pinned_product_id")
            if pinned_prod_id in products:
                c.pinned_product = products[pinned_prod_id]

        return candidates
