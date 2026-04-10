import io
import os

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, ImageDraw, ImageFont

from beyond_trend.inventory.models import Brand, Category, Product, ProductImage, SubCategory, Vendor


# ── Colour name → RGB mapping for placeholder images ────────────
_COLOR_MAP = {
    "black": (30, 30, 30),
    "white": (240, 240, 240),
    "grey": (160, 160, 160),
    "navy": (30, 40, 80),
    "blue": (50, 100, 200),
    "red": (200, 50, 50),
    "green": (50, 150, 70),
    "olive": (107, 142, 35),
    "beige": (210, 190, 160),
    "cream": (255, 253, 230),
    "indigo": (60, 50, 120),
    "brown": (120, 80, 50),
}


def _generate_placeholder(brand: str, model: str, color: str, label: str) -> ContentFile:
    """Create a 400×400 placeholder image with the product colour as background."""
    bg = _COLOR_MAP.get(color.lower(), (180, 180, 180))
    # pick contrasting text colour
    luminance = 0.299 * bg[0] + 0.587 * bg[1] + 0.114 * bg[2]
    fg = (255, 255, 255) if luminance < 140 else (0, 0, 0)

    img = Image.new("RGB", (400, 400), bg)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
        font_sm = font

    draw.text((200, 160), brand, fill=fg, anchor="mm", font=font)
    draw.text((200, 195), model, fill=fg, anchor="mm", font=font_sm)
    draw.text((200, 230), label, fill=fg, anchor="mm", font=font_sm)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    filename = f"{brand}_{model}_{label}.jpg".lower().replace(" ", "_").replace("'", "")
    return ContentFile(buf.getvalue(), name=filename)


