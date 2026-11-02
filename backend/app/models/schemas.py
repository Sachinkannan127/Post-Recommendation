"""
Pydantic Schemas for API Requests, Responses, and Data Models.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ScoringComponents(BaseModel):
    content_similarity: float = Field(..., ge=0.0, le=1.0, description="Content-based embedding similarity")
    user_engagement: float = Field(..., ge=0.0, le=1.0, description="Collaborative filtering / past engagement signal")
    social_relevance: float = Field(..., ge=0.0, le=1.0, description="Creator affinity and social follow graph")
    commerce_relevance: float = Field(..., ge=0.0, le=1.0, description="Cart and purchase intent category alignment")
    popularity: float = Field(..., ge=0.0, le=1.0, description="Global engagement and trending signal")
    freshness: float = Field(..., ge=0.0, le=1.0, description="Exponential recency decay")


class RecommendationItem(BaseModel):
    post_id: str
    caption: str
    image_url: str
    author_id: str
    author_name: str
    category: str
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    view_count: int = 0
    created_at: str
    final_score: float = Field(..., ge=0.0, le=1.0)
    components: ScoringComponents
    explanation: List[str]
    pinned_product: Optional[Dict[str, Any]] = None


class FeedResponse(BaseModel):
    user_id: str
    count: int
    cold_start: bool = False
    cold_start_type: Optional[str] = None
    execution_time_ms: float
    weights_used: Dict[str, float]
    posts: List[RecommendationItem]
    feed: Optional[List[RecommendationItem]] = None
    diagnostics: Optional[Dict[str, Any]] = None

    def model_post_init(self, __context: Any) -> None:
        if self.feed is None:
            self.feed = self.posts
        if self.diagnostics is None:
            self.diagnostics = {
                "execution_time_ms": self.execution_time_ms,
                "cold_start": self.cold_start,
                "count": self.count
            }


class PostExplanationItem(BaseModel):
    post_id: str
    caption: str
    final_score: float
    components: ScoringComponents
    reasons: List[str]


class ExplanationsResponse(BaseModel):
    user_id: str
    count: int
    recommendations: List[PostExplanationItem]


class ProductRecommendationItem(BaseModel):
    product_id: str
    title: str
    price: float
    image_url: str
    category: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    reason: str


class ProductRecommendationsResponse(BaseModel):
    user_id: str
    count: int
    products: List[ProductRecommendationItem]
    recommendations: Optional[List[ProductRecommendationItem]] = None

    def model_post_init(self, __context: Any) -> None:
        if self.recommendations is None:
            self.recommendations = self.products


class UserInterestsResponse(BaseModel):
    user_id: str
    top_categories: List[Dict[str, Any]]
    engagement_counts: Dict[str, int]
    followed_creators: List[str]
    cart_categories: List[str]
    viewed_posts_count: int
    liked_posts_count: int


class WeightsConfig(BaseModel):
    content: Optional[float] = Field(0.30, ge=0.0, le=1.0)
    engagement: Optional[float] = Field(0.20, ge=0.0, le=1.0)
    social: Optional[float] = Field(0.15, ge=0.0, le=1.0)
    commerce: Optional[float] = Field(0.15, ge=0.0, le=1.0)
    popularity: Optional[float] = Field(0.10, ge=0.0, le=1.0)
    freshness: Optional[float] = Field(0.10, ge=0.0, le=1.0)


class RefreshFeedRequest(BaseModel):
    weights: Optional[WeightsConfig] = None
    limit: Optional[int] = Field(15, ge=1, le=50)


class InteractionRequest(BaseModel):
    user_id: str
    post_id: str
    interaction_type: str = Field(..., description="like, bookmark, share, comment, view, add_to_cart")


class InteractionResponse(BaseModel):
    success: bool
    user_id: str
    post_id: str
    interaction_type: str
    message: str


class HealthResponse(BaseModel):
    status: str
    database: Dict[str, Any]
    engine: str = "Hybrid Social Commerce Engine v2.0"
    version: str = "2.0.0"
