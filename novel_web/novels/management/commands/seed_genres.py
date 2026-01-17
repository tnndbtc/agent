"""Management command to seed Genre and GenreTranslation data."""
from django.core.management.base import BaseCommand
from novels.models import Genre, GenreTranslation


class Command(BaseCommand):
    help = 'Seed Genre and GenreTranslation data with default genres'

    def handle(self, *args, **options):
        """Create default genres with English and Chinese translations."""

        genres_data = [
            {
                'name_key': 'fantasy',
                'translations': {
                    'en': 'Fantasy',
                    'zh-hans': '奇幻'
                }
            },
            {
                'name_key': 'sci_fi',
                'translations': {
                    'en': 'Science Fiction',
                    'zh-hans': '科幻'
                }
            },
            {
                'name_key': 'romance',
                'translations': {
                    'en': 'Romance',
                    'zh-hans': '浪漫'
                }
            },
            {
                'name_key': 'mystery',
                'translations': {
                    'en': 'Mystery',
                    'zh-hans': '悬疑'
                }
            },
            {
                'name_key': 'thriller',
                'translations': {
                    'en': 'Thriller',
                    'zh-hans': '惊悚'
                }
            },
            {
                'name_key': 'horror',
                'translations': {
                    'en': 'Horror',
                    'zh-hans': '恐怖'
                }
            },
            {
                'name_key': 'historical',
                'translations': {
                    'en': 'Historical Fiction',
                    'zh-hans': '历史小说'
                }
            },
            {
                'name_key': 'literary',
                'translations': {
                    'en': 'Literary Fiction',
                    'zh-hans': '文学小说'
                }
            },
            {
                'name_key': 'young_adult',
                'translations': {
                    'en': 'Young Adult',
                    'zh-hans': '青少年'
                }
            },
            {
                'name_key': 'adventure',
                'translations': {
                    'en': 'Adventure',
                    'zh-hans': '冒险'
                }
            },
            {
                'name_key': 'dystopian',
                'translations': {
                    'en': 'Dystopian',
                    'zh-hans': '反乌托邦'
                }
            },
        ]

        created_count = 0
        updated_count = 0

        for genre_data in genres_data:
            # Get or create genre
            genre, created = Genre.objects.get_or_create(
                name_key=genre_data['name_key'],
                defaults={'public': True}
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created genre: {genre_data["name_key"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Genre already exists: {genre_data["name_key"]}')
                )

            # Create or update translations
            for lang_code, translation_text in genre_data['translations'].items():
                translation, trans_created = GenreTranslation.objects.update_or_create(
                    genre=genre,
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
                f'\n✓ Seeding complete! Created {created_count} genres with translations.'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Total genres in database: {Genre.objects.count()}'
            )
        )
