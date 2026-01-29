"""Management command to seed content type scoring categories and configurations."""
from django.core.management.base import BaseCommand
from novels.models import (
    ScoreCategory,
    ScoreCategoryTranslation,
    ContentTypeScoringConfig,
    ContentTypeCategoryWeight
)


class Command(BaseCommand):
    help = 'Seed content type scoring categories and configurations'

    def handle(self, *args, **options):
        """Create scoring categories for poems, essays, and sketches."""

        # New categories for different content types
        new_categories_data = [
            # Poem categories
            {
                'name_key': 'imagery_sensory',
                'name': 'Imagery & Sensory Details',
                'default_weight': 30,
                'order': 10,
                'translations': {
                    'en': 'Imagery & Sensory Details',
                    'zh-hans': '意象与感官细节'
                }
            },
            {
                'name_key': 'rhythm_musicality',
                'name': 'Rhythm & Musicality',
                'default_weight': 25,
                'order': 11,
                'translations': {
                    'en': 'Rhythm & Musicality',
                    'zh-hans': '韵律与音乐性'
                }
            },
            {
                'name_key': 'form_structure',
                'name': 'Form & Structure',
                'default_weight': 20,
                'order': 12,
                'translations': {
                    'en': 'Form & Structure',
                    'zh-hans': '形式与结构'
                }
            },
            {
                'name_key': 'emotional_impact_poem',
                'name': 'Emotional Impact',
                'default_weight': 25,
                'order': 13,
                'translations': {
                    'en': 'Emotional Impact',
                    'zh-hans': '情感冲击力'
                }
            },
            # Essay categories
            {
                'name_key': 'thesis_clarity',
                'name': 'Thesis Clarity',
                'default_weight': 20,
                'order': 20,
                'translations': {
                    'en': 'Thesis Clarity',
                    'zh-hans': '论点清晰度'
                }
            },
            {
                'name_key': 'argument_strength',
                'name': 'Argument Strength',
                'default_weight': 25,
                'order': 21,
                'translations': {
                    'en': 'Argument Strength',
                    'zh-hans': '论证力度'
                }
            },
            {
                'name_key': 'evidence_quality',
                'name': 'Evidence Quality',
                'default_weight': 20,
                'order': 22,
                'translations': {
                    'en': 'Evidence Quality',
                    'zh-hans': '证据质量'
                }
            },
            {
                'name_key': 'organization_flow',
                'name': 'Organization & Flow',
                'default_weight': 15,
                'order': 23,
                'translations': {
                    'en': 'Organization & Flow',
                    'zh-hans': '组织与流畅性'
                }
            },
            {
                'name_key': 'writing_style_essay',
                'name': 'Writing Style',
                'default_weight': 20,
                'order': 24,
                'translations': {
                    'en': 'Writing Style',
                    'zh-hans': '写作风格'
                }
            },
            # Sketch categories
            {
                'name_key': 'observation_quality',
                'name': 'Observation Quality',
                'default_weight': 30,
                'order': 30,
                'translations': {
                    'en': 'Observation Quality',
                    'zh-hans': '观察质量'
                }
            },
            {
                'name_key': 'imagery_description',
                'name': 'Imagery & Description',
                'default_weight': 25,
                'order': 31,
                'translations': {
                    'en': 'Imagery & Description',
                    'zh-hans': '意象与描述'
                }
            },
            {
                'name_key': 'insight_reflection',
                'name': 'Insight & Reflection',
                'default_weight': 25,
                'order': 32,
                'translations': {
                    'en': 'Insight & Reflection',
                    'zh-hans': '洞察与反思'
                }
            },
            {
                'name_key': 'writing_style_sketch',
                'name': 'Writing Style',
                'default_weight': 20,
                'order': 33,
                'translations': {
                    'en': 'Writing Style',
                    'zh-hans': '写作风格'
                }
            },
        ]

        created_count = 0
        updated_count = 0

        # Create new categories
        self.stdout.write('\n=== Creating Score Categories ===')
        for cat_data in new_categories_data:
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
                    self.style.SUCCESS(f'✓ Created category: {cat_data["name_key"]}')
                )
            else:
                category.public = True
                category.is_system = True
                category.default_weight = cat_data['default_weight']
                category.order = cat_data['order']
                category.save()
                self.stdout.write(
                    self.style.WARNING(f'  Category already exists: {cat_data["name_key"]}')
                )

            # Create or update translations
            for lang_code, translation_text in cat_data['translations'].items():
                translation, trans_created = ScoreCategoryTranslation.objects.update_or_create(
                    category=category,
                    language_code=lang_code,
                    defaults={'name': translation_text}
                )

                if trans_created:
                    updated_count += 1

        # Configure content type scoring
        self.stdout.write('\n=== Configuring Content Type Scoring ===')

        content_type_configs = {
            'poem': [
                ('imagery_sensory', 30),
                ('rhythm_musicality', 25),
                ('form_structure', 20),
                ('emotional_impact_poem', 25),
            ],
            'essay': [
                ('thesis_clarity', 20),
                ('argument_strength', 25),
                ('evidence_quality', 20),
                ('organization_flow', 15),
                ('writing_style_essay', 20),
            ],
            'sketch': [
                ('observation_quality', 30),
                ('imagery_description', 25),
                ('insight_reflection', 25),
                ('writing_style_sketch', 20),
            ],
            'novel': [
                ('story_plot', 30),
                ('character_development', 20),
                ('world_building', 15),
                ('writing_style', 20),
                ('dialogue', 10),
                ('emotional_impact', 5),
            ],
        }

        for content_type, categories in content_type_configs.items():
            config, config_created = ContentTypeScoringConfig.objects.get_or_create(
                content_type=content_type
            )

            if config_created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created config for: {content_type}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  Config already exists for: {content_type}')
                )

            # Link categories with weights
            for category_key, weight in categories:
                try:
                    category = ScoreCategory.objects.get(name_key=category_key)
                    weight_obj, weight_created = ContentTypeCategoryWeight.objects.update_or_create(
                        config=config,
                        category=category,
                        defaults={'weight': weight}
                    )

                    if weight_created:
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Linked {category_key} ({weight}%)')
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(f'  ↻ Updated {category_key} ({weight}%)')
                        )
                except ScoreCategory.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Category not found: {category_key}')
                    )

        # Summary
        self.stdout.write('\n=== Summary ===')
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Created {created_count} new score categories'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Total score categories in database: {ScoreCategory.objects.count()}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Content type configs: {ContentTypeScoringConfig.objects.count()}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Category weights: {ContentTypeCategoryWeight.objects.count()}'
            )
        )
        self.stdout.write(self.style.SUCCESS('\n✓ Seeding complete!\n'))
