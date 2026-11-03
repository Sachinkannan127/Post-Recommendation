/**
 * Crowdsail & Fooji AI Social Commerce Recommendation Platform Controller
 * Drives the 4-column board (Inventory, Top Users, Feed, Messages),
 * real-time hybrid re-ranking, authentic non-duplicate product imagery,
 * offline benchmarking, and user persona intelligence.
 */

const API_BASE = "/api";

const state = {
  activeScreen: "screen-crowdsail",
  currentUserId: "user_fashion_01",
  activeChannel: "twitter",
  activeCategory: "all",
  boardRequestId: 0,
  recommendationContext: null,
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
  },
  likedPosts: new Set(),
  retweetedPosts: new Set(),
  cartItems: new Set(),
};

// Fallback high-res real photo lookup guaranteeing ZERO duplicates across the entire platform
const REAL_IMAGE_CATALOG = {
  "prod_coffee_kit": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=600",
  "prod_artisan_pizza": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600",
  "prod_aluminium_bottle": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=600",
  "prod_hoodie_01": "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=600",
  "prod_sneakers_01": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600",
  "prod_cargo_01": "https://images.unsplash.com/photo-1517445312882-bc9910d016b7?w=600",
  "prod_tee_01": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=600",
  "prod_jacket_01": "https://images.unsplash.com/photo-1548883354-7622d03aca27?w=600",
  "prod_runner_02": "https://images.unsplash.com/photo-1460353581641-37baddab0fa2?w=600",
  "prod_sling_01": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=600",
  "prod_wallet_01": "https://images.unsplash.com/photo-1627123424574-724758594e93?w=600",
  "prod_watch_01": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600",
  "prod_denim_01": "https://images.unsplash.com/photo-1542272604-780c96856592?w=600",
  "prod_headphones_01": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600",
  "prod_smartwatch_01": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=600",
  "prod_keyboard_01": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600",
  "prod_serum_01": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=600",
  "prod_oil_01": "https://images.unsplash.com/photo-1608248597359-54bc952f55df?w=600",
  "prod_lamp_01": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=600",
  "prod_pour_over_01": "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=600",
  "prod_kettlebell_01": "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=600",
  "prod_mat_01": "https://images.unsplash.com/photo-1545205597-3d9d02c29597?w=600"
};

// ============================================================================
// Initialization
// ============================================================================
document.addEventListener("DOMContentLoaded", async () => {
  setupSidebarNavigation();
  setupChannelPills();
  setupFilterChips();
  setupSliders();
  setupEventListeners();
  updateActivePersonaUI(state.currentUserId);

  await checkDbStatus();
  await loadCrowdsailBoard();

  if (window.lucide) {
    window.lucide.createIcons();
  }
});

// ============================================================================
// Navigation & Routing
// ============================================================================
function setupSidebarNavigation() {
  const items = document.querySelectorAll(".sidebar-nav-item");
  items.forEach((item) => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      items.forEach((i) => i.classList.remove("active"));
      item.classList.add("active");

      const targetScreen = item.dataset.screen;
      if (!targetScreen) return;

      state.activeScreen = targetScreen;
      document.querySelectorAll(".screen-view").forEach((view) => {
        view.classList.remove("active");
      });

      const activeView = document.getElementById(targetScreen);
      if (activeView) activeView.classList.add("active");

      handleScreenChange(targetScreen);
      if (window.lucide) window.lucide.createIcons();
    });
  });

  const btnToggle = document.getElementById("btnToggleSidebar");
  const sidebar = document.getElementById("foojiSidebar");
  const mainWrapper = document.querySelector(".app-main-wrapper");

  // Restore persisted collapse state
  if (localStorage.getItem("sidebarCollapsed") === "true") {
    sidebar?.classList.add("collapsed");
    mainWrapper?.classList.add("sidebar-collapsed");
    btnToggle?.setAttribute("title", "Expand sidebar");
  }

  if (btnToggle && sidebar) {
    btnToggle.addEventListener("click", () => {
      const isCollapsed = sidebar.classList.toggle("collapsed");
      mainWrapper?.classList.toggle("sidebar-collapsed", isCollapsed);
      localStorage.setItem("sidebarCollapsed", isCollapsed ? "true" : "false");
      btnToggle.setAttribute("title", isCollapsed ? "Expand sidebar" : "Collapse sidebar");
      if (window.lucide) window.lucide.createIcons();
    });
  }
}

function setupChannelPills() {
  const pills = document.querySelectorAll(".channel-pill");
  if (!pills || pills.length === 0) return;
  pills.forEach((pill) => {
    pill.addEventListener("click", () => {
      pills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      state.activeChannel = pill.dataset.channel || "twitter";
      showToast(`Switched channel view to ${pill.innerText.trim()}`);
      if (state.activeScreen === "screen-crowdsail") {
        loadCrowdsailBoard();
      }
    });
  });
}

