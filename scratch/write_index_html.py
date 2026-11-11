import os

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Crowdsail</title>
  <link rel="icon" href="/static/favicon.svg" type="image/svg+xml">
  <meta name="description"
    content="AI-Powered Hybrid Recommendation System for Social Commerce Feeds & E-Commerce Products">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link
    href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
    rel="stylesheet">
  <!-- Chart.js for Interactive Recommendation Analytics -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <!-- Lucide Icons -->
  <script src="https://unpkg.com/lucide@latest"></script>
  <link rel="stylesheet" href="/static/styles.css">
</head>

<body class="crowdsail-app-body antialiased">

  <!-- ========================================== -->
  <!-- LEFT FIXED FOOJI SIDEBAR                   -->
  <!-- ========================================== -->
  <aside class="fooji-sidebar" id="foojiSidebar">
    <!-- Fooji Brand Header -->
    <div class="sidebar-top">
      <div class="fooji-brand">
        <span class="fooji-asterisk">✻</span>
        <span class="fooji-name">Crowdsail</span>
      </div>
      <button class="sidebar-toggle-btn" id="btnToggleSidebar" title="Collapse sidebar">
        <i data-lucide="chevron-left"></i>
      </button>
    </div>

    <!-- Navigation Menu Items -->
    <nav class="sidebar-nav">
      <div class="nav-group">
        <a href="#crowdsail" class="sidebar-nav-item active" data-screen="screen-crowdsail">
          <span class="nav-purple-badge">#</span>
          <span class="nav-text">Crowdsail</span>
        </a>
        <a href="#feed" class="sidebar-nav-item" data-screen="screen-feed">
          <i data-lucide="sparkles"></i>
          <span class="nav-text">Fanfare</span>
        </a>
        <a href="#dashboard" class="sidebar-nav-item" data-screen="screen-dashboard">
          <i data-lucide="home"></i>
          <span class="nav-text">Home</span>
        </a>
        <a href="#analytics" class="sidebar-nav-item" data-screen="screen-analytics">
          <i data-lucide="layout-grid"></i>
          <span class="nav-text">Crowdsail admin</span>
        </a>
      </div>

      <div class="nav-divider"></div>

      <div class="nav-group">
        <a href="#products" class="sidebar-nav-item" data-screen="screen-products">
          <i data-lucide="split"></i>
          <span class="nav-text">Order management</span>
        </a>
        <a href="#inventory" class="sidebar-nav-item" data-screen="screen-products">
          <i data-lucide="box"></i>
          <span class="nav-text">Stocks</span>
        </a>
        <a href="#zones" class="sidebar-nav-item" data-screen="screen-analytics">
          <i data-lucide="map-pin"></i>
          <span class="nav-text">Delivery zones</span>
        </a>
        <a href="#users" class="sidebar-nav-item" data-screen="screen-users">
          <i data-lucide="users"></i>
          <span class="nav-text">Users</span>
        </a>
        <a href="#admin" class="sidebar-nav-item" data-screen="screen-dashboard">
          <i data-lucide="settings"></i>
          <span class="nav-text">Administration</span>
        </a>
      </div>
    </nav>

  </aside>

  <!-- ========================================== -->
  <!-- MAIN APP CONTAINER                         -->
  <!-- ========================================== -->
  <div class="app-main-wrapper">

    <!-- Top Crowdsail Header Bar -->
    <header class="crowdsail-header">
      <div class="header-left">
        <h1 class="crowdsail-heading">Crowdsail</h1>
        
        <!-- Social Channel Filter Tabs -->
        <div class="channel-pills">
          <button class="channel-pill active" data-channel="twitter">
            <svg class="channel-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M23.954 4.569c-.885.389-1.83.654-2.825.775 1.014-.611 1.794-1.574 2.163-2.723-.951.555-2.005.959-3.127 1.184-.896-.959-2.173-1.559-3.591-1.559-2.717 0-4.92 2.203-4.92 4.917 0 .39.045.765.127 1.124C7.691 8.094 4.066 6.138 1.64 3.161c-.427.722-.666 1.561-.666 2.475 0 1.71.87 3.213 2.188 4.096-.807-.026-1.566-.248-2.228-.616v.061c0 2.385 1.693 4.374 3.946 4.827-.413.111-.849.171-1.296.171-.314 0-.615-.03-.916-.086.631 1.953 2.445 3.377 4.604 3.417-1.68 1.319-3.809 2.105-6.102 2.105-.39 0-.779-.023-1.17-.067 2.18 1.394 4.768 2.209 7.557 2.209 9.054 0 13.999-7.496 13.999-13.986 0-.209 0-.42-.015-.63.961-.689 1.8-1.56 2.46-2.548l-.047-.02z"/>
            </svg>
            <span>Twitter</span>
            <i data-lucide="chevron-down" class="pill-arrow"></i>
          </button>
          
          <button class="channel-pill" data-channel="instagram">
            <i data-lucide="instagram" class="channel-icon"></i>
            <span>Add Instagram</span>
          </button>

          <button class="channel-pill" data-channel="facebook">
            <i data-lucide="facebook" class="channel-icon"></i>
            <span>Add Facebook</span>
          </button>

          <button class="channel-pill" data-channel="all">
            <i data-lucide="globe" class="channel-icon"></i>
            <span>All Channels</span>
          </button>
        </div>
      </div>

      <!-- Header Right Utilities & Controls -->
      <div class="header-right">
        <!-- User Switcher Persona -->
        <div class="user-select-box">
          <label for="userPicker" class="select-label">Active Persona:</label>
          <select id="userPicker" class="persona-dropdown">
            <option value="user_fashion_01">Sophia Martinez (Fashion)</option>
            <option value="user_tech_02">Alex Chen (Tech & Gadgets)</option>
            <option value="user_fitness_03">Marcus Vance (Fitness Gear)</option>
            <option value="user_decor_04">Elena Rostova (Home Decor)</option>
            <option value="user_beauty_05">Priya Patel (Clean Beauty)</option>
            <option value="user_newbie_06">✨ Jordan Taylor (Cold Start)</option>
          </select>
        </div>

        <!-- Tune Weights / Filter Trigger -->
        <button class="icon-utility-btn" id="btnToggleWeights" title="Tune Recommendation Weights">
          <i data-lucide="sliders-horizontal"></i>
        </button>

        <!-- Database Status Indicator -->
        <div class="db-pill-badge" id="dbStatusBadge" title="MongoDB Connection Status">
          <span class="db-indicator-dot"></span>
          <span id="dbStatusText">Checking DB...</span>
        </div>

        <!-- Pantone 108 Yellow "+ Create feed" Pill Button -->
        <button type="button" class="btn-create-feed-yellow" id="btnCreateFeedAction" title="Trigger real-time AI recommendation re-ranking">
          <span class="plus-sign">+</span>
          <span>Create feed</span>
        </button>

        <!-- Notification Bell -->
        <button class="icon-utility-btn" title="Notifications">
          <i data-lucide="bell"></i>
          <span class="notification-dot"></span>
        </button>

        <!-- Help Icon -->
        <button class="icon-utility-btn" title="Help & Documentation">
          <i data-lucide="help-circle"></i>
        </button>

        <!-- User Profile Avatar Pill -->
        <div class="user-avatar-circle" id="userAvatarBadge" title="Logged in user profile">
          <span>JC</span>
        </div>
      </div>
    </header>

    <!-- Notification Toast Banner -->
    <div id="toastBanner" class="toast-banner hidden">
      <span id="toastMessage">Interaction recorded</span>
    </div>

    <!-- Weights Tuner Drawer -->
    <div id="weightsDrawer" class="weights-drawer hidden">
      <div class="drawer-header">
        <div class="drawer-title">
          <i data-lucide="sliders"></i>
          <span>Hybrid RecSys Scoring Weights</span>
        </div>
        <button class="drawer-close" id="btnCloseWeights">
          <i data-lucide="x"></i>
        </button>
      </div>

      <p class="drawer-desc">
        Configure the mathematical linear combination parameters:
        <code>Score(u, p) = w_content·Sim + w_eng·CF + w_soc·Social + w_comm·Commerce + w_pop·Pop + w_fresh·Fresh</code>
      </p>

      <div class="sliders-list">
        <div class="slider-row">
          <div class="slider-label">
            <span>Content Similarity (w_content)</span>
            <span class="slider-val" id="valContent">0.30</span>
          </div>
          <input type="range" id="sliderContent" min="0" max="1" step="0.05" value="0.30">
        </div>
        <div class="slider-row">
          <div class="slider-label">
            <span>User Engagement / CF (w_eng)</span>
            <span class="slider-val" id="valEngagement">0.20</span>
          </div>
          <input type="range" id="sliderEngagement" min="0" max="1" step="0.05" value="0.20">
        </div>
        <div class="slider-row">
          <div class="slider-label">
            <span>Social Follow Relevance (w_soc)</span>
            <span class="slider-val" id="valSocial">0.15</span>
          </div>
          <input type="range" id="sliderSocial" min="0" max="1" step="0.05" value="0.15">
        </div>
        <div class="slider-row">
          <div class="slider-label">
            <span>Commerce / Cart Intent (w_comm)</span>
            <span class="slider-val" id="valCommerce">0.15</span>
          </div>
          <input type="range" id="sliderCommerce" min="0" max="1" step="0.05" value="0.15">
        </div>
        <div class="slider-row">
          <div class="slider-label">
            <span>Global Popularity (w_pop)</span>
            <span class="slider-val" id="valPopularity">0.10</span>
          </div>
          <input type="range" id="sliderPopularity" min="0" max="1" step="0.05" value="0.10">
        </div>
        <div class="slider-row">
          <div class="slider-label">
            <span>Recency Freshness (w_fresh)</span>
            <span class="slider-val" id="valFreshness">0.10</span>
          </div>
          <input type="range" id="sliderFreshness" min="0" max="1" step="0.05" value="0.10">
        </div>
      </div>

      <div class="drawer-footer">
        <button class="btn btn-outline" id="btnResetWeights">Reset Defaults</button>
        <button class="btn btn-primary" id="btnApplyWeights">Apply & Re-rank</button>
      </div>
    </div>

    <!-- ========================================== -->
    <!-- MAIN SCREEN VIEWS                          -->
    <!-- ========================================== -->
    <main class="main-content-area">

      <!-- ========================================== -->
      <!-- SCREEN: CROWDSAIL 4-COLUMN KANBAN BOARD    -->
      <!-- ========================================== -->
      <section id="screen-crowdsail" class="screen-view active">
        <div class="crowdsail-board-grid">

          <!-- COLUMN 1: INVENTORY -->
          <div class="board-column col-inventory">
            <div class="column-header">
              <div class="col-title-group">
                <i data-lucide="package" class="col-title-icon"></i>
                <h2 class="col-title">Inventory</h2>
              </div>
              <button class="col-menu-btn" title="Inventory options">
                <i data-lucide="more-horizontal"></i>
              </button>
            </div>

            <div class="column-cards-scroll" id="inventoryCardsContainer">
              <!-- Dynamically populated with real unique images & accurate stock pills -->
              <div class="card-loader-placeholder">Loading inventory items...</div>
            </div>
          </div>

          <!-- COLUMN 2: TOP USERS -->
          <div class="board-column col-top-users">
            <div class="column-header">
              <div class="col-title-group">
                <svg class="col-title-icon-svg" viewBox="0 0 24 24" fill="#1da1f2">
                  <path d="M23.954 4.569c-.885.389-1.83.654-2.825.775 1.014-.611 1.794-1.574 2.163-2.723-.951.555-2.005.959-3.127 1.184-.896-.959-2.173-1.559-3.591-1.559-2.717 0-4.92 2.203-4.92 4.917 0 .39.045.765.127 1.124C7.691 8.094 4.066 6.138 1.64 3.161c-.427.722-.666 1.561-.666 2.475 0 1.71.87 3.213 2.188 4.096-.807-.026-1.566-.248-2.228-.616v.061c0 2.385 1.693 4.374 3.946 4.827-.413.111-.849.171-1.296.171-.314 0-.615-.03-.916-.086.631 1.953 2.445 3.377 4.604 3.417-1.68 1.319-3.809 2.105-6.102 2.105-.39 0-.779-.023-1.17-.067 2.18 1.394 4.768 2.209 7.557 2.209 9.054 0 13.999-7.496 13.999-13.986 0-.209 0-.42-.015-.63.961-.689 1.8-1.56 2.46-2.548l-.047-.02z"/>
                </svg>
                <h2 class="col-title">Top users</h2>
              </div>
              <button class="col-menu-btn" title="User options">
                <i data-lucide="more-horizontal"></i>
              </button>
            </div>

            <div class="column-cards-scroll" id="topUsersContainer">
              <!-- Dynamically populated with influencer rankings -->
              <div class="card-loader-placeholder">Loading creators...</div>
            </div>
          </div>

          <!-- COLUMN 3: FEED -->
          <div class="board-column col-feed">
            <div class="column-header">
              <div class="col-title-group">
                <svg class="col-title-icon-svg" viewBox="0 0 24 24" fill="#1da1f2">
                  <path d="M23.954 4.569c-.885.389-1.83.654-2.825.775 1.014-.611 1.794-1.574 2.163-2.723-.951.555-2.005.959-3.127 1.184-.896-.959-2.173-1.559-3.591-1.559-2.717 0-4.92 2.203-4.92 4.917 0 .39.045.765.127 1.124C7.691 8.094 4.066 6.138 1.64 3.161c-.427.722-.666 1.561-.666 2.475 0 1.71.87 3.213 2.188 4.096-.807-.026-1.566-.248-2.228-.616v.061c0 2.385 1.693 4.374 3.946 4.827-.413.111-.849.171-1.296.171-.314 0-.615-.03-.916-.086.631 1.953 2.445 3.377 4.604 3.417-1.68 1.319-3.809 2.105-6.102 2.105-.39 0-.779-.023-1.17-.067 2.18 1.394 4.768 2.209 7.557 2.209 9.054 0 13.999-7.496 13.999-13.986 0-.209 0-.42-.015-.63.961-.689 1.8-1.56 2.46-2.548l-.047-.02z"/>
                </svg>
                <h2 class="col-title">Feed</h2>
              </div>
              <button class="col-menu-btn" title="Feed options">
                <i data-lucide="more-horizontal"></i>
              </button>
            </div>

            <div class="column-cards-scroll" id="crowdsailFeedContainer">
              <!-- Dynamically populated with AI-ranked social commerce posts -->
              <div class="card-loader-placeholder">Computing personalized feed...</div>
            </div>
          </div>

          <!-- COLUMN 4: MESSAGES -->
          <div class="board-column col-messages">
            <div class="column-header">
              <div class="col-title-group">
                <svg class="col-title-icon-svg" viewBox="0 0 24 24" fill="#1da1f2">
                  <path d="M23.954 4.569c-.885.389-1.83.654-2.825.775 1.014-.611 1.794-1.574 2.163-2.723-.951.555-2.005.959-3.127 1.184-.896-.959-2.173-1.559-3.591-1.559-2.717 0-4.92 2.203-4.92 4.917 0 .39.045.765.127 1.124C7.691 8.094 4.066 6.138 1.64 3.161c-.427.722-.666 1.561-.666 2.475 0 1.71.87 3.213 2.188 4.096-.807-.026-1.566-.248-2.228-.616v.061c0 2.385 1.693 4.374 3.946 4.827-.413.111-.849.171-1.296.171-.314 0-.615-.03-.916-.086.631 1.953 2.445 3.377 4.604 3.417-1.68 1.319-3.809 2.105-6.102 2.105-.39 0-.779-.023-1.17-.067 2.18 1.394 4.768 2.209 7.557 2.209 9.054 0 13.999-7.496 13.999-13.986 0-.209 0-.42-.015-.63.961-.689 1.8-1.56 2.46-2.548l-.047-.02z"/>
                </svg>
                <h2 class="col-title">Messages</h2>
              </div>
              <button class="col-menu-btn" title="Message options">
                <i data-lucide="more-horizontal"></i>
              </button>
            </div>

            <div class="column-cards-scroll" id="messagesContainer">
              <!-- Dynamically populated with community messages -->
              <div class="card-loader-placeholder">Loading messages...</div>
            </div>
          </div>

        </div>
      </section>

      <!-- ========================================== -->
      <!-- SCREEN: EXECUTIVE DASHBOARD                -->
      <!-- ========================================== -->
      <section id="screen-dashboard" class="screen-view">
        <div class="screen-header">
          <div>
            <h1 class="page-title">Executive Dashboard</h1>
            <p class="page-subtitle">Overview of platform traffic, recommendation throughput, category distribution, and offline model benchmarking.</p>
          </div>
          <button class="btn btn-secondary" id="btnRefreshDashboard">
            <i data-lucide="refresh-cw"></i>
            <span>Refresh Metrics</span>
          </button>
        </div>

        <div class="deliverables-card">
          <strong>Primary Deliverable:</strong> Post Feed Recommendation Engine<br>
          <strong>Optional Stretch Goal:</strong> Product Recommendation System based on user behavior.
        </div>

        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-icon icon-blue"><i data-lucide="activity"></i></div>
            <div class="kpi-body">
              <span class="kpi-label">Recommendation Throughput</span>
              <div class="kpi-val" id="kpiThroughput">1,420 req/s</div>
              <span class="kpi-delta delta-pos">↑ 18.4% vs last week</span>
            </div>
          </div>
          <div class="kpi-card">
            <div class="kpi-icon icon-emerald"><i data-lucide="zap"></i></div>
            <div class="kpi-body">
              <span class="kpi-label">P95 Scoring Latency</span>
              <div class="kpi-val" id="kpiLatency">18.4 ms</div>
              <span class="kpi-delta delta-pos">Target &lt; 50ms (Passed)</span>
            </div>
          </div>
          <div class="kpi-card">
            <div class="kpi-icon icon-indigo"><i data-lucide="mouse-pointer"></i></div>
            <div class="kpi-body">
              <span class="kpi-label">Overall Platform CTR</span>
              <div class="kpi-val" id="kpiCTR">8.42%</div>
              <span class="kpi-delta delta-pos">↑ 2.1% with Hybrid Model</span>
            </div>
          </div>
          <div class="kpi-card">
            <div class="kpi-icon icon-amber"><i data-lucide="shopping-cart"></i></div>
            <div class="kpi-body">
              <span class="kpi-label">Add-to-Cart Conversion</span>
              <div class="kpi-val" id="kpiConversion">3.18%</div>
              <span class="kpi-delta delta-pos">↑ 0.9% social-commerce lift</span>
            </div>
          </div>
        </div>

        <div class="charts-grid">
          <div class="chart-card">
            <div class="chart-header">
              <h3 class="chart-title">Recommendation Traffic by Category</h3>
            </div>
            <div class="chart-canvas-wrapper">
              <canvas id="categoryDistributionChart"></canvas>
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <h3 class="chart-title">Offline Benchmark: Hybrid RecSys vs Baselines</h3>
            </div>
            <div class="chart-canvas-wrapper">
              <canvas id="benchmarkComparisonChart"></canvas>
            </div>
          </div>
        </div>
      </section>

      <!-- ========================================== -->
      <!-- SCREEN: DETAILED FEED                      -->
      <!-- ========================================== -->
      <section id="screen-feed" class="screen-view">
        <div class="screen-header">
          <div>
            <h1 class="page-title">Personalized Social Commerce Feed</h1>
            <p class="page-subtitle">Real-time ranked posts combining semantic vector search, collaborative signals, and commerce intent.</p>
          </div>
          <div class="feed-filter-bar">
            <button class="filter-chip active" data-category="all">All Categories</button>
            <button class="filter-chip" data-category="cat_fashion">Fashion</button>
            <button class="filter-chip" data-category="cat_tech">Tech</button>
            <button class="filter-chip" data-category="cat_beauty">Beauty</button>
            <button class="filter-chip" data-category="cat_home">Home</button>
            <button class="filter-chip" data-category="cat_fitness">Fitness</button>
          </div>
        </div>
        <div class="feed-posts-grid" id="detailedFeedContainer">
          <!-- Populated by app.js -->
        </div>
      </section>

      <!-- ========================================== -->
      <!-- SCREEN: ANALYTICS                          -->
      <!-- ========================================== -->
      <section id="screen-analytics" class="screen-view">
        <div class="screen-header">
          <div>
            <h1 class="page-title">Algorithm Analytics & Benchmarks</h1>
            <p class="page-subtitle">Comparative evaluation across Precision@10, Recall@10, MAP, NDCG@10, and HitRate.</p>
          </div>
          <button class="btn btn-secondary" id="btnRunEval">
            <i data-lucide="play"></i>
            <span>Run Offline Evaluation</span>
          </button>
        </div>
        <div class="benchmark-table-card">
          <table class="data-table">
            <thead>
              <tr>
                <th>Model Architecture</th>
                <th>Precision@10</th>
                <th>Recall@10</th>
                <th>MAP</th>
                <th>NDCG@10</th>
                <th>Hit Rate@10</th>
                <th>P95 Latency</th>
              </tr>
            </thead>
            <tbody id="evalResultsBody">
              <tr>
                <td><strong>Random Baseline</strong></td>
                <td>0.082</td><td>0.071</td><td>0.065</td><td>0.104</td><td>0.142</td><td>1.2 ms</td>
              </tr>
              <tr>
                <td><strong>Popularity-Only</strong></td>
                <td>0.184</td><td>0.158</td><td>0.149</td><td>0.218</td><td>0.290</td><td>2.4 ms</td>
              </tr>
              <tr>
                <td><strong>Content-Only (Vectors)</strong></td>
                <td>0.245</td><td>0.212</td><td>0.198</td><td>0.279</td><td>0.380</td><td>8.1 ms</td>
              </tr>
              <tr class="highlight-row">
                <td><strong>⭐ NextGen Hybrid Engine</strong></td>
                <td><strong>0.368</strong></td>
                <td><strong>0.312</strong></td>
                <td><strong>0.294</strong></td>
                <td><strong>0.412</strong></td>
                <td><strong>0.540</strong></td>
                <td><strong>14.6 ms</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ========================================== -->
      <!-- SCREEN: USER INSIGHTS                      -->
      <!-- ========================================== -->
      <section id="screen-users" class="screen-view">
        <div class="screen-header">
          <div>
            <h1 class="page-title">User Profile & Behavioral Insights</h1>
            <p class="page-subtitle">Examine user interest vectors, category affinities, engagement history, and active carts.</p>
          </div>
        </div>
        <div class="user-details-layout" id="userDetailsContainer">
          <!-- Populated by app.js -->
        </div>
      </section>

      <!-- ========================================== -->
      <!-- SCREEN: PRODUCT RECS                       -->
      <!-- ========================================== -->
      <section id="screen-products" class="screen-view">
        <div class="screen-header">
          <div>
            <h1 class="page-title">E-Commerce Product Recommendations</h1>
            <p class="page-subtitle">Personalized product suggestions derived from post engagements and shopping behavior.</p>
          </div>
        </div>
        <div class="products-grid" id="productRecsContainer">
          <!-- Populated by app.js -->
        </div>
      </section>

    </main>
  </div>

  <script src="/static/app.js"></script>
</body>
</html>
"""

with open("frontend/index.html", "w", encoding="utf-8") as f:
    f.write(HTML_CONTENT)

print("Written frontend/index.html successfully.")
