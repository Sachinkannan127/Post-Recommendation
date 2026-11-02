"""
Comprehensive Seed Script Generating a Large-Scale Social Commerce Catalog.
Populates 15+ Sellers, 50+ E-Commerce Products, 120+ Social Commerce Posts,
Embeddings, Engagements, Views, Carts, and Orders across all 13 collections.
"""
import os
import random
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any

from backend.app.db.connection import get_db, get_db_manager

# Seed for reproducible, high quality generation
random.seed(42)
np.random.seed(42)

EMBEDDING_DIM = 64

def generate_cluster_embedding(centroid: np.ndarray, noise: float = 0.16) -> List[float]:
    """Generates a normalized embedding vector clustered around a centroid with Gaussian noise."""
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

    if not force_refresh and db.posts.count_documents({}) >= 100:
        print(f"Database already populated ({db.posts.count_documents({})} posts). Skipping re-seed.")
        return

    print("Generating comprehensive social commerce catalog (15+ Sellers, 50+ Products, 120+ Posts)...")

    # Clear all collections
    collections = [
        "posts", "postembeddings", "postengagements", "postmetrics",
        "postcomments", "follows", "views", "carts", "orders",
        "sellerdetails", "productcategories", "productsubcategories",
        "variants", "products"
    ]
    for c in collections:
        db[c].delete_many({})

    # 1. Product Categories
    categories_raw = [
        {"_id": "cat_fashion", "name": "Fashion & Apparel", "slug": "fashion", "icon": "shirt"},
        {"_id": "cat_tech", "name": "Electronics & Tech", "slug": "tech", "icon": "smartphone"},
        {"_id": "cat_beauty", "name": "Beauty & Cosmetics", "slug": "beauty", "icon": "sparkles"},
        {"_id": "cat_home", "name": "Home & Living", "slug": "home", "icon": "home"},
        {"_id": "cat_fitness", "name": "Fitness & Wellness", "slug": "fitness", "icon": "activity"}
    ]
    db.productcategories.insert_many(categories_raw)

    category_centroids = {
        cat["_id"]: create_normalized_centroid(EMBEDDING_DIM) for cat in categories_raw
    }

    # 2. Product Subcategories
    subcategories_raw = [
        # Fashion
        {"_id": "sub_streetwear", "parent_category_id": "cat_fashion", "name": "Streetwear & Hoodies", "slug": "streetwear"},
        {"_id": "sub_footwear", "parent_category_id": "cat_fashion", "name": "Sneakers & Footwear", "slug": "footwear"},
        {"_id": "sub_cargos", "parent_category_id": "cat_fashion", "name": "Cargos & Denim", "slug": "cargos"},
        {"_id": "sub_accessories_fashion", "parent_category_id": "cat_fashion", "name": "Bags & Leather", "slug": "accessories-fashion"},
        # Tech
        {"_id": "sub_audio", "parent_category_id": "cat_tech", "name": "Audio & Headphones", "slug": "audio"},
        {"_id": "sub_wearables", "parent_category_id": "cat_tech", "name": "Smartwatches & Trackers", "slug": "wearables"},
        {"_id": "sub_desk_setup", "parent_category_id": "cat_tech", "name": "Desk Setups & Keyboards", "slug": "desk-setup"},
        {"_id": "sub_chargers", "parent_category_id": "cat_tech", "name": "MagSafe & Fast Chargers", "slug": "chargers"},
        # Beauty
        {"_id": "sub_skincare", "parent_category_id": "cat_beauty", "name": "Barrier Serums & Creams", "slug": "skincare"},
        {"_id": "sub_lipcare", "parent_category_id": "cat_beauty", "name": "Peptide Lip Glazes", "slug": "lipcare"},
        {"_id": "sub_botanicals", "parent_category_id": "cat_beauty", "name": "Organic Facial Oils", "slug": "botanicals"},
        # Home
        {"_id": "sub_lighting", "parent_category_id": "cat_home", "name": "Ambient Lamps & Lighting", "slug": "lighting"},
        {"_id": "sub_coffee", "parent_category_id": "cat_home", "name": "Specialty Coffee Gear", "slug": "coffee"},
        {"_id": "sub_decor", "parent_category_id": "cat_home", "name": "Aesthetic Sanctuary Decor", "slug": "decor"},
        # Fitness
        {"_id": "sub_gym_gear", "parent_category_id": "cat_fitness", "name": "Kettlebells & Weights", "slug": "gym-gear"},
        {"_id": "sub_activewear", "parent_category_id": "cat_fitness", "name": "Compression & Leggings", "slug": "activewear"},
        {"_id": "sub_recovery", "parent_category_id": "cat_fitness", "name": "Massage Guns & Mobility", "slug": "recovery"}
    ]
    db.productsubcategories.insert_many(subcategories_raw)

    # 3. 15 Diverse Sellers & Creators
    sellers_raw = [
        {"_id": "seller_aurora", "name": "Aurora Urban Studio", "handle": "@aurora_streetwear", "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150", "rating": 4.9, "follower_count": 94200, "category": "cat_fashion", "bio": "Heavyweight oversized drops and minimalist silhouette streetwear."},
        {"_id": "seller_aerokinetix", "name": "AeroKinetix Footwear", "handle": "@aerokinetix", "avatar": "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=150", "rating": 4.85, "follower_count": 68400, "category": "cat_fashion", "bio": "Carbon plate running sneakers and daily lifestyle trainers."},
        {"_id": "seller_luxeleather", "name": "LuxeCraft Goods", "handle": "@luxecraft", "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150", "rating": 4.95, "follower_count": 42100, "category": "cat_fashion", "bio": "Vegetable-tanned leather everyday carry wallets and sling bags."},
        {"_id": "seller_soundwave", "name": "SoundWave Labs", "handle": "@soundwave_audio", "avatar": "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=150", "rating": 4.9, "follower_count": 89400, "category": "cat_tech", "bio": "Studio-grade wireless ANC headphones, planar drivers, and hi-fi DACs."},
        {"_id": "seller_techpulse", "name": "TechPulse Gadgets", "handle": "@techpulse", "avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150", "rating": 4.8, "follower_count": 134200, "category": "cat_tech", "bio": "Next-gen workspace tech, ergonomic desk mats, and wireless chargers."},
        {"_id": "seller_cyberkeys", "name": "CyberKeyboards", "handle": "@cyberkeyboards", "avatar": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150", "rating": 4.88, "follower_count": 51200, "category": "cat_tech", "bio": "Custom CNC aluminum mechanical keyboards and lubed linear switches."},
        {"_id": "seller_glowcraft", "name": "GlowCraft Organics", "handle": "@glowcraft", "avatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150", "rating": 4.96, "follower_count": 112000, "category": "cat_beauty", "bio": "Clean barrier repair serums, triple molecular hyaluronic glaze, and peptide lip tints."},
        {"_id": "seller_pureveda", "name": "PureVeda Botanicals", "handle": "@purevedabotanicals", "avatar": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150", "rating": 4.92, "follower_count": 76500, "category": "cat_beauty", "bio": "Cold-pressed organic facial elixirs, rosehip seed oils, and botanical balms."},
        {"_id": "seller_velvetbloom", "name": "VelvetBloom Beauty", "handle": "@velvetbloom", "avatar": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150", "rating": 4.84, "follower_count": 84100, "category": "cat_beauty", "bio": "Featherweight tinted moisturizers and dewy cream blushes."},
        {"_id": "seller_urbannest", "name": "UrbanNest Living", "handle": "@urbannest_home", "avatar": "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=150", "rating": 4.78, "follower_count": 67300, "category": "cat_home", "bio": "Nordic amber mushroom lamps, circadian lighting, and cozy sanctuary decor."},
        {"_id": "seller_zenbrew", "name": "ZenBrew Specialty Coffee", "handle": "@zenbrew", "avatar": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150", "rating": 4.94, "follower_count": 58900, "category": "cat_home", "bio": "Precision electric gooseneck kettles, conical burr grinders, and V60 drippers."},
        {"_id": "seller_fitforge", "name": "FitForge Athletics", "handle": "@fitforge", "avatar": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=150", "rating": 4.87, "follower_count": 128400, "category": "cat_fitness", "bio": "Adjustable competition cast-iron kettlebells, Olympic bars, and squat gear."},
        {"_id": "seller_aeroflex", "name": "AeroFlex Active", "handle": "@aeroflex", "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150", "rating": 4.89, "follower_count": 92100, "category": "cat_fitness", "bio": "High-rise compression leggings, squat-proof contour fabrics, and seamless crops."},
        {"_id": "seller_kineticpulse", "name": "KineticPulse Recovery", "handle": "@kineticpulse", "avatar": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150", "rating": 4.82, "follower_count": 48300, "category": "cat_fitness", "bio": "Quiet brushless deep-tissue massage guns and dynamic compression boots."},
        {"_id": "seller_nordictime", "name": "Nordic Chrono Studio", "handle": "@nordictime", "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150", "rating": 4.91, "follower_count": 39800, "category": "cat_fashion", "bio": "Bauhaus mechanical automatic timepieces and sapphire field watches."}
    ]
    db.sellerdetails.insert_many(sellers_raw)

    # 4. 50+ E-Commerce Products
    product_specs = [
        # Fashion (12 products)
        ("prod_hoodie_01", "seller_aurora", "cat_fashion", "sub_streetwear", "Heavyweight Cloud Fleece Oversized Hoodie", "500 GSM French Terry cotton hoodie with custom drop-shoulder silhouette.", 89.0, 4.9),
        ("prod_sneakers_01", "seller_aerokinetix", "cat_fashion", "sub_footwear", "Nomad Kinetic Runner V2", "Lightweight breathable knit mesh sneaker with responsive nitrogen-infused foam.", 145.0, 4.8),
        ("prod_cargo_01", "seller_aurora", "cat_fashion", "sub_cargos", "Tactical Multi-Pocket Techwear Cargos", "Water-resistant ripstop nylon pants with articulated knee seams and magnetic buckle pockets.", 110.0, 4.7),
        ("prod_tee_01", "seller_aurora", "cat_fashion", "sub_streetwear", "Raw Edge Vintage Washed Boxy Tee", "300 GSM combed cotton vintage garment-dyed boxy silhouette tee.", 48.0, 4.85),
        ("prod_jacket_01", "seller_aurora", "cat_fashion", "sub_streetwear", "Modular Windbreaker Bomber Jacket", "DWR coated lightweight shell jacket with detachable storm hood.", 165.0, 4.9),
        ("prod_runner_02", "seller_aerokinetix", "cat_fashion", "sub_footwear", "AeroStrata Carbon Marathon Shoe", "Full-length carbon fiber plate with ultra-rebound supercritical midsole.", 210.0, 4.95),
        ("prod_sling_01", "seller_luxeleather", "cat_fashion", "sub_accessories_fashion", "Minimalist Crossbody Sling Pack", "Full-grain vegetable-tanned leather pack with Fidlock V-buckle closure.", 125.0, 4.9),
        ("prod_wallet_01", "seller_luxeleather", "cat_fashion", "sub_accessories_fashion", "Slim RFID Bifold Cardholder", "Ultra-slim Italian pull-up leather wallet holding up to 10 cards.", 55.0, 4.8),
        ("prod_watch_01", "seller_nordictime", "cat_fashion", "sub_accessories_fashion", "Krono Bauhaus Automatic Field Watch", "Miyota 9015 automatic movement, sapphire crystal, and 100m water resistance.", 320.0, 4.92),
        ("prod_denim_01", "seller_aurora", "cat_fashion", "sub_cargos", "Selvedge Raw Relaxed Tapered Jeans", "14oz Japanese selvedge denim with copper hardware and chainstitched hem.", 135.0, 4.82),
        ("prod_beanie_01", "seller_aurora", "cat_fashion", "sub_streetwear", "Ribbed Merino Wool Fisherman Beanie", "100% extrafine merino wool watch cap with dense thermal knit.", 38.0, 4.75),
        ("prod_tote_01", "seller_luxeleather", "cat_fashion", "sub_accessories_fashion", "Heavy Canvas & Leather Carryall Tote", "Waxed 18oz duck canvas tote with bridle leather shoulder straps.", 98.0, 4.88),

        # Tech (12 products)
        ("prod_headphones_01", "seller_soundwave", "cat_tech", "sub_audio", "Aura ANC Spatial Wireless Headphones", "Hybrid active noise cancelling with custom 40mm beryllium drivers and 45hr battery.", 199.0, 4.9),
        ("prod_smartwatch_01", "seller_techpulse", "cat_tech", "sub_wearables", "ChronoTrack Pro Titanium Smartwatch", "Sapphire crystal display, ECG monitoring, offline GPS, and 14-day battery.", 279.0, 4.85),
        ("prod_deskmat_01", "seller_techpulse", "cat_tech", "sub_desk_setup", "MagCharge Merino Wool Desk Pad", "Integrated 15W Qi2 wireless charging spot with vegan leather accents.", 65.0, 4.75),
        ("prod_keyboard_01", "seller_cyberkeys", "cat_tech", "sub_desk_setup", "Luminary 75 CNC Aluminum Keyboard", "Gasket-mounted hot-swap mechanical keyboard with pre-lubed linear switches.", 185.0, 4.95),
        ("prod_earbuds_01", "seller_soundwave", "cat_tech", "sub_audio", "SonicPro True Wireless ANC Earbuds", "Quad-mic beamforming noise cancellation with IPX7 sweat resistance.", 129.0, 4.8),
        ("prod_charger_01", "seller_techpulse", "cat_tech", "sub_chargers", "140W GaN 4-Port Fast Travel Charger", "Ultra-compact Gallium Nitride charger capable of fast-charging 2 laptops simultaneously.", 79.0, 4.88),
        ("prod_dac_01", "seller_soundwave", "cat_tech", "sub_audio", "PulseAmp Portable Hi-Fi MQA DAC", "Dual ESS Sabre ES9219 DAC chips with 3.5mm and 4.4mm balanced outputs.", 115.0, 4.92),
        ("prod_monitor_light_01", "seller_techpulse", "cat_tech", "sub_desk_setup", "AuraScreen Asymmetric Monitor Light Bar", "Wireless dial controller, zero screen glare, and auto-dimming ambient sensor.", 69.0, 4.82),
        ("prod_smartring_01", "seller_techpulse", "cat_tech", "sub_wearables", "Circa Titanium Sleep & Recovery Ring", "Biometric sleep stage tracking, HRV, temperature sensors, and 7-day battery.", 249.0, 4.87),
        ("prod_keycaps_01", "seller_cyberkeys", "cat_tech", "sub_desk_setup", "CyberDune PBT Doubleshot Keycap Set", "Durable Cherry profile PBT keycaps with crisp legends and rich deep colors.", 49.0, 4.8),
        ("prod_stand_01", "seller_techpulse", "cat_tech", "sub_desk_setup", "Solid Walnut Wood Laptop & MagSafe Riser", "Handcrafted solid walnut laptop stand with felt padding and cable routing channels.", 85.0, 4.9),
        ("prod_powerbank_01", "seller_techpulse", "cat_tech", "sub_chargers", "MagFold 10,000mAh Magnetic Kickstand Battery", "Snap-on MagSafe wireless power bank with folding zinc-alloy kickstand.", 59.0, 4.79),

        # Beauty (10 products)
        ("prod_serum_01", "seller_glowcraft", "cat_beauty", "sub_skincare", "Hyaluronic Peptide Barrier Glaze Serum", "Triple molecular weight hyaluronic acid infused with niacinamide & ceramides.", 42.0, 4.95),
        ("prod_oil_01", "seller_pureveda", "cat_beauty", "sub_botanicals", "Cold-Pressed Rosehip Glow Elixir", "Unrefined organic cold-pressed oil rich in Vitamin A and linoleic acid for skin renewal.", 38.0, 4.85),
        ("prod_lip_01", "seller_glowcraft", "cat_beauty", "sub_lipcare", "HydraDew Tinted Peptide Lip Treatment", "Deeply nourishing peptide treatment that plumps and leaves a high-shine glossy tint.", 24.0, 4.9),
        ("prod_cream_01", "seller_glowcraft", "cat_beauty", "sub_skincare", "Ceramide Multi-Defense Barrier Cream", "Rich biomimetic ceramide matrix providing 48-hour deep lipid barrier lock.", 46.0, 4.92),
        ("prod_cleanser_01", "seller_pureveda", "cat_beauty", "sub_skincare", "Gentle Botanical Oat Milk Jelly Cleanser", "Non-stripping sulfate-free cleanser preserving the skin acid mantle.", 28.0, 4.8),
        ("prod_blush_01", "seller_velvetbloom", "cat_beauty", "sub_lipcare", "CloudDew Melting Cream Blush", "Whipped cream-to-powder blush melting seamlessly for a natural dewy flush.", 26.0, 4.86),
        ("prod_sunscreen_01", "seller_glowcraft", "cat_beauty", "sub_skincare", "Invisible Fluid SPF50+ PA++++ Sun Serum", "Weightless zero white-cast daily mineral sunscreen infused with green tea antioxidants.", 34.0, 4.94),
        ("prod_eyegel_01", "seller_pureveda", "cat_beauty", "sub_skincare", "Awaken Caffeine & Peptides Under-Eye Gel", "Depuffs fluid retention and reduces dark circles in 10 minutes.", 32.0, 4.81),
        ("prod_exfoliant_01", "seller_glowcraft", "cat_beauty", "sub_skincare", "2% BHA Pore Clarifying Liquid Exfoliant", "Salicylic acid liquid clearing clogged sebum pores without skin irritation.", 36.0, 4.89),
        ("prod_mask_01", "seller_pureveda", "cat_beauty", "sub_botanicals", "Manuka Honey & Saffron Glow Recovery Mask", "Raw bio-active manuka honey treatment restoring dehydrated tired skin.", 48.0, 4.93),

        # Home & Kitchen (10 products)
        ("prod_lamp_01", "seller_urbannest", "cat_home", "sub_lighting", "Lumina Ambient Mushroom Desk Lamp", "Hand-blown warm amber glass table lamp with touch dimming and RGB mood lighting.", 75.0, 4.8),
        ("prod_pour_over_01", "seller_zenbrew", "cat_home", "sub_coffee", "BaristaPro Precision Gooseneck Kettle", "Matte black electric temperature kettle with Strix controller and 0.9L capacity.", 95.0, 4.9),
        ("prod_grinder_01", "seller_zenbrew", "cat_home", "sub_coffee", "Apex Conical Burr Hand Coffee Grinder", "CNC stainless steel burrs with 40 stepped grind settings for espresso to French press.", 119.0, 4.94),
        ("prod_scale_01", "seller_zenbrew", "cat_home", "sub_coffee", "MicroFlow Precision Timer Espresso Scale", "0.1g accuracy scale with auto-timer for specialty coffee flow profiling.", 45.0, 4.84),
        ("prod_diffuser_01", "seller_urbannest", "cat_home", "sub_decor", "Ceramic Ultrasonic Stone Aroma Diffuser", "Matte handcrafted ceramic stone diffuser with ambient warm LED nightlight.", 68.0, 4.79),
        ("prod_blanket_01", "seller_urbannest", "cat_home", "sub_decor", "Chunky Knit Weighted Cooling Blanket", "15 lb organic knit cotton blanket designed to reduce evening anxiety naturally.", 135.0, 4.91),
        ("prod_dripper_01", "seller_zenbrew", "cat_home", "sub_coffee", "Double-Walled Borosilicate Glass V60", "Insulated pour-over dripper maintaining optimal thermal brew stability.", 38.0, 4.87),
        ("prod_pendant_01", "seller_urbannest", "cat_home", "sub_lighting", "Wabi-Sabi Paper Lantern Pendant Light", "Japanese washi paper hanging pendant casting soft atmospheric warmth.", 89.0, 4.83),
        ("prod_carafe_01", "seller_zenbrew", "cat_home", "sub_coffee", "Insulated Thermal Coffee Carafe 1.2L", "Stainless steel double-wall vacuum carafe keeping brew piping hot for 8 hours.", 52.0, 4.78),
        ("prod_clock_01", "seller_urbannest", "cat_home", "sub_decor", "Minimalist Concrete Desk Clock", "Cast architectural concrete analog desk clock with silent quartz sweep movement.", 42.0, 4.82),

        # Fitness & Recovery (10 products)
        ("prod_kettlebell_01", "seller_fitforge", "cat_fitness", "sub_gym_gear", "Adjustable Cast Iron Competition Kettlebell", "Quick-lock selector mechanism switching seamlessly from 8kg to 32kg.", 185.0, 4.9),
        ("prod_leggings_01", "seller_aeroflex", "cat_fitness", "sub_activewear", "AeroFlex High-Rise Seamless Compression Tights", "Squat-proof 4-way stretch fabric with targeted contour zones and phone pocket.", 68.0, 4.85),
        ("prod_massage_gun_01", "seller_kineticpulse", "cat_fitness", "sub_recovery", "ProPulse Brushless Deep Tissue Percussion Gun", "16mm amplitude, 5 speed settings, and whisper-quiet 45dB motor.", 159.0, 4.91),
        ("prod_straps_01", "seller_fitforge", "cat_fitness", "sub_gym_gear", "Figure 8 Heavy Duty Deadlift Straps", "Reinforced cotton webbing rated up to 1,000 lbs pull capacity.", 22.0, 4.83),
        ("prod_shorts_01", "seller_aeroflex", "cat_fitness", "sub_activewear", "2-in-1 Lined Performance Training Shorts", "Anti-chafing compression liner with zippered waterproof card pocket.", 52.0, 4.8),
        ("prod_foam_roller_01", "seller_kineticpulse", "cat_fitness", "sub_recovery", "Vibrating High-Density Trigger Point Roller", "4 vibration frequencies targeting myofascial trigger points.", 79.0, 4.86),
        ("prod_bra_01", "seller_aeroflex", "cat_fitness", "sub_activewear", "CoreSupport Cross-Back High Impact Sports Bra", "Sweat-wicking compressive athletic bra with removable molded cups.", 46.0, 4.82),
        ("prod_mat_01", "seller_aeroflex", "cat_fitness", "sub_activewear", "ProGrip Natural Tree Rubber Yoga Mat", "5mm thick non-slip alignment guide mat made from sustainably harvested rubber.", 78.0, 4.92),
        ("prod_grips_01", "seller_fitforge", "cat_fitness", "sub_gym_gear", "Gymnastic Carbon Hand Grips", "High-tack carbon fiber palms protecting skin during high-rep bar work.", 36.0, 4.79),
        ("prod_jump_rope_01", "seller_fitforge", "cat_fitness", "sub_gym_gear", "Ball-Bearing Speed Cable Jump Rope", "Dual 360-degree ball bearings designed for seamless double-unders.", 28.0, 4.84)
    ]

    products_raw = []
    variants_raw = []
    product_centroids = {}

    for p_id, s_id, c_id, sub_id, title, desc, price, rating in product_specs:
        emb = generate_cluster_embedding(category_centroids[c_id], noise=0.14)
        product_centroids[p_id] = emb

        products_raw.append({
            "_id": p_id,
            "seller_id": s_id,
            "category_id": c_id,
            "subcategory_id": sub_id,
            "title": title,
            "description": desc,
            "price": price,
            "rating": rating,
            "product_embedding": emb
        })

        # Variants
        if c_id == "cat_fashion" or sub_id == "sub_activewear":
            for s in ["S", "M", "L", "XL"]:
                for c in ["Onyx Black", "Heather Grey", "Sand Tan"]:
                    variants_raw.append({
                        "_id": f"var_{p_id}_{s}_{c}".replace(" ", "_"),
                        "product_id": p_id,
                        "size": s,
                        "color": c,
                        "stock": random.randint(15, 60),
                        "price": price
                    })
        elif c_id == "cat_tech":
            for col in ["Matte Black", "Space Grey", "Lunar Silver"]:
                variants_raw.append({
                    "_id": f"var_{p_id}_{col}".replace(" ", "_"),
                    "product_id": p_id,
                    "color": col,
                    "stock": random.randint(20, 80),
                    "price": price
                })
        else:
            variants_raw.append({
                "_id": f"var_{p_id}_standard",
                "product_id": p_id,
                "size": "Standard",
                "color": "Default",
                "stock": random.randint(30, 100),
                "price": price
            })

    db.products.insert_many(products_raw)
    db.variants.insert_many(variants_raw)

    # 5. 120+ Rich Social Commerce Posts
    post_images = {
        "cat_fashion": [
            "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=800",
            "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800",
            "https://images.unsplash.com/photo-1517445312882-bc9910d016b7?w=800",
            "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=800",
            "https://images.unsplash.com/photo-1607522370275-f14206abe5d3?w=800",
            "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=800",
            "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=800",
            "https://images.unsplash.com/photo-1485230895905-ec40ba36b9bc?w=800"
        ],
        "cat_tech": [
            "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800",
            "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800",
            "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=800",
            "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=800",
            "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=800",
            "https://images.unsplash.com/photo-1588702547919-26089e690ecc?w=800",
            "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800",
            "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800"
        ],
        "cat_beauty": [
            "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=800",
            "https://images.unsplash.com/photo-1608248597359-5f212720d3f8?w=800",
            "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=800",
            "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=800",
            "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800",
            "https://images.unsplash.com/photo-1512290900672-1f41d7f57321?w=800",
            "https://images.unsplash.com/photo-1526947425960-945c6e72858f?w=800"
        ],
        "cat_home": [
            "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800",
            "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=800",
            "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800",
            "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800",
            "https://images.unsplash.com/photo-1540574163026-643ea20ade25?w=800",
            "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=800"
        ],
        "cat_fitness": [
            "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=800",
            "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=800",
            "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=800",
            "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=800",
            "https://images.unsplash.com/photo-1538805060514-97d9cc17730c?w=800",
            "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=800"
        ]
    }

    caption_hooks = {
        "cat_fashion": [
            "Oversized drape styling breakdown. The weight on this French Terry fabric is unreal 🔥 #streetwear #fitcheck",
            "10,000 steps wear-test! Why these runners replaced every sneaker in my rotation 👟 #sneakers #streetstyle",
            "3 effortless styling combos for the autumn drop. Minimalist monochrome aesthetic #ootd #fashioninspo",
            "Restock alert! Our most viral piece is back in limited quantities. Check the pinned link ☁️ #drop #hoodie",
            "How to build a functional capsule wardrobe for 2026. Quality over quantity always #minimalism #styleguide",
            "Unboxing the handcrafted leather cross-body. The patina after 3 months is stunning ✨ #edc #leathergoods"
        ],
        "cat_tech": [
            "Noise cancellation test in the busiest airport in the world. Total silence achieved 🎧✨ #audiophile #techreview",
            "Titanium build + 14-day battery life. Why the ChronoTrack Pro completely replaced my daily watch ⌚ #smartwatch",
            "Clean desk setup transformation! Say goodbye to tangled charging cables with this wool pad ⚡ #workspace",
            "Testing mechanical switch acoustics: lubed linear switches vs tactile bump. Sound profile is creamy ⌨️ #keebs",
            "Fastest travel charging setup for 2026. 140W GaN power brick handles everything in my bag #edc #gadgets",
            "Is the spatial audio hype real? We benchmarked the beryllium drivers in a studio setting #audio #hifi"
        ],
        "cat_beauty": [
            "My 3-step morning skin barrier repair routine for glass skin all day long 🫧 #skincareroutine #glassskin",
            "Why unrefined cold-pressed rosehip seed oil faded my dark spots in under 4 weeks 🌸 #cleanbeauty #beautyhacks",
            "The viral glazed lip peptide treatment swatch test on 5 different skin undertones 💄✨ #lipcombo #viralproducts",
            "Dermatologist formulation deep-dive: how triple hyaluronic acid plumps every epidermal layer #skincarescience",
            "Mineral SPF that leaves absolutely ZERO white cast on deep skin tones! Sunscreen game changer ☀️ #spf #skincare",
            "Nighttime barrier recovery ritual. Waking up with dewy hydrated skin every single morning #selfcare #beauty"
        ],
        "cat_home": [
            "Turning off overhead lights forever. The ambient amber mushroom lamp changes the entire living room vibe 🛋️✨ #cozy",
            "Morning pour-over ritual with precision gooseneck flow. Perfect 93°C extraction every time ☕ #specialtycoffee",
            "How to set up a Nordic sanctuary corner in a small apartment. Clean lines and warm textiles #interior #decor",
            "Conical burr grinder dial-in tutorial for light roast Ethiopian beans. Flow profile is silky #barista #coffeegear",
            "Evening wind-down routine with ultrasonic stone aromatherapy. Stress melted away in 10 minutes #zen #homedecor",
            "Why weighted knit blankets improve REM sleep naturally according to sleep specialists #wellness #sleep"
        ],
        "cat_fitness": [
            "Full body 20-minute kettlebell EMOM workout! One adjustable bell replaces an entire weight rack 💪 #homeworkout",
            "Squat test approved: AeroFlex compression tights stay high-waisted through heavy leg days 🏋️‍♀️ #activewear #gymfit",
            "3 simple form cues that instantly fixed my kettlebell swing and protected my lower back #formcheck #training",
            "Deep tissue percussion gun test on tight hamstrings after a heavy deadlift session. Instant relief #mobility",
            "High-intensity sprint interval conditioning. 4-way compression keeps the legs feeling light #athlete #running",
            "Why grip strength is the #1 predictor of athletic longevity and deadlift PRs. Form tips #powerlifting #crossfit"
        ]
    }

    posts_raw = []
    embeddings_raw = []
    metrics_raw = []
    comments_raw = []

    now = datetime.now(timezone.utc)
    post_counter = 0

    # Generate 125 posts distributed across products and categories
    for cat in categories_raw:
        cat_id = cat["_id"]
        cat_products = [p for p in products_raw if p["category_id"] == cat_id]
        cat_sellers = [s for s in sellers_raw if s["category"] == cat_id] or sellers_raw[:3]
        images = post_images[cat_id]
        captions = caption_hooks[cat_id]

        # Generate 60 posts per category = 300 total posts
        for i in range(60):
            post_counter += 1
            p_id = f"post_{cat_id}_{i+1:02d}"
            seller = cat_sellers[i % len(cat_sellers)]
            prod = cat_products[i % len(cat_products)]
            img_url = images[i % len(images)]
            caption_base = captions[i % len(captions)]
            caption = f"{caption_base} (Item: {prod['title']})"

            days_ago = random.randint(0, 28)
            created_at = now - timedelta(days=days_ago, hours=random.randint(1, 23), minutes=random.randint(0, 59))
            media_type = "video" if (i % 3 != 0) else "image"

            posts_raw.append({
                "_id": p_id,
                "seller_id": seller["_id"],
                "category_id": cat_id,
                "pinned_product_id": prod["_id"],
                "caption": caption,
                "media_url": img_url,
                "media_type": media_type,
                "status": "active",
                "created_at": created_at.isoformat()
            })

            # Clustered embedding around category centroid with product affinity
            prod_emb = np.array(product_centroids[prod["_id"]])
            post_emb = generate_cluster_embedding(prod_emb, noise=0.10)
            embeddings_raw.append({
                "_id": f"emb_{p_id}",
                "post_id": p_id,
                "embedding": post_emb
            })

            # Realistic metrics
            base_views = random.randint(1200, 68000)
            likes = int(base_views * random.uniform(0.04, 0.14))
            comments = int(likes * random.uniform(0.03, 0.08))
            shares = int(likes * random.uniform(0.02, 0.09))
            saves = int(likes * random.uniform(0.05, 0.18))
            avg_watch = round(random.uniform(0.48, 0.96), 2)

            metrics_raw.append({
                "_id": f"metric_{p_id}",
                "post_id": p_id,
                "total_views": base_views,
                "total_likes": likes,
                "total_comments": comments,
                "total_shares": shares,
                "total_saves": saves,
                "avg_watch_time": avg_watch
            })

            # Sample comments
            c_pool = [
                f"Just checked out the pinned item ({prod['title']}), so clean!",
                "Does this run true to size? Planning to order today!",
                "Best purchase I made all year, honestly 10/10 quality.",
                "How fast was shipping? Loving the aesthetic here.",
                "Followed for more styling inspiration!"
            ]
            for c_idx, c_text in enumerate(random.sample(c_pool, k=random.randint(1, 3))):
                comments_raw.append({
                    "_id": f"comm_{p_id}_{c_idx}",
                    "post_id": p_id,
                    "user_id": f"user_shopper_{random.randint(10, 80)}",
                    "comment_text": c_text,
                    "sentiment": "positive",
                    "timestamp": (created_at + timedelta(hours=random.randint(1, 8))).isoformat()
                })

    db.posts.insert_many(posts_raw)
    db.postembeddings.insert_many(embeddings_raw)
    db.postmetrics.insert_many(metrics_raw)
    db.postcomments.insert_many(comments_raw)

    # 6. Personas with Dense Interaction Histories
    personas = {
        "user_cold_start": {
            "name": "New Visitor (Cold Start)",
            "follows": [],
            "views": [],
            "engagements": [],
            "carts": [],
            "orders": []
        },
        "user_fashion_lover": {
            "name": "Elena Vance - Fashion & Streetwear Shopper",
            "follows": ["seller_aurora", "seller_aerokinetix", "seller_luxeleather"],
            "views": [
                ("post_cat_fashion_01", 0.95), ("post_cat_fashion_02", 0.92),
                ("post_cat_fashion_03", 0.88), ("post_cat_fashion_04", 0.85),
                ("post_cat_fashion_05", 0.90), ("post_cat_fashion_06", 0.94)
            ],
            "engagements": [
                ("post_cat_fashion_01", "like"), ("post_cat_fashion_01", "bookmark"),
                ("post_cat_fashion_02", "like"), ("post_cat_fashion_03", "share"),
                ("post_cat_fashion_05", "like")
            ],
            "carts": ["prod_hoodie_01", "prod_cargo_01"],
            "orders": [{"product_id": "prod_sneakers_01", "amount": 145.0}]
        },
        "user_tech_geek": {
            "name": "David Chen - Audiophile & Techie",
            "follows": ["seller_soundwave", "seller_techpulse", "seller_cyberkeys"],
            "views": [
                ("post_cat_tech_01", 1.0), ("post_cat_tech_02", 0.92),
                ("post_cat_tech_03", 0.85), ("post_cat_tech_04", 0.94),
                ("post_cat_tech_05", 0.89), ("post_cat_tech_06", 0.91)
            ],
            "engagements": [
                ("post_cat_tech_01", "like"), ("post_cat_tech_01", "share"),
                ("post_cat_tech_02", "like"), ("post_cat_tech_04", "bookmark")
            ],
            "carts": ["prod_headphones_01", "prod_keyboard_01"],
            "orders": [{"product_id": "prod_deskmat_01", "amount": 65.0}]
        },
        "user_beauty_seeker": {
            "name": "Maya Lin - Skincare & Beauty Lover",
            "follows": ["seller_glowcraft", "seller_pureveda", "seller_velvetbloom"],
            "views": [
                ("post_cat_beauty_01", 0.98), ("post_cat_beauty_02", 0.90),
                ("post_cat_beauty_03", 0.94), ("post_cat_beauty_04", 0.88),
                ("post_cat_beauty_05", 0.91)
            ],
            "engagements": [
                ("post_cat_beauty_01", "like"), ("post_cat_beauty_01", "bookmark"),
                ("post_cat_beauty_02", "like"), ("post_cat_beauty_03", "share")
            ],
            "carts": ["prod_serum_01", "prod_lip_01"],
            "orders": [{"product_id": "prod_cream_01", "amount": 46.0}]
        },
        "user_fitness_buff": {
            "name": "Alex Miller - Crossfit & Home Gym Athlete",
            "follows": ["seller_fitforge", "seller_aeroflex", "seller_kineticpulse"],
            "views": [
                ("post_cat_fitness_01", 0.96), ("post_cat_fitness_02", 0.88),
                ("post_cat_fitness_03", 0.92), ("post_cat_fitness_04", 0.85)
            ],
            "engagements": [
                ("post_cat_fitness_01", "like"), ("post_cat_fitness_01", "share"),
                ("post_cat_fitness_02", "bookmark")
            ],
            "carts": ["prod_kettlebell_01", "prod_straps_01"],
            "orders": [{"product_id": "prod_leggings_01", "amount": 68.0}]
        }
    }

    follows_raw = []
    views_raw = []
    engagements_raw = []
    carts_raw = []
    orders_raw = []

    for u_id, prof in personas.items():
        for s_id in prof["follows"]:
            follows_raw.append({"_id": f"fol_{u_id}_{s_id}", "follower_id": u_id, "followee_id": s_id, "timestamp": (now - timedelta(days=20)).isoformat()})
        for p_id, w_pct in prof["views"]:
            views_raw.append({"_id": f"view_{u_id}_{p_id}", "user_id": u_id, "post_id": p_id, "watch_percentage": w_pct, "duration_seconds": int(w_pct * 30), "timestamp": (now - timedelta(days=random.randint(1, 6))).isoformat()})
        for p_id, act in prof["engagements"]:
            engagements_raw.append({"_id": f"eng_{u_id}_{p_id}_{act}", "user_id": u_id, "post_id": p_id, "action": act, "timestamp": (now - timedelta(days=random.randint(1, 5))).isoformat()})
        for pr_id in prof["carts"]:
            carts_raw.append({"_id": f"cart_{u_id}_{pr_id}", "user_id": u_id, "product_id": pr_id, "quantity": 1, "timestamp": (now - timedelta(days=1)).isoformat()})
        for o in prof["orders"]:
            orders_raw.append({"_id": f"ord_{u_id}_{o['product_id']}", "user_id": u_id, "items": [{"product_id": o["product_id"], "quantity": 1, "price": o["amount"]}], "total_amount": o["amount"], "status": "completed", "timestamp": (now - timedelta(days=7)).isoformat()})

    if follows_raw: db.follows.insert_many(follows_raw)
    if views_raw: db.views.insert_many(views_raw)
    if engagements_raw: db.postengagements.insert_many(engagements_raw)
    if carts_raw: db.carts.insert_many(carts_raw)
    if orders_raw: db.orders.insert_many(orders_raw)

    if hasattr(db, "save_to_disk") and manager.storage_file:
        db.save_to_disk(manager.storage_file)

    print("Large-Scale catalog seeded successfully!")
    status = manager.get_status()
    for coll_name, count in status["collection_counts"].items():
        print(f"  • {coll_name}: {count} records")


if __name__ == "__main__":
    seed_database(force_refresh=True)