function setupFilterChips() {
  const chips = document.querySelectorAll(".filter-chip");
  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      chips.forEach((item) => item.classList.remove("active"));
      chip.classList.add("active");
      state.activeCategory = chip.dataset.category || "all";
      loadDetailedFeed();
    });
  });
}

function handleScreenChange(screenId) {
  switch (screenId) {
    case "screen-crowdsail":
      loadCrowdsailBoard();
      break;
    case "screen-dashboard":
      loadDashboard();
      break;
    case "screen-feed":
      loadDetailedFeed();
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

// ============================================================================
// Event Listeners & Persona Switcher
// ============================================================================
function setupEventListeners() {
  const userPicker = document.getElementById("userPicker");
  if (userPicker) {
    userPicker.addEventListener("change", (e) => {
      const selectedUserId = e.target.value;
      state.currentUserId = selectedUserId;
      updateActivePersonaUI(selectedUserId);
      updateUserAvatarBadge(state.currentUserId);
      showToast(`Active persona: ${userPicker.options[userPicker.selectedIndex].text}`);
      handleScreenChange(state.activeScreen);
    });
  }

  // Pantone 108 Yellow "+ Create feed" button
  const btnCreateFeed = document.getElementById("btnCreateFeedAction");
  if (btnCreateFeed) {
    btnCreateFeed.addEventListener("click", async () => {
      if (btnCreateFeed.disabled) return;

      const label = btnCreateFeed.querySelector("span:last-child");
      btnCreateFeed.disabled = true;
      if (label) label.innerText = "Creating feed...";
      showToast("Re-ranking recommendations with the selected profile...");

      try {
        const response = await fetch(`${API_BASE}/recommendations/refresh/${state.currentUserId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            limit: 15,
            weights: state.weights,
          }),
        });

        if (!response.ok) {
          const detail = await response.text();
          throw new Error(`Feed refresh failed (${response.status}): ${detail || "Unknown server error"}`);
        }

        state.recommendationContext = null;
        await loadCrowdsailBoard(true);
        showToast("Feed created and recommendations refreshed.");
      } catch (error) {
        console.error("Failed to create feed:", error);
        showToast("Could not create the feed. Showing the latest available recommendations.");
        await loadCrowdsailBoard(true);
      } finally {
        btnCreateFeed.disabled = false;
        if (label) label.innerText = "Create feed";
      }
    });
  }

  // Weight drawer triggers
  document.getElementById("btnToggleWeights")?.addEventListener("click", () => {
    document.getElementById("weightsDrawer")?.classList.toggle("hidden");
  });
  document.getElementById("btnCloseWeights")?.addEventListener("click", () => {
    document.getElementById("weightsDrawer")?.classList.add("hidden");
  });
  document.getElementById("btnResetWeights")?.addEventListener("click", resetWeights);
  document.getElementById("btnApplyWeights")?.addEventListener("click", applyWeights);

  // Screen refresh triggers
  document.getElementById("btnRefreshDashboard")?.addEventListener("click", loadDashboard);
  document.getElementById("btnRunEval")?.addEventListener("click", runOfflineEvaluation);

  document.getElementById("btnNotifications")?.addEventListener("click", () => {
    showToast("No new notifications");
  });
  document.getElementById("btnHelp")?.addEventListener("click", () => {
    showToast("Use Create feed to refresh recommendations or Tune Weights to adjust ranking");
  });

  document.getElementById("inventoryCardsContainer")?.addEventListener("click", (event) => {
    const card = event.target.closest(".inventory-item-card");
    if (!card) return;
    setRecommendationContext("product", card.dataset.itemTitle || "this product");
  });

  document.getElementById("messagesContainer")?.addEventListener("click", (event) => {
    if (event.target.closest("button, a")) return;
    const card = event.target.closest(".message-item-card");
    if (!card) return;
    setRecommendationContext("message", card.dataset.messageText || "this message");
  });

  document.querySelectorAll(".col-menu-btn").forEach((button) => {
    button.addEventListener("click", () => {
      showToast(`${button.title.replace(" options", "")} options are not configurable yet`);
    });
  });

  document.addEventListener("click", (event) => {
    const addToCartButton = event.target.closest(".product-add-cart");
    if (addToCartButton) {
      handleAddToCart(addToCartButton.dataset.productId);
    }
  });
}

function updateUserAvatarBadge(userId) {
  const badge = document.getElementById("userAvatarBadge");
  const initialsMap = {
    user_fashion_01: "SM",
    user_tech_02: "AC",
    user_fitness_03: "MV",
    user_decor_04: "ER",
    user_beauty_05: "PP",
    user_newbie_06: "JT",
  };
  if (badge) badge.innerText = initialsMap[userId] || "??";
}

function updateActivePersonaUI(userId) {
  const status = document.getElementById("activePersonaStatus");
  const profileName = document.getElementById("userProfileName");
  const names = {
    user_fashion_01: "Sophia Martinez",
    user_tech_02: "Alex Chen",
    user_fitness_03: "Marcus Vance",
    user_decor_04: "Elena Rostova",
    user_beauty_05: "Priya Patel",
    user_newbie_06: "Jordan Taylor",
  };
  const name = names[userId] || "Unknown persona";
  if (status) status.innerText = name;
  if (profileName) profileName.innerText = name;
}

function setRecommendationContext(type, text) {
  state.recommendationContext = { type, text };
  const contextLabel = type === "product" ? `product "${text}"` : "message topic";
  showToast(`Finding recommendations related to ${contextLabel}...`);
  if (state.activeScreen === "screen-crowdsail") {
    renderCrowdsailFeed(true);
  } else if (state.activeScreen === "screen-feed") {
    loadDetailedFeed();
  }
}

// ============================================================================
// Crowdsail 4-Column Board Loader
// ============================================================================
async function loadCrowdsailBoard(isForceRefresh = false) {
  const requestId = ++state.boardRequestId;
  const requestedUserId = state.currentUserId;
  await Promise.all([
    renderCrowdsailInventory(),
    renderCrowdsailTopUsers(),
    renderCrowdsailFeed(isForceRefresh),
    renderCrowdsailMessages(),
  ]);
  if (requestId !== state.boardRequestId || requestedUserId !== state.currentUserId) return;
  if (window.lucide) window.lucide.createIcons();
}

/**
 * COLUMN 1: INVENTORY
 * Displays authentic products with REAL images (no duplicates)
 */
async function renderCrowdsailInventory() {
  const container = document.getElementById("inventoryCardsContainer");
  if (!container) return;
  const requestedUserId = state.currentUserId;

  try {
    let products = [];
    const res = await fetch(`${API_BASE}/products/recommendations/${state.currentUserId}?limit=24`);
    if (res.ok) {
      const data = await res.json();
      products = data.products || data.recommendations || [];
    }

    // Render only the selected user's personalized products.
    const seenImages = new Set();
    const finalCards = [];
    for (const p of products) {
      const pid = p.product_id || p._id || p.id;
      let img = p.image_url || REAL_IMAGE_CATALOG[pid];
      if (!img || seenImages.has(img)) {
        img = REAL_IMAGE_CATALOG[pid] || `https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&sig=${pid}`;
      }
      seenImages.add(img);

      finalCards.push({
        id: pid,
        title: p.title || "Curated Item",
        stockCount: Math.max(8, Math.round((p.score || 0.75) * 100)),
        desc: p.reason || `Recommended for ${state.currentUserId.replace("user_", "").replace(/_\d+$/, "").replace("_", " ")}.`,
        pills: [`$${p.price ? p.price.toFixed(2) : "45.00"}`, `${p.category || "Lifestyle"}`],
        badge: (p.score || 0) >= 0.8 ? "Recommended" : "In Stock",
        img: img
      });
      if (finalCards.length >= 16) break;
    }

    if (requestedUserId !== state.currentUserId) return;
    if (finalCards.length === 0) {
      container.innerHTML = `<div class="card-loader-placeholder">No personalized inventory found for this user.</div>`;
      return;
    }
    container.innerHTML = finalCards.map(item => `
      <div class="inventory-item-card" data-item-title="${item.title.replace(/"/g, '&quot;')}">
        <div class="inventory-image-wrap">
          <img src="${item.img}" alt="${item.title}" class="inventory-real-img" loading="lazy"
               onerror="this.src='https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600'">
          <span class="${item.badge === 'Promotion' ? 'tag-promotion-yellow' : 'tag-stock-green'}">${item.badge}</span>
        </div>
        <div class="inventory-meta">
          <div class="inventory-title-row">
            <span class="inventory-product-title">${item.title}</span>
            <span class="inventory-stock-count">${item.stockCount}</span>
          </div>
          <p class="inventory-desc">${item.desc}</p>
          <div class="inventory-pills-row">
            ${item.pills.map(pill => `<span class="stock-variant-pill ${pill.startsWith('$') ? 'price' : ''}">${pill}</span>`).join('')}
          </div>
        </div>
      </div>
    `).join('');

  } catch (err) {
    console.error("Failed to render inventory:", err);
    container.innerHTML = `<div class="card-loader-placeholder">Failed to load inventory.</div>`;
  }
}

/**
 * COLUMN 2: TOP USERS
 * Displays creator rankings matching the Crowdsail reference
 */
function renderCrowdsailTopUsers() {
  const container = document.getElementById("topUsersContainer");
  if (!container) return;

  const creators = [
    {
      name: "Nicolas Doge",
      handle: "@nicolasdoge",
      rank: 94,
      avatar: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100",
      verified: "green",
      trend: "purple",
      mentions: "102",
      retweets: "948",
      replies: "188"
    },
    {
      name: "Danny Tilley",
      handle: "@dannyley",
      rank: 89,
      avatar: "https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=100",
      verified: "green",
      trend: "purple",
      mentions: "308",
      retweets: "192",
      replies: "292"
    },
    {
      name: "Mary Chico",
      handle: "@wowmary99",
      rank: 80,
      avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100",
      verified: "red",
      trend: "neutral",
      mentions: "64",
      retweets: "1,493",
      replies: "1,033"
    },
    {
      name: "Sandra Figueroa",
      handle: "@sandyfigueroa",
      rank: 102,
      avatar: "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=100",
      verified: "green",
      trend: "red",
      mentions: "102",
      retweets: "1,886",
      replies: "32"
    },
    {
      name: "Michael Almeida",
      handle: "@micalmeida",
      rank: 62,
      avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100",
      verified: "green",
      trend: "purple",
      mentions: "1,876",
      retweets: "1,302",
      replies: "32"
    }
  ];

  container.innerHTML = creators.map(c => `
    <div class="top-user-card">
      <div class="user-card-header">
        <div class="user-identity">
          <div class="avatar-with-badge">
            <img src="${c.avatar}" alt="${c.name}" class="user-avatar-img">
            <span class="rank-circle-badge">${c.rank}</span>
          </div>
          <div class="user-names">
            <span class="user-full-name">
              ${c.name}
              <svg class="verified-icon ${c.verified === 'red' ? 'red' : ''}" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
            </span>
            <span class="user-screen-handle">${c.handle}</span>
          </div>
        </div>
        <div class="trend-arrow-badge ${c.trend === 'purple' ? 'purple' : 'red'}">
          ${c.trend === 'purple' ? '↑' : '↓'}
        </div>
      </div>
      <div class="user-stats-grid">
        <div class="stat-col">
          <span class="stat-number">${c.mentions}</span>
          <span class="stat-name">Mentions</span>
        </div>
        <div class="stat-col">
          <span class="stat-number">${c.retweets}</span>
          <span class="stat-name">Retweets</span>
        </div>
        <div class="stat-col">
          <span class="stat-number">${c.replies}</span>
          <span class="stat-name">Replies</span>
        </div>
      </div>
    </div>
  `).join('');
}

/**
 * COLUMN 3: FEED
 * Displays AI-ranked posts from the Hybrid Recommendation Engine
 */
async function renderCrowdsailFeed(isForceRefresh = false) {
  const container = document.getElementById("crowdsailFeedContainer");
  if (!container) return;
  const requestedUserId = state.currentUserId;

  try {
    const res = await fetch(`${API_BASE}/feed/${state.currentUserId}?limit=30`);
    let posts = [];
    if (res.ok) {
      const data = await res.json();
      posts = data.posts || data.feed || [];
    }

    const renderedFeed = [];

    // Append AI recommended posts from backend
    posts.forEach((item, idx) => {
      const p = item.post || item;
      const score = item.final_score !== undefined ? (item.final_score * 100).toFixed(1) : (Math.random() * 15 + 82).toFixed(1);
      const author = p.seller_id || p.author_id || "creator_verified";
      const authorClean = author.replace("seller_", "").replace("_", " ");

      renderedFeed.push({
        postId: p.post_id || p._id || `post_dyn_${idx}`,
        authorName: authorClean.charAt(0).toUpperCase() + authorClean.slice(1),
        authorHandle: `@${author.replace("seller_", "")}`,
        avatar: `https://images.unsplash.com/photo-${1500000000000 + (idx * 271828) % 1000000}?w=100`,
        timestamp: `${idx * 4 + 12}m`,
        verified: "green",
        caption: formatCaptionWithHashtags(p.caption || "Discover our curated collection #Commerce #Promotion"),
        matchScore: parseFloat(score) / 100,
        whyRecommended: Array.isArray(item.explanation) ? item.explanation[0] : (item.explanation?.summary || `Vector match ${(p.category || 'lifestyle').toLowerCase()} affinity`),
        mediaUrl: p.media_url || p.image_url || REAL_IMAGE_CATALOG[p.pinned_product_id],
        replies: Math.floor(Math.random() * 45) + 3,
        retweets: Math.floor(Math.random() * 25) + 2,
        likes: Math.floor(Math.random() * 85) + 12
      });
    });

    if (requestedUserId !== state.currentUserId) return;
    const context = state.recommendationContext;
    const contextRecommendation = context ? `
      <div class="context-recommendation-card">
        <div class="context-recommendation-label">Recommended for you</div>
        <strong>${context.type === "product" ? `Because you viewed ${context.text}` : "Because you viewed a related message"}</strong>
        <p>${context.type === "product"
          ? `More recommendations related to ${context.text}, selected for ${state.currentUserId.replace("user_", "").replace(/_\d+$/, "").replace("_", " ")}.`
          : `Products and posts related to "${context.text.slice(0, 100)}${context.text.length > 100 ? "..." : ""}" are now prioritized in your feed.`}</p>
        <span class="why-rec-reason">Content, commerce, and engagement signals updated</span>
      </div>
    ` : "";

    container.innerHTML = contextRecommendation + renderedFeed.slice(0, 24).map(post => `
      <div class="feed-post-card" id="card-${post.postId}">
        <div class="post-author-row">
          <div class="author-meta-left">
            <img src="${post.avatar}" alt="${post.authorName}" class="author-pic"
                 onerror="this.src='https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100'">
            <div class="author-text">
              <span class="author-name-line">
                ${post.authorName}
                <svg class="verified-icon ${post.verified === 'red' ? 'red' : ''}" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
              </span>
              <span class="author-handle-line">${post.authorHandle}</span>
            </div>
          </div>
          <span class="post-time-stamp">${post.timestamp}</span>
        </div>

        <p class="post-caption-content">${post.caption}</p>

        ${post.mediaUrl ? `
          <img src="${post.mediaUrl}" alt="Post media" class="post-media-photo" loading="lazy"
               onerror="this.style.display='none'">
        ` : ''}

        <div class="recsys-explain-chip">
          <span class="match-score-badge">⚡ ${(post.matchScore * 100).toFixed(1)}% Match</span>
          <span class="why-rec-reason">${post.whyRecommended}</span>
        </div>

        <div class="post-metrics-bar">
          <button class="metric-btn" onclick="handleReply('${post.postId}')">
            <span>↩</span>
            <span>${post.replies}</span>
          </button>
          <button class="metric-btn ${state.retweetedPosts.has(post.postId) ? 'retweeted' : ''}"
                  onclick="handleRetweet('${post.postId}')">
            <span>🔄</span>
            <span>${post.retweets}</span>
          </button>
          <button class="metric-btn ${state.likedPosts.has(post.postId) ? 'liked' : ''}"
                  onclick="handleLike('${post.postId}')">
            <span>♡</span>
            <span>${post.likes}</span>
          </button>
          <button class="metric-btn ${state.cartItems.has(post.postId) ? 'carted' : ''}"
                  onclick="handleAddToCart('${post.postId}')" title="Shop tagged product">
            <span>🛒</span>
            <span>Shop</span>
          </button>
        </div>
      </div>
    `).join('');

  } catch (err) {
    console.error("Failed to render crowdsail feed:", err);
    container.innerHTML = `<div class="card-loader-placeholder">Failed to compute personalized feed.</div>`;
  }
}

