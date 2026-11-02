/**
 * NextGen AI Social Commerce Recommendation Platform Frontend Controller
 * Connects to the FastAPI backend to demonstrate real personalized feeds,
 * transparent evidence-based explanations, offline benchmark analytics, and product recommendations.
 */

const API_BASE = "/api";

const state = {
  activeScreen: "screen-dashboard",
  currentUserId: "user_fashion_01",
  users: [],
  weights: {
    content: 0.30,
    engagement: 0.20,
    social: 0.15,
    commerce: 0.15,
    popularity: 0.10,
    freshness: 0.10,
  },
  charts: {
    category: null,
    benchmark: null,
    components: null,
    scoreDist: null,
  },
  feedPosts: [],
  feedOffset: 0,
  feedLimit: 20,
  feedTotal: 0,
  isFeedLoading: false,
  infiniteScroll: false,
  productRecs: [],
  productOffset: 0,
  productLimit: 16,
  productTotal: 0,
  selectedProductCategory: "all",
  isProductsLoading: false,
  likedPosts: new Set(),
  bookmarkedPosts: new Set(),
  cartItems: new Set(),
};

// ============================================================================
// Initialization
// ============================================================================
document.addEventListener("DOMContentLoaded", async () => {
  setupNavigation();
  setupSliders();
  setupEventListeners();
  
  // Initial API Fetches
  await fetchHealthStatus();
  await fetchUsers();
  await loadDashboard();
  
  if (window.lucide) {
    window.lucide.createIcons();
  }
});

function setupNavigation() {
  const tabs = document.querySelectorAll(".nav-tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");

      const targetScreen = tab.dataset.screen;
      state.activeScreen = targetScreen;

      document.querySelectorAll(".screen-view").forEach((view) => {
        view.classList.remove("active");
      });
      const activeView = document.getElementById(targetScreen);
      if (activeView) activeView.classList.add("active");

      // Load screen data
      handleScreenChange(targetScreen);
      if (window.lucide) window.lucide.createIcons();
    });
  });
}

function handleScreenChange(screenId) {
  switch (screenId) {
    case "screen-dashboard":
      loadDashboard();
      break;
    case "screen-feed":
      loadPersonalizedFeed();
      break;
    case "screen-analytics":
      loadAnalytics();
      break;
    case "screen-users":
      loadUserInsights();
      break;
    case "screen-products":
      loadProductRecommendations();
      break;
  }
}

function setupEventListeners() {
  // User switcher
  const userPicker = document.getElementById("userPicker");
  if (userPicker) {
    userPicker.addEventListener("change", (e) => {
      state.currentUserId = e.target.value;
      showToast(`Switched active user to ${state.currentUserId}`);
      handleScreenChange(state.activeScreen);
    });
  }

  // Refresh buttons
  document.getElementById("btnRefreshDashboard")?.addEventListener("click", loadDashboard);
  document.getElementById("btnRefreshFeed")?.addEventListener("click", () => loadPersonalizedFeed(true));
  document.getElementById("btnRefreshProducts")?.addEventListener("click", () => loadProductRecommendations(true));
  document.getElementById("btnRunBenchmark")?.addEventListener("click", runBenchmarkEvaluation);

  // Feed Batch Size Selector
  document.getElementById("selectFeedLimit")?.addEventListener("change", (e) => {
    state.feedLimit = parseInt(e.target.value) || 20;
    showToast(`Updated feed batch size to ${state.feedLimit} items`);
    loadPersonalizedFeed(true);
  });

  // Feed Load More & Scroll Top
  document.getElementById("btnLoadMoreFeed")?.addEventListener("click", loadMoreFeedPosts);
  document.getElementById("btnScrollTopFeed")?.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  // Infinite Scroll Toggle
  const toggleInfinite = document.getElementById("toggleInfiniteScroll");
  if (toggleInfinite) {
    toggleInfinite.addEventListener("change", (e) => {
      state.infiniteScroll = e.target.checked;
      showToast(state.infiniteScroll ? "Auto-scroll continuous recommendations enabled" : "Auto-scroll disabled");
    });
  }

  // Window scroll listener for continuous recommendations
  window.addEventListener("scroll", () => {
    if (!state.infiniteScroll || state.activeScreen !== "screen-feed" || state.isFeedLoading) return;
    const scrollPos = window.innerHeight + window.scrollY;
    const threshold = document.documentElement.scrollHeight - 300;
    if (scrollPos >= threshold && state.feedPosts.length < state.feedTotal) {
      loadMoreFeedPosts();
    }
  });

  // Product Load More & Filters
  document.getElementById("btnLoadMoreProducts")?.addEventListener("click", loadMoreProducts);

  document.querySelectorAll("#productCategoryFilterBar .filter-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      document.querySelectorAll("#productCategoryFilterBar .filter-chip").forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      state.selectedProductCategory = chip.dataset.cat;
      filterAndRenderProducts();
    });
  });

  // Weights drawer toggle
  const drawer = document.getElementById("weightsDrawer");
  document.getElementById("btnToggleWeights")?.addEventListener("click", () => {
    drawer.classList.toggle("hidden");
    if (window.lucide) window.lucide.createIcons();
  });
  document.getElementById("btnCloseDrawer")?.addEventListener("click", () => {
    drawer.classList.add("hidden");
  });

  // DB Modal toggle
  const dbModal = document.getElementById("dbModal");
  document.getElementById("dbStatusBadge")?.addEventListener("click", () => {
    dbModal.classList.remove("hidden");
    fetchDbModalDetails();
  });
  document.getElementById("btnCloseDbModal")?.addEventListener("click", () => {
    dbModal.classList.add("hidden");
  });

  // Live Reconnect
  document.getElementById("btnConnectLive")?.addEventListener("click", handleLiveReconnect);

  // Apply weights
  document.getElementById("btnApplyWeights")?.addEventListener("click", applyWeightsAndRefresh);
  document.getElementById("btnResetWeights")?.addEventListener("click", resetWeights);
}

