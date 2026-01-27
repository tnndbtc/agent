# Generated migration for adding order_key to Chapter model

from decimal import Decimal
from django.db import migrations, models


def populate_order_keys(apps, schema_editor):
    """Populate order_key for existing chapters based on current chapter_number."""
    Chapter = apps.get_model('novels', 'Chapter')
    for chapter in Chapter.objects.all():
        chapter.order_key = Decimal(str(chapter.chapter_number))
        chapter.save(update_fields=['order_key'])


class Migration(migrations.Migration):

    dependencies = [
        ("novels", "0024_add_act_to_chapter"),
    ]

    operations = [
        # Add order_key field (nullable first)
        migrations.AddField(
            model_name="chapter",
            name="order_key",
            field=models.DecimalField(
                decimal_places=6,
                default=1,
                help_text="Ordering key for flexible chapter reordering",
                max_digits=10,
            ),
        ),
        # Populate order_key for existing chapters
        migrations.RunPython(populate_order_keys, reverse_code=migrations.RunPython.noop),
        # Update model ordering
        migrations.AlterModelOptions(
            name="chapter",
            options={"ordering": ["order_key"]},
        ),
        # Add index for efficient queries
        migrations.AddIndex(
            model_name="chapter",
            index=models.Index(fields=["project", "order_key"], name="chapter_project_order_idx"),
        ),
    ]