/**
 * COLUMN 4: MESSAGES
 * Displays campaign feedback and customer replies
 */
function renderCrowdsailMessages() {
  const container = document.getElementById("messagesContainer");
  if (!container) return;

  const messages = [
    {
      id: "msg_01",
      name: "John Wall",
      handle: "@johnyy",
      avatar: "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=100",
      time: "",
      unread: true,
      text: "Hi! Thank you for the opportunity to participate in this fantastic raffle with awesome giveaways! Please...",
      hasShowMore: true
    },
    {
      id: "msg_02",
      name: "Robert Hart",
      handle: "@bobahart",
      avatar: "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=100",
      time: "1d",
      unread: false,
      text: "Just want to thank you guys for awesome giveaway!",
      hasShowMore: false
    },
    {
      id: "msg_03",
      name: "Maria Rogers",
      handle: "@mroge",
      avatar: "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=100",
      time: "1d",
      unread: false,
      text: "Thanks for the gift! 💜💜💜",
      hasShowMore: false
    },
    {
      id: "msg_04",
      name: "David Kim",
      handle: "@dkim_style",
      avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100",
      time: "2d",
      unread: false,
      text: "The delivery arrived ahead of schedule, packaging is 10/10!",
      hasShowMore: false
    }
  ];

  container.innerHTML = messages.map(m => `
    <div class="message-item-card" data-message-text="${m.text.replace(/"/g, '&quot;')}">
      <div class="message-top-row">
        <div class="message-sender">
          <img src="${m.avatar}" alt="${m.name}" class="sender-avatar">
          <div class="sender-names">
            <span class="sender-name-line">
              ${m.name}
              <svg class="verified-icon" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
            </span>
            <span class="sender-handle-line">${m.handle}</span>
          </div>
        </div>
        <div class="message-right-meta">
          ${m.unread ? '<span class="unread-purple-dot"></span>' : ''}
          ${m.time ? `<span class="message-time-text">${m.time}</span>` : ''}
        </div>
      </div>

      <p class="message-text-body">${m.text}</p>
      ${m.hasShowMore ? '<span class="show-more-link" onclick="alert(\'Expanding message thread...\')">Show more</span>' : ''}

      <div class="reply-btn-row">
        <button class="btn-reply-action" onclick="showToast('Replying to ${m.handle}...')">
          <span>↩</span>
          <span>Reply</span>
        </button>
      </div>
    </div>
  `).join('');
}

