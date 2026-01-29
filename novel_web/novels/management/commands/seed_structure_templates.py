"""Management command to seed ContentStructureTemplate data."""
from django.core.management.base import BaseCommand
from novels.models import ContentStructureTemplate


class Command(BaseCommand):
    help = 'Seed ContentStructureTemplate data with default templates'

    def handle(self, *args, **options):
        """Create default structure templates for essays and sketches."""

        templates_data = [
            # Essay Templates
            {
                'content_type': 'essay',
                'name': 'Five-Paragraph Essay',
                'is_system': True,
                'structure_data': {
                    'sections': [
                        'Introduction',
                        'Body 1',
                        'Body 2',
                        'Body 3',
                        'Conclusion'
                    ]
                },
                'description': 'Classic five-paragraph essay structure with introduction, three body paragraphs, and conclusion.'
            },
            {
                'content_type': 'essay',
                'name': 'Compare-Contrast',
                'is_system': True,
                'structure_data': {
                    'sections': [
                        'Introduction',
                        'Similarities',
                        'Differences',
                        'Conclusion'
                    ]
                },
                'description': 'Compare and contrast essay structure examining similarities and differences between two subjects.'
            },
            {
                'content_type': 'essay',
                'name': 'Argumentative',
                'is_system': True,
                'structure_data': {
                    'sections': [
                        'Introduction',
                        'Argument',
                        'Counter-argument',
                        'Rebuttal',
                        'Conclusion'
                    ]
                },
                'description': 'Argumentative essay structure presenting main argument, addressing counter-arguments, and providing rebuttals.'
            },
            # Sketch Template
            {
                'content_type': 'sketch',
                'name': 'Moment-Thought-Stop',
                'is_system': True,
                'structure_data': {
                    'parts': [
                        'Moment',
                        'Thought',
                        'Stop'
                    ]
                },
                'description': 'Classic sketch structure: capture a moment, reflect on it, then end abruptly.'
            },
        ]

        created_count = 0
        updated_count = 0

        self.stdout.write('\n=== Creating Structure Templates ===')

        for template_data in templates_data:
            template, created = ContentStructureTemplate.objects.update_or_create(
                content_type=template_data['content_type'],
                name=template_data['name'],
                defaults={
                    'is_system': template_data['is_system'],
                    'created_by': None,  # System templates have no user
                    'structure_data': template_data['structure_data'],
                    'description': template_data['description']
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created template: {template_data["content_type"]} - {template_data["name"]}'
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'↻ Updated template: {template_data["content_type"]} - {template_data["name"]}'
                    )
                )

        # Summary
        self.stdout.write('\n=== Summary ===')
        self.stdout.write(
            self.style.SUCCESS(f'✓ Created {created_count} new structure templates')
        )
        self.stdout.write(
            self.style.SUCCESS(f'↻ Updated {updated_count} existing templates')
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Total structure templates in database: {ContentStructureTemplate.objects.count()}'
            )
        )
        self.stdout.write(self.style.SUCCESS('\n✓ Seeding complete!\n'))
