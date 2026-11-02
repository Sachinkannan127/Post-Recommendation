"""
Collaborative Filtering Recommendation Service.
Analyzes user interaction patterns (likes, comments, bookmarks, shares, views)
and discovers posts engaged with by similar users.
"""
from typing import Dict, List, Optional, Set
from collections import defaultdict
from backend.app.database.mongodb import get_database
from backend.app.utils.normalization import clip_score


class CollaborativeRecommender:
    def __init__(self):
        self.db = get_database()
        self._user_item_matrix: Optional[Dict[str, Set[str]]] = None
        self._item_user_matrix: Optional[Dict[str, Set[str]]] = None

    def _build_matrix(self):
        """Construct user-item interaction sets from views and engagements."""
        user_items = defaultdict(set)
        item_users = defaultdict(set)

        for doc in self.db.postengagements.find({}):
            uid = doc.get("user_id")
            pid = doc.get("post_id")
            if uid and pid:
                user_items[uid].add(pid)
                item_users[pid].add(uid)

        for doc in self.db.views.find({}):
            uid = doc.get("user_id")
            pid = doc.get("post_id")
            if uid and pid:
                user_items[uid].add(pid)
                item_users[pid].add(uid)

        self._user_item_matrix = user_items
        self._item_user_matrix = item_users

    def _get_jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0

    def score_post(self, user_id: str, post_id: str) -> float:
        """
        Calculate collaborative preference score in [0.0, 1.0].
        Computes neighbor-weighted affinity for candidate post.
        """
        if self._user_item_matrix is None:
            self._build_matrix()

        user_history = self._user_item_matrix.get(user_id, set())
        if not user_history:
            return 0.20  # Cold-start baseline

        engaged_users = self._item_user_matrix.get(post_id, set())
        if not engaged_users:
            return 0.10

        # Sum similarities with other users who engaged with this post
        total_sim = 0.0
        count = 0
        for other_uid in engaged_users:
            if other_uid == user_id:
                continue
            other_history = self._user_item_matrix.get(other_uid, set())
            sim = self._get_jaccard_similarity(user_history, other_history)
            if sim > 0:
                total_sim += sim
                count += 1

        if count == 0:
            return 0.15

        avg_sim = total_sim / count
        # Normalize and boost
        boosted = avg_sim * (1.0 + 0.1 * min(count, 5))
        return clip_score(boosted)

    def score_candidates_batch(self, user_id: str, candidate_ids: List[str]) -> Dict[str, float]:
        if self._user_item_matrix is None:
            self._build_matrix()
        return {pid: self.score_post(user_id, pid) for pid in candidate_ids}
