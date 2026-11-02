/**
 * NextGen Social Commerce Recommendation Engine — Frontend Logic
 * Robust Event Delegation & Real-Time Feedback Handlers
 */

let activeUserId = "user_fashion_lover";
let activeWeights = {
  w_social: 0.28,
  w_content: 0.27,
  w_commerce: 0.25,
  w_quality: 0.20,
  enable_exploration: true
};

// DOM References
const personaSelect = document.getElementById("personaSelect");
const dbStatusPill = document.getElementById("dbStatusPill");
const dbStatusText = document.getElementById("dbStatusText");
const feedContainer = document.getElementById("feedContainer");
const productRecsList = document.getElementById("productRecsList");
const toastContainer = document.getElementById("toastContainer");

// Persona Card
const userAvatar = document.getElementById("userAvatar");
const userName = document.getElementById("userName");
const userBadge = document.getElementById("userBadge");
const userDesc = document.getElementById("userDesc");
const statFollows = document.getElementById("statFollows");
const statCart = document.getElementById("statCart");
const statOrders = document.getElementById("statOrders");
const statAvgWatch = document.getElementById("statAvgWatch");
const categoryBars = document.getElementById("categoryBars");

// Latency DOM
const latRetrieval = document.getElementById("latRetrieval");
const latRanking = document.getElementById("latRanking");
const latRerank = document.getElementById("latRerank");
const latTotal = document.getElementById("latTotal");

// Modals
const tunerModal = document.getElementById("tunerModal");
const evalModal = document.getElementById("evalModal");
const dbModal = document.getElementById("dbModal");

const btnOpenTuner = document.getElementById("btnOpenTuner");
const btnCloseTuner = document.getElementById("btnCloseTuner");
const btnOpenEval = document.getElementById("btnOpenEval");
const btnCloseEval = document.getElementById("btnCloseEval");
const btnCloseDbModal = document.getElementById("btnCloseDbModal");
const btnCloseDbModalFooter = document.getElementById("btnCloseDbModalFooter");
const btnRefreshFeed = document.getElementById("btnRefreshFeed");
const btnApplyWeights = document.getElementById("btnApplyWeights");
const btnResetWeights = document.getElementById("btnResetWeights");
const btnReRunEval = document.getElementById("btnReRunEval");
const btnTestReconnect = document.getElementById("btnTestReconnect");
const inputMongoUri = document.getElementById("inputMongoUri");
const reconnectFeedback = document.getElementById("reconnectFeedback");

// Sliders
const sliderSocial = document.getElementById("sliderSocial");
const sliderContent = document.getElementById("sliderContent");
const sliderCommerce = document.getElementById("sliderCommerce");
const sliderQuality = document.getElementById("sliderQuality");
const valSocial = document.getElementById("valSocial");
const valContent = document.getElementById("valContent");
const valCommerce = document.getElementById("valCommerce");
const valQuality = document.getElementById("valQuality");
const chkExploration = document.getElementById("chkExploration");


document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  checkDbStatus();
  loadFeed(activeUserId);
  loadProductRecs(activeUserId);
});


