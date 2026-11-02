"""
Social-Based Recommendation Service.
Prioritizes posts from followed creators and evaluates creator social engagement signals.
"""
from typing import Dict, List, Optional, Set
from backend.app.database.mongodb import get_database
from backend.app.utils.normalization import clip_score


class SocialRecommender:
    def __init__(self):
        self.db = get_database()
        self._creator_metrics: Optional[Dict[str, float]] = None

    def _get_creator_engagement_rate(self, author_id: str) -> float:
        """Estimate creator tier & engagement strength from followers and likes."""
        if not author_id:
            return 0.1
        
        # Follower count signal
        follower_count = self.db.follows.count_documents({
            "$or": [{"creator_id": author_id}, {"seller_id": author_id}]
        })
        
        # Post metrics for this creator
        author_posts = list(self.db.posts.find({"author_id": author_id}, {"post_id": 1}))
        if not author_posts:
            return min(1.0, 0.2 + (follower_count * 0.1))
            
        pids = [p["post_id"] for p in author_posts if "post_id" in p]
        metrics = list(self.db.postmetrics.find({"post_id": {"$in": pids}}))
        
        total_eng = sum(m.get("likes", 0) + m.get("shares", 0) * 2 for m in metrics)
        avg_eng = total_eng / max(len(author_posts), 1)
        
        norm_eng = min(1.0, avg_eng / 250.0)
        norm_followers = min(1.0, follower_count / 10.0)
        
        return 0.6 * norm_eng + 0.4 * norm_followers

    def score_post(self, user_id: str, author_id: str, followed_creators: Optional[Set[str]] = None) -> float:
        """
        Calculate social relevance score in [0.0, 1.0].
        If creator is followed, score is substantially boosted.
        """
        if not author_id:
            return 0.1
            
        if followed_creators is None:
            follows_cursor = self.db.follows.find({"user_id": user_id})
            followed_creators = {
                doc.get("creator_id") or doc.get("seller_id") 
                for doc in follows_cursor 
                if doc.get("creator_id") or doc.get("seller_id")
            }

        is_followed = author_id in followed_creators
        creator_eng = self._get_creator_engagement_rate(author_id)
        
        if is_followed:
            # Followed creators get baseline 0.70 + up to 0.30 creator engagement
            score = 0.70 + (0.30 * creator_eng)
        else:
            # Unfollowed creators get up to 0.35 based on creator quality
            score = 0.10 + (0.25 * creator_eng)
            
        return clip_score(score)

    def score_candidates_batch(
        self,
        user_id: str,
        candidates: List[Dict[str, str]]
    ) -> Dict[str, float]:
        """
        candidates: list of dicts with 'post_id' and 'author_id'
        """
        follows_cursor = self.db.follows.find({"user_id": user_id})
        followed_creators = {
            doc.get("creator_id") or doc.get("seller_id") 
            for doc in follows_cursor 
            if doc.get("creator_id") or doc.get("seller_id")
        }
        
        return {
            item["post_id"]: self.score_post(user_id, item.get("author_id", ""), followed_creators)
            for item in candidates
        }
