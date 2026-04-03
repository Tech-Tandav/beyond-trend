from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "beyond_trend.inventory"
    verbose_name = "Inventory"
    
    def ready(self):
        # Import signal handlers to ensure they're registered
        import beyond_trend.inventory.signals  # noqa: F401 