function initEventListeners() {
  // Persona switcher
  personaSelect.addEventListener("change", (e) => {
    activeUserId = e.target.value;
    showToast(`Switched active persona to ${personaSelect.options[personaSelect.selectedIndex].text}`, "info");
    loadFeed(activeUserId);
    loadProductRecs(activeUserId);
  });

  // Refresh Feed
  btnRefreshFeed.addEventListener("click", () => {
    btnRefreshFeed.style.transform = "rotate(180deg)";
    setTimeout(() => btnRefreshFeed.style.transform = "none", 300);
    loadFeed(activeUserId);
    loadProductRecs(activeUserId);
    showToast("Feed refreshed with latest behavioral signals", "info");
  });

  // Tuner Modal Open / Close
  btnOpenTuner.addEventListener("click", () => tunerModal.classList.add("active"));
  btnCloseTuner.addEventListener("click", () => tunerModal.classList.remove("active"));
  tunerModal.addEventListener("click", (e) => {
    if (e.target === tunerModal) tunerModal.classList.remove("active");
  });

  // Eval Modal Open / Close
  btnOpenEval.addEventListener("click", () => {
    evalModal.classList.add("active");
    runEvaluation();
  });
  btnCloseEval.addEventListener("click", () => evalModal.classList.remove("active"));
  evalModal.addEventListener("click", (e) => {
    if (e.target === evalModal) evalModal.classList.remove("active");
  });
  btnReRunEval.addEventListener("click", runEvaluation);

  // DB Modal Open / Close
  dbStatusPill.addEventListener("click", () => {
    openDbModal();
  });
  if (btnCloseDbModal) btnCloseDbModal.addEventListener("click", () => dbModal.classList.remove("active"));
  if (btnCloseDbModalFooter) btnCloseDbModalFooter.addEventListener("click", () => dbModal.classList.remove("active"));
  dbModal.addEventListener("click", (e) => {
    if (e.target === dbModal) dbModal.classList.remove("active");
  });

  // DB Reconnect Test Button
  if (btnTestReconnect) {
    btnTestReconnect.addEventListener("click", handleReconnect);
  }

  // Sliders binding
  sliderSocial.addEventListener("input", (e) => valSocial.textContent = parseFloat(e.target.value).toFixed(2));
  sliderContent.addEventListener("input", (e) => valContent.textContent = parseFloat(e.target.value).toFixed(2));
  sliderCommerce.addEventListener("input", (e) => valCommerce.textContent = parseFloat(e.target.value).toFixed(2));
  sliderQuality.addEventListener("input", (e) => valQuality.textContent = parseFloat(e.target.value).toFixed(2));

  // Apply weights
  btnApplyWeights.addEventListener("click", () => {
    activeWeights.w_social = parseFloat(sliderSocial.value);
    activeWeights.w_content = parseFloat(sliderContent.value);
    activeWeights.w_commerce = parseFloat(sliderCommerce.value);
    activeWeights.w_quality = parseFloat(sliderQuality.value);
    activeWeights.enable_exploration = chkExploration.checked;
    tunerModal.classList.remove("active");
    loadFeed(activeUserId);
    showToast("Ranking weights applied! Feed re-scored in real time.", "success");
  });

  // Reset weights
  btnResetWeights.addEventListener("click", () => {
    sliderSocial.value = 0.28; valSocial.textContent = "0.28";
    sliderContent.value = 0.27; valContent.textContent = "0.27";
    sliderCommerce.value = 0.25; valCommerce.textContent = "0.25";
    sliderQuality.value = 0.20; valQuality.textContent = "0.20";
    chkExploration.checked = true;

    activeWeights.w_social = 0.28;
    activeWeights.w_content = 0.27;
    activeWeights.w_commerce = 0.25;
    activeWeights.w_quality = 0.20;
    activeWeights.enable_exploration = true;
    loadFeed(activeUserId);
    showToast("Reset ranking weights to default baseline.", "info");
  });

  // Robust Event Delegation on Feed Container for all card actions
  feedContainer.addEventListener("click", handleFeedCardClick);
  feedContainer.addEventListener("change", handleFeedSliderChange);

  // Event Delegation for Product Recommendations list
  productRecsList.addEventListener("click", handleProductCardClick);
}


/**
 * Toast Notification Helper
 */
