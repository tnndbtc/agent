"""Management command to seed ScoreCategory and ScoreCategoryTranslation data."""
from django.core.management.base import BaseCommand
from novels.models import ScoreCategory, ScoreCategoryTranslation


class Command(BaseCommand):
    help = 'Seed ScoreCategory and ScoreCategoryTranslation data with default categories'

    def handle(self, *args, **options):
        """Create default score categories with English and Chinese translations."""

        categories_data = [
            {
                'name_key': 'story_plot',
                'name': 'Story/Plot',
                'default_weight': 30,
                'order': 1,
                'translations': {
                    'en': 'Story/Plot',
                    'zh-hans': '故事/情节'
                }
            },
            {
                'name_key': 'character_development',
                'name': 'Character Development',
                'default_weight': 20,
                'order': 2,
                'translations': {
                    'en': 'Character Development',
                    'zh-hans': '角色发展'
                }
            },
            {
                'name_key': 'world_building',
                'name': 'World-Building / Setting',
                'default_weight': 15,
                'order': 3,
                'translations': {
                    'en': 'World-Building / Setting',
                    'zh-hans': '世界构建/设定'
                }
            },
            {
                'name_key': 'writing_style',
                'name': 'Writing Style / Language',
                'default_weight': 20,
                'order': 4,
                'translations': {
                    'en': 'Writing Style / Language',
                    'zh-hans': '写作风格/语言'
                }
            },
            {
                'name_key': 'dialogue',
                'name': 'Dialogue & Interactions',
                'default_weight': 10,
                'order': 5,
                'translations': {
                    'en': 'Dialogue & Interactions',
                    'zh-hans': '对话与互动'
                }
            },
            {
                'name_key': 'emotional_impact',
                'name': 'Emotional Impact / Engagement',
                'default_weight': 5,
                'order': 6,
                'translations': {
                    'en': 'Emotional Impact / Engagement',
                    'zh-hans': '情感影响/参与度'
                }
            },
        ]

        created_count = 0
        updated_count = 0

        for cat_data in categories_data:
            # Get or create category
            category, created = ScoreCategory.objects.get_or_create(
                name_key=cat_data['name_key'],
                defaults={
                    'name': cat_data['name'],
                    'public': True,
                    'is_system': True,
                    'created_by': None,
                    'default_weight': cat_data['default_weight'],
                    'order': cat_data['order']
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {cat_data["name_key"]}')
                )
            else:
                # Update existing category fields
                category.public = True
                category.is_system = True
                category.default_weight = cat_data['default_weight']
                category.order = cat_data['order']
                category.save()
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {cat_data["name_key"]}')
                )

            # Create or update translations
            for lang_code, translation_text in cat_data['translations'].items():
                translation, trans_created = ScoreCategoryTranslation.objects.update_or_create(
                    category=category,
                    language_code=lang_code,
                    defaults={'name': translation_text}
                )

                if trans_created:
                    self.stdout.write(
                        self.style.SUCCESS(f'  Created translation: {lang_code} = {translation_text}')
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  Updated translation: {lang_code} = {translation_text}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Seeding complete! Created {created_count} score categories with translations.'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Total score categories in database: {ScoreCategory.objects.count()}'
            )
        )
