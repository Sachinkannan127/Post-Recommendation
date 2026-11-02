"""
Users Repository: Data Access Layer for User Profiles, Follows, and Personas.
"""
from typing import Dict, List, Optional, Any
from backend.app.database.mongodb import get_database


class UsersRepository:
    def __init__(self):
        self.db = get_database()

    def get_all_users(self) -> List[Dict[str, Any]]:
        # Distinct user IDs across views, follows, carts, engagements
        user_ids = set()
        for doc in self.db.views.find({}, {"user_id": 1}):
            if doc.get("user_id"):
                user_ids.add(doc["user_id"])
        for doc in self.db.postengagements.find({}, {"user_id": 1}):
            if doc.get("user_id"):
                user_ids.add(doc["user_id"])
        for doc in self.db.follows.find({}, {"user_id": 1}):
            if doc.get("user_id"):
                user_ids.add(doc["user_id"])
        for doc in self.db.carts.find({}, {"user_id": 1}):
            if doc.get("user_id"):
                user_ids.add(doc["user_id"])

        users = []
        persona_hints = {
            "user_fashion_01": ("Sophia Martinez", "Lover of sustainable chic, runway styles, and evening accessories", "Fashion Enthusiast"),
            "user_tech_02": ("Alex Chen", "Gadget reviewer, smart devices explorer, desk setup enthusiast", "Tech Reviewer"),
            "user_fitness_03": ("Marcus Vance", "Crossfit athlete, whey nutrition, gym wear and wellness tips", "Fitness Advocate"),
            "user_decor_04": ("Elena Rostova", "Bohemian interior decorator, ceramic pottery, modern minimalist", "Home Decorator"),
            "user_beauty_05": ("Priya Patel", "Korean skincare routine, cruelty-free cosmetic tutorials", "Beauty Influencer"),
            "user_newbie_06": ("Jordan Taylor", "Newcomer to social commerce exploring top curated feeds", "Cold-Start User"),
        }

        for uid in sorted(list(user_ids)):
            name, bio, role = persona_hints.get(uid, (f"Shopper {uid[-4:]}", "Active platform shopper and social creator follower", "Shopper"))
            users.append({
                "user_id": uid,
                "name": name,
                "bio": bio,
                "role": role,
                "avatar_url": f"https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80"
            })
        return users

    def get_user_follows(self, user_id: str) -> List[str]:
        cursor = self.db.follows.find({"user_id": user_id})
        return [doc.get("creator_id") or doc.get("seller_id") for doc in cursor if doc.get("creator_id") or doc.get("seller_id")]

    def get_creator_followers_count(self, creator_id: str) -> int:
        return self.db.follows.count_documents({"$or": [{"creator_id": creator_id}, {"seller_id": creator_id}]})
