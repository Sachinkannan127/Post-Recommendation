"""
User Profile Aggregator & Feature Extractor.
Synthesizes user behavioral signals from follows, views, postengagements,
carts, and orders into real-time preference vectors and category affinity distributions.
"""
from typing import Dict, List, Any, Optional, Set
import numpy as np
from datetime import datetime, timezone


class UserProfile:
    def __init__(
        self,
        user_id: str,
        is_cold_start: bool = True,
        followed_sellers: Optional[Set[str]] = None,
        category_affinities: Optional[Dict[str, float]] = None,
        user_vector: Optional[np.ndarray] = None,
        engaged_post_ids: Optional[Set[str]] = None,
        cart_product_ids: Optional[Set[str]] = None,
        ordered_product_ids: Optional[Set[str]] = None,
        avg_watch_pct: float = 0.0,
        total_interactions: int = 0
    ):
        self.user_id = user_id
        self.is_cold_start = is_cold_start
        self.followed_sellers = followed_sellers or set()
        self.category_affinities = category_affinities or {}
        self.user_vector = user_vector
        self.engaged_post_ids = engaged_post_ids or set()
        self.cart_product_ids = cart_product_ids or set()
        self.ordered_product_ids = ordered_product_ids or set()
        self.avg_watch_pct = avg_watch_pct
        self.total_interactions = total_interactions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "is_cold_start": self.is_cold_start,
            "followed_sellers": list(self.followed_sellers),
            "top_categories": sorted(self.category_affinities.items(), key=lambda x: x[1], reverse=True),
            "total_interactions": self.total_interactions,
            "cart_items_count": len(self.cart_product_ids),
            "orders_count": len(self.ordered_product_ids),
            "avg_watch_pct": round(self.avg_watch_pct, 2)
        }


def build_user_profile(user_id: str, db: Any) -> UserProfile:
    """
    Extracts all behavioral signals for a user from MongoDB collections:
    - follows: explicit social graph
    - views: implicit interest via watch percentage
    - postengagements: explicit signals (likes, bookmarks, shares, comments)
    - carts: high-intent commerce signal
    - orders: confirmed purchase commerce signal
    - postembeddings: aggregate weighted centroid for user preference representation
    """
    # 1. Follows
    follows_docs = list(db.follows.find({"follower_id": user_id}))
    followed_sellers = {f["followee_id"] for f in follows_docs if "followee_id" in f}

    # 2. Engagements
    engagements_docs = list(db.postengagements.find({"user_id": user_id}))
    engaged_post_ids = {e["post_id"] for e in engagements_docs if "post_id" in e}

    # Engagement action weights
    ACTION_WEIGHTS = {
        "like": 1.0,
        "comment": 1.5,
        "bookmark": 2.0,
        "share": 2.5
    }

    # 3. Views
    views_docs = list(db.views.find({"user_id": user_id}))
    viewed_posts_map = {v["post_id"]: float(v.get("watch_percentage", 0.0)) for v in views_docs if "post_id" in v}
    avg_watch = float(np.mean(list(viewed_posts_map.values()))) if viewed_posts_map else 0.0

    # 4. Commerce Signals (Carts & Orders)
    carts_docs = list(db.carts.find({"user_id": user_id}))
    cart_product_ids = {c["product_id"] for c in carts_docs if "product_id" in c}

    orders_docs = list(db.orders.find({"user_id": user_id}))
    ordered_product_ids = set()
    for o in orders_docs:
        for item in o.get("items", []):
            if "product_id" in item:
                ordered_product_ids.add(item["product_id"])

    total_interactions = len(engagements_docs) + len(views_docs) + len(carts_docs) + len(orders_docs)
    is_cold_start = total_interactions == 0 and len(followed_sellers) == 0

    if is_cold_start:
        return UserProfile(
            user_id=user_id,
            is_cold_start=True,
            followed_sellers=followed_sellers,
            category_affinities={},
            user_vector=None,
            engaged_post_ids=engaged_post_ids,
            cart_product_ids=cart_product_ids,
            ordered_product_ids=ordered_product_ids,
            avg_watch_pct=0.0,
            total_interactions=0
        )

    # 5. Compute Category Affinities & User Preference Vector
    category_scores: Dict[str, float] = {}
    weighted_vectors: List[np.ndarray] = []
    vector_weights: List[float] = []

    # Map posts to their category and embedding
    all_interacting_post_ids = list(engaged_post_ids.union(viewed_posts_map.keys()))
    if all_interacting_post_ids:
        posts_lookup = {p["_id"]: p for p in db.posts.find({"_id": {"$in": all_interacting_post_ids}})}
        embeddings_lookup = {e["post_id"]: np.array(e["embedding"], dtype=float) for e in db.postembeddings.find({"post_id": {"$in": all_interacting_post_ids}})}

        for eng in engagements_docs:
            p_id = eng.get("post_id")
            action = eng.get("action", "like")
            weight = ACTION_WEIGHTS.get(action, 1.0)
            post = posts_lookup.get(p_id)
            if post:
                cat = post.get("category_id")
                if cat:
                    category_scores[cat] = category_scores.get(cat, 0.0) + weight

            if p_id in embeddings_lookup:
                weighted_vectors.append(embeddings_lookup[p_id])
                vector_weights.append(weight)

        for p_id, watch_pct in viewed_posts_map.items():
            post = posts_lookup.get(p_id)
            if post:
                cat = post.get("category_id")
                # Watch time > 70% is a strong positive signal
                watch_weight = watch_pct * 1.5 if watch_pct > 0.7 else watch_pct * 0.5
                if cat:
                    category_scores[cat] = category_scores.get(cat, 0.0) + watch_weight
                if p_id in embeddings_lookup:
                    weighted_vectors.append(embeddings_lookup[p_id])
                    vector_weights.append(watch_weight)

    # Commerce category reinforcement (cart = 3.0, order = 5.0)
    all_prod_ids = list(cart_product_ids.union(ordered_product_ids))
    if all_prod_ids:
        prods = {p["_id"]: p for p in db.products.find({"_id": {"$in": all_prod_ids}})}
        for c_id in cart_product_ids:
            p = prods.get(c_id)
            if p and "category_id" in p:
                category_scores[p["category_id"]] = category_scores.get(p["category_id"], 0.0) + 3.0
        for o_id in ordered_product_ids:
            p = prods.get(o_id)
            if p and "category_id" in p:
                category_scores[p["category_id"]] = category_scores.get(p["category_id"], 0.0) + 5.0

    # Normalize category affinities to sum to 1.0
    total_cat_score = sum(category_scores.values())
    normalized_affinities = {
        cat: round(score / total_cat_score, 4) for cat, score in category_scores.items()
    } if total_cat_score > 0 else {}

    # Synthesize User Vector via Weighted Average
    user_vector = None
    if weighted_vectors and vector_weights:
        weights_arr = np.array(vector_weights)
        norm_weights = weights_arr / (np.sum(weights_arr) + 1e-8)
        stacked = np.stack(weighted_vectors)
        centroid = np.sum(stacked * norm_weights[:, None], axis=0)
        norm = np.linalg.norm(centroid)
        if norm > 0:
            user_vector = centroid / norm

    return UserProfile(
        user_id=user_id,
        is_cold_start=False,
        followed_sellers=followed_sellers,
        category_affinities=normalized_affinities,
        user_vector=user_vector,
        engaged_post_ids=engaged_post_ids,
        cart_product_ids=cart_product_ids,
        ordered_product_ids=ordered_product_ids,
        avg_watch_pct=avg_watch,
        total_interactions=total_interactions
    )
