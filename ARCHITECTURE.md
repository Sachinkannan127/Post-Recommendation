# System Architecture & Technical Reasoning: Social Commerce Recommendation Engine

## 1. Problem Formulation: The Social Commerce Paradox

A traditional feed recommendation system (e.g. YouTube, TikTok, Twitter) optimizes almost exclusively for **engagement metrics**:
- Click-Through Rate ($CTR$)
- Watch Completion Rate ($WCR$)
- Engagement Rate (Likes, Shares, Comments, Saves)

Conversely, a pure e-commerce recommendation system (e.g. Amazon) optimizes for **transactional efficiency**:
- Conversion Rate ($CVR$)
- Gross Merchandise Value ($GMV$)
- Average Order Value ($AOV$)

### The Challenge of Social Commerce
In a social commerce platform (e.g., TikTok Shop, Instagram Shop, Xiaohongshu), optimizing for either objective in isolation creates severe system degradation:
1. **The Infomercial Trap (Over-Commerce)**: If the algorithm prioritizes only high-conversion products, the feed degrades into repetitive shopping advertisements, causing user fatigue, drop-offs, and churn.
2. **The Zero-Conversion Trap (Over-Social)**: If the algorithm optimizes only for viral memes or high-energy creators, engagement is high, but creator merchandise goes unsold, alienating sellers.

**Solution Architecture**: A multi-objective, two-sided market ranking system that models both **organic interest** and **commercial intent**, dynamically tuning the trade-off based on real-time user intent signals.

---

## 2. End-to-End Pipeline Overview

```mermaid
flowchart LR
    A[User Request (user_id)] --> B[User Profile Extractor]
    B --> C[Candidate Generation (5 Channels)]
    C -->|Top ~100 Candidates| D[Multi-Objective Ranker]
    D -->|Scored & Explained| E[Re-Ranker & Diversity Capper]
    E -->|Top K Final Feed| F[Client Feed API]
```

---

## 3. Detailed Component Architecture & Mathematical Foundations

### Stage 1: User Profile Feature Synthesis ([user_profile.py](file:///d:/pro/Nextgen/backend/app/core/user_profile.py))

User taste is not static; it is composed of explicit social choices, passive dwell behaviors, and transactional intent.
We synthesize an aggregated **User Preference Vector** $\vec{u} \in \mathbb{R}^{d}$ ($d=64$):

$$\vec{u} = \frac{\sum_{i \in \mathcal{H}} w_i \cdot \vec{e}_i}{\left\| \sum_{i \in \mathcal{H}} w_i \cdot \vec{e}_i \right\|_2}$$

Where:
- $\vec{e}_i$ is the 64-dimensional embedding vector of post $i$.
- $\mathcal{H}$ is the set of all posts the user interacted with.
- Interaction weights $w_i$ reflect behavioral commitment:
  - Like: $1.0$
  - Comment: $1.5$
  - Bookmark / Save: $2.0$
  - Share: $2.5$
  - Watch Percentage: $w_{\text{watch}} = \text{pct} \cdot 1.5$ (if $\text{pct} \ge 0.7$) else $\text{pct} \cdot 0.5$
  - Cart addition for pinned item: $+3.0$
  - Order completion for pinned item: $+5.0$

---

### Stage 2: Multi-Channel Candidate Retrieval ([candidate_generator.py](file:///d:/pro/Nextgen/backend/app/core/candidate_generator.py))

To achieve high recall without linear scan bottlenecks, candidates are retrieved in parallel across 5 channels:

| Retrieval Channel | Data Source | Heuristic / Formula | Role in System |
|---|---|---|---|
| **1. Social Graph** | `follows`, `posts` | $\text{posts from } \{s \mid (u, s) \in \text{follows}\}$ | High-precision explicit user interest |
| **2. Vector Similarity** | `postembeddings` | $\cos(\vec{u}, \vec{v}_p) = \frac{\vec{u} \cdot \vec{v}_p}{\|\vec{u}\| \|\vec{v}_p\|}$ | Semantic content matching independent of author |
| **3. Commerce Intent** | `carts`, `orders`, `products` | Matches pinned products to cart items & category purchases | High-intent purchasing conversion |
| **4. Collaborative Filtering** | `postengagements` | User-to-User taste co-occurrence | Serendipitous community discovery |
| **5. Trending & Viral Velocity** | `postmetrics` | Bayesian smoothed viral rate $\times$ recency decay | Cold-start anchor & global quality |

---

### Stage 3: Multi-Objective Ranking Function ([ranker.py](file:///d:/pro/Nextgen/backend/app/core/ranker.py))

For each candidate post $p$ for user $u$, the composite ranking score is defined as:

$$\text{FinalScore}(u, p) = w_{\text{soc}} S_{\text{social}}(u, p) + w_{\text{cont}} S_{\text{content}}(u, p) + w_{\text{comm}} S_{\text{commerce}}(u, p) + w_{\text{qual}} S_{\text{quality}}(p) \cdot R(t_p) - P_{\text{fatigue}}(u, p)$$

#### 1. Social Affinity Score ($S_{\text{social}}$)
$$S_{\text{social}}(u, p) = \begin{cases} 
1.0 & \text{if } \text{seller}(p) \in \text{Follows}(u) \\
\frac{\text{Rating}(\text{seller}(p))}{5.0} \cdot 0.4 & \text{otherwise}
\end{cases}$$

#### 2. Content Semantic Similarity ($S_{\text{content}}$)
$$S_{\text{content}}(u, p) = \frac{\cos(\vec{u}, \vec{v}_p) + 1.0}{2.0} \in [0, 1]$$

