"""Celery tasks for async AI generation operations."""
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from .models import GenerationTask, NovelProject, Chapter, ChapterOutline
from .services import (
    BrainstormService, PlotService, CharacterService,
    SettingService, OutlineService, WritingService,
    EditingService, ScoringService
)

logger = get_task_logger(__name__)


def update_task_progress(task_id, progress, message=""):
    """Update generation task progress."""
    try:
        task = GenerationTask.objects.get(id=task_id)
        task.progress = progress
        task.progress_message = message
        if progress >= 100:
            task.status = 'completed'
            task.completed_at = timezone.now()
        task.save(update_fields=['progress', 'progress_message', 'status', 'completed_at'])
    except GenerationTask.DoesNotExist:
        logger.error(f"Task {task_id} not found")


@shared_task(bind=True, max_retries=3)
def brainstorm_ideas_task(self, task_id, project_id, genre=None, theme=None, num_ideas=3):
    """Generate plot ideas asynchronously."""
    try:
        task = GenerationTask.objects.get(id=task_id)
        task.status = 'running'
        task.started_at = timezone.now()
        task.celery_task_id = self.request.id
        task.save(update_fields=['status', 'started_at', 'celery_task_id'])

        update_task_progress(task_id, 10, "Initializing brainstorming...")

        project = NovelProject.objects.get(id=project_id)

        update_task_progress(task_id, 30, "Generating plot ideas...")

        ideas = BrainstormService.generate_ideas(
            project,
            genre=genre,
            theme=theme,
            num_ideas=num_ideas,
            use_context=False  # Skip context retrieval for faster generation
        )

        update_task_progress(task_id, 90, "Finalizing ideas...")

        task.result_data = {'ideas': ideas}
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.progress = 100
        task.save()

        update_task_progress(task_id, 100, "Complete!")

        return {'ideas': ideas}

    except Exception as exc:
        logger.error(f"Brainstorm task failed: {exc}")
        task.status = 'failed'
        task.error_message = str(exc)
        task.save()
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def write_chapter_task(self, task_id, project_id, chapter_outline_id, writing_style='literary', language='English'):
    """Write a chapter asynchronously."""
    try:
        task = GenerationTask.objects.get(id=task_id)
        task.status = 'running'
        task.started_at = timezone.now()
        task.celery_task_id = self.request.id
        task.save(update_fields=['status', 'started_at', 'celery_task_id'])

        update_task_progress(task_id, 10, "Initializing chapter writer...")

        project = NovelProject.objects.get(id=project_id)
        outline = ChapterOutline.objects.get(id=chapter_outline_id)

        outline_data = {
            'number': outline.number,
            'title': outline.title,
            'pov': outline.pov,
            'setting': outline.setting,
            'events': outline.events,
            'character_development': outline.character_development,
            'pacing': outline.pacing,
            'story_beats': outline.story_beats
        }

        update_task_progress(task_id, 30, "Generating chapter content...")

        chapter_data = WritingService.write_chapter(
            project,
            outline_data,
            writing_style=writing_style,
            language=language
        )

        update_task_progress(task_id, 80, "Saving chapter...")

        # Create or update chapter
        chapter, created = Chapter.objects.update_or_create(
            project=project,
            chapter_number=chapter_data['chapter_number'],
            defaults={
                'outline': outline,
                'title': chapter_data['title'],
                'content': chapter_data['content'],
                'summary': chapter_data.get('summary', ''),
                'word_count': chapter_data['word_count'],
                'language': language,
                'writing_style': writing_style,
                'is_draft': True
            }
        )

        update_task_progress(task_id, 95, "Finalizing...")

        task.result_data = {
            'chapter_id': str(chapter.id),
            'word_count': chapter_data['word_count']
        }
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.progress = 100
        task.save()

        update_task_progress(task_id, 100, "Chapter complete!")

        return {'chapter_id': str(chapter.id)}

    except Exception as exc:
        logger.error(f"Write chapter task failed: {exc}")
        task.status = 'failed'
        task.error_message = str(exc)
        task.save()
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def create_outline_task(self, task_id, project_id, num_chapters=20):
    """Create chapter outline asynchronously."""
    try:
        task = GenerationTask.objects.get(id=task_id)
        task.status = 'running'
        task.started_at = timezone.now()
        task.celery_task_id = self.request.id
        task.save(update_fields=['status', 'started_at', 'celery_task_id'])

        update_task_progress(task_id, 10, "Initializing outliner...")

        project = NovelProject.objects.get(id=project_id)

        # Get plot data
        if not hasattr(project, 'plot'):
            raise ValueError("Project must have a plot before creating outline")

        plot_data = {
            'title': project.plot.premise,
            'genre': project.plot.genre,
            'premise': project.plot.premise,
            'themes': project.plot.themes,
            'conflict': project.plot.conflict,
            'structure': project.plot.structure,
            'arc': project.plot.arc
        }

        update_task_progress(task_id, 30, f"Generating {num_chapters} chapter outline...")

        outline = OutlineService.create_outline(project, plot_data, num_chapters)

        update_task_progress(task_id, 80, "Saving outline...")

        # Save chapter outlines to database
        for chapter_data in outline['chapters']:
            ChapterOutline.objects.update_or_create(
                project=project,
                number=chapter_data['number'],
                defaults={
                    'title': chapter_data.get('title', f"Chapter {chapter_data['number']}"),
                    'pov': chapter_data.get('pov', ''),
                    'setting': chapter_data.get('setting', ''),
                    'events': chapter_data.get('events', ''),
                    'character_development': chapter_data.get('character_development', ''),
                    'pacing': chapter_data.get('pacing', 'medium'),
                    'story_beats': chapter_data.get('story_beats', '')
                }
            )

        update_task_progress(task_id, 95, "Finalizing...")

        task.result_data = {'num_chapters': len(outline['chapters'])}
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.progress = 100
        task.save()

        update_task_progress(task_id, 100, "Outline complete!")

        return {'num_chapters': len(outline['chapters'])}

    except Exception as exc:
        logger.error(f"Create outline task failed: {exc}")
        task.status = 'failed'
        task.error_message = str(exc)
        task.save()
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def score_novel_task(self, task_id, project_id):
    """Score novel asynchronously."""
    try:
        task = GenerationTask.objects.get(id=task_id)
        task.status = 'running'
        task.started_at = timezone.now()
        task.celery_task_id = self.request.id
        task.save(update_fields=['status', 'started_at', 'celery_task_id'])

        update_task_progress(task_id, 10, "Initializing scorer...")

        project = NovelProject.objects.get(id=project_id)

        # Gather novel data
        novel_data = {
            'title': project.title,
            'genre': project.genre if project.genre else '',
            'plot': {},
            'characters': [],
            'chapters': []
        }

        if hasattr(project, 'plot'):
            novel_data['plot'] = {
                'premise': project.plot.premise,
                'themes': project.plot.themes
            }

        update_task_progress(task_id, 30, "Analyzing content...")

        # Get chapters
        for chapter in project.chapters.all()[:5]:  # Sample first 5 chapters
            novel_data['chapters'].append({
                'chapter_number': chapter.chapter_number,
                'content': chapter.content,
                'word_count': chapter.word_count
            })

        update_task_progress(task_id, 60, "Scoring novel...")

        score_report = ScoringService.score_novel(project, novel_data)

        update_task_progress(task_id, 90, "Finalizing score...")

        task.result_data = score_report
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.progress = 100
        task.save()

        update_task_progress(task_id, 100, "Scoring complete!")

        return score_report

    except Exception as exc:
        logger.error(f"Score novel task failed: {exc}")
        task.status = 'failed'
        task.error_message = str(exc)
        task.save()
        raise self.retry(exc=exc, countdown=60)
