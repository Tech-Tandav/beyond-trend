from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="orderitem",
            old_name="variant",
            new_name="product",
        ),
    ]
