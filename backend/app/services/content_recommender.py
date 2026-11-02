"""
Content-Based Recommendation Service.
Uses the postembeddings collection and user taste profile vectors to calculate cosine similarity.
"""
from typing import Dict, List, Optional
import numpy as np
from backend.app.utils.scoring import cosine_similarity
from backend.app.utils.normalization import clip_score
from backend.app.repositories.posts_repository import PostsRepository
from backend.app.core.user_profile import build_user_profile, UserProfile


class ContentRecommender:
    def __init__(self, posts_repo: Optional[PostsRepository] = None):
        self.posts_repo = posts_repo or PostsRepository()

    def score_post(self, user_profile: UserProfile, post_id: str, post_embedding: Optional[List[float]]) -> float:
        """
        Calculate content similarity between user taste vector and candidate post embedding.
        Score normalized to [0.0, 1.0].
        """
        if not user_profile.embedding or not post_embedding:
            # Fallback to category affinity if embedding missing
            post = self.posts_repo.get_post_by_id(post_id)
            if post and post.get("category"):
                return clip_score(user_profile.category_affinities.get(post["category"], 0.2))
            return 0.25

        sim = cosine_similarity(user_profile.embedding, post_embedding)
        return clip_score(sim)

    def score_candidates_batch(
        self,
        user_profile: UserProfile,
        candidate_ids: List[str],
        embedding_map: Optional[Dict[str, List[float]]] = None
    ) -> Dict[str, float]:
        """Compute content similarity for a batch of candidate posts."""
        embeddings = embedding_map or self.posts_repo.get_post_embeddings_batch(candidate_ids)
        scores = {}
        for pid in candidate_ids:
            emb = embeddings.get(pid)
            scores[pid] = self.score_post(user_profile, pid, emb)
        return scores