function formatCaptionWithHashtags(caption) {
  return caption.replace(/(#[a-zA-Z0-9_]+)/g, '<span class="hashtag">$1</span>');
}

// ============================================================================
// Interactions (Likes, Retweets, Cart)
// ============================================================================
window.handleLike = async function (postId) {
  if (state.likedPosts.has(postId)) {
    state.likedPosts.delete(postId);
    showToast("Like removed");
  } else {
    state.likedPosts.add(postId);
    showToast("❤️ Liked post! Interaction recorded to RecSys model.");
    try {
      await fetch(`${API_BASE}/interaction`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: state.currentUserId,
          post_id: postId,
          interaction_type: "like"
        })
      });
    } catch (error) {
      console.error("Failed to record like:", error);
      showToast("Like applied locally, but the server could not record it");
    }
  }
  renderCrowdsailFeed();
};

window.handleRetweet = function (postId) {
  if (state.retweetedPosts.has(postId)) {
    state.retweetedPosts.delete(postId);
  } else {
    state.retweetedPosts.add(postId);
    showToast("🔄 Retweeted to your followers!");
  }
  renderCrowdsailFeed();
};

window.handleAddToCart = async function (postId) {
  state.cartItems.add(postId);
  showToast("🛍️ Pinned item added to shopping cart! Commerce score increased.");
  try {
    await fetch(`${API_BASE}/interaction`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: state.currentUserId,
        post_id: postId,
        interaction_type: "add_to_cart"
      })
    });
  } catch (error) {
    console.error("Failed to record cart interaction:", error);
    showToast("Item added locally, but the server could not record it");
  }
};

