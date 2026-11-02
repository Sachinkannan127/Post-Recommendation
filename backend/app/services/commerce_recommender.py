"""
Commerce-Based Recommendation Service.
Leverages cart items, past orders, and pinned product category alignment
to score shopping intent and commercial relevance.
"""
from typing import Dict, List, Optional, Set
from collections import Counter
from backend.app.database.mongodb import get_database
from backend.app.utils.normalization import clip_score


class CommerceRecommender:
    def __init__(self):
        self.db = get_database()

    def get_user_commerce_profile(self, user_id: str) -> Dict[str, float]:
        """
        Aggregate category shopping affinities from cart items and past orders.
        Cart items weighted 1.5, historical orders weighted 2.0.
        """
        category_weights = Counter()
        
        # Carts
        for cart in self.db.carts.find({"user_id": user_id}):
            prod_id = cart.get("product_id")
            if prod_id:
                prod = self.db.products.find_one({"product_id": prod_id})
                if prod and prod.get("category"):
                    category_weights[prod["category"]] += 1.5

        # Orders
        for order in self.db.orders.find({"user_id": user_id}):
            for item in order.get("items", []):
                prod_id = item.get("product_id")
                if prod_id:
                    prod = self.db.products.find_one({"product_id": prod_id})
                    if prod and prod.get("category"):
                        category_weights[prod["category"]] += 2.0

        total = sum(category_weights.values())
        if total == 0:
            return {}
            
        return {cat: weight / total for cat, weight in category_weights.items()}

    def score_post(
        self,
        post_category: Optional[str],
        has_pinned_product: bool,
        pinned_product_category: Optional[str],
        commerce_profile: Dict[str, float]
    ) -> float:
        """
        Compute commerce relevance score in [0.0, 1.0].
        """
        if not commerce_profile:
            # Baseline commerce score for posts with shoppable pinned products
            return 0.35 if has_pinned_product else 0.15

        target_cat = pinned_product_category or post_category
        cat_affinity = commerce_profile.get(target_cat, 0.0) if target_cat else 0.0

        # Base score from category affinity (0.0 to 0.70)
        score = cat_affinity * 0.70

        # Pinned shoppable product bonus (+0.30 if aligned, +0.15 general)
        if has_pinned_product:
            if cat_affinity > 0.1:
                score += 0.30
            else:
                score += 0.15
        else:
            if cat_affinity > 0.1:
                score += 0.10

        return clip_score(score)

    def score_candidates_batch(
        self,
        user_id: str,
        candidates: List[Dict[str, Any]],
        products_map: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, float]:
        """
        candidates: list of post dicts
        """
        profile = self.get_user_commerce_profile(user_id)
        scores = {}
        
        for post in candidates:
            pid = post.get("post_id")
            cat = post.get("category")
            prod_id = post.get("product_id")
            has_prod = bool(prod_id)
            
            prod_cat = None
            if has_prod:
                if products_map and prod_id in products_map:
                    prod_cat = products_map[prod_id].get("category")
                else:
                    prod = self.db.products.find_one({"product_id": prod_id})
                    if prod:
                        prod_cat = prod.get("category")

            scores[pid] = self.score_post(cat, has_prod, prod_cat, profile)

        return scores
