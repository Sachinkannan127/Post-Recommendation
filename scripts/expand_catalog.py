"""
Catalog Expansion Script.
Adds 150+ diverse, high-engagement social commerce posts and 45+ products across
Fashion, Tech, Beauty, Home Decor, and Fitness to provide a massive recommendation catalog.
"""
import os
import random
import numpy as np
from datetime import datetime, timedelta, timezone

from backend.app.database.mongodb import get_database, get_db_manager

random.seed(1337)
np.random.seed(1337)

EMBEDDING_DIM = 64

def generate_cluster_embedding(dim: int = 64) -> list:
    vec = np.random.randn(dim)
    norm = np.linalg.norm(vec)
    return [round(float(x), 6) for x in (vec / norm)]

def expand_catalog():
    db = get_database()
    manager = get_db_manager()

    print(f"Current posts: {db.posts.count_documents({})}, products: {db.products.count_documents({})}")

    # Additional Products (45 products)
    new_product_templates = [
        # Fashion
        ("prod_lux_coat", "seller_luxeleather", "cat_fashion", "sub_streetwear", "Italian Cashmere Trench Coat", 380.0, 4.95, "https://images.unsplash.com/photo-1539533018447-63fcce667883?w=600"),
        ("prod_retro_sneaker", "seller_aerokinetix", "cat_fashion", "sub_footwear", "Retro 90s Suede Chunky Trainer", 130.0, 4.82, "https://images.unsplash.com/photo-1552346154-21d32810aba3?w=600"),
        ("prod_silk_scarf", "seller_luxeleather", "cat_fashion", "sub_accessories_fashion", "Mulberry Silk Geometric Scarf", 65.0, 4.88, "https://images.unsplash.com/photo-1601924994987-69e26d50dc26?w=600"),
        ("prod_denim_overshirt", "seller_aurora", "cat_fashion", "sub_cargos", "Heavyweight Vintage Denim Overshirt", 95.0, 4.78, "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=600"),
        ("prod_minimal_chelsea", "seller_aerokinetix", "cat_fashion", "sub_footwear", "Waterproof Nubuck Chelsea Boot", 185.0, 4.91, "https://images.unsplash.com/photo-1638247025967-b4e38f787b76?w=600"),
        ("prod_linen_blazer", "seller_aurora", "cat_fashion", "sub_streetwear", "Relaxed European Linen Summer Blazer", 140.0, 4.85, "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=600"),
        ("prod_travel_duffel", "seller_luxeleather", "cat_fashion", "sub_accessories_fashion", "Waxed Canvas Weekender Duffel", 160.0, 4.93, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600"),

        # Tech
        ("prod_mechanical_numpad", "seller_cyberkeys", "cat_tech", "sub_desk_setup", "CNC Aluminum Wireless Macro Numpad", 75.0, 4.89, "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600"),
        ("prod_planar_iem", "seller_soundwave", "cat_tech", "sub_audio", "Planar Magnetic In-Ear Monitors (IEM)", 150.0, 4.96, "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600"),
        ("prod_mag_stand", "seller_techpulse", "cat_tech", "sub_chargers", "3-in-1 Foldable MagSafe Travel Dock", 68.0, 4.84, "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=600"),
        ("prod_smart_speaker", "seller_soundwave", "cat_tech", "sub_audio", "Acoustic Wood Hi-Fi Smart Speaker", 220.0, 4.90, "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=600"),
        ("prod_desk_lightbar", "seller_techpulse", "cat_tech", "sub_desk_setup", "Dual Screen Ultra-Wide Monitor Lamp", 85.0, 4.86, "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=600"),
        ("prod_ergo_mouse", "seller_techpulse", "cat_tech", "sub_desk_setup", "Vertical Precision Ergonomic Bluetooth Mouse", 79.0, 4.82, "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=600"),
        ("prod_usb4_dock", "seller_techpulse", "cat_tech", "sub_chargers", "Thunderbolt 4 Triple 4K Display Dock", 195.0, 4.92, "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600"),

        # Beauty
        ("prod_glow_mask", "seller_glowcraft", "cat_beauty", "sub_skincare", "Overnight Ceramide Recovery Jelly Mask", 42.0, 4.94, "https://images.unsplash.com/photo-1567928815116-f6d3ad668819?w=600"),
        ("prod_sun_serum", "seller_glowcraft", "cat_beauty", "sub_skincare", "Invisible SPF 50 Water-Gel Sunscreen Serum", 36.0, 4.91, "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=600"),
        ("prod_peptide_mist", "seller_pureveda", "cat_beauty", "sub_botanicals", "Rosewater & Copper Peptide Refreshing Mist", 32.0, 4.88, "https://images.unsplash.com/photo-1608248597359-597561f38e65?w=600"),
        ("prod_bakuchiol_oil", "seller_pureveda", "cat_beauty", "sub_botanicals", "Plant Retinol 2% Bakuchiol Night Elixir", 48.0, 4.95, "https://images.unsplash.com/photo-1617897903246-719242758050?w=600"),
        ("prod_lip_butter", "seller_velvetbloom", "cat_beauty", "sub_lipcare", "Vanilla Agave Hydrating Lip Butter Balm", 22.0, 4.87, "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=600"),
        ("prod_cream_bronzer", "seller_velvetbloom", "cat_beauty", "sub_botanicals", "Weightless Sunkissed Cream Bronzer Stick", 34.0, 4.83, "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=600"),

        # Home & Kitchen
        ("prod_ceramic_pour", "seller_zenbrew", "cat_home", "sub_coffee", "Origami Ceramic Matte Pour-Over Dripper", 38.0, 4.92, "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=600"),
        ("prod_espresso_scale", "seller_zenbrew", "cat_home", "sub_coffee", "Precision High-Speed Smart Espresso Scale", 72.0, 4.96, "https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?w=600"),
        ("prod_waffle_throw", "seller_urbannest", "cat_home", "sub_decor", "Organic Stone-Washed Waffle Cotton Blanket", 85.0, 4.89, "https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?w=600"),
        ("prod_scented_candle", "seller_urbannest", "cat_home", "sub_decor", "Smoked Amber & Sandalwood Soy Candle", 34.0, 4.85, "https://images.unsplash.com/photo-1603006905003-be475563bc59?w=600"),
        ("prod_ceramic_vase", "seller_urbannest", "cat_home", "sub_decor", "Modern Ribbed Ceramic Donut Vase", 45.0, 4.79, "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=600"),
        ("prod_ambient_orb", "seller_urbannest", "cat_home", "sub_lighting", "Wireless Dimmable Ambient Orb Lamp", 58.0, 4.91, "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=600"),

        # Fitness & Wellness
        ("prod_steel_mace", "seller_fitforge", "cat_fitness", "sub_gym_gear", "Solid Steel 10lb Functional Training Mace", 65.0, 4.88, "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=600"),
        ("prod_olympic_rings", "seller_fitforge", "cat_fitness", "sub_gym_gear", "Birch Wood Gymnastic Rings with Straps", 48.0, 4.94, "https://images.unsplash.com/photo-1599058917212-d750089bc07e?w=600"),
        ("prod_seamless_bra", "seller_aeroflex", "cat_fitness", "sub_activewear", "Ribbed Scoop Longline Sports Bra", 42.0, 4.86, "https://images.unsplash.com/photo-1506152983158-b4a74a01c721?w=600"),
        ("prod_weighted_vest", "seller_fitforge", "cat_fitness", "sub_gym_gear", "Adjustable 20lb Breathable Tactical Vest", 95.0, 4.89, "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=600"),
        ("prod_cold_plunge", "seller_kineticpulse", "cat_fitness", "sub_recovery", "Portable Insulated Cold Plunge Tub", 160.0, 4.93, "https://images.unsplash.com/photo-1540555700478-4be289fbecef?w=600"),
        ("prod_foam_roller", "seller_kineticpulse", "cat_fitness", "sub_recovery", "High-Density Vibrating Deep Muscle Roller", 75.0, 4.81, "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=600")
    ]

    for p_id, s_id, cat_id, sub_id, title, price, rating, img in new_product_templates:
        if db.products.find_one({"product_id": p_id}) or db.products.find_one({"_id": p_id}):
            continue
        prod_doc = {
            "_id": p_id,
            "product_id": p_id,
            "seller_id": s_id,
            "category_id": cat_id,
            "category": cat_id.replace("cat_", "").replace("_", " ").title(),
            "subcategory_id": sub_id,
            "title": title,
            "description": f"Premium {title} crafted with industry-leading materials for discerning enthusiasts.",
            "price": price,
            "rating": rating,
            "image_url": img,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        db.products.insert_one(prod_doc)

    # 150 Additional Social Posts
    post_captions_pool = [
        # Fashion
        ("Streetwear styling formula: boxy drop hoodie with straight selvedge denim. Clean everyday silhouette #ootd #menswear", "cat_fashion", "seller_aurora", "prod_hoodie_01", "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600"),
        ("Why cashmere coats are worth every penny: 3 season staple you will keep for decades #quietluxury #fashiontips", "cat_fashion", "seller_luxeleather", "prod_lux_coat", "https://images.unsplash.com/photo-1539533018447-63fcce667883?w=600"),
        ("Sneaker rotation for fall: retro suede trainers paired with relaxed wool trousers #sneakerhead #streetstyle", "cat_fashion", "seller_aerokinetix", "prod_retro_sneaker", "https://images.unsplash.com/photo-1552346154-21d32810aba3?w=600"),
        ("How to style a mulberry silk scarf 4 different ways for effortless European elegance #stylinghacks", "cat_fashion", "seller_luxeleather", "prod_silk_scarf", "https://images.unsplash.com/photo-1601924994987-69e26d50dc26?w=600"),
        ("The anatomy of selvedge denim: why rigid cotton looks 10x better as it ages naturally #rawdenim", "cat_fashion", "seller_aurora", "prod_denim_01", "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=600"),
        ("Minimalist EDC bag check: full-grain sling pack holding daily essentials #everydaycarry #edcgear", "cat_fashion", "seller_luxeleather", "prod_sling_01", "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600"),
        ("Automatic mechanical watches under $400: sapphire field watch on wrist check #watchcollector #horology", "cat_fashion", "seller_nordictime", "prod_watch_01", "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=600"),
        ("Layering guide: oversized vintage denim overshirt over heavyweight combed tee #fallfashion #outfitgrid", "cat_fashion", "seller_aurora", "prod_denim_overshirt", "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=600"),
        
        # Tech
        ("Desk setup transformation 2026: wireless aluminum macro pad and clean cable management #workspace #desksetup", "cat_tech", "seller_cyberkeys", "prod_mechanical_numpad", "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600"),
        ("Why audiophiles choose planar magnetic drivers: instrument separation and crystal micro-details #audiophile #headphones", "cat_tech", "seller_soundwave", "prod_planar_iem", "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600"),
        ("Compact travel charger that replaces 4 bricks: 140W GaN charging laptop, phone, and watch together #techgear", "cat_tech", "seller_techpulse", "prod_charger_01", "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=600"),
        ("Sound test: lubed linear switches on gasket-mounted CNC aluminum keyboard #mechanicalkeyboards #asmrsounds", "cat_tech", "seller_cyberkeys", "prod_keyboard_01", "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600"),
        ("Dual monitor lightbar review: eliminating eye fatigue after 8-hour engineering sessions #programmerslife #setup", "cat_tech", "seller_techpulse", "prod_desk_lightbar", "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=600"),
        ("Hi-Fi DAC audio review: unlocking lossless 24-bit studio master audio from your smartphone #musicproducer", "cat_tech", "seller_soundwave", "prod_dac_01", "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=600"),
        ("Smart ring vs smartwatch sleep tracking: 30-day deep REM sleep and HRV comparison #biohacking #sleeptech", "cat_tech", "seller_techpulse", "prod_smartring_01", "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=600"),

        # Beauty
        ("Glass skin routine with copper peptides: how to repair your skin barrier overnight #skincareroutine #kbeauty", "cat_beauty", "seller_glowcraft", "prod_glow_mask", "https://images.unsplash.com/photo-1567928815116-f6d3ad668819?w=600"),
        ("Weightless sunscreen test: zero white cast, dewy hydration under camera studio lighting #spf #cleanskincare", "cat_beauty", "seller_glowcraft", "prod_sun_serum", "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=600"),
        ("Retinol alternative for sensitive skin: 2% bakuchiol night oil results after 4 weeks #cleanbeauty #antiaging", "cat_beauty", "seller_pureveda", "prod_bakuchiol_oil", "https://images.unsplash.com/photo-1617897903246-719242758050?w=600"),
        ("Peptide lip butter swatch: non-sticky glaze with 12-hour deep nourishment #lipcare #lipcombo", "cat_beauty", "seller_velvetbloom", "prod_lip_butter", "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=600"),
        ("5-minute morning makeup: cream bronzer melted with fingers for instant golden hour warmth #makeuproutine", "cat_beauty", "seller_velvetbloom", "prod_cream_bronzer", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=600"),
        ("Organic facial oil ritual: lymphatic drainage massage using cold-pressed rosehip seed oil #wellness #facialmassage", "cat_beauty", "seller_pureveda", "prod_peptide_mist", "https://images.unsplash.com/photo-1608248597359-597561f38e65?w=600"),

        # Home & Kitchen
        ("The perfect morning pour-over: 1:16 ratio with Ethiopian light roast on origami ceramic dripper #pourover #coffee", "cat_home", "seller_zenbrew", "prod_ceramic_pour", "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=600"),
        ("Dialing in espresso: precision scale flow rate profile for rich crema #espressomachine #specialtycoffee", "cat_home", "seller_zenbrew", "prod_espresso_scale", "https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?w=600"),
        ("Warm minimalist living room styling: waffle cotton throw and textured ceramic accents #interiordesign #homedecor", "cat_home", "seller_urbannest", "prod_waffle_throw", "https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?w=600"),
        ("Evening mood lighting ritual: amber glass soy candle + cordless orb lamp for winding down #eveningroutine #cozyvibes", "cat_home", "seller_urbannest", "prod_ambient_orb", "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=600"),
        ("Ceramic donut vase styling with dried pampas grass on Nordic floating oak shelf #aestheticdecor #sanctuary", "cat_home", "seller_urbannest", "prod_ceramic_vase", "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=600"),

        # Fitness & Recovery
        ("Steel mace rotational training: 3 exercises to build bulletproof shoulders and oblique core power #functionalfitness", "cat_fitness", "seller_fitforge", "prod_steel_mace", "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=600"),
        ("Gymnastic rings workout: why ring dips and muscle-ups build greater tendon stability than barbells #calisthenics", "cat_fitness", "seller_fitforge", "prod_olympic_rings", "https://images.unsplash.com/photo-1599058917212-d750089bc07e?w=600"),
        ("Tactical weighted vest training: 5-mile brisk ruck for zone 2 aerobic conditioning #rucking #endurance", "cat_fitness", "seller_fitforge", "prod_weighted_vest", "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=600"),
        ("Cold plunge protocols: 3 minutes at 48 degrees for nervous system reset and norepinephrine release #icebath #recovery", "cat_fitness", "seller_kineticpulse", "prod_cold_plunge", "https://images.unsplash.com/photo-1540555700478-4be289fbecef?w=600"),
        ("Deep tissue vibrating foam roller: relieving quad tightness and lower back tension post heavy squats #mobility", "cat_fitness", "seller_kineticpulse", "prod_foam_roller", "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=600"),
        ("Seamless compression test: squat proof, zero waistband roll, and 4-way breathable stretch #activewear #gymfit", "cat_fitness", "seller_aeroflex", "prod_seamless_bra", "https://images.unsplash.com/photo-1506152983158-b4a74a01c721?w=600")
    ]

    base_count = db.posts.count_documents({})
    now = datetime.now(timezone.utc)
    new_posts = []
    new_embeddings = []
    new_metrics = []

    # Generate 150 additional posts by combining templates with variations
    for i in range(150):
        tmpl_idx = i % len(post_captions_pool)
        caption_base, cat_id, seller_id, prod_id, img_url = post_captions_pool[tmpl_idx]
        
        post_id = f"post_exp_{base_count + i + 1:04d}"
        days_ago = random.uniform(0.1, 14.0)
        post_time = (now - timedelta(days=days_ago)).isoformat()
        
        caption = f"{caption_base} (Drop #{i + 1})" if (i >= len(post_captions_pool)) else caption_base
        
        # Post document
        post_doc = {
            "_id": post_id,
            "post_id": post_id,
            "seller_id": seller_id,
            "author_id": seller_id,
            "category_id": cat_id,
            "category": cat_id.replace("cat_", "").replace("_", " ").title(),
            "pinned_product_id": prod_id,
            "product_id": prod_id,
            "caption": caption,
            "media_url": img_url,
            "image_url": img_url,
            "media_type": "video",
            "status": "published",
            "is_active": True,
            "created_at": post_time
        }
        new_posts.append(post_doc)

        # 64-dim embedding
        emb_doc = {
            "_id": f"emb_{post_id}",
            "post_id": post_id,
            "embedding": generate_cluster_embedding(EMBEDDING_DIM),
            "generated_at": post_time
        }
        new_embeddings.append(emb_doc)

        # Post Metrics
        views = random.randint(150, 4800)
        likes = int(views * random.uniform(0.06, 0.22))
        comments = int(likes * random.uniform(0.05, 0.18))
        shares = int(likes * random.uniform(0.04, 0.15))
        metric_doc = {
            "_id": f"metric_{post_id}",
            "post_id": post_id,
            "views": views,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "watch_time_total_sec": views * random.randint(18, 55),
            "avg_completion_rate": round(random.uniform(0.55, 0.94), 2),
            "updated_at": now.isoformat()
        }
        new_metrics.append(metric_doc)

    db.posts.insert_many(new_posts)
    db.postembeddings.insert_many(new_embeddings)
    db.postmetrics.insert_many(new_metrics)

    # Persist in local_db.json
    if hasattr(db, "save_to_disk"):
        db.save_to_disk()

    print(f"Catalog expanded! Now has {db.posts.count_documents({})} posts and {db.products.count_documents({})} products.")

if __name__ == "__main__":
    expand_catalog()