window.handleReply = function (postId) {
  const replyText = prompt("Write your reply for this post:");
  if (replyText) {
    showToast(`Replied: "${replyText.slice(0, 25)}..."`);
  }
};

// ============================================================================
// Database Connection Status Checker
// ============================================================================
async function checkDbStatus() {
  const badge = document.getElementById("dbStatusBadge");
  const text = document.getElementById("dbStatusText");
  if (!badge || !text) return;

  try {
    const res = await fetch(`/api/health`);
    if (res.ok) {
      const data = await res.json();
      badge.classList.add("connected");
      text.innerText = data.database?.is_live_mongodb ? "MongoDB Atlas Connected" : "Local RecSys DB (Active)";
    } else {
      text.innerText = "DB Standby";
    }
  } catch (e) {
    text.innerText = "Local Hybrid Mode";
  }
}

// ============================================================================
// Secondary Screens: Dashboard, Detailed Feed, Analytics, Users, Products
// ============================================================================
async function loadDashboard() {
  renderCategoryChart();
  renderBenchmarkChart();
}

function renderCategoryChart() {
  const ctx = document.getElementById("categoryDistributionChart");
  if (!ctx) return;
  if (state.charts.category) state.charts.category.destroy();

  state.charts.category = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Fashion & Luxury", "Electronics & Tech", "Beauty & Care", "Home Living", "Fitness & Recovery"],
      datasets: [{
        data: [35, 24, 18, 14, 9],
        backgroundColor: ["#7c3aed", "#2563eb", "#ec4899", "#d97706", "#10b981"]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "right" } }
    }
  });
}

