"""
Products Recommendation API Routes.
Provides personalized e-commerce product recommendations based on user browsing,
cart activity, and post-engagement affinities (Section 8 Screen 5).
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from backend.app.models.schemas import ProductRecommendationsResponse, ProductRecommendationItem
from backend.app.core.product_recommender import recommend_products
from backend.app.database.mongodb import get_database

router = APIRouter(tags=["products"])
db = get_database()


@router.get("/products/recommendations/{user_id}", response_model=ProductRecommendationsResponse)
def get_product_recommendations(
    user_id: str,
    limit: int = Query(16, ge=1, le=100, description="Number of products to recommend"),
    offset: int = Query(0, ge=0, description="Pagination offset for continuous product feed")
):
    """
    Personalized product recommendations based on shopping behavior and social affinities.
    """
    try:
        raw_recs = recommend_products(user_id=user_id, limit=limit, offset=offset, db=db)
        items = []
        for r in raw_recs:
            prod = r.get("product") or {}
            items.append(
                ProductRecommendationItem(
                    product_id=prod.get("product_id", r.get("product_id", "")),
                    title=prod.get("title", "Curated Commerce Product"),
                    price=float(prod.get("price", 49.99)),
                    image_url=prod.get("image_url", "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600"),
                    category=prod.get("category", "General"),
                    similarity_score=round(min(1.0, max(0.0, float(r.get("score", 0.75)) / 2.0)), 4),
                    reason=r.get("reason", "Matches your browsing and purchase history")
                )
            )

        return ProductRecommendationsResponse(
            user_id=user_id,
            count=len(items),
            products=items
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/recommendations", response_model=ProductRecommendationsResponse)
def get_product_recommendations_query(
    user_id: str = Query(..., description="Target user ID"),
    limit: int = Query(16, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    return get_product_recommendations(user_id=user_id, limit=limit, offset=offset)