function showToast(message, type = "info") {
  if (!toastContainer) return;
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${type === "success" ? "✓" : "ℹ"}</span>
    <span>${message}</span>
  `;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}


/**
 * Handle card button clicks via event delegation
 */
async function handleFeedCardClick(e) {
  // 1. Add to cart button
  const cartBtn = e.target.closest(".btn-add-cart");
  if (cartBtn) {
    const postId = cartBtn.dataset.postId;
    cartBtn.classList.add("added");
    cartBtn.textContent = "✓ In Cart";
    cartBtn.disabled = true;

    // Increment sidebar cart counter
    const curVal = parseInt(statCart.textContent) || 0;
    statCart.textContent = curVal + 1;

    showToast("Pinned item added to cart! High-intent commerce signal logged.", "success");
    await triggerInteractionApi(postId, "cart");
    // Reload products to reflect cart intent
    loadProductRecs(activeUserId);
    return;
  }

  // 2. Action buttons (Like, Bookmark, Share)
  const actBtn = e.target.closest(".act-btn");
  if (actBtn) {
    const action = actBtn.dataset.action;
    const postId = actBtn.dataset.postId;
    const countEl = actBtn.querySelector(".count-num");

    if (action === "like") {
      const isLiked = actBtn.classList.toggle("liked");
      if (countEl) {
        const cur = parseInt(countEl.textContent) || 0;
        countEl.textContent = isLiked ? cur + 1 : Math.max(0, cur - 1);
      }
      showToast(isLiked ? "❤️ Liked! Content affinity boosted." : "Like removed.", "success");
      await triggerInteractionApi(postId, "like");
    } else if (action === "bookmark") {
      const isSaved = actBtn.classList.toggle("saved");
      if (countEl) {
        const cur = parseInt(countEl.textContent) || 0;
        countEl.textContent = isSaved ? cur + 1 : Math.max(0, cur - 1);
      }
      showToast(isSaved ? "🔖 Saved to bookmarks! Long-term interest logged." : "Bookmark removed.", "success");
      await triggerInteractionApi(postId, "bookmark");
    } else if (action === "share") {
      actBtn.classList.add("shared");
      if (countEl) {
        const cur = parseInt(countEl.textContent) || 0;
        countEl.textContent = cur + 1;
      }
      // Simulate clipboard copy
      if (navigator.clipboard) {
        navigator.clipboard.writeText(window.location.href);
      }
      showToast("🔗 Post link copied! High social resonance signal logged.", "info");
      await triggerInteractionApi(postId, "share");
    }
  }
}


/**
 * Handle watch slider change via event delegation
 */
async function handleFeedSliderChange(e) {
  const slider = e.target.closest(".watch-slider");
  if (slider) {
    const postId = slider.dataset.postId;
    const pctVal = parseFloat(slider.value);
    showToast(`Watch time recorded: ${pctVal}% completed.`, "info");
    await triggerInteractionApi(postId, "view", pctVal / 100.0);
  }
}


/**
 * Handle Product Spotlight clicks
 */
async function handleProductCardClick(e) {
  const prodCartBtn = e.target.closest(".btn-prod-cart");
  if (prodCartBtn) {
    const prodId = prodCartBtn.dataset.productId;
    prodCartBtn.textContent = "✓ In Cart";
    prodCartBtn.disabled = true;

    // Increment sidebar cart counter
    const curVal = parseInt(statCart.textContent) || 0;
    statCart.textContent = curVal + 1;

    showToast("Product added to cart! Direct conversion signal logged.", "success");

    // Log cart interaction
    try {
      await fetch("/api/interactions/engage", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: activeUserId,
          post_id: "prod_direct",
          interaction_type: "cart"
        })
      });
    } catch (err) {
      console.warn("Direct cart log:", err);
    }
  }
}


/**
 * API Caller for user interactions
 */
async function triggerInteractionApi(postId, action, value = null) {
  try {
    await fetch("/api/interactions/engage", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: activeUserId,
        post_id: postId,
        interaction_type: action,
        value: value
      })
    });
  } catch (err) {
    console.error(`Interaction error (${action}):`, err);
  }
}


/**
 * Check DB Status
 */
async function checkDbStatus() {
  try {
    const res = await fetch("/api/db/status");
    const data = await res.json();
    if (data.is_live_mongodb) {
      dbStatusPill.classList.remove("mock");
      dbStatusText.textContent = "Live MongoDB Atlas";
    } else {
      dbStatusPill.classList.add("mock");
      dbStatusText.textContent = "Mock Test DB (Active)";
    }
  } catch (err) {
    dbStatusPill.classList.add("mock");
    dbStatusText.textContent = "Offline DB";
  }
}


/**
 * Open Database Modal with Live Counts
 */
async function openDbModal() {
  dbModal.classList.add("active");
  const statusEl = document.getElementById("dbModalStatusText");
  const totalDocsEl = document.getElementById("dbModalTotalDocs");
  const collsListEl = document.getElementById("dbModalCollectionsList");

  statusEl.textContent = "Checking...";
  collsListEl.innerHTML = `<span style="font-size:0.75rem; color:var(--text-muted);">Fetching counts...</span>`;

  try {
    const res = await fetch("/api/db/status");
    const data = await res.json();
    statusEl.textContent = data.status;
    totalDocsEl.textContent = `${data.total_documents} documents`;

    collsListEl.innerHTML = "";
    for (const [coll, count] of Object.entries(data.collection_counts)) {
      const item = document.createElement("div");
      item.className = "collections-item";
      item.innerHTML = `
        <span>${coll}</span>
        <span>${count}</span>
      `;
      collsListEl.appendChild(item);
    }
  } catch (err) {
    statusEl.textContent = "Error reading database status.";
  }
}


/**
 * Handle MongoDB Reconnection
 */
async function handleReconnect() {
  const uri = inputMongoUri.value.trim();
  if (!uri) {
    reconnectFeedback.style.color = "var(--accent-amber)";
    reconnectFeedback.textContent = "Please enter a valid MongoDB connection string.";
    return;
  }

  btnTestReconnect.disabled = true;
  btnTestReconnect.textContent = "Connecting...";
  reconnectFeedback.style.color = "var(--text-muted)";
  reconnectFeedback.textContent = "Testing MongoDB Atlas connection...";

  try {
    const res = await fetch("/api/db/reconnect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mongodb_uri: uri })
    });
    const data = await res.json();

    if (res.ok) {
      reconnectFeedback.style.color = "var(--accent-emerald)";
      reconnectFeedback.textContent = "✓ Connected successfully to MongoDB Atlas!";
      checkDbStatus();
      openDbModal();
      loadFeed(activeUserId);
      showToast("Connected to live MongoDB Atlas cluster!", "success");
    } else {
      reconnectFeedback.style.color = "var(--accent-rose)";
      reconnectFeedback.textContent = data.detail || "Authentication / connection failed.";
    }
  } catch (err) {
    reconnectFeedback.style.color = "var(--accent-rose)";
    reconnectFeedback.textContent = `Connection error: ${err.message}`;
  } finally {
    btnTestReconnect.disabled = false;
    btnTestReconnect.textContent = "Test & Connect";
  }
}


/**
 * Load Personalized Post Feed
 */
async function loadFeed(userId) {
  feedContainer.innerHTML = `
    <div class="feed-loading">
      <div class="spinner"></div>
      <p>Generating personalized recommendations...</p>
    </div>
  `;

  try {
    const params = new URLSearchParams({
      user_id: userId,
      limit: 15,
      w_social: activeWeights.w_social,
      w_content: activeWeights.w_content,
      w_commerce: activeWeights.w_commerce,
      w_quality: activeWeights.w_quality,
      enable_exploration: activeWeights.enable_exploration
    });

    const res = await fetch(`/api/feed?${params.toString()}`);
    const data = await res.json();

    updateUserSidebar(data.user_profile, data.is_cold_start);
    updateDiagnostics(data.diagnostics);
    renderFeed(data.feed);
  } catch (err) {
    console.error("Error loading feed:", err);
    feedContainer.innerHTML = `<div class="feed-loading"><p>⚠️ Failed to load recommendations.</p></div>`;
  }
}


/**
 * Update Sidebar with User Profile Insights
 */
function updateUserSidebar(profile, isColdStart) {
  const personasMap = {
    "user_fashion_lover": {
      name: "Elena Vance",
      badge: "Fashion & Streetwear Shopper",
      desc: "Passionate about high-weight oversized hoodies, sneaker drops, and minimal streetwear.",
      avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100"
    },
    "user_tech_geek": {
      name: "David Chen",
      badge: "Audiophile & Gadget Techie",
      desc: "Prioritizes studio noise cancellation, ergonomic desk accessories, and smartwatch accuracy.",
      avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100"
    },
    "user_beauty_seeker": {
      name: "Maya Lin",
      badge: "Clean Beauty & Barrier Care",
      desc: "Enthusiastic about glazed lip peptides, organic cold-pressed serums, and skin barrier routines.",
      avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100"
    },
    "user_fitness_buff": {
      name: "Alex Miller",
      badge: "Crossfit & Home Gym Athlete",
      desc: "Regularly tracks form cues, heavy kettlebell EMOMs, and high-rise athletic compression gear.",
      avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100"
    },
    "user_cold_start": {
      name: "New Visitor",
      badge: "Cold Start Discovery",
      desc: "Brand new user with 0 history. Tests trending viral heuristics & initial category exploration.",
      avatar: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100"
    }
  };

  const curr = personasMap[profile.user_id] || {
    name: profile.user_id,
    badge: isColdStart ? "Cold Start User" : "Active Shopper",
    desc: "Personalized social commerce user profile.",
    avatar: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100"
  };

  userName.textContent = curr.name;
  userBadge.textContent = curr.badge;
  userDesc.textContent = curr.desc;
  userAvatar.src = curr.avatar;

  statFollows.textContent = profile.followed_sellers.length;
  statCart.textContent = profile.cart_items_count;
  statOrders.textContent = profile.orders_count;
  statAvgWatch.textContent = isColdStart ? "0%" : `${Math.round(profile.avg_watch_pct * 100)}%`;

  // Render category bars
  categoryBars.innerHTML = "";
  if (profile.top_categories.length === 0) {
    categoryBars.innerHTML = `<span style="font-size:0.75rem; color:var(--text-muted);">No category signals yet (Cold Start).</span>`;
  } else {
    profile.top_categories.forEach(([cat, score]) => {
      const cleanName = cat.replace("cat_", "").replace("_", " ").toUpperCase();
      const pct = Math.round(score * 100);
      const item = document.createElement("div");
      item.className = "cat-bar-item";
      item.innerHTML = `
        <div class="cat-bar-labels">
          <span>${cleanName}</span>
          <span>${pct}%</span>
        </div>
        <div class="cat-bar-track">
          <div class="cat-bar-fill" style="width: ${pct}%"></div>
        </div>
      `;
      categoryBars.appendChild(item);
    });
  }
}


/**
 * Update Latency Diagnostics
 */
function updateDiagnostics(diag) {
  if (!diag) return;
  latRetrieval.textContent = `${diag.retrieval_latency_ms} ms`;
  latRanking.textContent = `${diag.ranking_latency_ms} ms`;
  latRerank.textContent = `${diag.rerank_latency_ms} ms`;
  latTotal.textContent = `${diag.total_latency_ms} ms`;
}


/**
 * Render Feed Posts with Reliable Event Attributes
 */
function renderFeed(feed) {
  if (!feed || feed.length === 0) {
    feedContainer.innerHTML = `<div class="feed-loading"><p>No posts available.</p></div>`;
    return;
  }

  feedContainer.innerHTML = "";

  feed.forEach((item, index) => {
    const post = item.post;
    const seller = item.seller;
    const prod = item.pinned_product;
    const m = item.metrics;

    const card = document.createElement("article");
    card.className = "post-card";
    card.id = `post-${post.id}`;

    const channelTag = item.retrieval_channel.replace("_", " ").toUpperCase();

    card.innerHTML = `
      <div class="post-header">
        <div class="creator-info">
          <img src="${seller.avatar}" class="creator-avatar" alt="${seller.name}">
          <div>
            <div class="creator-name">${seller.name}</div>
            <div class="creator-handle">${seller.handle} • ⭐ ${seller.rating}</div>
          </div>
        </div>
        <div class="post-rank-badge" title="Overall Multi-Factor Match Score">
          <span>#${index + 1}</span>
          <span>Match ${Math.round(item.total_score * 100)}%</span>
        </div>
      </div>

      <div class="post-media-container">
        <img src="${post.media_url}" class="post-media-img" alt="Post Visual" loading="lazy">
        <div class="media-type-badge">
          ${post.media_type === "video" ? "▶ Video" : "📷 Photo"}
        </div>

        ${prod ? `
          <div class="pinned-product-drawer">
            <div class="pinned-prod-info">
              <span class="pinned-label">Pinned Item</span>
              <span class="pinned-title">${prod.title}</span>
              <span class="pinned-price">$${prod.price.toFixed(2)}</span>
            </div>
            <button class="btn-add-cart" data-post-id="${post.id}">
              + Cart
            </button>
          </div>
        ` : ""}
      </div>

      <div class="post-body">
        <div class="action-bar">
          <div class="action-buttons-group">
            <button class="act-btn" data-action="like" data-post-id="${post.id}" title="Like this post">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
              <span class="count-num">${m.likes}</span>
            </button>
            <button class="act-btn" data-action="bookmark" data-post-id="${post.id}" title="Save to bookmarks">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/></svg>
              <span class="count-num">${m.saves}</span>
            </button>
            <button class="act-btn" data-action="share" data-post-id="${post.id}" title="Share post link">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
              <span class="count-num">${m.shares}</span>
            </button>
          </div>

          <div class="watch-simulator-group" title="Drag slider to simulate watch time completion">
            <span>Watch %:</span>
            <input type="range" class="watch-slider" data-post-id="${post.id}" min="10" max="100" value="${Math.round(m.avg_watch_time * 100)}">
          </div>
        </div>

        <p class="post-caption">${post.caption}</p>

        <!-- Explainability Factor Drawer -->
        <div class="explain-drawer">
          <div class="explain-header">
            <span class="explain-title">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
              Why Recommended
            </span>
            <span class="retrieval-channel-tag">${channelTag}</span>
          </div>

          <div class="reasons-tags-row">
            ${item.explanations.map(r => `<span class="reason-tag">${r}</span>`).join("")}
          </div>

          <div class="subscores-bar">
            <span>Social: <strong>${Math.round(item.subscores.social * 100)}%</strong></span>
            <span>Content: <strong>${Math.round(item.subscores.content * 100)}%</strong></span>
            <span>Commerce: <strong>${Math.round(item.subscores.commerce * 100)}%</strong></span>
            <span>Quality: <strong>${Math.round(item.subscores.quality * 100)}%</strong></span>
          </div>
        </div>
      </div>
    `;

    feedContainer.appendChild(card);
  });
}


/**
 * Load Product Recommendations with "+ Cart" Action Button
 */
async function loadProductRecs(userId) {
  productRecsList.innerHTML = `<span style="font-size:0.75rem; color:var(--text-muted);">Finding relevant products...</span>`;

  try {
    const res = await fetch(`/api/products/recommendations?user_id=${userId}&limit=5`);
    const data = await res.json();

    if (!data.recommendations || data.recommendations.length === 0) {
      productRecsList.innerHTML = `<span style="font-size:0.75rem; color:var(--text-muted);">No products found.</span>`;
      return;
    }

    productRecsList.innerHTML = "";
    data.recommendations.forEach(prod => {
      const card = document.createElement("div");
      card.className = "product-rec-card";
      card.innerHTML = `
        <div class="prod-rec-top">
          <span class="prod-rec-title">${prod.title}</span>
          <span class="prod-rec-price">$${prod.price.toFixed(2)}</span>
        </div>
        <p class="prod-rec-desc">${prod.description}</p>
        <div class="prod-rec-bottom">
          <span class="prod-rec-reason">${prod.reasons[0] || "Trending Product"}</span>
          <button class="btn-prod-cart" data-product-id="${prod.product_id}">+ Cart</button>
        </div>
      `;
      productRecsList.appendChild(card);
    });
  } catch (err) {
    console.error("Error loading products:", err);
  }
}


/**
 * Run Offline Evaluation Suite
 */
async function runEvaluation() {
  const metricNdcg = document.getElementById("metricNdcg");
  const metricHitRate = document.getElementById("metricHitRate");
  const metricDiversity = document.getElementById("metricDiversity");
  const metricLatency = document.getElementById("metricLatency");
  const evalTableBody = document.getElementById("evalTableBody");

  metricNdcg.textContent = "...";
  metricHitRate.textContent = "...";
  metricDiversity.textContent = "...";
  metricLatency.textContent = "...";
  evalTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:1.5rem;">Running offline evaluation across cohort...</td></tr>`;

  try {
    const res = await fetch("/api/metrics/evaluate?k=10");
    const data = await res.json();
    const agg = data.aggregate_metrics;

    metricNdcg.textContent = agg.mean_ndcg.toFixed(4);
    metricHitRate.textContent = `${Math.round(agg.mean_hit_rate * 100)}%`;
    metricDiversity.textContent = agg.mean_intra_list_diversity.toFixed(4);
    metricLatency.textContent = `${agg.latency_p95_ms} ms`;

    evalTableBody.innerHTML = "";
    data.per_user_results.forEach(row => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${row.user_id.replace("user_", "").replace("_", " ").toUpperCase()}</td>
        <td>${row.relevant_count} items</td>
        <td style="color:var(--accent-emerald); font-weight:700;">${row.ndcg_k.toFixed(4)}</td>
        <td>${(row.precision_k * 100).toFixed(1)}%</td>
        <td>${(row.recall_k * 100).toFixed(1)}%</td>
        <td>${row.diversity_ild.toFixed(4)}</td>
        <td>${row.latency_ms} ms</td>
      `;
      evalTableBody.appendChild(tr);
    });
  } catch (err) {
    evalTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--accent-rose);">Failed to run evaluation benchmark.</td></tr>`;
  }
}