function setupSliders() {
  const mapping = [
    { id: "sliderContent", key: "content", label: "valContent" },
    { id: "sliderEngagement", key: "engagement", label: "valEngagement" },
    { id: "sliderSocial", key: "social", label: "valSocial" },
    { id: "sliderCommerce", key: "commerce", label: "valCommerce" },
    { id: "sliderPopularity", key: "popularity", label: "valPopularity" },
    { id: "sliderFreshness", key: "freshness", label: "valFreshness" },
  ];

  mapping.forEach(({ id, key, label }) => {
    const el = document.getElementById(id);
    const lbl = document.getElementById(label);
    if (el && lbl) {
      el.addEventListener("input", (e) => {
        const val = parseFloat(e.target.value);
        state.weights[key] = val;
        lbl.textContent = val.toFixed(2);
      });
    }
  });
}

function resetWeights() {
  state.weights = {
    content: 0.30,
    engagement: 0.20,
    social: 0.15,
    commerce: 0.15,
    popularity: 0.10,
    freshness: 0.10,
  };
  for (const [k, v] of Object.entries(state.weights)) {
    const keyCap = k.charAt(0).toUpperCase() + k.slice(1);
    const slider = document.getElementById(`slider${keyCap}`);
    const valLabel = document.getElementById(`val${keyCap}`);
    if (slider) slider.value = v;
    if (valLabel) valLabel.textContent = v.toFixed(2);
  }
  showToast("Weights reset to default values");
}

