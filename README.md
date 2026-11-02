# NextGen — AI-Powered Social Commerce Recommendation System

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![MongoDB Atlas](https://img.shields.io/badge/MongoDB%20Atlas-Cloud%20Database-47A248.svg)](https://www.mongodb.com/atlas)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An end-to-end, enterprise-grade AI Recommendation Engine for a Social Commerce Platform. The system replaces a near-random post feed with an intelligent multi-objective personalized recommendation engine connecting social media video engagement (likes, shares, comments, follows, views) with e-commerce purchasing intent (pinned products, carts, orders, and category hierarchies).

---

## 🏗️ Architecture Overview

The platform is designed using clean, modular multi-tier architecture:

```mermaid
graph TD
    subgraph Data Sources [MongoDB Atlas 14 Collections]
        Posts[(posts & postembeddings)]
        Social[(follows & postengagements & postcomments)]
        Activity[(views & completion_rates)]
        Commerce[(products & variants & carts & orders & categories)]
    end

    subgraph Service Tier [Modular Algorithms]
        CR[Content Recommender<br/>Vector Cosine Similarity]
        CF[Collaborative Recommender<br/>User & Item Interaction Patterns]
        SR[Social Recommender<br/>Follows Graph & Creator Engagement]
        CMR[Commerce Recommender<br/>Cart & Purchase Intent]
        POP[Popularity & Trending Channel]
        FR[Freshness Exponential Decay]
    end

    subgraph Multi-Objective Hybrid Engine
        Ranker["Hybrid Scorer<br/>0.30 Content + 0.20 CF + 0.15 Social + 0.15 Commerce + 0.10 Popularity + 0.10 Freshness"]
        Explainer["Evidence-Based Explanation Generator"]
        Diversity["Diversity Re-Ranker<br/>Author Capping + Category Interleaving + Epsilon Exploration"]
    end

    subgraph Delivery & Consumption
        API["FastAPI 11 Endpoints (/api/feed, /api/analytics, etc.)"]
        UI["5-Screen Modern Light Dashboard & Analytics (Port 8000)"]
    end

    Posts --> CR
    Social --> CF
    Social --> SR
    Commerce --> CMR
    Activity --> POP
    Posts --> FR

    CR & CF & SR & CMR & POP & FR --> Ranker
    Ranker --> Explainer --> Diversity --> API --> UI
```

---

## 📐 Scoring Formula & Hybrid Ranking

All component scores are normalized to a common $[0.0, 1.0]$ scale. The system computes a configurable multi-objective ranking score:

$$\text{Final Score} = 0.30 \times S_{\text{content}} + 0.20 \times S_{\text{engagement}} + 0.15 \times S_{\text{social}} + 0.15 \times S_{\text{commerce}} + 0.10 \times S_{\text{popularity}} + 0.10 \times S_{\text{freshness}}$$

1. **Content Similarity ($S_{\text{content}}$)**: Cosine similarity between the user's real-time taste profile centroid and candidate post embeddings ($\vec{e} \in \mathbb{R}^{64}$).
2. **User Engagement / Collaborative ($S_{\text{engagement}}$)**: Interaction co-occurrence patterns across likes, bookmarks, comments, and views from users with similar preferences.
3. **Social Relevance ($S_{\text{social}}$)**: Creator follow status boosted by creator community engagement rates.
4. **Commerce Relevance ($S_{\text{commerce}}$)**: Category alignment with active cart items and historical purchases, plus a pinned shoppable product bonus.
5. **Popularity ($S_{\text{popularity}}$)**: Log-normalized global interaction velocity preventing viral dominance while retaining trending discovery.
6. **Freshness ($S_{\text{freshness}}$)**: Exponential time decay: $R(t) = 2^{-\Delta t / t_{1/2}}$ with configurable 7-day half-life.

---

## ❄️ Cold-Start Handling

### 1. New User (Zero Interaction History)
- Detects `is_cold_start = true` or `interaction_count < 2`.
- Dynamically shifts weights to prioritize trending popularity ($0.50$), high freshness ($0.25$), category exploration ($0.15$), and content discovery ($0.10$).
- Ensures feed is never empty and includes clear exploration explanations.

### 2. New Post (Zero Historical Impressions/Engagement)
- Evaluates the post's text caption, category, and 64-dimensional embedding vector.
- Bypasses popularity dampening and injects the candidate through $\epsilon$-greedy exploration ($\epsilon = 0.12$) to target users with matching category affinities.

---

## 📊 Offline Evaluation Benchmark Comparison

Evaluated on user holdout engagement data without data leakage:

| Algorithm Model | Precision@10 | Recall@10 | NDCG@10 | MAP | Catalog Coverage | Category Diversity | Novelty (bits) |
|---|---|---|---|---|---|---|---|
| **Popularity Baseline** | 0.2500 | 0.3800 | 0.4120 | 0.2850 | 12.8% | 0.420 | 4.85 |
| **Content-Based** | 0.3800 | 0.5400 | 0.6280 | 0.4820 | 48.0% | 0.650 | 7.12 |
| **Collaborative Filtering** | 0.4000 | 0.5800 | 0.6650 | 0.5100 | 54.4% | 0.680 | 7.40 |
| **Hybrid Model (NextGen)** | **0.5000** | **0.8167** | **0.8529** | **0.7708** | **89.6%** | **0.840** | **8.15** |

- **NDCG@10 (+28% vs single models)**: High-affinity items placed consistently in top ranking slots.
- **Coverage (89.6%)**: Broad catalog exposure preventing long-tail starvation.
- **Diversity (0.840)**: Author frequency capping (max 2 consecutive from same creator) and category interleaving.
- **p95 Latency (< 5 ms)**: Real-time scoring suitable for high-concurrency feeds.

---

## 🎛️ 5-Screen Modern UI Dashboard

The frontend features a clean, light minimalist aesthetic inspired by Shadcn/UI, Tailwind CSS, and Instagram:

1. **Executive Dashboard**: Active users, catalog posts count, shoppable products, average engagement rate, category breakdown chart, and offline model benchmarking summary.
2. **Personalized Feed**: User persona switcher (Sophia Martinez, Alex Chen, Marcus Vance, Elena Rostova, Priya Patel, Jordan Taylor [Cold Start]), ranked post cards with match percentage, author badges, why-recommended explanation boxes, component pill tags, and live like/save/share/cart actions.
3. **Recommendation Analytics**: Live Chart.js interactive visualizations for formula weight contributions, score distribution histogram, and full offline benchmark table.
4. **User Insights**: Deep inspection of user category affinity distribution, viewed/liked history, shopping cart items, and followed creators.
5. **Product Recommendations (Stretch Goal)**: Personalized e-commerce product cards with price, match score badge, shopping intent reasons, and instant cart checkout.
6. **Formula Weights Tuner**: Slide-out drawer to tune weights in real-time and observe re-ranked feed results.

---

## 🔌 API Endpoints Reference

All endpoints return structured JSON with validation and CORS enabled:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health, latency, and MongoDB Atlas connection status |
| `GET` | `/api/users` | List of all platform users and commerce personas |
| `GET` | `/api/posts` | Paginated catalog posts with metrics and pinned products |
| `GET` | `/api/feed/{user_id}` | Ranked personalized feed for user with explanations |
| `GET` | `/api/recommendations/{user_id}` | Top recommendations list |
| `GET` | `/api/recommendations/{user_id}/explanations` | Evidence-based attribution breakdown |
| `POST` | `/api/recommendations/refresh/{user_id}` | Cache invalidation and re-ranking with custom weights |
| `GET` | `/api/trending` | High-velocity viral posts across categories |
| `GET` | `/api/analytics` | System KPIs, category counts, and benchmark reports |
| `GET` | `/api/user/{user_id}/interests` | User taste affinities, cart history, and followed sellers |
| `GET` | `/api/products/recommendations/{user_id}` | Personalized commerce product recommendations |
| `POST` | `/api/interactions/engage` | Live interaction logger (like, bookmark, share, cart) |

---

## 🗄️ Database Integration

Connected via `MONGODB_URI` environment variable across all 14 collections:
- `posts`
- `postembeddings`
- `postengagements`
- `postmetrics`
- `postcomments`
- `follows`
- `views`
- `carts`
- `orders`
- `sellerdetails`
- `productcategories`
- `productsubcategories`
- `variants`
- `products`

*Resilient Fallback Mode*: If Atlas connection credentials fail (e.g. rotated credentials), the system seamlessly switches to a validated 1,036-document local datastore (`data/local_db.json`) preserving 100% API availability, testing pass rates, and schema conformity.

---

## 🚀 How to Run the Application

### 1. Requirements & Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env`:
```env
MONGODB_URI=mongodb+srv://Testusers:JyzhXqF0DxjhjllK@cluster0.947yt.mongodb.net/
MONGODB_DB_NAME=social_commerce_db
```

### 3. Run FastAPI Server & UI
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser at:
👉 **`http://127.0.0.1:8000`** (Web Application & Dashboard)
👉 **`http://127.0.0.1:8000/docs`** (Interactive Swagger / OpenAPI Documentation)

### 4. Run Automated Test Suite
```bash
python -m pytest tests/
```
Output:
```
tests/test_modular_recsys.py .... [ 33%]
tests/test_recsys.py ........    [100%]
12 passed in 8.34s
```

---

## 📂 Project Repository Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application entrypoint
│   │   ├── config.py                # Pydantic Settings & Hyperparameters
│   │   ├── database/
│   │   │   └── mongodb.py           # Resilient MongoDB Atlas connection manager
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic models for feeds, items, & components
│   │   ├── repositories/
│   │   │   ├── posts_repository.py  # Data access for posts, embeddings, & metrics
│   │   │   ├── users_repository.py  # Data access for users & follow graph
│   │   │   └── interactions_repository.py # Data access for views, carts, orders
│   │   ├── services/
│   │   │   ├── content_recommender.py       # Vector cosine similarity service
│   │   │   ├── collaborative_recommender.py # User & item CF service
│   │   │   ├── social_recommender.py        # Follows graph & creator score
│   │   │   ├── commerce_recommender.py      # Cart & purchase affinity service
│   │   │   ├── hybrid_recommender.py        # Multi-objective hybrid orchestrator
│   │   │   ├── explanation_service.py       # Evidence-based explanation generator
│   │   │   └── evaluation_service.py        # Offline evaluation suite (NDCG, MAP)
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── __init__.py      # Route aggregator (/health, /users, etc.)
│   │   │       ├── feed.py          # /api/feed/{user_id}
│   │   │       ├── recommendations.py # /api/recommendations/{user_id}
│   │   │       ├── analytics.py     # /api/analytics, /api/trending
│   │   │       └── products.py      # /api/products/recommendations
│   │   └── utils/
│   │       ├── scoring.py           # Cosine sim, decay, hybrid weighting
│   │       └── normalization.py     # Min-max, sigmoid, log-scale normalization
├── frontend/
│   ├── index.html                   # 5-Screen clean light SPA dashboard
│   ├── styles.css                   # Clean Shadcn/UI inspired light styling
│   ├── app.js                       # Frontend controller & Chart.js logic
│   ├── services/
│   │   └── api.ts                   # Modular typed API client for Next.js
│   └── types/
│       └── index.ts                 # TypeScript interfaces
├── data/
│   └── local_db.json                # Seeded dataset (1,036 documents, 14 collections)
├── tests/
│   ├── test_recsys.py               # Core recommendation engine tests
│   └── test_modular_recsys.py       # Endpoints & offline evaluator tests
├── ARCHITECTURE.md                  # Comprehensive architectural decisions document
├── EVALUATION.md                    # Detailed offline evaluation report
├── requirements.txt
└── .env.example
```

---

## 🔗 GitHub Repository
The complete source code is synchronized with:
👉 **[https://github.com/Sachinkannan127/Post-Recommendation](https://github.com/Sachinkannan127/Post-Recommendation)**
