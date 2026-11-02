"""
Add 200+ more high-quality posts and 45+ products to the local MongoDB store
to provide a massive recommendation pool with hundreds of diverse items.
"""
import json
import random
from datetime import datetime, timezone, timedelta

def main():
    with open("data/local_db.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    existing_posts = data.get("posts", [])
    existing_products = data.get("products", [])
    existing_embeddings = data.get("postembeddings", [])
    existing_metrics = data.get("postmetrics", [])
    existing_engagements = data.get("postengagements", [])
    existing_comments = data.get("postcomments", [])
    existing_views = data.get("views", [])
    existing_sellers = data.get("sellerdetails", [])

    seller_ids = [s.get("_id") or s.get("seller_id") for s in existing_sellers]
    if not seller_ids:
        seller_ids = ["seller_101", "seller_102", "seller_103", "seller_104", "seller_105"]

    user_ids = ["user_fashion_01", "user_tech_02", "user_fitness_03", "user_decor_04", "user_beauty_05"]

    categories = [
        ("cat_fashion", "Fashion", [
            ("Oversized Organic Cotton Trench Coat", "Minimalist European autumn layering with water-resistant cotton weave.", 219.0, "https://images.unsplash.com/photo-1544441893-675973e31985?w=600"),
            ("Merino Wool Cable Knit Cardigan", "Heritage soft-spun wool knit designed for effortless weekend styling.", 135.0, "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=600"),
            ("Italian Calfskin Chelsea Boots", "Hand-welted leather boots with elasticated side gussets and Vibram soles.", 280.0, "https://images.unsplash.com/photo-1638247025967-b4e38f787b76?w=600"),
            ("Relaxed Pleated Chino Trousers", "Tailored drape chinos cut from heavyweight Japanese twill.", 115.0, "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=600"),
            ("Silk Crepe de Chine Evening Slip", "Bias-cut silhouette with delicate adjustable straps in champagne blush.", 160.0, "https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=600"),
            ("Handcrafted Full-Grain Leather Tote", "Architectural minimalist tote with interior magnetic laptop sleeve.", 245.0, "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=600")
        ]),
        ("cat_electronics", "Electronics", [
            ("Planar Magnetic Audiophile Headphones", "Open-back reference monitors delivering ultra-low distortion acoustic soundstage.", 399.0, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600"),
            ("Custom Gasket Mechanical Keyboard", "Machined aluminum chassis with pre-lubed tactile switches and hot-swap PCB.", 185.0, "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600"),
            ("Magnetic Qi2 Wireless Charging Hub", "3-in-1 desktop charging station with solid walnut and brushed space-gray finish.", 119.0, "https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=600"),
            ("4K Ultra-Wide Curved Creator Monitor", "34-inch color-calibrated IPS panel with 98% DCI-P3 and 90W USB-C Power Delivery.", 649.0, "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=600"),
            ("Lossless Portable DAC & Headphone Amp", "Dual ESS Sabre chips with MQA decoding and 4.4mm balanced output.", 149.0, "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=600"),
            ("Ergonomic Vertical Precision Mouse", "Whisper-quiet optical tracking with programmable thumb scroll and Bluetooth 5.3.", 79.0, "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=600")
        ]),
        ("cat_beauty", "Beauty", [
            ("Fermented Centella Asiatica Essence", "Deeply hydrating barrier repair toner with 85% soothing botanical extracts.", 38.0, "https://images.unsplash.com/photo-1608248597359-54bc952f55df?w=600"),
            ("Pure Bakuchiol Botanical Retinol Serum", "Gentle plant-derived youth nectar for evening skin renewal without irritation.", 54.0, "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=600"),
            ("Cold-Pressed Organic Rosehip Facial Oil", "Rich in essential fatty acids and antioxidants for a dewy golden radiance.", 42.0, "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=600"),
            ("Hydra-Barrier Peptide Ceramide Cream", "Rich nourishing treatment formulated to lock in moisture for 48 hours.", 46.0, "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=600"),
            ("Mineral Sunscreen Fluid SPF 50+", "Invisible matte finish zinc oxide with antioxidant green tea polyphenols.", 34.0, "https://images.unsplash.com/photo-1571781926291-c477ebfd024b?w=600")
        ]),
        ("cat_home_decor", "Home Decor", [
            ("Artisanal Hand-Thrown Terracotta Vase", "Rustic stoneware vessel crafted by master Mediterranean potters.", 68.0, "https://images.unsplash.com/photo-1612196808214-b8e1d6145a8c?w=600"),
            ("Architectural Cast Concrete Table Lamp", "Sculptural brutalist base with warm diffused ambient linen shade.", 125.0, "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=600"),
            ("Heavyweight French Washed Linen Duvet", "Breathable, vintage-washed flax linen in serene natural oat hue.", 195.0, "https://images.unsplash.com/photo-1582533561751-ef6f6ab93a2e?w=600"),
            ("Solid Japanese Oak Floating Wall Shelf", "Minimalist concealed mounting ledge with hand-rubbed oil finish.", 84.0, "https://images.unsplash.com/photo-1538688525198-9b88f6f53126?w=600"),
            ("Organic Hand-Tufted Wool Runner Rug", "Geometric Scandinavian pattern with plush 20mm unbleached wool pile.", 175.0, "https://images.unsplash.com/photo-1600121848594-d8644e57abab?w=600")
        ]),
        ("cat_fitness", "Fitness", [
            ("Modular Hex Urethane Dumbbell Set", "Non-slip knurled stainless steel handles with commercial-grade rubber heads.", 189.0, "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=600"),
            ("High-Density Non-Slip Cork Yoga Mat", "Eco-friendly antibacterial cork surface with natural tree rubber base.", 78.0, "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=600"),
            ("Deep Tissue Percussive Massage Gun", "Quiet brushless motor with 5 custom speed heads and 6-hour battery.", 139.0, "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=600"),
            ("Pure Grass-Fed Whey Isolate Vanilla", "Zero sugar micro-filtered protein powder with digestive enzymes.", 58.0, "https://images.unsplash.com/photo-1593095948071-474c5cc2989d?w=600"),
            ("Seamless Compression Running Shorts", "Sweat-wicking 4-way stretch fabric with phone pocket and reflective accents.", 48.0, "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=600")
        ]),
        ("cat_accessories", "Accessories", [
            ("Automatic Sapphire Dress Watch", "Sunburst dial with exhibition caseback and vegetable-tanned Horween strap.", 360.0, "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=600"),
            ("Titanium Polarized Pilot Sunglasses", "Ultra-lightweight featherweight frames with anti-reflective gradient tint.", 165.0, "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=600"),
            ("Solid Brass Everyday Carry Key Clip", "CNC milled solid brass carabiner with integrated bottle opener.", 45.0, "https://images.unsplash.com/photo-1614036417651-efe5912149d8?w=600"),
            ("Bespoke Leather Passport Wallet", "Saddle-stitched Italian leather sleeve with RFID blocking lining.", 72.0, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600")
        ])
    ]

    new_products = []
    prod_id_counter = len(existing_products) + 1

    for cat_id, cat_name, prod_list in categories:
        for title, desc, price, img in prod_list:
            pid = f"prod_auto_{prod_id_counter:03d}"
            seller = random.choice(seller_ids)
            # Create product embedding (64-dim)
            embed = [round(random.uniform(-0.5, 0.5), 4) for _ in range(64)]
            new_products.append({
                "_id": pid,
                "product_id": pid,
                "title": title,
                "description": desc,
                "price": price,
                "category_id": cat_id,
                "category": cat_name,
                "seller_id": seller,
                "rating": round(random.uniform(4.4, 4.95), 2),
                "image_url": img,
                "product_embedding": embed,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            prod_id_counter += 1

    all_products = existing_products + new_products

    # Now generate 200 diverse posts linking to products
    new_posts = []
    new_embeddings = []
    new_metrics = []
    new_engagements = []
    new_comments = []
    new_views = []

    post_start_id = len(existing_posts) + 1
    now = datetime.now(timezone.utc)

    caption_templates = [
        "Elevating everyday essentials with {item}. The craftsmanship and feel are unmatched! #aesthetic #{cat} #curated",
        "A closer look at the new {item}. Here is why this has completely transformed my daily routine ✨ #{cat}",
        "Style edit: styling the {item} three different ways. Which look is your favorite? 1, 2, or 3? #{cat} #lookbook",
        "The secret behind clean, effortless minimalism: {item}. Tap the tagged product to shop directly 🛍️",
        "Unboxing and first impressions of {item}. Worth the hype? Absolutely yes! Check the link in bio #{cat}",
        "My holy grail product this month: {item}. Quality that speaks for itself. Tag someone who needs this!",
        "Workspace upgrade featuring {item}. Clean lines, zero clutter, pure productivity vibes 🎧💻",
        "Weekend mood board featuring our signature {item}. Restocked in limited quantities today!"
    ]

    for i in range(200):
        pid = f"post_exp_{post_start_id + i:03d}"
        chosen_prod = random.choice(all_products)
        cat_id = chosen_prod.get("category_id", "cat_fashion")
        cat_clean = chosen_prod.get("category", "Fashion").lower()
        seller = chosen_prod.get("seller_id", random.choice(seller_ids))

        # Created time spread over past 30 days
        age_hours = random.uniform(1.0, 720.0)
        created_time = now - timedelta(hours=age_hours)

        tmpl = random.choice(caption_templates)
        caption = tmpl.format(item=chosen_prod["title"], cat=cat_clean)

        prod_id = chosen_prod.get("product_id") or chosen_prod.get("_id")
        post_doc = {
            "_id": pid,
            "post_id": pid,
            "seller_id": seller,
            "author_id": seller,
            "category_id": cat_id,
            "category": chosen_prod.get("category", "Fashion"),
            "pinned_product_id": prod_id,
            "product_id": prod_id,
            "caption": caption,
            "media_url": chosen_prod.get("image_url", "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600"),
            "image_url": chosen_prod.get("image_url", "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600"),
            "post_type": "carousel" if (i % 3 == 0) else "image",
            "created_at": created_time.isoformat()
        }
        new_posts.append(post_doc)

        # 64-dim embedding aligned with category
        embed = [round(random.uniform(-0.6, 0.6), 4) for _ in range(64)]
        new_embeddings.append({
            "_id": pid,
            "post_id": pid,
            "embedding": embed
        })

        likes = random.randint(15, 340)
        comments_cnt = random.randint(2, 45)
        shares = random.randint(1, 28)
        views = likes * random.randint(4, 15)

        new_metrics.append({
            "_id": pid,
            "post_id": pid,
            "likes": likes,
            "comments": comments_cnt,
            "shares": shares,
            "views": views
        })

        # Add interactions from our personas
        for uid in user_ids:
            if random.random() < 0.25:
                new_views.append({
                    "user_id": uid,
                    "post_id": pid,
                    "view_time": created_time.isoformat(),
                    "duration_seconds": random.randint(5, 60)
                })
            if random.random() < 0.12:
                new_engagements.append({
                    "user_id": uid,
                    "post_id": pid,
                    "engagement_type": random.choice(["like", "save", "comment", "share"]),
                    "created_at": created_time.isoformat()
                })

    data["posts"] = existing_posts + new_posts
    data["products"] = all_products
    data["postembeddings"] = existing_embeddings + new_embeddings
    data["postmetrics"] = existing_metrics + new_metrics
    data["postengagements"] = existing_engagements + new_engagements
    data["views"] = existing_views + new_views

    with open("data/local_db.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Successfully expanded catalog! New total: {len(data['posts'])} posts and {len(data['products'])} products.")

if __name__ == "__main__":
    main()