async function applyWeightsAndRefresh() {
  document.getElementById("weightsDrawer")?.classList.add("hidden");
  showToast("Re-ranking feed with new formula weights...");
  try {
    const res = await fetch(`${API_BASE}/recommendations/refresh/${state.currentUserId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ weights: state.weights, limit: 15 }),
    });
    if (res.ok) {
      const data = await res.json();
      state.feedPosts = data.posts || [];
      renderFeedPosts(state.feedPosts, data);
      showToast("Feed re-ranked successfully!");
      // Switch to feed screen if not active
      if (state.activeScreen !== "screen-feed") {
        document.querySelector('[data-screen="screen-feed"]')?.click();
      }
    }
  } catch (err) {
    showToast(`Failed to refresh feed: ${err.message}`);
  }
}

// ============================================================================
// SCREEN 1: Dashboard Logic
// ============================================================================
async function loadDashboard() {
  try {
    const res = await fetch(`${API_BASE}/analytics`);
    if (!res.ok) return;
    const data = await res.json();

    const m = data.metrics || {};
    document.getElementById("kpiUsers").textContent = m.total_users || "6";
    document.getElementById("kpiPosts").textContent = m.total_posts || "125";
    document.getElementById("kpiProducts").textContent = m.total_products || "54";
    document.getElementById("kpiEngagement").textContent = `${m.average_engagement_rate_pct || 64.2}%`;

    // Render Category Distribution Chart
    renderCategoryChart(data.category_distribution || []);

    // Render Benchmark Comparison Chart
    renderBenchmarkSummaryChart(data.benchmark_evaluation?.comparison || {});

    // Render Trending Posts Grid
    await loadTrendingSection();
  } catch (err) {
    console.error("Dashboard error:", err);
  }
}

function renderCategoryChart(categories) {
  const ctx = document.getElementById("categoryChart")?.getContext("2d");
  if (!ctx) return;
  if (state.charts.category) state.charts.category.destroy();

  const labels = categories.map((c) => c.category);
  const counts = categories.map((c) => c.posts_count);

  state.charts.category = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Catalog Posts",
          data: counts,
          backgroundColor: ["#0f172a", "#334155", "#475569", "#64748b", "#94a3b8"],
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: "#f1f5f9" } },
        x: { grid: { display: false } },
      },
    },
  });
}

function renderBenchmarkSummaryChart(comparison) {
  const ctx = document.getElementById("benchmarkChart")?.getContext("2d");
  if (!ctx) return;
  if (state.charts.benchmark) state.charts.benchmark.destroy();

  const models = Object.keys(comparison);
  const ndcgScores = models.map((m) => comparison[m]["NDCG@10"] || 0.0);
  const precisionScores = models.map((m) => comparison[m]["Precision@10"] || 0.0);

  state.charts.benchmark = new Chart(ctx, {
    type: "bar",
    data: {
      labels: models,
      datasets: [
        {
          label: "NDCG@10",
          data: ndcgScores,
          backgroundColor: "#2563eb",
          borderRadius: 6,
        },
        {
          label: "Precision@10",
          data: precisionScores,
          backgroundColor: "#10b981",
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "top" } },
      scales: {
        y: { beginAtZero: true, max: 1.0, grid: { color: "#f1f5f9" } },
        x: { grid: { display: false } },
      },
    },
  });
}

async function loadTrendingSection() {
  try {
    const res = await fetch(`${API_BASE}/trending?limit=8`);
    if (!res.ok) return;
    const data = await res.json();
    const container = document.getElementById("trendingPostsGrid");
    if (!container) return;

    container.innerHTML = (data.posts || []).map((p) => `
      <div class="trending-card">
        <img src="${p.media_url || p.image_url || 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600'}" alt="Trending">
        <div class="trending-info">
          <div class="flex items-center justify-between mb-1">
            <span class="badge badge-neutral">${p.category_id ? p.category_id.replace('cat_', '').toUpperCase() : (p.category || 'GENERAL')}</span>
            <span class="text-xs text-slate-500 font-mono">⚡ ${p.like_count || p.likes || 120} likes</span>
          </div>
          <p class="text-xs font-semibold text-slate-800 line-clamp-2">${p.caption || 'Trending viral lifestyle look'}</p>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Trending error:", err);
  }
}

// ============================================================================
// SCREEN 2: Personalized Feed Logic (With Infinite Pagination)
// ============================================================================
async function loadPersonalizedFeed(reset = true) {
  if (state.isFeedLoading) return;
  state.isFeedLoading = true;

  const container = document.getElementById("feedPostsContainer");
  const loadMoreBtn = document.getElementById("btnLoadMoreFeed");
  const loadMoreText = document.getElementById("btnLoadMoreFeedText");

  if (reset) {
    state.feedOffset = 0;
    state.feedPosts = [];
    if (container) {
      container.innerHTML = `
        <div class="p-8 text-center text-slate-400">
          <div class="inline-block animate-spin mb-2"><i data-lucide="loader"></i></div>
          <p>Synthesizing taste vectors and ranking personalized posts...</p>
        </div>
      `;
      if (window.lucide) window.lucide.createIcons();
    }
  } else {
    if (loadMoreBtn) {
      loadMoreBtn.disabled = true;
      if (loadMoreText) loadMoreText.textContent = "Loading More Recommendations...";
    }
  }

  try {
    if (reset) {
      await loadFeedUserProfile(state.currentUserId);
    }

    const url = `${API_BASE}/feed/${state.currentUserId}?limit=${state.feedLimit}&offset=${state.feedOffset}&w_content=${state.weights.content}&w_engagement=${state.weights.engagement}&w_social=${state.weights.social}&w_commerce=${state.weights.commerce}&w_popularity=${state.weights.popularity}&w_freshness=${state.weights.freshness}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const newPosts = data.posts || [];
    state.feedTotal = data.total_available || (state.feedPosts.length + newPosts.length);

    if (reset) {
      state.feedPosts = newPosts;
    } else {
      state.feedPosts = state.feedPosts.concat(newPosts);
    }

    renderFeedPosts(state.feedPosts, data);
  } catch (err) {
    if (container && reset) {
      container.innerHTML = `
        <div class="p-8 text-center text-rose-500">
          <p class="font-bold">Failed to load feed</p>
          <p class="text-xs text-slate-500 mt-1">${err.message}</p>
        </div>
      `;
    }
  } finally {
    state.isFeedLoading = false;
    if (loadMoreBtn) {
      const isExhausted = state.feedPosts.length >= state.feedTotal;
      loadMoreBtn.disabled = isExhausted;
      if (loadMoreText) {
        loadMoreText.textContent = isExhausted ? "All Recommendations Caught Up" : "Load More Recommendations";
      }
    }
  }
}

async function loadMoreFeedPosts() {
  if (state.isFeedLoading) return;
  if (state.feedPosts.length >= state.feedTotal && state.feedTotal > 0) return;
  state.feedOffset = state.feedPosts.length;
  await loadPersonalizedFeed(false);
}

async function loadFeedUserProfile(userId) {
  try {
    const res = await fetch(`${API_BASE}/user/${userId}/interests`);
    if (!res.ok) return;
    const user = await res.json();

    const currentUserObj = state.users.find((u) => u.user_id === userId) || {};
    document.getElementById("feedUserName").textContent = currentUserObj.name || userId;
    document.getElementById("feedUserRole").textContent = currentUserObj.role || "Shopper";
    document.getElementById("feedUserBio").textContent = currentUserObj.bio || "Active platform shopper";
    document.getElementById("feedUserAvatar").src = currentUserObj.avatar_url || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100";

    const s = user.stats || {};
    document.getElementById("feedUserViews").textContent = s.views_count || 0;
    document.getElementById("feedUserLikes").textContent = s.engagements_count || 0;
    document.getElementById("feedUserCart").textContent = s.cart_items_count || 0;
    document.getElementById("feedUserFollows").textContent = (user.followed_creators || []).length;

    // Render affinity bars
    const affContainer = document.getElementById("feedUserAffinities");
    if (affContainer) {
      affContainer.innerHTML = (user.top_categories || []).slice(0, 4).map((c) => {
        const pct = Math.round(c.affinity * 100);
        return `
          <div class="affinity-bar-item">
            <div class="affinity-label-row">
              <span class="font-medium">${c.category.replace('cat_', '').replace('_', ' ').toUpperCase()}</span>
              <span class="font-mono font-bold">${pct}%</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill" style="width: ${pct}%"></div>
            </div>
          </div>
        `;
      }).join("");
    }
  } catch (err) {
    console.error("Profile error:", err);
  }
}

function renderFeedPosts(posts, meta) {
  const container = document.getElementById("feedPostsContainer");
  if (!container) return;

  document.getElementById("feedCountBadge").textContent = `${posts.length} Posts Ranked`;
  document.getElementById("feedLatency").textContent = `${meta.execution_time_ms || 2.4} ms`;
  
  const paginationText = document.getElementById("feedPaginationText");
  if (paginationText) {
    paginationText.textContent = `Showing ${posts.length} of ${state.feedTotal || posts.length} Recommended Posts`;
  }

  const coldStartBadge = document.getElementById("feedColdStartBadge");
  if (meta.cold_start) {
    coldStartBadge?.classList.remove("hidden");
  } else {
    coldStartBadge?.classList.add("hidden");
  }

  if (posts.length === 0) {
    container.innerHTML = `
      <div class="p-12 text-center text-slate-400 bg-white rounded-xl border border-slate-200">
        <i data-lucide="inbox" class="w-12 h-12 mx-auto mb-2 text-slate-300"></i>
        <p class="font-semibold text-slate-600">No recommended posts found</p>
        <p class="text-xs text-slate-400 mt-1">Try resetting weights or exploring other categories.</p>
      </div>
    `;
    if (window.lucide) window.lucide.createIcons();
    return;
  }

  container.innerHTML = posts.map((post, idx) => {
    const isLiked = state.likedPosts.has(post.post_id);
    const isBookmarked = state.bookmarkedPosts.has(post.post_id);
    const reasons = post.explanation || ["High overall platform engagement"];
    const comp = post.components || {};

    let pinnedHtml = "";
    if (post.pinned_product) {
      const prod = post.pinned_product;
      pinnedHtml = `
        <div class="pinned-product-banner">
          <div class="product-mini-details">
            <img class="product-mini-img" src="${prod.image_url || 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=100'}" alt="Product">
            <div>
              <span class="product-mini-title">${prod.title || 'Curated Product'}</span>
              <span class="product-mini-price ml-2">$${prod.price || '49.99'}</span>
            </div>
          </div>
          <button class="btn btn-sm btn-primary" onclick="handleAddToCart('${post.post_id}', '${prod.title || 'Product'}')">
            <i data-lucide="shopping-cart"></i>
            <span>Add to Cart</span>
          </button>
        </div>
      `;
    }

    return `
      <article class="post-card">
        <div class="post-media-box">
          <img src="${post.image_url || 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600'}" alt="${post.caption}">
          <span class="post-rank-badge">#${idx + 1} RANK</span>
        </div>

        <div class="post-content-box">
          <div>
            <div class="post-header-row">
              <div class="creator-info">
                <span class="creator-name">@${post.author_name || 'creator'}</span>
                <span class="badge badge-neutral">${post.category || 'General'}</span>
              </div>
              <div class="post-score-pill" title="Hybrid Multi-Objective Recommendation Score">
                <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
                <span>Match: ${(post.final_score * 100).toFixed(1)}%</span>
              </div>
            </div>

            <p class="post-caption">${post.caption}</p>

            <!-- Evidence Box (Section 9) -->
            <div class="reasons-box">
              <span class="reasons-title">
                <i data-lucide="check-circle" class="w-3.5 h-3.5"></i>
                Why this is recommended:
              </span>
              <ul class="reasons-list">
                ${reasons.map((r) => `<li>${r}</li>`).join("")}
              </ul>
            </div>

            <!-- Scoring Components Breakdown -->
            <div class="components-row">
              <span class="component-pill" title="Content Similarity">Sim: ${(comp.content_similarity || 0).toFixed(2)}</span>
              <span class="component-pill" title="Collaborative / User Engagement">CF: ${(comp.user_engagement || 0).toFixed(2)}</span>
              <span class="component-pill" title="Social Follow Relevance">Social: ${(comp.social_relevance || 0).toFixed(2)}</span>
              <span class="component-pill" title="Commerce & Cart Alignment">Cart: ${(comp.commerce_relevance || 0).toFixed(2)}</span>
              <span class="component-pill" title="Global Popularity">Pop: ${(comp.popularity || 0).toFixed(2)}</span>
              <span class="component-pill" title="Freshness">Fresh: ${(comp.freshness || 0).toFixed(2)}</span>
            </div>

            ${pinnedHtml}
          </div>

          <!-- Interaction Actions -->
          <div class="post-actions-row">
            <div class="action-buttons-group">
              <button class="btn-action ${isLiked ? 'active-like' : ''}" onclick="handleInteraction('${post.post_id}', 'like', this)">
                <i data-lucide="heart" class="w-3.5 h-3.5"></i>
                <span class="count">${post.like_count + (isLiked ? 1 : 0)}</span>
              </button>
              <button class="btn-action ${isBookmarked ? 'active-bookmark' : ''}" onclick="handleInteraction('${post.post_id}', 'bookmark', this)">
                <i data-lucide="bookmark" class="w-3.5 h-3.5"></i>
                <span>Save</span>
              </button>
              <button class="btn-action" onclick="handleInteraction('${post.post_id}', 'share', this)">
                <i data-lucide="share-2" class="w-3.5 h-3.5"></i>
                <span>${post.share_count}</span>
              </button>
            </div>
            <span class="text-xs text-slate-400 font-mono">${post.view_count || 120} views</span>
          </div>
        </div>
      </article>
    `;
  }).join("");

  if (window.lucide) window.lucide.createIcons();
}

// ============================================================================
// Real-Time Interaction Handling
// ============================================================================
async function handleInteraction(postId, type, btnEl) {
  if (type === "like") {
    if (state.likedPosts.has(postId)) {
      state.likedPosts.delete(postId);
      btnEl?.classList.remove("active-like");
    } else {
      state.likedPosts.add(postId);
      btnEl?.classList.add("active-like");
    }
  } else if (type === "bookmark") {
    if (state.bookmarkedPosts.has(postId)) {
      state.bookmarkedPosts.delete(postId);
      btnEl?.classList.remove("active-bookmark");
    } else {
      state.bookmarkedPosts.add(postId);
      btnEl?.classList.add("active-bookmark");
    }
  }

  showToast(`Recorded '${type}' on post. Updating user taste profile in real-time.`);

  try {
    await fetch(`${API_BASE}/interactions/engage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: state.currentUserId,
        post_id: postId,
        interaction_type: type,
      }),
    });
  } catch (err) {
    console.error("Interaction record failed:", err);
  }
}

