"""
Product Recommendation Engine (Assignment Stretch Goal).
Bridges social video/post engagement with commerce purchasing intent:
- Pinned product affinity from engaged posts
- Category & price tier preference alignment
- Vector similarity using product_embedding
- Social seller trust multiplier
"""
from typing import Dict, List, Any, Optional
import numpy as np

from backend.app.core.user_profile import build_user_profile, UserProfile


class ProductRecommender:
    def __init__(self, db: Any):
        self.db = db

    def recommend_products(self, user_id: str, limit: int = 16, offset: int = 0) -> List[Dict[str, Any]]:
        profile = build_user_profile(user_id, self.db)
        all_products = list(self.db.products.find({}))
        if not all_products:
            return []

        # Find products pinned to posts the user has engaged with or watched
        engaged_pinned_prods = set()
        posts = list(self.db.posts.find({"_id": {"$in": list(profile.engaged_post_ids)}}))
        for p in posts:
            if p.get("pinned_product_id"):
                engaged_pinned_prods.add(p["pinned_product_id"])

        scored_products = []

        for prod in all_products:
            p_id = prod["_id"]
            cat_id = prod.get("category_id")
            seller_id = prod.get("seller_id")
            rating = prod.get("rating", 4.5)
            p_embedding = prod.get("product_embedding")

            reasons = []
            score = 0.0

            # 1. Social Commerce Cross-Pollination Signal
            if p_id in engaged_pinned_prods:
                score += 0.40
                reasons.append("Featured in posts you engaged with")

            # 2. Seller Trust Multiplier (Followed Creator)
            if seller_id in profile.followed_sellers:
                score += 0.25
                reasons.append("From a creator you follow")

            # 3. Category Affinity Match
            if cat_id in profile.category_affinities:
                aff = profile.category_affinities[cat_id]
                score += (aff * 0.35)
                if aff > 0.3:
                    reasons.append(f"Matches your interest in {cat_id.replace('cat_', '').title()}")

            # 4. Product Vector Similarity
            if profile.user_vector is not None and p_embedding is not None and len(p_embedding) == len(profile.user_vector):
                sim = float(np.dot(profile.user_vector, np.array(p_embedding, dtype=float)))
                score += (max(0.0, sim) * 0.30)

            # 5. Rating & Quality Baseline
            score += (rating / 5.0) * 0.15

            # Deduplication: slightly discount if already ordered
            if p_id in profile.ordered_product_ids:
                score *= 0.5
                reasons.append("Previously purchased")
            elif p_id in profile.cart_product_ids:
                score += 0.30
                reasons.append("Currently in your cart")

            # Cold start fallback reason
            if not reasons:
                reasons.append("Trending top-rated item in category")

            # Hydrate seller info
            seller_doc = self.db.sellerdetails.find_one({"_id": seller_id}) or {}

            scored_products.append({
                "product_id": p_id,
                "title": prod.get("title"),
                "description": prod.get("description"),
                "price": prod.get("price"),
                "rating": prod.get("rating"),
                "category_id": cat_id,
                "score": round(score, 4),
                "reasons": reasons[:2],
                "seller": {
                    "id": seller_doc.get("_id"),
                    "name": seller_doc.get("name"),
                    "handle": seller_doc.get("handle"),
                    "avatar": seller_doc.get("avatar")
                }
            })

        scored_products.sort(key=lambda x: x["score"], reverse=True)
        return scored_products[offset : offset + limit]


def recommend_products(user_id: str, limit: int = 16, offset: int = 0, db: Optional[Any] = None) -> List[Dict[str, Any]]:
    if db is None:
        from backend.app.database.mongodb import get_database
        db = get_database()
    engine = ProductRecommender(db)
    raw = engine.recommend_products(user_id=user_id, limit=limit, offset=offset)
    # Format for API route
    formatted = []
    for item in raw:
        prod_doc = db.products.find_one({"product_id": item["product_id"]}) or db.products.find_one({"_id": item["product_id"]}) or {}
        img = prod_doc.get("image_url") or "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600"
        formatted.append({
            "product_id": item["product_id"],
            "score": item["score"],
            "reason": item["reasons"][0] if item["reasons"] else "Popular product match",
            "product": {
                "product_id": item["product_id"],
                "title": item["title"] or prod_doc.get("title", "Curated Product"),
                "price": float(item["price"] or prod_doc.get("price", 49.99)),
                "image_url": img,
                "category": prod_doc.get("category", "General")
            }
        })
    return formatted
