"""
Interactions Repository: Data Access Layer for Views, Engagements, Carts, and Orders.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from backend.app.database.mongodb import get_database


class InteractionsRepository:
    def __init__(self):
        self.db = get_database()

    def get_user_views(self, user_id: str) -> List[Dict[str, Any]]:
        return list(self.db.views.find({"user_id": user_id}))

    def get_user_engagements(self, user_id: str) -> List[Dict[str, Any]]:
        return list(self.db.postengagements.find({"user_id": user_id}))

    def get_user_comments(self, user_id: str) -> List[Dict[str, Any]]:
        return list(self.db.postcomments.find({"user_id": user_id}))

    def get_user_carts(self, user_id: str) -> List[Dict[str, Any]]:
        return list(self.db.carts.find({"user_id": user_id}))

    def get_user_orders(self, user_id: str) -> List[Dict[str, Any]]:
        return list(self.db.orders.find({"user_id": user_id}))

    def record_interaction(self, user_id: str, post_id: str, interaction_type: str) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        
        if interaction_type in ("like", "bookmark", "share", "click"):
            self.db.postengagements.insert_one({
                "user_id": user_id,
                "post_id": post_id,
                "engagement_type": interaction_type,
                "timestamp": now
            })
            # Increment metric
            inc_field = f"{interaction_type}s" if not interaction_type.endswith("s") else interaction_type
            self.db.postmetrics.update_one(
                {"post_id": post_id},
                {"$inc": {inc_field: 1}},
                upsert=True
            )
            return True
            
        elif interaction_type == "view":
            self.db.views.insert_one({
                "user_id": user_id,
                "post_id": post_id,
                "completion_rate": 0.85,
                "viewed_at": now
            })
            self.db.postmetrics.update_one(
                {"post_id": post_id},
                {"$inc": {"views": 1}},
                upsert=True
            )
            return True

        elif interaction_type == "add_to_cart":
            # Lookup post to find pinned product
            post = self.db.posts.find_one({"post_id": post_id})
            product_id = post.get("product_id") if post else f"prod_{post_id}"
            self.db.carts.insert_one({
                "user_id": user_id,
                "product_id": product_id,
                "quantity": 1,
                "added_at": now
            })
            return True
            
        return False