def _is_truthy(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class Command(BaseCommand):
    help = (
        "Seed the inventory database with sample data. "
        "Only runs when the SEED environment variable is truthy and the "
        "inventory tables are empty. Pass --force to bypass the empty check."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Seed even if SEED env var is not set or tables are not empty.",
        )

    def handle(self, *args, **options):
        force = options["force"]

        if not force and not _is_truthy(os.environ.get("SEED")):
            self.stdout.write("SEED env var not truthy; skipping seed.")
            return

        if not force and (
            Vendor.objects.exists()
            or Brand.objects.exists()
            or Product.objects.exists()
            or Category.objects.exists()
        ):
            self.stdout.write("Inventory tables not empty; skipping seed.")
            return

        with transaction.atomic():
            self._seed()

        self.stdout.write(self.style.SUCCESS("Inventory seed data created."))

    def _seed(self):
        # ── Vendors ──────────────────────────────────────────────
        vendors = [
            Vendor.objects.create(
                name="Kathmandu Footwear Imports",
                contact_info="sales@ktmfootwear.example",
                pan_number="123456789",
                vat_number="987654321",
            ),
            Vendor.objects.create(
                name="Himalayan Sports Distributors",
                contact_info="contact@himalayansports.example",
                pan_number="234567890",
                vat_number="876543210",
            ),
            Vendor.objects.create(
                name="Nepal Fashion House",
                contact_info="info@nepalfashion.example",
                pan_number="345678901",
                vat_number="765432109",
            ),
        ]

        # ── Brands ───────────────────────────────────────────────
        brand_names = [
            "Nike", "Adidas", "Puma", "New Balance", "Asics",
            "Levi's", "H&M", "Zara", "Uniqlo", "The North Face",
        ]
        brands = {name: Brand.objects.create(name=name) for name in brand_names}

        # ── Categories & SubCategories ───────────────────────────
        category_tree = {
            "Footwear": {
                "description": "All types of footwear including shoes, sandals, and boots",
                "subcategories": [
                    ("Sneakers", "Casual and athletic sneakers"),
                    ("Running Shoes", "Performance running footwear"),
                    ("Formal Shoes", "Dress shoes and oxfords"),
                    ("Sandals", "Open-toe sandals and slides"),
                    ("Boots", "Ankle boots, hiking boots, and winter boots"),
                ],
            },
            "Apparels": {
                "description": "Clothing and garments for men and women",
                "subcategories": [
                    ("T-Shirts", "Casual and graphic tees"),
                    ("Jackets", "Outerwear jackets and hoodies"),
                    ("Pants", "Jeans, trousers, and joggers"),
                    ("Shorts", "Casual and athletic shorts"),
                    ("Dresses", "Casual and formal dresses"),
                ],
            },
            "Accessories": {
                "description": "Bags, hats, socks, and other accessories",
                "subcategories": [
                    ("Bags", "Backpacks, duffels, and tote bags"),
                    ("Hats", "Caps, beanies, and sun hats"),
                    ("Socks", "Athletic and casual socks"),
                    ("Belts", "Leather and casual belts"),
                ],
            },
        }

        categories = {}
        subcategories = {}

        for cat_name, cat_info in category_tree.items():
            cat = Category.objects.create(
                name=cat_name,
                description=cat_info["description"],
            )
            categories[cat_name] = cat
            for sub_name, sub_desc in cat_info["subcategories"]:
                sub = SubCategory.objects.create(
                    category=cat,
                    name=sub_name,
                    description=sub_desc,
                )
                subcategories[sub_name] = sub

        # ── Products ─────────────────────────────────────────────
        # (brand, model, color, size, qty, selling_price, cost_price, category, subcategory)
        catalog = [
            # --- Footwear: Sneakers ---
            ("Nike", "Air Max 90", "Black", "42", 12, "8500.00", "6000.00", "Footwear", "Sneakers"),
            ("Nike", "Air Max 90", "White", "43", 8, "8500.00", "6000.00", "Footwear", "Sneakers"),
            ("Adidas", "Samba OG", "White", "44", 0, "7500.00", "5200.00", "Footwear", "Sneakers"),
            ("Puma", "Suede Classic", "Red", "40", 3, "5500.00", "3800.00", "Footwear", "Sneakers"),
            ("Puma", "RS-X", "Black", "43", 7, "7200.00", "5000.00", "Footwear", "Sneakers"),
            ("New Balance", "574", "Navy", "42", 15, "6800.00", "4700.00", "Footwear", "Sneakers"),
            # --- Footwear: Running Shoes ---
            ("Nike", "Pegasus 40", "Blue", "41", 5, "9500.00", "6800.00", "Footwear", "Running Shoes"),
            ("Adidas", "Ultraboost 22", "Grey", "42", 10, "11000.00", "7800.00", "Footwear", "Running Shoes"),
            ("Asics", "Gel-Kayano 30", "Blue", "41", 6, "10500.00", "7500.00", "Footwear", "Running Shoes"),
            ("New Balance", "990v5", "Grey", "44", 2, "12500.00", "9000.00", "Footwear", "Running Shoes"),
            # --- Footwear: Boots ---
            ("The North Face", "Vectiv Fastpack", "Brown", "43", 4, "14000.00", "10000.00", "Footwear", "Boots"),
            ("Nike", "Air Force 1 Boot", "Black", "42", 6, "9800.00", "7000.00", "Footwear", "Boots"),
            # --- Footwear: Sandals ---
            ("Adidas", "Adilette Comfort", "Black", "41", 20, "2800.00", "1800.00", "Footwear", "Sandals"),
            ("Nike", "Victori One Slide", "White", "42", 18, "2500.00", "1600.00", "Footwear", "Sandals"),
            # --- Apparels: T-Shirts ---
            ("Nike", "Dri-FIT Training Tee", "White", "M", 25, "2500.00", "1500.00", "Apparels", "T-Shirts"),
            ("Nike", "Sportswear Essential Crop Top", "Black", "S", 18, "2800.00", "1600.00", "Apparels", "T-Shirts"),
            ("Adidas", "Essentials 3-Stripes Tee", "Black", "L", 20, "2200.00", "1300.00", "Apparels", "T-Shirts"),
            ("Adidas", "Originals Trefoil Tee", "White", "M", 22, "2400.00", "1400.00", "Apparels", "T-Shirts"),
            ("Uniqlo", "Supima Cotton Crew Neck", "Navy", "M", 30, "1500.00", "800.00", "Apparels", "T-Shirts"),
            ("H&M", "Oversized Graphic Print Tee", "Grey", "S", 35, "900.00", "450.00", "Apparels", "T-Shirts"),
            ("Zara", "Relaxed Fit V-Neck Tee", "Olive", "L", 28, "1200.00", "600.00", "Apparels", "T-Shirts"),
            # --- Apparels: Jackets ---
            ("The North Face", "Thermoball Eco Jacket", "Black", "L", 5, "18000.00", "12500.00", "Apparels", "Jackets"),
            ("The North Face", "Nuptse Puffer Jacket", "Red", "M", 4, "22000.00", "15000.00", "Apparels", "Jackets"),
            ("Nike", "Windrunner Jacket", "Blue", "M", 8, "8500.00", "5800.00", "Apparels", "Jackets"),
            ("Adidas", "Essentials Down Jacket", "Green", "XL", 3, "12000.00", "8500.00", "Apparels", "Jackets"),
            ("Zara", "Faux Leather Biker Jacket", "Black", "M", 6, "7500.00", "4200.00", "Apparels", "Jackets"),
            ("H&M", "Denim Trucker Jacket", "Blue", "L", 10, "4500.00", "2500.00", "Apparels", "Jackets"),
            ("Levi's", "Sherpa Trucker Jacket", "Indigo", "M", 7, "9500.00", "6500.00", "Apparels", "Jackets"),
            # --- Apparels: Pants ---
            ("Levi's", "501 Original Fit Jeans", "Indigo", "32", 15, "6500.00", "4000.00", "Apparels", "Pants"),
            ("Levi's", "511 Slim Fit Jeans", "Black", "30", 12, "6000.00", "3800.00", "Apparels", "Pants"),
            ("Nike", "Tech Fleece Joggers", "Grey", "M", 12, "7200.00", "4800.00", "Apparels", "Pants"),
            ("Adidas", "Tiro 23 Track Pants", "Black", "L", 18, "4500.00", "2800.00", "Apparels", "Pants"),
            ("Uniqlo", "Smart Ankle Pants", "Beige", "30", 22, "3200.00", "1800.00", "Apparels", "Pants"),
            ("Zara", "Wide Leg Palazzo Pants", "Cream", "28", 14, "3800.00", "2200.00", "Apparels", "Pants"),
            ("H&M", "Cargo Jogger Pants", "Olive", "M", 16, "2800.00", "1500.00", "Apparels", "Pants"),
            # --- Apparels: Shorts ---
            ("Nike", "Dri-FIT Challenger Shorts", "Black", "M", 14, "3200.00", "2000.00", "Apparels", "Shorts"),
            ("Adidas", "Aeroready 3-Stripes Shorts", "Navy", "L", 10, "2800.00", "1700.00", "Apparels", "Shorts"),
            ("Puma", "Essentials Sweat Shorts", "Grey", "M", 12, "2400.00", "1400.00", "Apparels", "Shorts"),
            ("Uniqlo", "Chino Shorts", "Beige", "32", 20, "1800.00", "900.00", "Apparels", "Shorts"),
            # --- Apparels: Dresses ---
            ("Zara", "Satin Midi Slip Dress", "Black", "S", 8, "5500.00", "3200.00", "Apparels", "Dresses"),
            ("H&M", "Floral Wrap Dress", "Red", "M", 10, "3200.00", "1800.00", "Apparels", "Dresses"),
            ("Zara", "Ribbed Knit Bodycon Dress", "Cream", "S", 6, "4200.00", "2500.00", "Apparels", "Dresses"),
            # --- Accessories: Bags ---
            ("Nike", "Brasilia Backpack", "Black", "One Size", 10, "4500.00", "2800.00", "Accessories", "Bags"),
            ("The North Face", "Borealis Backpack", "Navy", "One Size", 7, "8500.00", "5800.00", "Accessories", "Bags"),
            ("Adidas", "Defender Duffel", "Grey", "One Size", 5, "3800.00", "2200.00", "Accessories", "Bags"),
            # --- Accessories: Hats ---
            ("Nike", "Club Cap", "White", "One Size", 30, "1800.00", "900.00", "Accessories", "Hats"),
            ("Adidas", "Originals Trefoil Beanie", "Black", "One Size", 25, "1500.00", "750.00", "Accessories", "Hats"),
            # --- Accessories: Socks ---
            ("Nike", "Everyday Cushioned Crew Socks", "White", "M", 50, "800.00", "350.00", "Accessories", "Socks"),
            ("Adidas", "Cushioned Athletic Socks", "Black", "L", 40, "700.00", "300.00", "Accessories", "Socks"),
        ]

        products = []
        for idx, (
            brand_name, model, color, size, qty,
            selling_price, cost_price, cat_name, subcat_name,
        ) in enumerate(catalog):
            product = Product.objects.create(
                brand=brands[brand_name],
                vendor=vendors[idx % len(vendors)],
                category=categories[cat_name],
                subcategory=subcategories[subcat_name],
                model=model,
                description=f"{brand_name} {model} in {color}, size {size}.",
                size=size,
                color=color,
                cost_price=cost_price,
                selling_price=selling_price,
                quantity=qty,
                low_stock_threshold=5,
                is_published=True,
            )
            products.append(product)

        # ── Product Images (generated placeholders) ────────────
        for product in products:
            brand_name = product.brand.name
            front = _generate_placeholder(brand_name, product.model, product.color, "front")
            img = ProductImage(product=product, is_primary=True, order=0)
            img.image.save(front.name, front, save=True)

            back = _generate_placeholder(brand_name, product.model, product.color, "back")
            img2 = ProductImage(product=product, is_primary=False, order=1)
            img2.image.save(back.name, back, save=True)
