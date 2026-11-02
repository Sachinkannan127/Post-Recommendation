"""
Posts Repository: Data Access Layer for Posts, Embeddings, Metrics, and Products.
"""
from typing import Dict, List, Optional, Any
from backend.app.database.mongodb import get_database


class PostsRepository:
    def __init__(self):
        self.db = get_database()

    def get_all_posts(self, limit: int = 100, offset: int = 0, category: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {"is_active": True} if "is_active" in self.db.posts.find_one({}) or {} else {}
        if category:
            query["category"] = category
        return list(self.db.posts.find(query).skip(offset).limit(limit))

    def get_post_by_id(self, post_id: str) -> Optional[Dict[str, Any]]:
        return self.db.posts.find_one({"post_id": post_id}) or self.db.posts.find_one({"_id": post_id})

    def get_post_embeddings_batch(self, post_ids: Optional[List[str]] = None) -> Dict[str, List[float]]:
        query = {"post_id": {"$in": post_ids}} if post_ids else {}
        cursor = self.db.postembeddings.find(query)
        embedding_map = {}
        for doc in cursor:
            pid = doc.get("post_id")
            emb = doc.get("embedding")
            if pid and isinstance(emb, list):
                embedding_map[pid] = emb
        return embedding_map

    def get_post_metrics_batch(self, post_ids: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        query = {"post_id": {"$in": post_ids}} if post_ids else {}
        cursor = self.db.postmetrics.find(query)
        metrics_map = {}
        for doc in cursor:
            pid = doc.get("post_id")
            if pid:
                metrics_map[pid] = doc
        return metrics_map

    def get_pinned_products_batch(self, product_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        if not product_ids:
            return {}
        cursor = self.db.products.find({"product_id": {"$in": product_ids}})
        product_map = {}
        for doc in cursor:
            pid = doc.get("product_id")
            if pid:
                product_map[pid] = doc
        return product_map

    def get_all_products(self, limit: int = 50, category: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {}
        if category:
            query["category"] = category
        return list(self.db.products.find(query).limit(limit))

    def get_trending_posts(self, limit: int = 10) -> List[Dict[str, Any]]:
        # Fetch posts with highest engagement rate / likes
        metrics = list(self.db.postmetrics.find().sort("likes", -1).limit(limit * 2))
        top_ids = [m.get("post_id") for m in metrics if m.get("post_id")]
        posts = list(self.db.posts.find({"post_id": {"$in": top_ids}}))
        
        # Merge metrics and sort by engagement
        metrics_dict = {m.get("post_id"): m for m in metrics}
        for p in posts:
            m = metrics_dict.get(p.get("post_id"), {})
            p["like_count"] = m.get("likes", 0)
            p["comment_count"] = m.get("comments", 0)
            p["share_count"] = m.get("shares", 0)
            p["view_count"] = m.get("views", 0)
            p["engagement_score"] = (p["like_count"] * 2 + p["comment_count"] * 3 + p["share_count"] * 4)
            
        posts.sort(key=lambda x: x.get("engagement_score", 0), reverse=True)
        return posts[:limit]
