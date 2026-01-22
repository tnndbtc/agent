# Generated migration to remove premise field from Plot model
# This completes the two-phase migration strategy:
# - 0021: Made premise nullable (safe rollback)
# - 0022: Remove premise field entirely (this migration)

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('novels', '0021_make_premise_nullable'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='plot',
            name='premise',
        ),
    ]
