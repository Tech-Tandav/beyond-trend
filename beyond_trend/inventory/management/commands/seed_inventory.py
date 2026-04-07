import os

from django.core.management.base import BaseCommand
from django.db import transaction

from beyond_trend.inventory.models import Brand, Product, Stock, Vendor


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
        ):
            self.stdout.write("Inventory tables not empty; skipping seed.")
            return

        with transaction.atomic():
            self._seed()

        self.stdout.write(self.style.SUCCESS("Inventory seed data created."))

    def _seed(self):
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
        ]

        brand_names = ["Nike", "Adidas", "Puma", "New Balance", "Asics"]
        brands = {name: Brand.objects.create(name=name) for name in brand_names}

        catalog = [
            ("Nike", "Air Max 90", "Black", "42", 12, "1500.00"),
            ("Nike", "Air Max 90", "White", "43", 8, "1500.00"),
            ("Nike", "Pegasus 40", "Blue", "41", 5, "1800.00"),
            ("Adidas", "Ultraboost 22", "Grey", "42", 10, "2200.00"),
            ("Adidas", "Samba OG", "White", "44", 0, "1700.00"),
            ("Puma", "Suede Classic", "Red", "40", 3, "1200.00"),
            ("Puma", "RS-X", "Black", "43", 7, "1600.00"),
            ("New Balance", "574", "Navy", "42", 15, "1400.00"),
            ("New Balance", "990v5", "Grey", "44", 2, "2500.00"),
            ("Asics", "Gel-Kayano 30", "Blue", "41", 6, "2100.00"),
        ]

        for idx, (brand_name, model, color, size, qty, price) in enumerate(catalog):
            product = Product.objects.create(
                brand=brands[brand_name],
                vendor=vendors[idx % len(vendors)],
                model=model,
                description=f"{brand_name} {model} in {color}, size {size}.",
                size=size,
                color=color,
                selling_price=price,
                low_stock_threshold=5,
                is_published=True,
            )
            Stock.objects.create(product=product, quantity=qty)
