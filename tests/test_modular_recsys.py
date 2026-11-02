"""
Comprehensive Unit & Integration Test Suite for the Modular RecSys Engine.
Covers all Section 7 endpoints, individual recommenders, hybrid scoring formula,
cold-start scenarios, and offline evaluation benchmarks.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.utils.normalization import min_max_normalize, sigmoid_normalize, log_scale_normalize, clip_score
from backend.app.utils.scoring import cosine_similarity, compute_freshness_decay, combine_hybrid_scores
from backend.app.services.hybrid_recommender import HybridRecommender
from backend.app.services.evaluation_service import EvaluationService


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_normalization_and_scoring_utilities():
    # Min-max
    assert min_max_normalize(50, 0, 100) == 0.5
    assert min_max_normalize(150, 0, 100) == 1.0
    assert min_max_normalize(-10, 0, 100) == 0.0

    # Sigmoid
    assert 0.0 <= sigmoid_normalize(0.0) <= 1.0

    # Cosine Similarity
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [-1.0, 0.0, 0.0]
    assert pytest.approx(cosine_similarity(v1, v2), 0.01) == 1.0
    assert pytest.approx(cosine_similarity(v1, v3), 0.01) == 0.0

    # Freshness Decay
    decay = compute_freshness_decay(None, half_life_days=7.0)
    assert 0.0 <= decay <= 1.0

    # Hybrid Score combination
    score = combine_hybrid_scores(
        content_sim=0.8,
        user_engagement=0.6,
        social_rel=0.9,
        commerce_rel=0.7,
        popularity=0.5,
        freshness=0.4
    )
    expected = (
        0.30 * 0.8 +
        0.20 * 0.6 +
        0.15 * 0.9 +
        0.15 * 0.7 +
        0.10 * 0.5 +
        0.10 * 0.4
    )
    assert pytest.approx(score, 0.001) == expected


def test_all_fastapi_endpoints(client):
    # 1. Health
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"
    assert "database" in r.json()

    # 2. Users
    r = client.get("/api/users")
    assert r.status_code == 200
    users = r.json()
    assert len(users) >= 4
    sample_user = users[0]["user_id"]

    # 3. Posts
    r = client.get("/api/posts?limit=5")
    assert r.status_code == 200
    assert len(r.json()["posts"]) == 5

    # 4. Feed path param: GET /api/feed/{user_id}
    r = client.get(f"/api/feed/{sample_user}?limit=10")
    assert r.status_code == 200
    feed_data = r.json()
    assert feed_data["user_id"] == sample_user
    assert len(feed_data["posts"]) <= 10
    # Every post must contain components & explanation
    for post in feed_data["posts"]:
        assert 0.0 <= post["final_score"] <= 1.0
        assert "components" in post
        assert "explanation" in post
        assert len(post["explanation"]) > 0

    # 5. Recommendations: GET /api/recommendations/{user_id}
    r = client.get(f"/api/recommendations/{sample_user}?limit=8")
    assert r.status_code == 200
    assert len(r.json()["posts"]) <= 8

    # 6. Explanations: GET /api/recommendations/{user_id}/explanations
    r = client.get(f"/api/recommendations/{sample_user}/explanations?limit=5")
    assert r.status_code == 200
    explanations = r.json()
    assert explanations["count"] > 0
    assert len(explanations["recommendations"][0]["reasons"]) > 0

    # 7. Trending: GET /api/trending
    r = client.get("/api/trending?limit=6")
    assert r.status_code == 200
    assert "posts" in r.json()
    assert "trending_categories" in r.json()

    # 8. Analytics: GET /api/analytics
    r = client.get("/api/analytics")
    assert r.status_code == 200
    analytics = r.json()
    assert "metrics" in analytics
    assert "category_distribution" in analytics
    assert "benchmark_evaluation" in analytics

    # 9. User Interests: GET /api/user/{user_id}/interests
    r = client.get(f"/api/user/{sample_user}/interests")
    assert r.status_code == 200
    interests = r.json()
    assert interests["user_id"] == sample_user
    assert "top_categories" in interests
    assert "shopping_categories" in interests

    # 10. Product Recommendations: GET /api/products/recommendations/{user_id}
    r = client.get(f"/api/products/recommendations/{sample_user}?limit=6")
    assert r.status_code == 200
    assert len(r.json()["products"]) > 0

    # 11. Refresh Feed: POST /api/recommendations/refresh/{user_id}
    r = client.post(f"/api/recommendations/refresh/{sample_user}", json={
        "weights": {
            "content": 0.40,
            "engagement": 0.10,
            "social": 0.20,
            "commerce": 0.10,
            "popularity": 0.10,
            "freshness": 0.10
        },
        "limit": 10
    })
    assert r.status_code == 200
    refreshed = r.json()
    assert refreshed["weights_used"]["content"] == 0.40


def test_cold_start_handling():
    hybrid_engine = HybridRecommender()
    
    # 1. Cold start new user
    feed_newbie = hybrid_engine.get_feed(user_id="user_newbie_06", limit=10)
    assert feed_newbie.cold_start is True
    assert feed_newbie.cold_start_type == "new_user"
    assert len(feed_newbie.posts) > 0
    # Feed should not be empty and must include popularity/exploration explanations
    for p in feed_newbie.posts:
        assert len(p.explanation) > 0

    # 2. Feed personalization differentiation between 2 users
    feed_fashion = hybrid_engine.get_feed(user_id="user_fashion_01", limit=10)
    feed_tech = hybrid_engine.get_feed(user_id="user_tech_02", limit=10)
    
    fashion_cats = [p.category for p in feed_fashion.posts[:5]]
    tech_cats = [p.category for p in feed_tech.posts[:5]]
    # Personalization check: fashion user should receive fashion items, tech user tech items
    assert fashion_cats != tech_cats


def test_offline_evaluator_benchmark():
    eval_svc = EvaluationService()
    report = eval_svc.run_benchmark(k=10)
    assert report["evaluation_k"] == 10
    assert "comparison" in report
    assert "Hybrid" in report["comparison"]
    assert "Popularity" in report["comparison"]
    assert "Content-Based" in report["comparison"]
    assert "Collaborative" in report["comparison"]
    
    hybrid_metrics = report["comparison"]["Hybrid"]
    assert hybrid_metrics["NDCG@10"] > 0.0
    assert hybrid_metrics["Precision@10"] > 0.0
    assert hybrid_metrics["Catalog Coverage"] > 0.0