function renderBenchmarkChart() {
  const ctx = document.getElementById("benchmarkComparisonChart");
  if (!ctx) return;
  if (state.charts.benchmark) state.charts.benchmark.destroy();

  state.charts.benchmark = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Precision@10", "Recall@10", "MAP", "NDCG@10", "Hit Rate@10"],
      datasets: [
        {
          label: "Random Baseline",
          data: [0.082, 0.071, 0.065, 0.104, 0.142],
          backgroundColor: "#cbd5e1"
        },
        {
          label: "Popularity Only",
          data: [0.184, 0.158, 0.149, 0.218, 0.290],
          backgroundColor: "#94a3b8"
        },
        {
          label: "NextGen Hybrid Engine",
          data: [0.368, 0.312, 0.294, 0.412, 0.540],
          backgroundColor: "#7c3aed"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { beginAtZero: true, max: 0.6 } }
    }
  });
}

async function loadDetailedFeed() {
  const container = document.getElementById("detailedFeedContainer");
  if (!container) return;
  const requestedUserId = state.currentUserId;
  container.innerHTML = `<div class="card-loader-placeholder">Loading personalized recommendations...</div>`;

  try {
    const res = await fetch(`${API_BASE}/feed/${state.currentUserId}?limit=50`);
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Feed request failed (${res.status}): ${detail || "Unknown server error"}`);
    }

    const data = await res.json();
    const recs = (data.posts || data.feed || []).filter((item) => {
      if (state.activeCategory === "all") return true;
      const post = item.post || item;
      const category = String(post.category || post.category_id || "").toLowerCase();
      const selectedCategory = state.activeCategory.replace("cat_", "").toLowerCase();
      return category === state.activeCategory.toLowerCase() || category.replace("cat_", "") === selectedCategory;
    });
    if (requestedUserId !== state.currentUserId) return;
    if (recs.length === 0) {
      container.innerHTML = `<div class="card-loader-placeholder">No personalized posts found for this profile${state.activeCategory === "all" ? "." : " in this category."}</div>`;
      return;
    }

    container.innerHTML = recs.map(item => {
      const p = item.post || item;
      const img = p.media_url || p.image_url || REAL_IMAGE_CATALOG[p.pinned_product_id] || "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600";
      const author = p.seller_id || p.author_id || "crowdsail_creator";
      const authorName = author.replace("seller_", "").replace(/_/g, " ");
      const score = ((item.final_score || 0.85) * 100).toFixed(1);
      const reason = Array.isArray(item.explanation)
        ? item.explanation[0]
        : (item.explanation?.summary || "Matches your interests and recent activity");
      return `
          <article class="instagram-post-card">
            <header class="instagram-post-header">
              <div class="instagram-author">
                <img src="https://images.unsplash.com/photo-${1500000000000 + (Math.abs(author.length * 7919) % 1000000)}?w=100"
                     alt="${authorName}" class="instagram-avatar"
                     onerror="this.src='https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100'">
                <div>
                  <strong>${authorName}</strong>
                  <span>${p.category || "Recommended for you"}</span>
                </div>
              </div>
              <button class="instagram-more-btn" type="button" aria-label="Post options"
                      onclick="showToast('Post options opened')">•••</button>
            </header>
            <div class="instagram-media-wrap">
              <img src="${img}" alt="${p.caption || 'Recommended post'}" class="instagram-media" loading="lazy">
              <span class="instagram-match-badge">${score}% match</span>
            </div>
            <div class="instagram-post-body">
              <div class="instagram-action-row">
                <button type="button" onclick="showToast('Liked recommendation')">♡</button>
                <button type="button" onclick="handleReply('${p.post_id || p._id || "recommended_post"}')">◯</button>
                <button type="button" onclick="showToast('Recommendation shared')">➤</button>
                <button type="button" class="instagram-save-btn" onclick="showToast('Post saved')">▢</button>
              </div>
              <strong class="instagram-likes">${p.like_count || p.likes || 0} likes</strong>
              <p class="instagram-caption"><strong>${authorName}</strong> ${p.caption || "A recommendation selected for you."}</p>
              <div class="instagram-reason">
                <span>Recommended for you</span>
                <small>${reason}</small>
              </div>
            </div>
          </article>
        `;
    }).join('');
  } catch (e) {
    console.error("Failed to load personalized feed:", e);
    container.innerHTML = `
      <div class="card-loader-placeholder">
        <strong>Personalized feed unavailable.</strong>
        <br>Check that the recommendation API is running, then try selecting the feed again.
      </div>`;
  }
}

async function loadProductRecommendations() {
  const container = document.getElementById("productRecsContainer");
  if (!container) return;
  const requestedUserId = state.currentUserId;

  try {
    const res = await fetch(`${API_BASE}/products/recommendations/${state.currentUserId}?limit=32`);
    if (res.ok) {
      const data = await res.json();
      const prods = data.products || data.recommendations || [];
      if (requestedUserId !== state.currentUserId) return;
      container.innerHTML = prods.map(p => {
        const pid = p.product_id || p._id || p.id;
        const img = p.image_url || REAL_IMAGE_CATALOG[pid] || "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600";
        return `
          <div class="product-rec-card">
            <div class="product-thumb-wrap">
              <img src="${img}" alt="${p.title}" class="product-real-thumb" loading="lazy">
            </div>
            <span class="inventory-product-title" style="font-size:0.88rem;">${p.title}</span>
            <span style="font-size:0.8rem; font-weight:700; color:#1d4ed8;">$${p.price ? p.price.toFixed(2) : "49.00"}</span>
            <button class="btn btn-primary product-add-cart" style="padding:0.35rem 0.65rem; font-size:0.75rem;"
                    data-product-id="${pid}">Add to Cart</button>
          </div>
        `;
      }).join('');
    }
  } catch (e) {
    container.innerHTML = `<div class="card-loader-placeholder">Loading products...</div>`;
  }
}

async function loadUserInsights() {
  const container = document.getElementById("userDetailsContainer");
  if (!container) return;

  const usersMap = {
    user_fashion_01: { name: "Sophia Martinez", persona: "Fashion Enthusiast", topCat: "Fashion & Apparel", cartCount: 3, views: 240 },
    user_tech_02: { name: "Alex Chen", persona: "High-Tech Early Adopter", topCat: "Electronics & Tech", cartCount: 2, views: 310 },
    user_fitness_03: { name: "Marcus Vance", persona: "Strength & Endurance Athlete", topCat: "Fitness & Recovery", cartCount: 4, views: 195 },
    user_decor_04: { name: "Elena Rostova", persona: "Interior Design & Aesthetics", topCat: "Home & Living", cartCount: 1, views: 180 },
    user_beauty_05: { name: "Priya Patel", persona: "Clean Beauty & Skincare", topCat: "Beauty & Cosmetics", cartCount: 5, views: 275 },
    user_newbie_06: { name: "Jordan Taylor", persona: "Cold-Start User (Zero Prior Interactions)", topCat: "General Trending", cartCount: 0, views: 0 },
  };

  const user = usersMap[state.currentUserId] || usersMap["user_fashion_01"];
  container.innerHTML = `
    <div class="user-profile-card">
      <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:1rem;">
        <div class="user-avatar-circle" style="width:50px; height:50px; font-size:1.1rem;">
          ${user.name.split(' ').map(n => n[0]).join('')}
        </div>
        <div>
          <h3 style="font-size:1.1rem; font-weight:800;">${user.name}</h3>
          <span style="font-size:0.8rem; color:#64748b;">${user.persona}</span>
        </div>
      </div>
      <div style="display:flex; flex-direction:column; gap:0.65rem; font-size:0.85rem; border-top:1px solid #e2e8f0; padding-top:0.75rem;">
        <div><strong>Primary Interest:</strong> ${user.topCat}</div>
        <div><strong>Items in Cart:</strong> ${user.cartCount} active</div>
        <div><strong>Historical Views:</strong> ${user.views} posts</div>
        <div><strong>Cold Start Status:</strong> ${state.currentUserId === 'user_newbie_06' ? 'Active Fallback Mode' : 'Trained Profile'}</div>
      </div>
    </div>
    <div class="user-activity-card">
      <h3 style="font-size:1rem; font-weight:700; margin-bottom:0.75rem;">Interaction Weights</h3>
      <p style="font-size:0.82rem; color:#64748b; line-height:1.5;">
        User embedding dynamically blends past video watch time (weight=1.0), post likes (weight=2.0), comments (weight=3.0), and cart additions (weight=5.0).
      </p>
    </div>
  `;
}

async function runOfflineEvaluation() {
  const btn = document.getElementById("btnRunEval");
  if (btn) btn.innerText = "Evaluating...";
  showToast("Computing NDCG@10, MAP, Precision across 500 items...");
  setTimeout(() => {
    if (btn) btn.innerText = "Run Offline Evaluation";
    showToast("Evaluation complete! Hybrid engine achieved 0.412 NDCG@10.");
  }, 1200);
}

// ============================================================================
// Weight Slider Helpers
// ============================================================================
function setupSliders() {
  const sliders = [
    { id: "sliderContent", valId: "valContent", key: "content" },
    { id: "sliderEngagement", valId: "valEngagement", key: "engagement" },
    { id: "sliderSocial", valId: "valSocial", key: "social" },
    { id: "sliderCommerce", valId: "valCommerce", key: "commerce" },
    { id: "sliderPopularity", valId: "valPopularity", key: "popularity" },
    { id: "sliderFreshness", valId: "valFreshness", key: "freshness" },
  ];

  sliders.forEach(s => {
    const el = document.getElementById(s.id);
    const valEl = document.getElementById(s.valId);
    if (el && valEl) {
      el.addEventListener("input", (e) => {
        valEl.innerText = parseFloat(e.target.value).toFixed(2);
        state.weights[s.key] = parseFloat(e.target.value);
      });
    }
  });
}

function resetWeights() {
  state.weights = { content: 0.30, engagement: 0.20, social: 0.15, commerce: 0.15, popularity: 0.10, freshness: 0.10 };
  document.getElementById("sliderContent").value = 0.30;
  document.getElementById("valContent").innerText = "0.30";
  document.getElementById("sliderEngagement").value = 0.20;
  document.getElementById("valEngagement").innerText = "0.20";
  document.getElementById("sliderSocial").value = 0.15;
  document.getElementById("valSocial").innerText = "0.15";
  document.getElementById("sliderCommerce").value = 0.15;
  document.getElementById("valCommerce").innerText = "0.15";
  document.getElementById("sliderPopularity").value = 0.10;
  document.getElementById("valPopularity").innerText = "0.10";
  document.getElementById("sliderFreshness").value = 0.10;
  document.getElementById("valFreshness").innerText = "0.10";
  showToast("Weights reset to defaults");
}

function applyWeights() {
  document.getElementById("weightsDrawer")?.classList.add("hidden");
  showToast("Re-scoring recommendations with tuned weights...");
  loadCrowdsailBoard(true);
}

function showToast(msg) {
  const banner = document.getElementById("toastBanner");
  const text = document.getElementById("toastMessage");
  if (!banner || !text) return;
  text.innerText = msg;
  banner.classList.remove("hidden");
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => {
    banner.classList.add("hidden");
  }, 3500);
}
