"""
Re-ranking & Feed Polishing Engine.
Applies business rules, author frequency capping, category interleaving,
and epsilon-greedy serendipity exploration.
"""
from typing import List, Dict, Any, Optional
import random
from backend.app.core.ranker import ScoredPost


class Reranker:
    def __init__(
        self,
        max_consecutive_same_seller: int = 1,
        max_same_seller_total: int = 2,
        exploration_rate: float = 0.12  # Epsilon for bandit exploration
    ):
        self.max_consecutive_same_seller = max_consecutive_same_seller
        self.max_same_seller_total = max_same_seller_total
        self.exploration_rate = exploration_rate

    def rerank(
        self,
        scored_posts: List[ScoredPost],
        limit: int = 20,
        enable_exploration: bool = True
    ) -> List[ScoredPost]:
        if not scored_posts:
            return []

        selected: List[ScoredPost] = []
        remaining = list(scored_posts)
        seller_counts: Dict[str, int] = {}
        category_counts: Dict[str, int] = {}

        last_seller_id: Optional[str] = None
        last_category_id: Optional[str] = None

        while remaining and len(selected) < limit:
            best_idx = -1

            # Epsilon-greedy exploration: occasionally select a high-quality fresh post
            # from an unrepresented category
            is_explore_step = (
                enable_exploration
                and len(selected) >= 3
                and random.random() < self.exploration_rate
                and len(remaining) > 5
            )

            if is_explore_step:
                # Find candidate from an underrepresented category
                for i, sp in enumerate(remaining[3:]):
                    cat = sp.candidate.post_doc.get("category_id")
                    seller = sp.candidate.post_doc.get("seller_id")
                    if cat != last_category_id and seller_counts.get(seller, 0) < self.max_same_seller_total:
                        best_idx = i + 3
                        sp.explanations.append("Discovery pick to explore new styles")
                        break

            # If not exploring or no suitable explore candidate found, do diversity-constrained greedy selection
            if best_idx == -1:
                for i, sp in enumerate(remaining):
                    seller = sp.candidate.post_doc.get("seller_id")
                    cat = sp.candidate.post_doc.get("category_id")

                    # Avoid consecutive same seller
                    if seller == last_seller_id and len(remaining) > 2:
                        continue

                    # Respect max total posts per seller in feed
                    if seller_counts.get(seller, 0) >= self.max_same_seller_total and len(remaining) > 3:
                        continue

                    # Soft category diversity: avoid 3 in a row of the exact same category
                    if cat == last_category_id and category_counts.get(cat, 0) >= 2 and len(remaining) > 3:
                        continue

                    best_idx = i
                    break

            # Fallback to top scored if strict constraints blocked all remaining
            if best_idx == -1:
                best_idx = 0

            chosen = remaining.pop(best_idx)
            selected.append(chosen)

            # Update tracking counters
            c_seller = chosen.candidate.post_doc.get("seller_id", "")
            c_cat = chosen.candidate.post_doc.get("category_id", "")

            last_seller_id = c_seller
            last_category_id = c_cat

            seller_counts[c_seller] = seller_counts.get(c_seller, 0) + 1
            category_counts[c_cat] = category_counts.get(c_cat, 0) + 1

        return selected
