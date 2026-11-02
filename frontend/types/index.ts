/**
 * TypeScript Type Definitions for NextGen Social Commerce Recommendation System.
 * Matches backend Pydantic schemas and database collections.
 */

export interface ScoringComponents {
  content_similarity: number;
  user_engagement: number;
  social_relevance: number;
  commerce_relevance: number;
  popularity: number;
  freshness: number;
}

export interface PinnedProduct {
  product_id: string;
  title: string;
  price: number;
  image_url: string;
  category?: string;
  rating?: number;
}

export interface RecommendationItem {
  post_id: string;
  caption: string;
  image_url: string;
  author_id: string;
  author_name: string;
  category: string;
  like_count: number;
  comment_count: number;
  share_count: number;
  view_count: number;
  created_at: string;
  final_score: number;
  components: ScoringComponents;
  explanation: string[];
  pinned_product?: PinnedProduct | null;
}

export interface FeedResponse {
  user_id: string;
  count: number;
  cold_start: boolean;
  cold_start_type?: string | null;
  execution_time_ms: number;
  weights_used: Record<string, number>;
  posts: RecommendationItem[];
  feed?: RecommendationItem[];
  diagnostics?: Record<string, any>;
}

export interface UserPersona {
  user_id: string;
  name: string;
  bio: string;
  role: string;
  avatar_url: string;
}

export interface UserInterestsResponse {
  user_id: string;
  is_cold_start: boolean;
  interaction_count: number;
  top_categories: Array<{ category: string; affinity: number }>;
  followed_creators: string[];
  shopping_categories: string[];
  stats: {
    views_count: number;
    engagements_count: number;
    cart_items_count: number;
    orders_count: number;
  };
  recent_liked_posts: string[];
  taste_vector_active: boolean;
}

export interface ProductRecommendationItem {
  product_id: string;
  title: string;
  price: number;
  image_url: string;
  category: string;
  similarity_score: number;
  reason: string;
}

export interface ProductRecommendationsResponse {
  user_id: string;
  count: number;
  products: ProductRecommendationItem[];
  recommendations?: ProductRecommendationItem[];
}

export interface FormulaWeights {
  content: number;
  engagement: number;
  social: number;
  commerce: number;
  popularity: number;
  freshness: number;
}

export interface BenchmarkMetrics {
  [key: string]: number;
}

export interface BenchmarkReport {
  evaluation_k: number;
  evaluated_users_count: number;
  total_catalog_items: number;
  comparison: Record<string, Record<string, number>>;
  aggregate_metrics?: Record<string, number>;
  summary: string;
}

export interface PlatformAnalytics {
  metrics: {
    total_users: number;
    total_posts: number;
    total_products: number;
    total_views: number;
    total_engagements: number;
    total_cart_additions: number;
    total_orders: number;
    average_engagement_rate_pct: number;
  };
  category_distribution: Array<{ category: string; posts_count: number }>;
  benchmark_evaluation: BenchmarkReport;
}
