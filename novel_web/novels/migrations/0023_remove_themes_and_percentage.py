# Generated manually to remove themes and percentage fields

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('novels', '0022_remove_premise'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='plot',
            name='themes',
        ),
        migrations.RemoveField(
            model_name='act',
            name='percentage',
        ),
    ]