import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0003_product_size_to_array"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="product",
                    name="color",
                    field=django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=50),
                        blank=True,
                        default=list,
                        size=None,
                        verbose_name="Color",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        'ALTER TABLE "inventory_product" '
                        'ALTER COLUMN "color" DROP DEFAULT, '
                        'ALTER COLUMN "color" TYPE varchar(50)[] '
                        "USING CASE "
                        "WHEN \"color\" IS NULL OR \"color\" = '' THEN ARRAY[]::varchar(50)[] "
                        'ELSE ARRAY["color"]::varchar(50)[] '
                        "END, "
                        'ALTER COLUMN "color" SET DEFAULT \'{}\'::varchar(50)[];'
                    ),
                    reverse_sql=(
                        'ALTER TABLE "inventory_product" '
                        'ALTER COLUMN "color" DROP DEFAULT, '
                        'ALTER COLUMN "color" TYPE varchar(50) '
                        "USING COALESCE(array_to_string(\"color\", ','), '');"
                    ),
                ),
            ],
        ),
    ]
