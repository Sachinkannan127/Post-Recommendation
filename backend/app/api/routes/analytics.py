"""
Analytics API Routes.
Provides trending posts, platform-wide metrics, model benchmark comparisons, and user interest profiles.
"""
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, Query
from backend.app.database.mongodb import get_database
from backend.app.repositories.posts_repository import PostsRepository
from backend.app.repositories.users_repository import UsersRepository
from backend.app.repositories.interactions_repository import InteractionsRepository
from backend.app.services.evaluation_service import EvaluationService
from backend.app.services.commerce_recommender import CommerceRecommender
from backend.app.core.user_profile import build_user_profile

router = APIRouter(tags=["analytics"])
db = get_database()
posts_repo = PostsRepository()
users_repo = UsersRepository()
interactions_repo = InteractionsRepository()
evaluation_service = EvaluationService()
commerce_service = CommerceRecommender()


@router.get("/trending")
def get_trending_posts(limit: int = Query(10, ge=1, le=50)):
    """
    Get top trending posts based on engagement velocity and interaction counts.
    """
    try:
        trending = posts_repo.get_trending_posts(limit=limit)
        # Category breakdown
        category_counts = {}
        for p in trending:
            cat = p.get("category", "General")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "count": len(trending),
            "posts": trending,
            "trending_categories": [
                {"category": k, "count": v}
                for k, v in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
def get_platform_analytics():
    """
    Platform-wide analytics:
    Total users, posts, products, interactions, average engagement rate,
    and offline recommendation algorithm benchmark comparison.
    """
    try:
        total_posts = db.posts.count_documents({})
        total_products = db.products.count_documents({})
        total_views = db.views.count_documents({})
        total_engagements = db.postengagements.count_documents({})
        total_carts = db.carts.count_documents({})
        total_orders = db.orders.count_documents({})

        # User count
        users = users_repo.get_all_users()
        total_users = len(users)

        # Average engagement rate
        avg_eng_rate = (total_engagements / max(total_views, 1)) * 100.0

        # Category distribution
        categories = {}
        for p in db.posts.find({}, {"category": 1}):
            cat = p.get("category", "Other")
            categories[cat] = categories.get(cat, 0) + 1

        # Recommendation Benchmark Report
        benchmark = evaluation_service.run_benchmark(k=10)

        return {
            "metrics": {
                "total_users": total_users,
                "total_posts": total_posts,
                "total_products": total_products,
                "total_views": total_views,
                "total_engagements": total_engagements,
                "total_cart_additions": total_carts,
                "total_orders": total_orders,
                "average_engagement_rate_pct": round(avg_eng_rate, 2),
            },
            "category_distribution": [
                {"category": k, "posts_count": v}
                for k, v in sorted(categories.items(), key=lambda x: x[1], reverse=True)
            ],
            "benchmark_evaluation": benchmark
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/interests")
def get_user_interests(user_id: str):
    """
    Detailed user interests profile:
    Category affinities, viewed posts, liked posts, followed creators,
    and shopping intent from cart and purchase history.
    """
    try:
        profile = build_user_profile(user_id, db)
        follows = users_repo.get_user_follows(user_id)
        commerce_profile = commerce_service.get_user_commerce_profile(user_id)
        
        # Interactions
        views = interactions_repo.get_user_views(user_id)
        engagements = interactions_repo.get_user_engagements(user_id)
        carts = interactions_repo.get_user_carts(user_id)
        orders = interactions_repo.get_user_orders(user_id)

        # Format top categories
        top_cats = [
            {"category": cat, "affinity": round(aff, 3)}
            for cat, aff in sorted(profile.category_affinities.items(), key=lambda x: x[1], reverse=True)
        ]

        return {
            "user_id": user_id,
            "is_cold_start": profile.is_cold_start,
            "interaction_count": profile.interaction_count,
            "top_categories": top_cats,
            "followed_creators": follows,
            "shopping_categories": list(commerce_profile.keys()),
            "stats": {
                "views_count": len(views),
                "engagements_count": len(engagements),
                "cart_items_count": len(carts),
                "orders_count": len(orders),
            },
            "recent_liked_posts": [e.get("post_id") for e in engagements[-5:] if e.get("post_id")],
            "taste_vector_active": bool(profile.embedding)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/evaluate")
def evaluate_metrics(k: int = Query(10, ge=1, le=50)):
    """
    Offline evaluation endpoint returning Precision@K, Recall@K, NDCG@K, MAP, Diversity, and Coverage.
    """
    try:
        return evaluation_service.run_benchmark(k=k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
