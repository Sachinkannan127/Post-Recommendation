"""
Hybrid Recommendation Engine Service.
Orchestrates multi-channel candidate generation, hybrid multi-objective ranking,
diversity re-ranking, and evidence-based explanation generation.
"""
import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

from backend.app.config import settings
from backend.app.database.mongodb import get_database
from backend.app.models.schemas import ScoringComponents, RecommendationItem, FeedResponse
from backend.app.repositories.posts_repository import PostsRepository
from backend.app.repositories.users_repository import UsersRepository
from backend.app.repositories.interactions_repository import InteractionsRepository
from backend.app.services.content_recommender import ContentRecommender
from backend.app.services.collaborative_recommender import CollaborativeRecommender
from backend.app.services.social_recommender import SocialRecommender
from backend.app.services.commerce_recommender import CommerceRecommender
from backend.app.services.explanation_service import ExplanationService
from backend.app.core.user_profile import build_user_profile, UserProfile
from backend.app.utils.normalization import clip_score, log_scale_normalize
from backend.app.utils.scoring import compute_freshness_decay, combine_hybrid_scores


class HybridRecommender:
    def __init__(self):
        self.db = get_database()
        self.posts_repo = PostsRepository()
        self.users_repo = UsersRepository()
        self.interactions_repo = InteractionsRepository()
        
        self.content_service = ContentRecommender(self.posts_repo)
        self.collab_service = CollaborativeRecommender()
        self.social_service = SocialRecommender()
        self.commerce_service = CommerceRecommender()
        self.explanation_service = ExplanationService()

    def get_feed(
        self,
        user_id: str,
        limit: int = 15,
        weights: Optional[Dict[str, float]] = None,
        exploration_rate: Optional[float] = None,
        is_evaluation: bool = False
    ) -> FeedResponse:
        start_time = time.perf_counter()

        # 1. Configurable Weights Resolution
        w = {
            "content": weights.get("content", settings.WEIGHT_CONTENT) if weights else settings.WEIGHT_CONTENT,
            "engagement": weights.get("engagement", settings.WEIGHT_ENGAGEMENT) if weights else settings.WEIGHT_ENGAGEMENT,
            "social": weights.get("social", settings.WEIGHT_SOCIAL) if weights else settings.WEIGHT_SOCIAL,
            "commerce": weights.get("commerce", settings.WEIGHT_COMMERCE) if weights else settings.WEIGHT_COMMERCE,
            "popularity": weights.get("popularity", settings.WEIGHT_POPULARITY) if weights else settings.WEIGHT_POPULARITY,
            "freshness": weights.get("freshness", settings.WEIGHT_FRESHNESS) if weights else settings.WEIGHT_FRESHNESS,
        }

        # 2. Build User Profile & Detect Cold-Start
        profile: UserProfile = build_user_profile(user_id, self.db)
        is_new_user = profile.is_cold_start or profile.interaction_count < 2
        cold_start_type = "new_user" if is_new_user else None

        # 3. Candidate Generation
        # Retrieve active posts
        all_posts = list(self.db.posts.find({"is_active": True}))
        if not all_posts:
            all_posts = list(self.db.posts.find())

        # Exclude interacted posts unless in offline evaluation
        viewed_ids = set() if is_evaluation else set(profile.viewed_post_ids)
        candidates = [p for p in all_posts if (p.get("post_id") or p.get("_id")) not in viewed_ids]
        if len(candidates) < limit:
            candidates = all_posts  # fallback if catalog exhausted

        candidate_ids = [str(p.get("post_id") or p.get("_id")) for p in candidates if (p.get("post_id") or p.get("_id"))]
        
        # Batch load embeddings, metrics, and pinned products
        embeddings = self.posts_repo.get_post_embeddings_batch(candidate_ids)
        metrics = self.posts_repo.get_post_metrics_batch(candidate_ids)
        product_ids = [p.get("product_id") for p in candidates if p.get("product_id")]
        products_map = self.posts_repo.get_pinned_products_batch(product_ids)

        # Batch component scoring
        content_scores = self.content_service.score_candidates_batch(profile, candidate_ids, embeddings)
        collab_scores = self.collab_service.score_candidates_batch(user_id, candidate_ids)
        
        social_candidates = [{"post_id": str(p.get("post_id") or p.get("_id")), "author_id": str(p.get("author_id") or p.get("seller_id") or "")} for p in candidates]
        social_scores = self.social_service.score_candidates_batch(user_id, social_candidates)
        
        commerce_scores = self.commerce_service.score_candidates_batch(user_id, candidates, products_map)

        followed_creators = set(self.users_repo.get_user_follows(user_id))
        cart_categories = set(self.commerce_service.get_user_commerce_profile(user_id).keys())
        top_user_cat = max(profile.category_affinities.items(), key=lambda x: x[1])[0] if profile.category_affinities else None

        now = datetime.now(timezone.utc)
        scored_items = []

        for post in candidates:
            pid = str(post.get("post_id") or post.get("_id"))
            m = metrics.get(pid, {})
            likes = m.get("likes", 0)
            comments = m.get("comments", 0)
            shares = m.get("shares", 0)
            views = m.get("views", 0)

            # Component 1: Content Similarity
            c_sim = content_scores.get(pid, 0.25)
            # Component 2: User Engagement (Collaborative)
            c_eng = collab_scores.get(pid, 0.20)
            # Component 3: Social Relevance
            c_soc = social_scores.get(pid, 0.15)
            # Component 4: Commerce Relevance
            c_comm = commerce_scores.get(pid, 0.15)

            # Component 5: Popularity (normalized 0-1)
            raw_pop = (likes * 1.0) + (comments * 2.0) + (shares * 3.0) + (views * 0.05)
            c_pop = log_scale_normalize(raw_pop, max_expected=250.0)

            # Component 6: Freshness (exponential decay)
            created_at_dt = None
            if post.get("created_at"):
                try:
                    created_at_dt = datetime.fromisoformat(post["created_at"].replace("Z", "+00:00"))
                except Exception:
                    pass
            c_fresh = compute_freshness_decay(created_at_dt, half_life_days=settings.RECENCY_HALF_LIFE_DAYS, reference_time=now)

            # Cold-start new post handling: if post has no views or engagement yet
            is_new_post = (views == 0 and likes == 0)
            if is_new_post:
                # Cold-start exploration boost for unexposed high-quality posts
                c_fresh = max(c_fresh, 0.90)
                c_pop = 0.50

            # Compute Final Weighted Score
            final_score = combine_hybrid_scores(
                content_sim=c_sim,
                user_engagement=c_eng,
                social_rel=c_soc,
                commerce_rel=c_comm,
                popularity=c_pop,
                freshness=c_fresh,
                weights=w
            )

            # Cold start user adjustment: if new user, blend with trending popularity
            if is_new_user:
                final_score = (0.50 * c_pop) + (0.25 * c_fresh) + (0.15 * c_soc) + (0.10 * c_sim)

            # Apply fatigue penalty for recently viewed items if evaluated in feed
            if pid in profile.viewed_post_ids and not is_evaluation:
                final_score *= (1.0 - settings.FATIGUE_PENALTY)

            components = ScoringComponents(
                content_similarity=round(c_sim, 4),
                user_engagement=round(c_eng, 4),
                social_relevance=round(c_soc, 4),
                commerce_relevance=round(c_comm, 4),
                popularity=round(c_pop, 4),
                freshness=round(c_fresh, 4),
            )

            # Generate Transparent Explanation
            is_followed = post.get("author_id") in followed_creators
            has_cart_match = post.get("category") in cart_categories
            reasons = self.explanation_service.generate_reasons(
                post=post,
                components=components.model_dump(),
                is_followed=is_followed,
                creator_name=post.get("author_name"),
                user_top_category=top_user_cat,
                has_cart_match=has_cart_match
            )

            # Category resolution
            raw_cat = post.get("category") or post.get("category_id") or "General"
            cat_clean = raw_cat.replace("cat_", "").replace("_", " ").title() if isinstance(raw_cat, str) else "General"
            
            author_id = str(post.get("author_id") or post.get("seller_id") or "")
            author_name = post.get("author_name")
            if not author_name and author_id:
                seller = self.db.sellerdetails.find_one({"_id": author_id}) or self.db.sellerdetails.find_one({"seller_id": author_id}) or {}
                author_name = seller.get("name") or seller.get("handle") or f"Creator {author_id[-4:]}"

            img_url = post.get("image_url") or post.get("media_url") or "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600"
            pinned_prod_id = post.get("product_id") or post.get("pinned_product_id")
            pinned = products_map.get(pinned_prod_id) if pinned_prod_id else None

            scored_items.append({
                "post_id": pid,
                "caption": post.get("caption", ""),
                "image_url": img_url,
                "author_id": author_id,
                "author_name": author_name,
                "category": cat_clean,
                "like_count": likes,
                "comment_count": comments,
                "share_count": shares,
                "view_count": views,
                "created_at": post.get("created_at", now.isoformat()),
                "final_score": round(clip_score(final_score), 4),
                "components": components,
                "explanation": reasons,
                "pinned_product": pinned
            })

        # Sort descending by Final Score
        scored_items.sort(key=lambda x: x["final_score"], reverse=True)

        # 4. Diversity Re-ranking & Exploration
        reranked = self._apply_diversity_and_exploration(
            items=scored_items,
            limit=limit,
            exploration_rate=exploration_rate or settings.EXPLORATION_RATE
        )

        execution_time_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return FeedResponse(
            user_id=user_id,
            count=len(reranked),
            cold_start=is_new_user,
            cold_start_type=cold_start_type,
            execution_time_ms=execution_time_ms,
            weights_used=w,
            posts=[RecommendationItem(**item) for item in reranked]
        )

    def _apply_diversity_and_exploration(
        self,
        items: List[Dict[str, Any]],
        limit: int,
        exploration_rate: float
    ) -> List[Dict[str, Any]]:
        """
        Applies:
        1. Author Frequency Capping (max 2 consecutive from same creator).
        2. Category interleaving.
        3. Epsilon-greedy exploration for fresh discovery.
        """
        if not items:
            return []

        selected: List[Dict[str, Any]] = []
        pool = list(items)
        recent_authors: List[str] = []
        recent_categories: List[str] = []

        while pool and len(selected) < limit:
            # Epsilon exploration: randomly inject a diverse candidate
            if random.random() < exploration_rate and len(pool) > 5:
                # Pick a candidate outside the current top category
                alt_idx = next((i for i, x in enumerate(pool[3:]) if x["category"] not in recent_categories[-2:]), None)
                if alt_idx is not None:
                    chosen = pool.pop(alt_idx + 3)
                    selected.append(chosen)
                    recent_authors.append(chosen["author_id"])
                    recent_categories.append(chosen["category"])
                    continue

            # Greedy selection with author capping
            chosen_idx = None
            for idx, candidate in enumerate(pool):
                auth = candidate["author_id"]
                # Avoid 3 in a row from same author
                if len(recent_authors) >= 2 and recent_authors[-1] == auth and recent_authors[-2] == auth:
                    continue
                chosen_idx = idx
                break

            if chosen_idx is None:
                chosen_idx = 0

            chosen = pool.pop(chosen_idx)
            selected.append(chosen)
            recent_authors.append(chosen["author_id"])
            recent_categories.append(chosen["category"])

        return selected