async function handleAddToCart(postId, title) {
  showToast(`Added '${title}' to shopping cart!`);
  try {
    await fetch(`${API_BASE}/interactions/engage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: state.currentUserId,
        post_id: postId,
        interaction_type: "add_to_cart",
      }),
    });
    // Refresh user profile stats
    loadFeedUserProfile(state.currentUserId);
  } catch (err) {
    console.error("Cart error:", err);
  }
}

// ============================================================================
// SCREEN 3: Analytics Logic
// ============================================================================
async function loadAnalytics() {
  renderComponentWeightsChart();
  renderScoreDistributionChart();
  await runBenchmarkEvaluation();
}

function renderComponentWeightsChart() {
  const ctx = document.getElementById("componentsBarChart")?.getContext("2d");
  if (!ctx) return;
  if (state.charts.components) state.charts.components.destroy();

  const labels = ["Content Sim", "Engagement (CF)", "Social Follow", "Commerce/Cart", "Popularity", "Freshness"];
  const weights = [
    state.weights.content,
    state.weights.engagement,
    state.weights.social,
    state.weights.commerce,
    state.weights.popularity,
    state.weights.freshness,
  ];

  state.charts.components = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Formula Weight (w_i)",
          data: weights,
          backgroundColor: ["#2563eb", "#4f46e5", "#059669", "#d97706", "#dc2626", "#0891b2"],
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, max: 0.5, grid: { color: "#f1f5f9" } },
        x: { grid: { display: false } },
      },
    },
  });
}

function renderScoreDistributionChart() {
  const ctx = document.getElementById("scoreDistributionChart")?.getContext("2d");
  if (!ctx) return;
  if (state.charts.scoreDist) state.charts.scoreDist.destroy();

  // Bucket post scores
  const buckets = [0, 0, 0, 0, 0];
  state.feedPosts.forEach((p) => {
    const s = p.final_score || 0;
    if (s < 0.2) buckets[0]++;
    else if (s < 0.4) buckets[1]++;
    else if (s < 0.6) buckets[2]++;
    else if (s < 0.8) buckets[3]++;
    else buckets[4]++;
  });

  state.charts.scoreDist = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["0.0–0.2", "0.2–0.4", "0.4–0.6", "0.6–0.8", "0.8–1.0"],
      datasets: [
        {
          label: "Number of Ranked Posts",
          data: buckets,
          backgroundColor: "#0f172a",
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: "#f1f5f9" } },
        x: { grid: { display: false } },
      },
    },
  });
}

async function runBenchmarkEvaluation() {
  try {
    const res = await fetch(`${API_BASE}/metrics/evaluate?k=10`);
    if (!res.ok) return;
    const data = await res.json();
    const tableBody = document.getElementById("benchmarkTableBody");
    if (!tableBody) return;

    const comp = data.comparison || {};
    tableBody.innerHTML = Object.entries(comp).map(([model, m]) => {
      const isHybrid = model === "Hybrid";
      return `
        <tr class="${isHybrid ? 'highlight-row' : ''}">
          <td class="font-bold flex items-center gap-1.5">
            ${isHybrid ? '<i data-lucide="award" class="w-4 h-4 text-emerald-600"></i>' : ''}
            <span>${model}</span>
          </td>
          <td class="font-mono">${(m['Precision@10'] || 0).toFixed(4)}</td>
          <td class="font-mono">${(m['Recall@10'] || 0).toFixed(4)}</td>
          <td class="font-mono font-bold ${isHybrid ? 'text-emerald-700' : ''}">${(m['NDCG@10'] || 0).toFixed(4)}</td>
          <td class="font-mono">${(m['MAP'] || 0).toFixed(4)}</td>
          <td class="font-mono">${((m['Catalog Coverage'] || 0) * 100).toFixed(1)}%</td>
          <td class="font-mono">${(m['Category Diversity'] || 0).toFixed(3)}</td>
          <td class="font-mono">${(m['Novelty (bits)'] || 0).toFixed(2)}</td>
        </tr>
      `;
    }).join("");

    if (window.lucide) window.lucide.createIcons();
  } catch (err) {
    console.error("Benchmark error:", err);
  }
}

// ============================================================================
// SCREEN 4: User Insights Logic
// ============================================================================
async function loadUserInsights() {
  try {
    const res = await fetch(`${API_BASE}/user/${state.currentUserId}/interests`);
    if (!res.ok) return;
    const data = await res.json();

    const currentUserObj = state.users.find((u) => u.user_id === state.currentUserId) || {};
    document.getElementById("insightsName").textContent = currentUserObj.name || state.currentUserId;
    document.getElementById("insightsBio").textContent = currentUserObj.bio || "Active Shopper";
    document.getElementById("insightsRole").textContent = currentUserObj.role || "Shopper";
    document.getElementById("insightsAvatar").src = currentUserObj.avatar_url || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100";

    const s = data.stats || {};
    document.getElementById("insViews").textContent = s.views_count || 0;
    document.getElementById("insLikes").textContent = s.engagements_count || 0;
    document.getElementById("insCart").textContent = s.cart_items_count || 0;
    document.getElementById("insOrders").textContent = s.orders_count || 0;

    // Category affinity bars
    const barsContainer = document.getElementById("insightsCategoryBars");
    if (barsContainer) {
      barsContainer.innerHTML = (data.top_categories || []).map((c) => {
        const pct = Math.round(c.affinity * 100);
        return `
          <div class="space-y-1">
            <div class="flex justify-between text-xs text-slate-700">
              <span class="font-medium">${c.category.replace('cat_', '').replace('_', ' ').toUpperCase()}</span>
              <span class="font-mono font-bold">${pct}%</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill" style="width: ${pct}%"></div>
            </div>
          </div>
        `;
      }).join("");
    }

    // Shopping Categories Pills
    const shopPills = document.getElementById("insightsShoppingPills");
    if (shopPills) {
      shopPills.innerHTML = (data.shopping_categories || ["Fashion", "Apparel"]).map((c) => `
        <span class="badge badge-primary">${c.toUpperCase()}</span>
      `).join("");
    }

    // Followed Creators Pills
    const followList = document.getElementById("insightsFollowsList");
    if (followList) {
      followList.innerHTML = (data.followed_creators || ["@aurora_fashion", "@alex_tech"]).map((c) => `
        <span class="badge badge-neutral">@${c}</span>
      `).join("");
    }
  } catch (err) {
    console.error("User insights error:", err);
  }
}

// ============================================================================
// SCREEN 5: Product Recommendations Logic (With Pagination & Category Filters)
// ============================================================================
async function loadProductRecommendations(reset = true) {
  if (state.isProductsLoading) return;
  state.isProductsLoading = true;

  const container = document.getElementById("productRecsGrid");
  const loadMoreBtn = document.getElementById("btnLoadMoreProducts");
  const loadMoreText = document.getElementById("btnLoadMoreProductsText");

  if (reset) {
    state.productOffset = 0;
    state.productRecs = [];
    if (container) {
      container.innerHTML = `
        <div class="col-span-full p-8 text-center text-slate-400">
          <div class="inline-block animate-spin mb-2"><i data-lucide="loader"></i></div>
          <p>Loading personalized e-commerce products for ${state.currentUserId}...</p>
        </div>
      `;
      if (window.lucide) window.lucide.createIcons();
    }
  } else {
    if (loadMoreBtn) {
      loadMoreBtn.disabled = true;
      if (loadMoreText) loadMoreText.textContent = "Loading More Products...";
    }
  }

  try {
    const res = await fetch(`${API_BASE}/products/recommendations/${state.currentUserId}?limit=${state.productLimit}&offset=${state.productOffset}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const prods = data.products || [];
    if (reset) {
      state.productRecs = prods;
    } else {
      state.productRecs = state.productRecs.concat(prods);
    }

    state.productTotal = data.total_available || (state.productRecs.length + (prods.length < state.productLimit ? 0 : 25));

    filterAndRenderProducts();
  } catch (err) {
    if (container && reset) {
      container.innerHTML = `<p class="col-span-full text-rose-500 text-center">Failed: ${err.message}</p>`;
    }
  } finally {
    state.isProductsLoading = false;
    if (loadMoreBtn) {
      const isExhausted = state.productRecs.length >= state.productTotal || (state.productRecs.length % state.productLimit !== 0 && state.productRecs.length > 0);
      loadMoreBtn.disabled = isExhausted;
      if (loadMoreText) {
        loadMoreText.textContent = isExhausted ? "All Products Caught Up" : "Load More Products";
      }
    }
  }
}

async function loadMoreProducts() {
  if (state.isProductsLoading) return;
  state.productOffset = state.productRecs.length;
  await loadProductRecommendations(false);
}

function filterAndRenderProducts() {
  const container = document.getElementById("productRecsGrid");
  if (!container) return;

  let displayList = state.productRecs;
  if (state.selectedProductCategory && state.selectedProductCategory !== "all") {
    displayList = displayList.filter(p => (p.category || "").toLowerCase() === state.selectedProductCategory.toLowerCase());
  }

  const paginationText = document.getElementById("productPaginationText");
  if (paginationText) {
    paginationText.textContent = `Showing ${displayList.length} of ${state.productRecs.length} Recommended Products`;
  }

  if (displayList.length === 0) {
    container.innerHTML = `<p class="col-span-full text-center text-slate-400 p-8">No products found for this category</p>`;
    return;
  }

  container.innerHTML = displayList.map((prod) => `
    <div class="product-card">
      <div class="product-img-box">
        <img src="${prod.image_url || 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600'}" alt="${prod.title}">
        <span class="product-sim-badge">${(prod.similarity_score * 100).toFixed(0)}% MATCH</span>
      </div>
      <div class="product-body">
        <span class="badge badge-neutral mb-1">${prod.category || 'General'}</span>
        <h4 class="product-title line-clamp-1">${prod.title}</h4>
        <span class="product-reason">${prod.reason}</span>
        <div class="product-price-row">
          <span class="product-price">$${prod.price.toFixed(2)}</span>
          <button class="btn btn-sm btn-primary" onclick="showToast('Added to cart!')">
            <i data-lucide="shopping-cart"></i>
            <span>Add</span>
          </button>
        </div>
      </div>
    </div>
  `).join("");

  if (window.lucide) window.lucide.createIcons();
}

// ============================================================================
// Global Helpers: Health, DB Modal & Toast
// ============================================================================
async function fetchHealthStatus() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) return;
    const data = await res.json();
    const isLive = data.database?.is_live_mongodb;
    const textEl = document.getElementById("dbStatusText");
    const dotEl = document.querySelector(".db-dot");

    if (isLive) {
      textEl.textContent = "MongoDB Atlas Connected";
      dotEl.style.backgroundColor = "#10b981";
    } else {
      textEl.textContent = "Resilient Store (1,036 Docs)";
      dotEl.style.backgroundColor = "#3b82f6";
    }
  } catch (err) {
    document.getElementById("dbStatusText").textContent = "DB Disconnected";
  }
}

