from decimal import Decimal

from django.core.management.base import BaseCommand

from beyond_trend.loyalty.models import LoyaltySettings


class Command(BaseCommand):
    help = "Seed or update the singleton LoyaltySettings row."

    def add_arguments(self, parser):
        parser.add_argument(
            "--points-per-100-npr",
            type=int,
            default=1,
            help="Points earned per NPR 100 spent (default: 1).",
        )
        parser.add_argument(
            "--point-value-npr",
            type=Decimal,
            default=Decimal("100.00"),
            help="NPR value of 1 loyalty point when redeemed (default: 100).",
        )

    def handle(self, *args, **options):
        points_per_100_npr = options["points_per_100_npr"]
        point_value_npr = options["point_value_npr"]

        settings_obj = LoyaltySettings.objects.first()
        if settings_obj is None:
            settings_obj = LoyaltySettings.objects.create(
                points_per_100_npr=points_per_100_npr,
                point_value_npr=point_value_npr,
            )
            action = "Created"
        else:
            settings_obj.points_per_100_npr = points_per_100_npr
            settings_obj.point_value_npr = point_value_npr
            settings_obj.save(update_fields=["points_per_100_npr", "point_value_npr"])
            action = "Updated"

        self.stdout.write(
            self.style.SUCCESS(
                f"{action} LoyaltySettings: {points_per_100_npr} point(s) per NPR 100, "
                f"NPR {point_value_npr} per point."
            )
        )
