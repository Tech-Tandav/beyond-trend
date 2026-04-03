from django.db.models.signals import post_save
from django.dispatch import receiver
from beyond_trend.inventory.models import  ShoeProduct


@receiver(post_save, sender=ShoeProduct)
def shoe_product(sender, instance, created, **kwargs):
    if instance.quantity == 0:
        instance.delete()