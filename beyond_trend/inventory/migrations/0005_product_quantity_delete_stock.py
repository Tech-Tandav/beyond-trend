from django.db import migrations, models


def copy_stock_to_product(apps, schema_editor):
    Stock = apps.get_model("inventory", "Stock")
    for stock in Stock.objects.all().iterator():
        Product = stock.product.__class__
        Product.objects.filter(pk=stock.product_id).update(quantity=stock.quantity)


def noop_reverse(apps, schema_editor):
    # Stock model is gone after this migration; nothing to restore.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0004_rename_variant_inventorylog_product"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="quantity",
            field=models.PositiveIntegerField(default=0, verbose_name="Quantity"),
        ),
        migrations.RunPython(copy_stock_to_product, noop_reverse),
        migrations.DeleteModel(
            name="Stock",
        ),
    ]
