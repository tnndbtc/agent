# Generated migration to add generation metadata to ContentPiece

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('novels', '0047_populate_model_names_and_duplicate'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentpiece',
            name='ai_model',
            field=models.CharField(
                blank=True,
                null=True,
                max_length=50,
                help_text="AI model used to generate this content (e.g., 'gpt-4o-mini', 'gpt-5.2')"
            ),
        ),
        migrations.AddField(
            model_name='contentpiece',
            name='writing_style',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='content_pieces',
                to='novels.writingstyle',
                help_text="System-level writing style used (if applicable)"
            ),
        ),
        migrations.AddField(
            model_name='contentpiece',
            name='custom_writing_style',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='content_pieces',
                to='novels.customwritingstyle',
                help_text="Custom writing style used (if applicable)"
            ),
        ),
    ]
