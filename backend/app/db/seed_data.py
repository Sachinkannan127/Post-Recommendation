"""
Seed script to generate realistic social commerce test data across all 13 collections.
Supports both Live MongoDB and Local Mock DB.
"""
import os
import random
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
from bson import ObjectId

from backend.app.db.connection import get_db, get_db_manager, DEFAULT_LOCAL_STORAGE


# Fix seed for reproducible, high quality benchmarks
random.seed(42)
np.random.seed(42)

EMBEDDING_DIM = 64

def generate_cluster_embedding(centroid: np.ndarray, noise: float = 0.18) -> List[float]:
    """Generates a normalized embedding vector around a category centroid."""
    vec = centroid + np.random.normal(0, noise, size=centroid.shape)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return [round(float(x), 6) for x in vec]


def create_normalized_centroid(dim: int) -> np.ndarray:
    v = np.random.randn(dim)
    return v / np.linalg.norm(v)


def seed_database(force_refresh: bool = False):
    db = get_db()
    manager = get_db_manager()

    # Check if already seeded
    if not force_refresh and db.posts.count_documents({}) > 0:
        print(f"Database already populated ({db.posts.count_documents({})} posts). Skipping re-seed.")
        return

    print("Generating synthetic social commerce dataset across all 13 collections...")

    # Clear existing collections if force_refresh
    collections = [
        "posts", "postembeddings", "postengagements", "postmetrics",
        "postcomments", "follows", "views", "carts", "orders",
        "sellerdetails", "productcategories", "productsubcategories",
        "variants", "products"
    ]
    for c in collections:
        db[c].delete_many({})

    # 1. Product Categories & Category Centroids for Semantic Vectors
    categories_raw = [
        {"_id": "cat_fashion", "name": "Fashion & Apparel", "slug": "fashion", "icon": "shirt"},
        {"_id": "cat_tech", "name": "Electronics & Tech", "slug": "tech", "icon": "smartphone"},
        {"_id": "cat_beauty", "name": "Beauty & Cosmetics", "slug": "beauty", "icon": "sparkles"},
        {"_id": "cat_home", "name": "Home & Living", "slug": "home", "icon": "home"},
        {"_id": "cat_fitness", "name": "Fitness & Wellness", "slug": "fitness", "icon": "activity"}
    ]
    db.productcategories.insert_many(categories_raw)

    # Pre-generate distinct semantic centroids for each category
    category_centroids = {
        cat["_id"]: create_normalized_centroid(EMBEDDING_DIM) for cat in categories_raw
    }

    # 2. Product Subcategories
    subcategories_raw = [
        # Fashion
        {"_id": "sub_streetwear", "parent_category_id": "cat_fashion", "name": "Streetwear", "slug": "streetwear"},
        {"_id": "sub_footwear", "parent_category_id": "cat_fashion", "name": "Footwear", "slug": "footwear"},
        {"_id": "sub_accessories", "parent_category_id": "cat_fashion", "name": "Accessories", "slug": "accessories"},
        # Tech
        {"_id": "sub_audio", "parent_category_id": "cat_tech", "name": "Audio & Headphones", "slug": "audio"},
        {"_id": "sub_wearables", "parent_category_id": "cat_tech", "name": "Wearables & Smartwatches", "slug": "wearables"},
        {"_id": "sub_accessories_tech", "parent_category_id": "cat_tech", "name": "Gadgets & Chargers", "slug": "gadgets"},
        # Beauty
        {"_id": "sub_skincare", "parent_category_id": "cat_beauty", "name": "Skincare & Serums", "slug": "skincare"},
        {"_id": "sub_makeup", "parent_category_id": "cat_beauty", "name": "Makeup & Lips", "slug": "makeup"},
        # Home
        {"_id": "sub_decor", "parent_category_id": "cat_home", "name": "Lighting & Ambience", "slug": "decor"},
        {"_id": "sub_kitchen", "parent_category_id": "cat_home", "name": "Kitchen & Brew", "slug": "kitchen"},
        # Fitness
        {"_id": "sub_activewear", "parent_category_id": "cat_fitness", "name": "Activewear", "slug": "activewear"},
        {"_id": "sub_gear", "parent_category_id": "cat_fitness", "name": "Workout Equipment", "slug": "gear"}
    ]
    db.productsubcategories.insert_many(subcategories_raw)

    # 3. Sellers & Creators
    sellers_raw = [
        {
            "_id": "seller_aurora",
            "name": "Aurora Urban Studio",
            "handle": "@aurora_streetwear",
            "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
            "rating": 4.9,
            "follower_count": 84200,
            "category": "cat_fashion",
            "bio": "Minimal oversized aesthetic & modern streetwear drops."
        },
        {
            "_id": "seller_techpulse",
            "name": "TechPulse Gear",
            "handle": "@techpulse",
            "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
            "rating": 4.8,
            "follower_count": 128500,
            "category": "cat_tech",
            "bio": "Next-gen workspace gadgets, audio gear, and tech accessories."
        },
        {
            "_id": "seller_glowcraft",
            "name": "GlowCraft Organics",
            "handle": "@glowcraft",
            "avatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150",
            "rating": 4.95,
            "follower_count": 96400,
            "category": "cat_beauty",
            "bio": "Botanical skincare formulated for barrier repair & natural glow."
        },
        {
            "_id": "seller_urbannest",
            "name": "UrbanNest Living",
            "handle": "@urbannest_home",
            "avatar": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150",
            "rating": 4.75,
            "follower_count": 61200,
            "category": "cat_home",
            "bio": "Nordic lamps, desk aesthetics, and modern sanctuary decor."
        },
        {
            "_id": "seller_fitforge",
            "name": "FitForge Athletics",
            "handle": "@fitforge",
            "avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150",
            "rating": 4.85,
            "follower_count": 110300,
            "category": "cat_fitness",
            "bio": "Performance gym equipment & precision athletic compression wear."
        },
        {
            "_id": "seller_soundwave",
            "name": "SoundWave Labs",
            "handle": "@soundwave_audio",
            "avatar": "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=150",
            "rating": 4.9,
            "follower_count": 78900,
            "category": "cat_tech",
            "bio": "Studio-grade wireless ANC headphones and portable hi-fi DACs."
        }
    ]
    db.sellerdetails.insert_many(sellers_raw)

    # 4. Products
    products_raw = [
        # Fashion
        {
            "_id": "prod_hoodie_01",
            "seller_id": "seller_aurora",
            "title": "Heavyweight Cloud Fleece Oversized Hoodie",
            "description": "500 GSM French Terry cotton hoodie with custom drop-shoulder silhouette.",
            "price": 89.0,
            "category_id": "cat_fashion",
            "subcategory_id": "sub_streetwear",
            "rating": 4.9,
            "product_embedding": generate_cluster_embedding(category_centroids["cat_fashion"])
        },
        {
            "_id": "prod_sneakers_01",
            "seller_id": "seller_aurora",
            "title": "Nomad Kinetic Runner V2",
            "description": "Lightweight breathable knit mesh sneaker with chunky EVA cushioning.",
            "price": 145.0,
            "category_id": "cat_fashion",
            "subcategory_id": "sub_footwear",
            "rating": 4.8,
            "product_embedding": generate_cluster_embedding(category_centroids["cat_fashion"])
        },
        {
            "_id": "prod_cargo_01",
            "seller_id": "seller_aurora",
            "title": "Tactical Multi-Pocket Techwear Cargos",
            "description": "Water-resistant ripstop nylon pants with articulated knee seams.",
            "price": 110.0,
            "category_id": "cat_fashion",
            "subcategory_id": "sub_streetwear",
            "rating": 4.7,
            "product_embedding": generate_cluster_embedding(category_centroids["cat_fashion"])
        },
        # Tech
        {
            "_id": "prod_headphones_01",
            "seller_id": "seller_soundwave",
            "title": "Aura ANC Spatial Wireless Headphones",
            "description": "Hybrid active noise cancelling with custom 40mm beryllium drivers and 45hr battery.",
            "price": 199.0,
            "category_id": "cat_tech",
            "subcategory_id": "sub_audio",
            "rating": 4.9,
            "product_embedding": generate_cluster_embedding(category_centroids["cat_tech"])
        },
        {
            "_id": "prod_smartwatch_01",
            "seller_id": "seller_techpulse",
            "title": "ChronoTrack Pro Titanium Smartwatch",
            "description": "Sapphire crystal display, ECG monitoring, offline GPS, and 14-day battery.",
            "price": 279.0,
            "category_id": "cat_tech",
            "subcategory_id": "sub_wearables",
            "rating": 4.85,
            "product_embedding": generate_cluster_embedding(category_centroids["cat_tech"])
        },
        {
            "_id": "prod_deskmat_01",
            "seller_id": "seller_techpulse",
            "title": "MagCharge Merino Wool Desk Pad",
            "description": "Integrated 15W Qi2 wireless charging spot with vegan leather accents.",
            "price": 65.0,
            "category_id": "cat_tech",
            "subcategory_id": "sub_accessories_tech",
            "rating": 4.75,
            "product_embedding": generate_cluster_embedding(category_centroids["cat_tech"])
        },
        # Beauty
        {
            "_id": "prod_serum_01",
            "seller_id": "seller_glowcraft",
            "title": "Hyaluronic Peptide Barrier Glaze Serum",
            "description": "Triple molecular weight hyaluronic acid infused with niacinamide & ceramides.",
            "price": 42.0,
            "category_id": "cat_beauty",
            "subcategory_id": "sub_skincare",
            "rating": 4.95,
            "product_embedding": generate_cluster_embedding(category_centroids["cat_beauty"])
        },
        {
            "_id": "prod_oil_01",
            "seller_id": "seller_glowcraft",
            "title": "Cold-Pressed Rosehip Glow Elixir",
            "description": "Unrefined organic cold-pressed oil rich in Vitamin A and linoleic acid for skin rejuvenation.",
            "price": 38.0,
            "category_id": "cat_beauty",
            "subcategory_id": "sub_skincare",
            "rating": 4.85,
            "product_embedding": generate_cluster_embedding(category_centroids["cat_beauty"])
        },
        {
            "_id": "prod_lip_01",
            "seller_id": "seller_glowcraft",
            "title": "HydraDew Tinted Peptide Lip Treatment",
            "description": "Deeply nourishing peptide treatment that plumps and leaves a high-shine glossy tint.",
            "price": 24.0,
            "category_id": "cat_beauty",
            "subcategory_id": "sub_makeup",
            "rating": 4.9,
            "product_embedding": generate_cluster_embedding(category_centroids["cat_beauty"])
        },
        # Home
        {
            "_id": "prod_lamp_01",
            "seller_id": "seller_urbannest",
            "title": "Lumina Ambient Mushroom Desk Lamp",
            "description": "Hand-blown warm amber glass table lamp with touch dimming and RGB mood lighting.",
            "price": 75.0,
            "category_id": "cat_home",
            "subcategory_id": "sub_decor",
            "rating": 4.8,
            "product_embedding": generate_cluster_embedding(category_centroids["cat_home"])
        },
        {
            "_id": "prod_pour_over_01",
            "seller_id": "seller_urbannest",
            "title": "BaristaPro Precision Gooseneck Kettle",
            "description": "Matte black electric temperature kettle with Strix controller and 0.9L capacity.",
            "price": 95.0,
            "category_id": "cat_home",
            "subcategory_id": "sub_kitchen",
            "rating": 4.9,
            "product_embedding": generate_cluster_embedding(category_centroids["cat_home"])
        },
        # Fitness
        {
            "_id": "prod_kettlebell_01",
            "seller_id": "seller_fitforge",
            "title": "Adjustable Cast Iron Competition Kettlebell",
            "description": "Quick-lock selector mechanism switching seamlessly from 8kg to 32kg.",
            "price": 185.0,
            "category_id": "cat_fitness",
            "subcategory_id": "sub_gear",
            "rating": 4.9,
            "product_embedding": generate_cluster_embedding(category_centroids["cat_fitness"])
        },
        {
            "_id": "prod_leggings_01",
            "seller_id": "seller_fitforge",
            "title": "AeroFlex High-Rise Seamless Compression Tights",
            "description": "Squat-proof 4-way stretch fabric with targeted contour zones and phone pocket.",
            "price": 68.0,
            "category_id": "cat_fitness",
            "subcategory_id": "sub_activewear",
            "rating": 4.85,
            "product_embedding": generate_cluster_embedding(category_centroids["cat_fitness"])
        }
    ]
    db.products.insert_many(products_raw)

    # 5. Variants
    variants_raw = []
    for p in products_raw:
        if p["category_id"] == "cat_fashion":
            for s in ["S", "M", "L", "XL"]:
                for c in ["Onyx Black", "Heather Grey", "Sand Moss"]:
                    variants_raw.append({
                        "_id": f"var_{p['_id']}_{s}_{c}".replace(" ", "_"),
                        "product_id": p["_id"],
                        "size": s,
                        "color": c,
                        "stock": random.randint(15, 80),
                        "price": p["price"]
                    })
        elif p["category_id"] == "cat_tech":
            for c in ["Matte Black", "Silver Frost", "Midnight Blue"]:
                variants_raw.append({
                    "_id": f"var_{p['_id']}_{c}".replace(" ", "_"),
                    "product_id": p["_id"],
                    "color": c,
                    "stock": random.randint(20, 100),
                    "price": p["price"]
                })
        else:
            variants_raw.append({
                "_id": f"var_{p['_id']}_standard",
                "product_id": p["_id"],
                "size": "Standard",
                "color": "Default",
                "stock": random.randint(30, 120),
                "price": p["price"]
            })
    db.variants.insert_many(variants_raw)

    # 6. Posts, Post Embeddings, Post Metrics, Comments
    # Generate 45 realistic, high-engagement social commerce posts across categories
    post_templates = [
        # Fashion
        ("post_fashion_01", "seller_aurora", "cat_fashion", "prod_hoodie_01",
         "Oversized silhouette styling guide for Autumn. The 500 GSM drape is unmatched 🔥 #streetwear #hoodie #fitcheck",
         "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=800", "video", 2),
        ("post_fashion_02", "seller_aurora", "cat_fashion", "prod_sneakers_01",
         "Unboxing the Nomad Kinetic Runner V2. 10,000 steps test review: 10/10 comfort! 👟 #sneakerhead #streetstyle",
         "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800", "video", 5),
        ("post_fashion_03", "seller_aurora", "cat_fashion", "prod_cargo_01",
         "3 ways to style techwear cargos for work and street. Durable ripstop nylon fabric. #ootd #styleguide",
         "https://images.unsplash.com/photo-1517445312882-bc9910d016b7?w=800", "image", 8),
        ("post_fashion_04", "seller_aurora", "cat_fashion", "prod_hoodie_01",
         "Restock alert! Cloud Fleece Hoodie in Moss Green just dropped. Limited batch! ☁️ #drop #hoodieseason",
         "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=800", "image", 1),
        ("post_fashion_05", "seller_aurora", "cat_fashion", "prod_sneakers_01",
         "Sneaker rotation essentials for 2026. Which colorway are you rocking? #kicks #fashion",
         "https://images.unsplash.com/photo-1607522370275-f14206abe5d3?w=800", "video", 14),

        # Tech
        ("post_tech_01", "seller_soundwave", "cat_tech", "prod_headphones_01",
         "Testing the Aura ANC on a noisy flight. The background roar disappeared instantly 🎧✨ #audiophile #headphones #techreview",
         "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800", "video", 1),
        ("post_tech_02", "seller_techpulse", "cat_tech", "prod_smartwatch_01",
         "Titanium build + 14-day battery life. Why the ChronoTrack Pro replaced my daily watch ⌚ #smartwatch #wearables",
         "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800", "video", 3),
        ("post_tech_03", "seller_techpulse", "cat_tech", "prod_deskmat_01",
         "Clean desk setup transformation with the Merino wool charging mat. Wireless cable clutter solved! ⚡ #desksetup #workspace",
         "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=800", "image", 7),
        ("post_tech_04", "seller_soundwave", "cat_tech", "prod_headphones_01",
         "Bass response vs soundstage comparison: Studio reference benchmark. Beryllium drivers make a difference. #hifi #tech",
         "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=800", "video", 12),
        ("post_tech_05", "seller_techpulse", "cat_tech", "prod_smartwatch_01",
         "Heart rate zone & sleep tracking breakdown. Bio-sensor accuracy test! 📊 #fitnessgear #tech",
         "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=800", "image", 18),

        # Beauty
        ("post_beauty_01", "seller_glowcraft", "cat_beauty", "prod_serum_01",
         "Morning skin barrier routine! Barrier Glaze serum before sunscreen for glass skin all day 🫧 #skincareroutine #glassskin",
         "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=800", "video", 1),
        ("post_beauty_02", "seller_glowcraft", "cat_beauty", "prod_oil_01",
         "Why pure cold-pressed Rosehip oil is the holy grail for hyperpigmentation & glowing skin 🌸 #cleanskincare #beautyhacks",
         "https://images.unsplash.com/photo-1608248597359-5f212720d3f8?w=800", "video", 4),
        ("post_beauty_03", "seller_glowcraft", "cat_beauty", "prod_lip_01",
         "The viral glazed peptide lip tint swatch test on 4 different undertones! Plump and hydrating 💄✨ #lipcombo #makeupreview",
         "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=800", "video", 6),
        ("post_beauty_04", "seller_glowcraft", "cat_beauty", "prod_serum_01",
         "Dermatologist formulation breakdown: How triple hyaluronic acid plumps every skin layer. #scienceofskincare",
         "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=800", "image", 10),
        ("post_beauty_05", "seller_glowcraft", "cat_beauty", "prod_lip_01",
         "Restock in Berry Glaze is finally live! Grab yours before it sells out again. #viralproducts #beauty",
         "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800", "image", 21),

        # Home
        ("post_home_01", "seller_urbannest", "cat_home", "prod_lamp_01",
         "Turning off the big overhead lights for good. The amber mushroom lamp changes the entire living room vibe 🛋️✨ #cozyvibes #roomdecor",
         "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800", "video", 2),
        ("post_home_02", "seller_urbannest", "cat_home", "prod_pour_over_01",
         "Morning pour-over ritual with precision gooseneck flow control. Perfect 93°C extraction ☕ #coffeetime #specialtycoffee",
         "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=800", "video", 4),
        ("post_home_03", "seller_urbannest", "cat_home", "prod_lamp_01",
         "Nordic ambient lighting guide for evening wind-down. High CRI light protects circadian rhythm. #interiordesign #homedecor",
         "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800", "image", 9),
        ("post_home_04", "seller_urbannest", "cat_home", "prod_pour_over_01",
         "V60 bloom recipe & flow technique for floral Ethiopian roasts. #barista #coffeegear",
         "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800", "image", 15),

        # Fitness
        ("post_fit_01", "seller_fitforge", "cat_fitness", "prod_kettlebell_01",
         "Full body 20-minute kettlebell EMOM workout! One adjustable kettlebell replaces an entire rack 💪 #workout #homeworkout #fitness",
         "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=800", "video", 1),
        ("post_fit_02", "seller_fitforge", "cat_fitness", "prod_leggings_01",
         "Squat test approved: AeroFlex compression tights stay high-waisted through heavy leg days 🏋️‍♀️ #activewear #gymfit",
         "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=800", "video", 3),
        ("post_fit_03", "seller_fitforge", "cat_fitness", "prod_kettlebell_01",
         "How to fix your kettlebell swing form in 3 simple cues. Protect your lower back! #formcheck #training",
         "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=800", "image", 11),
        ("post_fit_04", "seller_fitforge", "cat_fitness", "prod_leggings_01",
         "High-intensity sprint interval recovery. Breathable 4-way compression keeps muscles warm. #runninggear #athlete",
         "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=800", "image", 16)
    ]

    posts_raw = []
    embeddings_raw = []
    metrics_raw = []
    comments_raw = []

    now = datetime.now(timezone.utc)

    for p_id, seller_id, cat_id, prod_id, caption, media_url, media_type, days_ago in post_templates:
        created_at = now - timedelta(days=days_ago, hours=random.randint(1, 23))

        post_doc = {
            "_id": p_id,
            "seller_id": seller_id,
            "category_id": cat_id,
            "pinned_product_id": prod_id,
            "caption": caption,
            "media_url": media_url,
            "media_type": media_type,
            "status": "active",
            "created_at": created_at.isoformat()
        }
        posts_raw.append(post_doc)

        # Generate realistic 64-dim embedding clustered around category centroid
        emb = generate_cluster_embedding(category_centroids[cat_id], noise=0.15)
        embeddings_raw.append({
            "_id": f"emb_{p_id}",
            "post_id": p_id,
            "embedding": emb
        })

        # Generate realistic metrics
        base_views = random.randint(2500, 48000)
        likes = int(base_views * random.uniform(0.04, 0.12))
        comments = int(likes * random.uniform(0.03, 0.09))
        shares = int(likes * random.uniform(0.02, 0.08))
        saves = int(likes * random.uniform(0.05, 0.15))
        avg_watch_time = round(random.uniform(0.45, 0.92), 2)

        metrics_raw.append({
            "_id": f"metric_{p_id}",
            "post_id": p_id,
            "total_views": base_views,
            "total_likes": likes,
            "total_comments": comments,
            "total_shares": shares,
            "total_saves": saves,
            "avg_watch_time": avg_watch_time
        })

        # Comments
        sample_comments = [
            "Need this! Just checked the pinned product link 😍",
            "How fast is shipping? The quality looks incredible.",
            "Been using this for 2 weeks now, honestly exceeded my expectations!",
            "Such great aesthetic and detail. Followed for more drops!"
        ]
        for idx, text in enumerate(sample_comments[:random.randint(1, 3)]):
            comments_raw.append({
                "_id": f"comm_{p_id}_{idx}",
                "post_id": p_id,
                "user_id": f"user_shopper_{random.randint(10, 50)}",
                "comment_text": text,
                "sentiment": "positive",
                "timestamp": (created_at + timedelta(hours=random.randint(1, 10))).isoformat()
            })

    db.posts.insert_many(posts_raw)
    db.postembeddings.insert_many(embeddings_raw)
    db.postmetrics.insert_many(metrics_raw)
    db.postcomments.insert_many(comments_raw)

    # 7. User Profiles, Follows, Views, Engagements, Carts, Orders
    # Defined Personas for realistic evaluation & demonstration
    personas = {
        "user_cold_start": {
            "name": "New Visitor (Cold Start)",
            "follows": [],
            "engaged_categories": [],
            "views": [],
            "carts": [],
            "orders": []
        },
        "user_fashion_lover": {
            "name": "Elena - Streetwear & Fashion Enthusiast",
            "follows": ["seller_aurora"],
            "engaged_categories": ["cat_fashion"],
            "views": [("post_fashion_01", 0.95), ("post_fashion_02", 0.90), ("post_fashion_04", 0.85)],
            "engagements": [("post_fashion_01", "like"), ("post_fashion_01", "bookmark"), ("post_fashion_02", "like")],
            "carts": ["prod_hoodie_01"],
            "orders": [{"product_id": "prod_sneakers_01", "amount": 145.0}]
        },
        "user_tech_geek": {
            "name": "David - Audiophile & Tech Geek",
            "follows": ["seller_soundwave", "seller_techpulse"],
            "engaged_categories": ["cat_tech"],
            "views": [("post_tech_01", 1.0), ("post_tech_02", 0.88), ("post_tech_04", 0.92)],
            "engagements": [("post_tech_01", "share"), ("post_tech_01", "like"), ("post_tech_04", "like")],
            "carts": ["prod_headphones_01"],
            "orders": [{"product_id": "prod_headphones_01", "amount": 199.0}]
        },
        "user_beauty_seeker": {
            "name": "Maya - Skincare & Beauty Lover",
            "follows": ["seller_glowcraft"],
            "engaged_categories": ["cat_beauty"],
            "views": [("post_beauty_01", 0.98), ("post_beauty_02", 0.85), ("post_beauty_03", 0.90)],
            "engagements": [("post_beauty_01", "like"), ("post_beauty_03", "bookmark")],
            "carts": ["prod_serum_01", "prod_lip_01"],
            "orders": [{"product_id": "prod_serum_01", "amount": 42.0}]
        },
        "user_fitness_buff": {
            "name": "Alex - Crossfit & Home Gym Athlete",
            "follows": ["seller_fitforge"],
            "engaged_categories": ["cat_fitness"],
            "views": [("post_fit_01", 0.95), ("post_fit_02", 0.80)],
            "engagements": [("post_fit_01", "like"), ("post_fit_01", "share")],
            "carts": ["prod_kettlebell_01"],
            "orders": [{"product_id": "prod_leggings_01", "amount": 68.0}]
        }
    }

    follows_raw = []
    views_raw = []
    engagements_raw = []
    carts_raw = []
    orders_raw = []

    for user_id, profile in personas.items():
        # Follows
        for s_id in profile.get("follows", []):
            follows_raw.append({
                "_id": f"fol_{user_id}_{s_id}",
                "follower_id": user_id,
                "followee_id": s_id,
                "timestamp": (now - timedelta(days=15)).isoformat()
            })

        # Views
        for p_id, watch_pct in profile.get("views", []):
            views_raw.append({
                "_id": f"view_{user_id}_{p_id}",
                "user_id": user_id,
                "post_id": p_id,
                "watch_percentage": watch_pct,
                "duration_seconds": int(watch_pct * 30),
                "timestamp": (now - timedelta(days=random.randint(1, 5))).isoformat()
            })

        # Engagements
        for p_id, act in profile.get("engagements", []):
            engagements_raw.append({
                "_id": f"eng_{user_id}_{p_id}_{act}",
                "user_id": user_id,
                "post_id": p_id,
                "action": act,
                "timestamp": (now - timedelta(days=random.randint(1, 4))).isoformat()
            })

        # Carts
        for prod_id in profile.get("carts", []):
            carts_raw.append({
                "_id": f"cart_{user_id}_{prod_id}",
                "user_id": user_id,
                "product_id": prod_id,
                "quantity": 1,
                "timestamp": (now - timedelta(days=2)).isoformat()
            })

        # Orders
        for o in profile.get("orders", []):
            orders_raw.append({
                "_id": f"ord_{user_id}_{o['product_id']}",
                "user_id": user_id,
                "items": [{"product_id": o["product_id"], "quantity": 1, "price": o["amount"]}],
                "total_amount": o["amount"],
                "status": "completed",
                "timestamp": (now - timedelta(days=6)).isoformat()
            })

    if follows_raw:
        db.follows.insert_many(follows_raw)
    if views_raw:
        db.views.insert_many(views_raw)
    if engagements_raw:
        db.postengagements.insert_many(engagements_raw)
    if carts_raw:
        db.carts.insert_many(carts_raw)
    if orders_raw:
        db.orders.insert_many(orders_raw)

    # Persist if mock db
    if hasattr(db, "save_to_disk") and manager.storage_file:
        db.save_to_disk(manager.storage_file)

    print("Successfully seeded all 13 collections!")
    status = manager.get_status()
    for coll_name, count in status["collection_counts"].items():
        print(f"  - {coll_name}: {count} records")


if __name__ == "__main__":
    seed_database(force_refresh=True)
