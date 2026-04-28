import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0002_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="product",
                    name="size",
                    field=django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=20),
                        blank=True,
                        default=list,
                        size=None,
                        verbose_name="Size",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        'ALTER TABLE "inventory_product" '
                        'ALTER COLUMN "size" DROP DEFAULT, '
                        'ALTER COLUMN "size" TYPE varchar(20)[] '
                        "USING CASE "
                        "WHEN \"size\" IS NULL OR \"size\" = '' THEN ARRAY[]::varchar(20)[] "
                        'ELSE ARRAY["size"]::varchar(20)[] '
                        "END, "
                        'ALTER COLUMN "size" SET DEFAULT \'{}\'::varchar(20)[];'
                    ),
                    reverse_sql=(
                        'ALTER TABLE "inventory_product" '
                        'ALTER COLUMN "size" DROP DEFAULT, '
                        'ALTER COLUMN "size" TYPE varchar(20) '
                        "USING COALESCE(array_to_string(\"size\", ','), '');"
                    ),
                ),
            ],
        ),
    ]
