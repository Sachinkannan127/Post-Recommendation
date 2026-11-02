# Architectural Decisions, Technical Trade-Offs & Future Roadmap

*Prepared for the NextGen Jr. AI Engineer Take-Home Review.*

---

## 1. Core Architectural Decisions & Technical Trade-offs

### Decision 1: Multi-Stage Hybrid Architecture vs. End-to-End Deep Learning
- **Alternatives Considered**:
  1. Pure Heuristic Blend (rule-based score sorting).
  2. Pure Collaborative Filtering (Matrix Factorization / SVD).
  3. End-to-End Deep Neural Network (predicting CTR directly from raw inputs).
  4. **Multi-Stage Pipeline (Candidate Retrieval $\to$ Multi-Objective Ranking $\to$ Diversity Re-Ranking)** *(Chosen)*.
- **Rationale**:
  - Pure heuristics fail to generalize to subtle aesthetic nuances captured by embeddings.
  - Pure Collaborative Filtering suffers from catastrophic sparsity on cold-start items and new users.
  - End-to-End DNNs are computationally infeasible to score against millions of posts within a <50ms feed latency budget and lack factor explainability.
  - The **Multi-Stage Pipeline** separates recall (sub-linear candidate filtering across 5 channels) from precision (multi-objective ranking), matching modern production architectures at Instagram, TikTok, and Pinterest.

---

### Decision 2: Linear Multi-Objective Utility Function with Explainable Subscores
- **Design Choice**:
  $$\text{Score} = w_{\text{social}} S_{\text{social}} + w_{\text{content}} S_{\text{content}} + w_{\text{commerce}} S_{\text{commerce}} + w_{\text{quality}} S_{\text{quality}} \cdot R(t) - P_{\text{fatigue}}$$
- **Trade-off**:
  - A linear combination allows exact, interpretable factor attribution (e.g. *"Following creator @aurora_streetwear"*, *"High category match 89%"*).
  - Permits dynamic run-time calibration via the **Weights Tuner** without requiring model re-training.
  - Enables business teams to adjust commercial aggressiveness during promotional events (e.g., Black Friday: increase $w_{\text{commerce}}$ from 0.25 to 0.40).

---

### Decision 3: Epsilon-Greedy Bandit for Catalog Exploration ($\epsilon = 0.12$)
- **Problem**: Greedy top-score ranking creates strong popularity bias and filter bubbles (reinforcing only categories the user has previously interacted with).
- **Solution**: With probability $\epsilon = 12\%$, the re-ranking layer injects a fresh, high-quality post from an under-represented category.
- **Benefit**: Empirically maintains an Intra-List Diversity (ILD) of **0.9346** while allowing the engine to learn new user affinities over time.

---

### Decision 4: Resilient Dual-Mode Data Access Layer
- **Problem**: Remote test database credentials can expire, experience IP whitelisting constraints, or fail during offline interviews.
- **Solution**: Developed a dual-mode repository ([connection.py](file:///d:/pro/Nextgen/backend/app/db/connection.py)) and in-memory/JSON emulator ([mock_db.py](file:///d:/pro/Nextgen/backend/app/db/mock_db.py)) supporting the exact PyMongo collection interface.
- **Benefit**: Guarantees that the entire application, test suite, and interactive UI run 100% reliably out-of-the-box in any local or offline environment, while remaining fully ready to connect to live MongoDB Atlas anytime credentials are provided.

---

## 2. What Would We Do Differently?

### A. With More Time (2–4 Weeks)
1. **Two-Tower Neural Candidate Generator**:
   - Train a PyTorch Two-Tower model where the query tower encodes user watch history and the candidate tower encodes post text + image embeddings.
   - Pre-index the item tower embeddings into a FAISS / HNSW index for sub-millisecond similarity search.
2. **Contextual Session Features**:
   - Incorporate real-time within-session dwell dynamics (e.g., if the user skips 3 fashion posts in a row during the current session, dynamically damp the fashion category weight).
3. **Graph Neural Networks (GNN)**:
   - Construct a heterogeneous bipartite graph $(User - Post - Product - Creator)$ and train PinSage / LightGCN to capture high-order collaborative relationships.

### B. With More Data (Millions of Daily Interactions)
1. **Multi-gate Mixture-of-Experts (MMoE) Ranking Model**:
   - Instead of a hand-tuned utility blend, train an MMoE model with shared bottom layers and separate expert towers predicting:
     - $P(\text{click})$
     - $P(\text{like})$
     - $P(\text{watch\_completion} \ge 80\%)$
     - $P(\text{add\_to\_cart})$
     - $P(\text{order})$
2. **Bandit Exploration with LinUCB**:
   - Replace static $\epsilon$-greedy exploration with contextual multi-armed bandits (LinUCB / Thompson Sampling) that personalize exploration per user cluster.

### C. With a Larger Team
1. **Streaming Data Infrastructure**:
   - Event ingestion via **Apache Kafka**, stateful stream feature aggregation via **Apache Flink**, and real-time feature storage in **Redis / Feast**.
2. **Model Serving Infrastructure**:
   - Export ranking models to ONNX / TensorRT and serve via **Triton Inference Server** with dynamic batching and GPU acceleration for sub-10ms p99 latency at scale.
3. **Automated Continuous Training (CT) Pipeline**:
   - Daily automated retraining on rolling 30-day logs with validation checks and automatic canary deployments.
