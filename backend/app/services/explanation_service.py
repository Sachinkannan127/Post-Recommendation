"""
Recommendation Explanation Service.
Synthesizes evidence-based, transparent explanations grounded in actual
component scores and database interaction records.
"""
from typing import Dict, List, Optional, Any


class ExplanationService:
    @staticmethod
    def generate_reasons(
        post: Dict[str, Any],
        components: Dict[str, float],
        is_followed: bool = False,
        creator_name: Optional[str] = None,
        user_top_category: Optional[str] = None,
        has_cart_match: bool = False
    ) -> List[str]:
        """
        Generate bullet reasons explaining why a post is recommended.
        Directly grounded in numerical scoring signals.
        """
        reasons: List[str] = []
        c_sim = components.get("content_similarity", 0.0)
        c_eng = components.get("user_engagement", 0.0)
        c_soc = components.get("social_relevance", 0.0)
        c_comm = components.get("commerce_relevance", 0.0)
        c_pop = components.get("popularity", 0.0)
        c_fresh = components.get("freshness", 0.0)
        
        category = post.get("category", "General")
        author = creator_name or post.get("author_name") or f"Creator {post.get('author_id', '')[-4:]}"

        # 1. Social Follow Evidence
        if is_followed:
            reasons.append(f"Published by {author}, whom you actively follow")
        elif c_soc > 0.45:
            reasons.append(f"Trending creator {author} with high community engagement")

        # 2. Content Similarity Evidence
        if c_sim >= 0.70:
            reasons.append(f"Strong content alignment ({c_sim:.0%}) with your taste in {category}")
        elif c_sim >= 0.50:
            reasons.append(f"Matches your recent aesthetic preferences in {category}")
        elif user_top_category and category.lower() == user_top_category.lower():
            reasons.append(f"Coincides with your primary category interest: {category}")

        # 3. Collaborative / User Engagement Evidence
        if c_eng >= 0.65:
            reasons.append("Highly rated by shoppers who have similar interaction patterns to you")
        elif c_eng >= 0.40:
            reasons.append("Engaged with by users with comparable taste profiles")

        # 4. Commerce Evidence
        if has_cart_match:
            reasons.append(f"Directly connects to products in your active shopping cart ({category})")
        elif c_comm >= 0.60:
            reasons.append(f"Features shoppable items relevant to your purchase and cart history")
        elif post.get("product_id") and c_comm >= 0.35:
            reasons.append("Includes a curated product available for instant checkout")

        # 5. Popularity / Freshness Signals
        if c_pop >= 0.75:
            reasons.append(f"Viral post currently trending across the social commerce feed")
        elif c_fresh >= 0.85:
            reasons.append("Freshly published today with rapid early engagement")

        # Fallback if no specific high thresholds were met (e.g. cold start exploration)
        if not reasons:
            reasons.append(f"Recommended for discovery to broaden your {category} feed")
            reasons.append("High overall platform engagement and visual quality")

        return reasons[:4]
