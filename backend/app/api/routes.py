"""
FastAPI Route Handlers for Social Commerce Recommendation System.
"""
from fastapi import APIRouter, Query, Body, HTTPException
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from backend.app.db.connection import get_db, get_db_manager
from backend.app.core.recommender import FeedRecommender
from backend.app.core.product_recommender import ProductRecommender
from backend.app.core.evaluator import RecSysEvaluator
from backend.app.core.ranker import RankingWeights

router = APIRouter()


class InteractionRequest(BaseModel):
    user_id: str
    post_id: str
    interaction_type: str = Field(..., description="view, like, bookmark, share, cart, order")
    value: Optional[float] = Field(None, description="watch_percentage if view")


class ReconnectRequest(BaseModel):
    mongodb_uri: str
    db_name: Optional[str] = "social_commerce_db"


@router.get("/health")
def health_check():
    manager = get_db_manager()
    return {
        "status": "healthy",
        "service": "Social Commerce Recommendation Engine",
        "db": manager.get_status()
    }


@router.get("/users")
def get_user_personas():
    """Returns available test personas to test personalized feeds vs cold start."""
    return [
        {
            "id": "user_cold_start",
            "name": "New Visitor (Cold Start)",
            "role": "Brand New User",
            "description": "Zero previous interactions. Tests trending viral heuristics & category exploration.",
            "avatar": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100"
        },
        {
            "id": "user_fashion_lover",
            "name": "Elena Vance",
            "role": "Streetwear & Fashion Shopper",
            "description": "Follows Aurora Urban Studio, carted Cloud Fleece hoodie, purchased sneakers.",
            "avatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100"
        },
        {
            "id": "user_tech_geek",
            "name": "David Chen",
            "role": "Audiophile & Gadget Enthusiast",
            "description": "Watches audio gear reviews to 100% completion, follows SoundWave Labs & TechPulse.",
            "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100"
        },
        {
            "id": "user_beauty_seeker",
            "name": "Maya Lin",
            "role": "Skincare & Barrier Care Lover",
            "description": "Saved peptide barrier glaze tutorials, orders organic botanical serums.",
            "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100"
        },
        {
            "id": "user_fitness_buff",
            "name": "Alex Miller",
            "role": "Athletics & Home Gym Buff",
            "description": "Engaged with kettlebell workouts and compression tights from FitForge.",
            "avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100"
        }
    ]


@router.get("/feed")
def get_recommended_feed(
    user_id: str = Query("user_fashion_lover", description="User ID to personalize feed for"),
    limit: int = Query(20, ge=1, le=100),
    w_social: Optional[float] = Query(None, ge=0.0, le=1.0),
    w_content: Optional[float] = Query(None, ge=0.0, le=1.0),
    w_commerce: Optional[float] = Query(None, ge=0.0, le=1.0),
    w_quality: Optional[float] = Query(None, ge=0.0, le=1.0),
    enable_exploration: bool = Query(True, description="Enable serendipity bandit exploration")
):
    """
    Primary Deliverable: Post Feed Recommendation Engine.
    Generates intelligent personalized post ranking with explainable factors.
    """
    db = get_db()
    recommender = FeedRecommender(db)

    # Optional ranking weights override for interactive studio tuning
    weights_override = None
    if any(w is not None for w in [w_social, w_content, w_commerce, w_quality]):
        weights_override = RankingWeights(
            w_social=w_social if w_social is not None else 0.28,
            w_content=w_content if w_content is not None else 0.27,
            w_commerce=w_commerce if w_commerce is not None else 0.25,
            w_quality=w_quality if w_quality is not None else 0.20
        )

    feed_response = recommender.get_feed(
        user_id=user_id,
        limit=limit,
        weights_override=weights_override,
        enable_exploration=enable_exploration
    )
    return feed_response


@router.get("/products/recommendations")
def get_product_recommendations(
    user_id: str = Query("user_fashion_lover", description="User ID for product recommendations"),
    limit: int = Query(8, ge=1, le=24)
):
    """
    Optional Stretch Goal: Product Recommendation Component.
    Surfaces products based on browsing/purchase and social post interactions.
    """
    db = get_db()
    recommender = ProductRecommender(db)
    return {
        "user_id": user_id,
        "recommendations": recommender.recommend_products(user_id, limit=limit)
    }


@router.post("/interactions/engage")
def log_user_interaction(payload: InteractionRequest):
    """
    Real-time interaction logger: like, view, bookmark, share, cart, order.
    Dynamically recalculates feedback loop.
    """
    db = get_db()
    recommender = FeedRecommender(db)
    res = recommender.log_interaction(
        user_id=payload.user_id,
        post_id=payload.post_id,
        interaction_type=payload.interaction_type,
        value=payload.value
    )
    return res


@router.get("/metrics/evaluate")
def run_offline_evaluation(k: int = Query(10, ge=1, le=25)):
    """Runs automated offline evaluation benchmark (NDCG@K, Recall, Precision, Diversity, Latency)."""
    db = get_db()
    evaluator = RecSysEvaluator(db)
    return evaluator.evaluate(k=k)


@router.get("/db/status")
def get_database_status():
    """Returns database connection mode (Live MongoDB Atlas vs Local Mock)."""
    manager = get_db_manager()
    return manager.get_status()


@router.post("/db/reconnect")
def reconnect_database(payload: ReconnectRequest):
    """Dynamically connects to a new MongoDB connection string if provided."""
    manager = get_db_manager()
    success, msg = manager.reconnect(payload.mongodb_uri, payload.db_name)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to connect: {msg}")
    return {"status": "success", "message": msg, "db_status": manager.get_status()}
