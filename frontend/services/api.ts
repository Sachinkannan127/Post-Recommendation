/**
 * Modular API Client Service for NextGen Recommendation Engine.
 * Provides typed methods for all Section 7 API endpoints.
 */

import {
  FeedResponse,
  ProductRecommendationsResponse,
  UserPersona,
  UserInterestsResponse,
  PlatformAnalytics,
  BenchmarkReport,
  FormulaWeights
} from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

export class RecSysApiClient {
  private static async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {})
      }
    });

    if (!res.ok) {
      throw new Error(`API error ${res.status}: ${res.statusText}`);
    }

    return res.json();
  }

  // 1. Health & Database Diagnostics
  public static async getHealth(): Promise<{ status: string; database: any; latency_ms: number }> {
    return this.request('/health');
  }

  // 2. Users
  public static async getUsers(): Promise<UserPersona[]> {
    return this.request('/users');
  }

  // 3. Personalized Feed (Section 7: GET /api/feed/{user_id})
  public static async getFeed(
    userId: string,
    limit: number = 15,
    weights?: Partial<FormulaWeights>
  ): Promise<FeedResponse> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (weights) {
      if (weights.content !== undefined) params.append('w_content', weights.content.toString());
      if (weights.engagement !== undefined) params.append('w_engagement', weights.engagement.toString());
      if (weights.social !== undefined) params.append('w_social', weights.social.toString());
      if (weights.commerce !== undefined) params.append('w_commerce', weights.commerce.toString());
      if (weights.popularity !== undefined) params.append('w_popularity', weights.popularity.toString());
      if (weights.freshness !== undefined) params.append('w_freshness', weights.freshness.toString());
    }

    return this.request(`/feed/${userId}?${params.toString()}`);
  }

  // 4. Recommendation Explanations (Section 7: GET /api/recommendations/{user_id}/explanations)
  public static async getExplanations(userId: string, limit: number = 10): Promise<any> {
    return this.request(`/recommendations/${userId}/explanations?limit=${limit}`);
  }

  // 5. Refresh Recommendations with Weight Overrides (POST /api/recommendations/refresh/{user_id})
  public static async refreshFeed(
    userId: string,
    weights?: Partial<FormulaWeights>,
    limit: number = 15
  ): Promise<FeedResponse> {
    return this.request(`/recommendations/refresh/${userId}`, {
      method: 'POST',
      body: JSON.stringify({ weights, limit })
    });
  }

  // 6. Trending Posts (GET /api/trending)
  public static async getTrending(limit: number = 10): Promise<{ count: number; posts: any[]; trending_categories: any[] }> {
    return this.request(`/trending?limit=${limit}`);
  }

  // 7. Platform Analytics & Benchmarks (GET /api/analytics)
  public static async getAnalytics(): Promise<PlatformAnalytics> {
    return this.request('/analytics');
  }

  // 8. User Interests Profile (GET /api/user/{user_id}/interests)
  public static async getUserInterests(userId: string): Promise<UserInterestsResponse> {
    return this.request(`/user/${userId}/interests`);
  }

  // 9. Product Recommendations Stretch Goal (GET /api/products/recommendations/{user_id})
  public static async getProductRecommendations(
    userId: string,
    limit: number = 8
  ): Promise<ProductRecommendationsResponse> {
    return this.request(`/products/recommendations/${userId}?limit=${limit}`);
  }

  // 10. Record User Interaction (POST /api/interactions/engage)
  public static async recordInteraction(
    userId: string,
    postId: string,
    interactionType: 'like' | 'bookmark' | 'share' | 'view' | 'add_to_cart'
  ): Promise<{ status: string; success: boolean; message: string }> {
    return this.request('/interactions/engage', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        post_id: postId,
        interaction_type: interactionType
      })
    });
  }

  // 11. Offline Benchmark Evaluation (GET /api/metrics/evaluate)
  public static async getBenchmark(k: number = 10): Promise<BenchmarkReport> {
    return this.request(`/metrics/evaluate?k=${k}`);
  }
}
