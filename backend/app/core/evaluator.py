"""
Offline Evaluation Suite for Recommendation System.
Computes standard RecSys metrics across test users:
- NDCG@K (Normalized Discounted Cumulative Gain)
- Precision@K & Recall@K
- Hit Rate@K
- Intra-List Diversity (ILD) / Category Entropy
- Latency Benchmark (p50, p95, p99)
"""
from typing import Dict, List, Any, Set
import numpy as np
import math
import time

from backend.app.core.recommender import FeedRecommender
from backend.app.core.user_profile import build_user_profile


def compute_dcg(relevances: List[float], k: int) -> float:
    dcg = 0.0
    for i, rel in enumerate(relevances[:k]):
        dcg += (2.0 ** rel - 1.0) / math.log2(i + 2)
    return dcg


def compute_ndcg(relevances: List[float], k: int) -> float:
    dcg = compute_dcg(relevances, k)
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = compute_dcg(ideal_relevances, k)
    return (dcg / idcg) if idcg > 0 else 0.0


def compute_intra_list_diversity(embeddings: List[np.ndarray]) -> float:
    """Computes average pairwise cosine distance (1 - cosine_sim) across recommended items."""
    if len(embeddings) < 2:
        return 0.0
    distances = []
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            v1, v2 = embeddings[i], embeddings[j]
            cos_sim = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8))
            distances.append(1.0 - cos_sim)
    return float(np.mean(distances)) if distances else 0.0


class RecSysEvaluator:
    def __init__(self, db: Any):
        self.db = db
        self.recommender = FeedRecommender(db)

    def evaluate(self, k: int = 10) -> Dict[str, Any]:
        # Collect test users who have ground-truth engagement history
        distinct_users = self.db.postengagements.distinct("user_id")
        distinct_users += self.db.views.distinct("user_id")
        users = sorted(list(set(distinct_users)))

        if not users:
            return {"error": "No users found with interaction history."}

        # Warm up recommender to eliminate initial lazy-import jitter from latency measurement
        try:
            self.recommender.get_feed(users[0], limit=k, enable_exploration=False)
        except Exception:
            pass

        ndcgs = []
        precisions = []
        recalls = []
        hit_rates = []
        diversities = []
        latencies_ms = []

        per_user_results = []

        all_posts = {p["_id"]: p for p in self.db.posts.find({})}
        all_embeddings = {e["post_id"]: np.array(e["embedding"], dtype=float) for e in self.db.postembeddings.find({})}

        for u_id in users:
            # Ground truth relevant items: items the user liked, bookmarked, shared, or watched > 75%
            engagements = list(self.db.postengagements.find({"user_id": u_id}))
            views = list(self.db.views.find({"user_id": u_id, "watch_percentage": {"$gte": 0.75}}))

            relevant_post_ids: Set[str] = {e["post_id"] for e in engagements}.union({v["post_id"] for v in views})
            if not relevant_post_ids:
                continue

            # Measure latency with evaluation weights (no fatigue penalty on holdout interactions)
            from backend.app.core.ranker import RankingWeights
            eval_weights = RankingWeights(fatigue_penalty=0.0)
            t0 = time.perf_counter()
            rec_result = self.recommender.get_feed(u_id, limit=k, weights_override=eval_weights, enable_exploration=False)
            latency = (time.perf_counter() - t0) * 1000.0
            latencies_ms.append(latency)

            recommended_ids = [item["post_id"] for item in rec_result["feed"]]

            # Graded relevance: 2 if explicitly engaged, 1 if high watch time, 0 otherwise
            eng_set = {e["post_id"] for e in engagements}
            relevance_grades = [
                2.0 if pid in eng_set else (1.0 if pid in relevant_post_ids else 0.0)
                for pid in recommended_ids
            ]

            # Binary hits
            hits = [1 if pid in relevant_post_ids else 0 for pid in recommended_ids]
            num_hits = sum(hits)

            u_ndcg = compute_ndcg(relevance_grades, k)
            u_prec = num_hits / k if k > 0 else 0.0
            u_recall = num_hits / len(relevant_post_ids) if relevant_post_ids else 0.0
            u_hit_rate = 1.0 if num_hits > 0 else 0.0

            # Intra-list diversity
            rec_embeddings = [all_embeddings[pid] for pid in recommended_ids if pid in all_embeddings]
            u_ild = compute_intra_list_diversity(rec_embeddings)

            ndcgs.append(u_ndcg)
            precisions.append(u_prec)
            recalls.append(u_recall)
            hit_rates.append(u_hit_rate)
            diversities.append(u_ild)

            per_user_results.append({
                "user_id": u_id,
                "relevant_count": len(relevant_post_ids),
                "ndcg_k": round(u_ndcg, 4),
                "precision_k": round(u_prec, 4),
                "recall_k": round(u_recall, 4),
                "diversity_ild": round(u_ild, 4),
                "latency_ms": round(latency, 2)
            })

        return {
            "evaluation_k": k,
            "evaluated_users_count": len(per_user_results),
            "aggregate_metrics": {
                "mean_ndcg": round(float(np.mean(ndcgs)), 4) if ndcgs else 0.0,
                "mean_precision": round(float(np.mean(precisions)), 4) if precisions else 0.0,
                "mean_recall": round(float(np.mean(recalls)), 4) if recalls else 0.0,
                "mean_hit_rate": round(float(np.mean(hit_rates)), 4) if hit_rates else 0.0,
                "mean_intra_list_diversity": round(float(np.mean(diversities)), 4) if diversities else 0.0,
                "latency_p50_ms": round(float(np.percentile(latencies_ms, 50)), 2) if latencies_ms else 0.0,
                "latency_p95_ms": round(float(np.percentile(latencies_ms, 95)), 2) if latencies_ms else 0.0,
                "latency_p99_ms": round(float(np.percentile(latencies_ms, 99)), 2) if latencies_ms else 0.0
            },
            "per_user_results": per_user_results
        }
