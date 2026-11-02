"""
Feed API Routes.
Provides personalized post feeds using the Hybrid Recommendation Engine.
"""
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from backend.app.services.hybrid_recommender import HybridRecommender
from backend.app.models.schemas import FeedResponse

router = APIRouter(tags=["feed"])
hybrid_engine = HybridRecommender()


@router.get("/feed/{user_id}", response_model=FeedResponse)
def get_user_feed(
    user_id: str,
    limit: int = Query(15, ge=1, le=50, description="Number of posts to return"),
    w_content: Optional[float] = Query(None, ge=0.0, le=1.0),
    w_engagement: Optional[float] = Query(None, ge=0.0, le=1.0),
    w_social: Optional[float] = Query(None, ge=0.0, le=1.0),
    w_commerce: Optional[float] = Query(None, ge=0.0, le=1.0),
    w_popularity: Optional[float] = Query(None, ge=0.0, le=1.0),
    w_freshness: Optional[float] = Query(None, ge=0.0, le=1.0),
):
    """
    Generate personalized feed for a given user.
    Uses multi-objective hybrid scoring and diversity reranking.
    """
    weights = None
    if any(w is not None for w in [w_content, w_engagement, w_social, w_commerce, w_popularity, w_freshness]):
        weights = {
            "content": w_content if w_content is not None else 0.30,
            "engagement": w_engagement if w_engagement is not None else 0.20,
            "social": w_social if w_social is not None else 0.15,
            "commerce": w_commerce if w_commerce is not None else 0.15,
            "popularity": w_popularity if w_popularity is not None else 0.10,
            "freshness": w_freshness if w_freshness is not None else 0.10,
        }

    try:
        return hybrid_engine.get_feed(user_id=user_id, limit=limit, weights=weights)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate feed: {str(e)}")


@router.get("/feed", response_model=FeedResponse)
def get_user_feed_query(
    user_id: str = Query(..., description="Target User ID"),
    limit: int = Query(15, ge=1, le=50, description="Number of posts to return"),
    w_content: Optional[float] = Query(None, ge=0.0, le=1.0),
    w_engagement: Optional[float] = Query(None, ge=0.0, le=1.0),
    w_social: Optional[float] = Query(None, ge=0.0, le=1.0),
    w_commerce: Optional[float] = Query(None, ge=0.0, le=1.0),
    w_popularity: Optional[float] = Query(None, ge=0.0, le=1.0),
    w_freshness: Optional[float] = Query(None, ge=0.0, le=1.0),
):
    return get_user_feed(
        user_id=user_id,
        limit=limit,
        w_content=w_content,
        w_engagement=w_engagement,
        w_social=w_social,
        w_commerce=w_commerce,
        w_popularity=w_popularity,
        w_freshness=w_freshness,
    )