async function fetchDbModalDetails() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) return;
    const data = await res.json();
    const dbInfo = data.database || {};

    const statusBanner = document.getElementById("modalDbStatus");
    statusBanner.innerHTML = `
      <p class="font-bold">${dbInfo.status || 'Active'}</p>
      <p class="text-xs text-slate-600 mt-1">Target Cluster: <code class="font-mono">${dbInfo.target_uri || 'Atlas'}</code></p>
      ${dbInfo.last_error ? `<p class="text-xs text-amber-700 mt-1">Note: ${dbInfo.last_error}</p>` : ''}
    `;

    const counts = dbInfo.collection_counts || {};
    const collList = document.getElementById("modalCollectionsList");
    collList.innerHTML = Object.entries(counts).map(([coll, count]) => `
      <div class="coll-badge">
        <span class="coll-name">${coll}</span>
        <span class="coll-count">${count}</span>
      </div>
    `).join("");
  } catch (err) {
    console.error("DB modal error:", err);
  }
}

async function handleLiveReconnect() {
  const uriInput = document.getElementById("inputMongoUri");
  const msgEl = document.getElementById("reconnectStatusMsg");
  const uri = uriInput.value.trim();
  if (!uri) {
    msgEl.textContent = "Please enter a valid MongoDB connection string.";
    msgEl.className = "text-xs text-rose-600 mt-2";
    return;
  }

  msgEl.textContent = "Attempting connection...";
  msgEl.className = "text-xs text-blue-600 mt-2";

  try {
    const res = await fetch(`${API_BASE}/reconnect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ uri }),
    });
    const data = await res.json();
    if (data.success) {
      msgEl.textContent = "Connected successfully to MongoDB Atlas!";
      msgEl.className = "text-xs text-emerald-600 mt-2";
      fetchHealthStatus();
      fetchDbModalDetails();
    } else {
      msgEl.textContent = `Connection failed: ${data.message}`;
      msgEl.className = "text-xs text-rose-600 mt-2";
    }
  } catch (err) {
    msgEl.textContent = `Error: ${err.message}`;
    msgEl.className = "text-xs text-rose-600 mt-2";
  }
}

async function fetchUsers() {
  try {
    const res = await fetch(`${API_BASE}/users`);
    if (!res.ok) return;
    state.users = await res.json();
    const select = document.getElementById("userPicker");
    if (select && state.users.length > 0) {
      select.innerHTML = state.users.map((u) => `
        <option value="${u.user_id}" ${u.user_id === state.currentUserId ? 'selected' : ''}>
          ${u.name} (${u.role || 'Shopper'})
        </option>
      `).join("");
    }
  } catch (err) {
    console.error("Fetch users error:", err);
  }
}

function showToast(message) {
  const toast = document.getElementById("toastBanner");
  const toastText = document.getElementById("toastMessage");
  if (!toast || !toastText) return;

  toastText.textContent = message;
  toast.classList.remove("hidden");

  setTimeout(() => {
    toast.classList.add("hidden");
  }, 3000);
}
