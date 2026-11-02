"""
Comprehensive Unit & Integration Test Suite for NextGen Recommendation Engine.
Tests:
- Database connectivity & fallback
- User Profile feature extraction
- Candidate generation across multiple channels
- Multi-factor ranking, time decay, fatigue penalty, and explainability
- Diversity re-ranking and creator frequency capping
- Product recommendation engine (stretch goal)
- Offline evaluation metrics (NDCG, Hit Rate, Diversity, Latency)
- FastAPI REST endpoints
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.db.connection import get_db, get_db_manager
from backend.app.db.seed_data import seed_database
from backend.app.core.user_profile import build_user_profile
from backend.app.core.candidate_generator import CandidateGenerator
from backend.app.core.ranker import Ranker, RankingWeights
from backend.app.core.reranker import Reranker
from backend.app.core.recommender import FeedRecommender
from backend.app.core.product_recommender import ProductRecommender
from backend.app.core.evaluator import RecSysEvaluator
from backend.app.main import app


@pytest.fixture(scope="module")
def setup_db():
    db = get_db()
    seed_database(force_refresh=True)
    return db


def test_db_seeding_and_counts(setup_db):
    db = setup_db
    assert db.posts.count_documents({}) > 0
    assert db.postembeddings.count_documents({}) > 0
    assert db.products.count_documents({}) > 0
    assert db.sellerdetails.count_documents({}) > 0
    assert db.productcategories.count_documents({}) > 0


def test_user_profile_warm_vs_cold(setup_db):
    db = setup_db

    # Warm user
    warm_profile = build_user_profile("user_fashion_lover", db)
    assert not warm_profile.is_cold_start
    assert len(warm_profile.followed_sellers) > 0
    assert warm_profile.user_vector is not None
    assert len(warm_profile.category_affinities) > 0
    assert "cat_fashion" in warm_profile.category_affinities

    # Cold start user
    cold_profile = build_user_profile("user_cold_start", db)
    assert cold_profile.is_cold_start
    assert len(cold_profile.followed_sellers) == 0
    assert cold_profile.user_vector is None


def test_candidate_generation_channels(setup_db):
    db = setup_db
    cand_gen = CandidateGenerator(db)

    # Test warm user candidate retrieval
    warm_profile = build_user_profile("user_fashion_lover", db)
    candidates = cand_gen.generate_candidates(warm_profile, max_candidates=50)

    assert len(candidates) > 0
    channels = {c.channel for c in candidates}
    # Should retrieve from multiple channels
    assert any("social_graph" in ch or "vector_similarity" in ch or "trending" in ch for ch in channels)

    # Test cold start candidate retrieval
    cold_profile = build_user_profile("user_cold_start", db)
    cold_candidates = cand_gen.generate_candidates(cold_profile, max_candidates=50)
    assert len(cold_candidates) > 0
    # Cold start must rely on trending/viral channel
    assert all("trending" in c.channel for c in cold_candidates)


def test_ranking_and_explainability(setup_db):
    db = setup_db
    cand_gen = CandidateGenerator(db)
    ranker = Ranker()

    profile = build_user_profile("user_fashion_lover", db)
    candidates = cand_gen.generate_candidates(profile, max_candidates=30)
    scored = ranker.rank(profile, candidates)

    assert len(scored) > 0
    # Output must be sorted descending by total_score
    for i in range(len(scored) - 1):
        assert scored[i].total_score >= scored[i + 1].total_score

    # Top scored post must have explanations
    top_post = scored[0]
    assert len(top_post.explanations) > 0
    assert "social" in top_post.subscores
    assert "content" in top_post.subscores
    assert "commerce" in top_post.subscores
    assert "quality" in top_post.subscores


def test_diversity_reranker(setup_db):
    db = setup_db
    recommender = FeedRecommender(db)
    res = recommender.get_feed("user_fashion_lover", limit=10)

    feed = res["feed"]
    assert len(feed) > 0
    assert len(feed) <= 10

    # Verify no 3 consecutive posts from same seller
    seller_streak = 1
    last_seller = None
    for item in feed:
        seller_id = item["seller"]["id"]
        if seller_id == last_seller:
            seller_streak += 1
            assert seller_streak <= 2
        else:
            seller_streak = 1
        last_seller = seller_id


def test_product_recommender_stretch_goal(setup_db):
    db = setup_db
    prod_recommender = ProductRecommender(db)
    recs = prod_recommender.recommend_products("user_fashion_lover", limit=5)

    assert len(recs) > 0
    assert len(recs) <= 5
    # First item should match fashion category
    assert recs[0]["category_id"] == "cat_fashion"
    assert len(recs[0]["reasons"]) > 0


def test_offline_evaluator(setup_db):
    db = setup_db
    evaluator = RecSysEvaluator(db)
    res = evaluator.evaluate(k=5)

    agg = res["aggregate_metrics"]
    assert agg["mean_ndcg"] > 0.0
    assert agg["mean_hit_rate"] > 0.0
    assert agg["mean_intra_list_diversity"] > 0.0
    assert agg["latency_p95_ms"] < 100.0  # Fast sub-100ms response


def test_fastapi_endpoints():
    client = TestClient(app)

    # Health
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

    # Users
    r = client.get("/api/users")
    assert r.status_code == 200
    assert len(r.json()) >= 4

    # Feed
    r = client.get("/api/feed?user_id=user_fashion_lover&limit=10")
    assert r.status_code == 200
    data = r.json()
    assert "feed" in data
    assert len(data["feed"]) > 0
    assert "diagnostics" in data

    # Products Recs (Stretch Goal)
    r = client.get("/api/products/recommendations?user_id=user_fashion_lover&limit=4")
    assert r.status_code == 200
    assert len(r.json()["recommendations"]) > 0

    # Feedback Log
    r = client.post("/api/interactions/engage", json={
        "user_id": "user_fashion_lover",
        "post_id": "post_fashion_01",
        "interaction_type": "like"
    })
    assert r.status_code == 200
    assert r.json()["status"] == "success"

    # Evaluation
    r = client.get("/api/metrics/evaluate?k=5")
    assert r.status_code == 200
    assert "aggregate_metrics" in r.json()
