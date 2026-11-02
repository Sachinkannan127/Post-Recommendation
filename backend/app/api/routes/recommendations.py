"""
Recommendations API Routes.
Provides recommendation rankings, detailed explanations, and cache refresh triggers.
"""
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Body
from backend.app.services.hybrid_recommender import HybridRecommender
from backend.app.models.schemas import (
    FeedResponse,
    ExplanationsResponse,
    PostExplanationItem,
    RefreshFeedRequest
)

router = APIRouter(tags=["recommendations"])
hybrid_engine = HybridRecommender()


@router.get("/recommendations/{user_id}", response_model=FeedResponse)
def get_recommendations(
    user_id: str,
    limit: int = Query(15, ge=1, le=50)
):
    """
    Get top personalized post recommendations for a user.
    """
    try:
        return hybrid_engine.get_feed(user_id=user_id, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/{user_id}/explanations", response_model=ExplanationsResponse)
def get_recommendation_explanations(
    user_id: str,
    limit: int = Query(10, ge=1, le=30)
):
    """
    Retrieve explainability breakdowns and evidence reasons for each recommended item.
    """
    try:
        feed = hybrid_engine.get_feed(user_id=user_id, limit=limit)
        items = [
            PostExplanationItem(
                post_id=p.post_id,
                caption=p.caption,
                final_score=p.final_score,
                components=p.components,
                reasons=p.explanation
            )
            for p in feed.posts
        ]
        return ExplanationsResponse(
            user_id=user_id,
            count=len(items),
            recommendations=items
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommendations/refresh/{user_id}", response_model=FeedResponse)
def refresh_user_recommendations(
    user_id: str,
    payload: Optional[RefreshFeedRequest] = Body(default=None)
):
    """
    Invalidate cached session rankings and generate refreshed recommendations.
    Accepts customized weight overrides.
    """
    weights_dict = None
    limit = 15
    if payload:
        limit = payload.limit or 15
        if payload.weights:
            weights_dict = payload.weights.model_dump(exclude_unset=True)

    try:
        return hybrid_engine.get_feed(user_id=user_id, limit=limit, weights=weights_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