#### 3. Commerce Intent Score ($S_{\text{commerce}}$)
$$S_{\text{commerce}}(u, p) = \begin{cases}
1.0 & \text{if pinned product is in } \text{Cart}(u) \\
0.85 & \text{if pinned product was previously purchased by } u \\
0.3 + 0.6 \cdot \text{Affinity}(u, \text{category}(p)) & \text{category match} \\
0.2 & \text{baseline}
\end{cases}$$

#### 4. Bayesian Smoothed Quality Score ($S_{\text{quality}}$)
Small posts with 1 view and 1 like should not have a 100% engagement rate. We apply Empirical Bayes smoothing:
$$\text{SmoothedEng}(p) = \frac{\text{Likes} + 1.5 \cdot \text{Comments} + 2.5 \cdot \text{Shares} + 2.0 \cdot \text{Saves} + \alpha}{\text{Views} + \beta}$$
where prior hyperparameters $\alpha = 10, \beta = 100$.
$$S_{\text{quality}}(p) = 0.6 \cdot \min(1.0, 5 \cdot \text{SmoothedEng}) + 0.4 \cdot \text{AvgWatchTime}(p)$$

#### 5. Exponential Recency Decay ($R(t_p)$)
Freshness is enforced via half-life decay:
$$R(t_p) = \exp\left( -\frac{\ln(2)}{t_{\text{half}}} \cdot \Delta t_{\text{days}} \right)$$
where $t_{\text{half}} = 7.0 \text{ days}$.

#### 6. Fatigue Penalty ($P_{\text{fatigue}}$)
If user $u$ has already viewed or engaged with post $p$, we subtract a penalty of $0.35$ to guarantee feed freshness.

---

### Stage 4: Re-Ranking & Feed Polishing ([reranker.py](file:///d:/pro/Nextgen/backend/app/core/reranker.py))

Sorting purely by greedy score creates pathological feed clusters (e.g. 5 consecutive posts from the same seller). We enforce three business constraints:
1. **Author Frequency Capping**: No two consecutive posts from the same seller, and maximum 2 total posts per seller in the top 15.
2. **Category Interleaving**: Maximum 2 consecutive posts from the same category to maintain visual interest.
3. **Epsilon-Greedy Exploration ($\epsilon = 0.12$)**: With probability $\epsilon$, inject high-quality candidate items from unrepresented categories to break filter bubbles and discover new user interests.

---

## 4. Cold-Start Handling Strategy

For a brand-new user with zero engagement history:
1. **Signal Detection**: `total_interactions == 0` flags `is_cold_start = True`.
2. **Candidate Channel Shift**: Automatically pivots to Channel 5 (**Trending & Viral Velocity**).
3. **Adaptive Ranking Weights**: Shift ranking weights away from missing personalization signals:
   $$\text{Score}_{\text{cold}}(p) = 0.55 \cdot S_{\text{quality}}(p) \cdot R(t_p) + 0.25 \cdot S_{\text{commerce}}(p) + 0.20 \cdot S_{\text{social}}(p)$$
4. **Category Exploration Bandits**: Evenly distributes top posts from all major categories (Fashion, Tech, Beauty, Home, Fitness) to rapidly discover the user's initial affinity.

---

## 5. Stretch Goal: Product Recommendation Component ([product_recommender.py](file:///d:/pro/Nextgen/backend/app/core/product_recommender.py))

The product recommender surfaces standalone products based on:
1. **Social Video Engagement**: Products pinned in posts watched to completion receive an affinity boost ($+0.40$).
2. **Seller Trust**: Products sold by creators the user follows receive a $+0.25$ trust multiplier.
3. **Vector Similarity**: Cosine similarity between `user_vector` and 64-dim `product_embedding`.
4. **Cart/Purchase Re-ranking**: Products already in cart receive high priority; previously ordered items receive a slight discount to avoid repurchase spam.

---

## 6. Scalability & High-Throughput Production Roadmap

To scale this system from prototype to 10M+ Daily Active Users (DAU) and 100M+ posts:

```mermaid
graph LR
    User[Client Request] --> CDN[CloudFront / Fastly]
    CDN --> GW[API Gateway]
    GW --> RecService[Recommendation Microservice (Go / C++ / Triton)]
    RecService --> VectorDB[(Milvus / FAISS ANN Cluster)]
    RecService --> FeatureStore[(Redis Cluster / Feast)]
    RecService --> RankerService[Triton Model Server (Two-Tower / DLRM)]
    Kafka[(Kafka Event Log)] --> Flink[Apache Flink Stream Processor]
    Flink --> FeatureStore
```

1. **Approximate Nearest Neighbor (ANN) Retrieval**:
   - Replace linear embedding scans with **FAISS / Milvus / HNSW Indexing** for sub-millisecond retrieval across millions of vector embeddings.
2. **Two-Tower Deep Neural Network (Two-Tower DNN)**:
   - User Tower: Encodes real-time user context, demographics, and session history into a dense vector.
   - Item Tower: Encodes media vision embeddings (e.g. CLIP/SigLIP), text captions, and seller features.
   - Inner product serves as the candidate score.
3. **Real-time Feature Store (Redis / Feast)**:
   - User interaction events stream through **Kafka** into **Apache Flink** to update rolling user vectors and category affinity counters in sub-second latency.
4. **Multi-Task Ranking with MMoE (Multi-gate Mixture-of-Experts)**:
   - Jointly predict $P(\text{like}), P(\text{share}), P(\text{watch\_finish}), P(\text{add\_to\_cart}), P(\text{order})$ using a shared representation backbone.
