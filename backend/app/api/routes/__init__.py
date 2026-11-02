"""
API Router Aggregator.
Combines modular route subpackages (feed, recommendations, analytics, products)
and exposes system endpoints (/health, /users, /posts, /interaction).
"""
import time
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Body
from pydantic import BaseModel

from backend.app.api.routes.feed import router as feed_router
from backend.app.api.routes.recommendations import router as recs_router
from backend.app.api.routes.analytics import router as analytics_router
from backend.app.api.routes.products import router as products_router

from backend.app.database.mongodb import get_database, get_db_manager
from backend.app.repositories.users_repository import UsersRepository
from backend.app.repositories.posts_repository import PostsRepository
from backend.app.repositories.interactions_repository import InteractionsRepository
from backend.app.models.schemas import InteractionRequest, InteractionResponse

router = APIRouter()

# Include sub-routers
router.include_router(feed_router)
router.include_router(recs_router)
router.include_router(analytics_router)
router.include_router(products_router)

db = get_database()
db_manager = get_db_manager()
users_repo = UsersRepository()
posts_repo = PostsRepository()
interactions_repo = InteractionsRepository()


@router.get("/health")
def health_check():
    """
    Health check returning system and MongoDB Atlas connection status.
    """
    start = time.perf_counter()
    diag = db_manager.get_diagnostics()
    latency_ms = round((time.perf_counter() - start) * 1000.0, 2)
    return {
        "status": "healthy",
        "engine": "Hybrid AI Social Commerce Recommendation Engine v2.0",
        "database": diag,
        "latency_ms": latency_ms
    }


@router.get("/users")
def get_users():
    """
    Get all active users with their commerce persona profiles.
    """
    try:
        return users_repo.get_all_users()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts")
def get_posts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: Optional[str] = Query(None)
):
    """
    Get raw catalog posts with metrics and pinned products.
    """
    try:
        posts = posts_repo.get_all_posts(limit=limit, offset=offset, category=category)
        pids = [p["post_id"] for p in posts if "post_id" in p]
        metrics = posts_repo.get_post_metrics_batch(pids)
        product_ids = [p.get("product_id") for p in posts if p.get("product_id")]
        products = posts_repo.get_pinned_products_batch(product_ids)

        result = []
        for p in posts:
            pid = p.get("post_id")
            m = metrics.get(pid, {})
            p_copy = dict(p)
            p_copy["like_count"] = m.get("likes", 0)
            p_copy["comment_count"] = m.get("comments", 0)
            p_copy["share_count"] = m.get("shares", 0)
            p_copy["view_count"] = m.get("views", 0)
            p_copy["pinned_product"] = products.get(p.get("product_id"))
            result.append(p_copy)

        return {
            "count": len(result),
            "offset": offset,
            "posts": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interaction", response_model=InteractionResponse)
@router.post("/interactions/engage")
def record_user_interaction(payload: InteractionRequest):
    """
    Record live interaction (like, bookmark, share, view, add_to_cart).
    Updates user taste profile and engagement metrics in real-time.
    """
    success = interactions_repo.record_interaction(
        user_id=payload.user_id,
        post_id=payload.post_id,
        interaction_type=payload.interaction_type
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to record interaction or unknown type")

    return {
        "status": "success",
        "success": True,
        "user_id": payload.user_id,
        "post_id": payload.post_id,
        "interaction_type": payload.interaction_type,
        "message": f"Recorded '{payload.interaction_type}' on post '{payload.post_id}'."
    }


class ReconnectRequest(BaseModel):
    uri: str
    db_name: Optional[str] = "social_commerce_db"


@router.post("/reconnect")
def reconnect_database(payload: ReconnectRequest):
    """
    Live reconnect to a custom MongoDB Atlas URI.
    """
    success, msg = db_manager.reconnect(payload.uri, payload.db_name)
    return {
        "success": success,
        "message": msg,
        "diagnostics": db_manager.get_diagnostics()
    }
