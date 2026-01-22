# Generated migration for making premise field nullable
# This is Phase 1 of removing premise field entirely

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('novels', '0020_remove_genre'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plot',
            name='premise',
            field=models.TextField(
                blank=True,
                null=True,
                help_text="One-paragraph premise (deprecated, will be removed)"
            ),
        ),
    ]
