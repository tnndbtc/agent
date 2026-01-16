"""Celery tasks for async AI generation operations."""
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from celery.utils.log import get_task_logger
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import threading
import time
from .models import GenerationTask, NovelProject, Chapter, ChapterOutline, APIPerformanceMetric
from .services import (
    BrainstormService, PlotService, CharacterService,
    SettingService, OutlineService, WritingService,
    EditingService, ScoringService
)

logger = get_task_logger(__name__)


class ProgressUpdater:
    """Helper class to incrementally update progress during long operations."""

    def __init__(self, task_id, start_progress, max_progress, increment=5, interval=2):
        self.task_id = task_id
        self.current_progress = start_progress
        self.max_progress = max_progress
        self.increment = increment
        self.interval = interval
        self.running = False
        self.thread = None

    def _update_loop(self):
        """Background loop that updates progress every interval."""
        while self.running and self.current_progress < self.max_progress:
            time.sleep(self.interval)
            if self.running:
                self.current_progress = min(self.current_progress + self.increment, self.max_progress)
                update_task_progress(self.task_id, self.current_progress, self.message)

    def start(self, message="Processing..."):
        """Start the progress updater."""
        self.message = message
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the progress updater."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)


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

        # Broadcast progress to WebSocket
        channel_layer = get_channel_layer()
        if channel_layer:
            try:
                async_to_sync(channel_layer.group_send)(
                    f'generation_{task_id}',
                    {
                        'type': 'task_progress',
                        'progress': progress,
                        'message': message,
                        'status': task.status
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to broadcast progress to WebSocket: {e}")
    except GenerationTask.DoesNotExist:
        logger.error(f"Task {task_id} not found")
    except Exception as e:
        logger.error(f"Error updating task progress: {e}")


@shared_task(bind=True, max_retries=3)
def brainstorm_ideas_task(self, task_id, project_id, genre=None, theme=None, num_ideas=3, custom_prompt=None, user_language='en'):
    """Generate plot ideas asynchronously."""
    logger.info(f"Brainstorm task started - task_id: {task_id}, project_id: {project_id}, "
               f"genre: {genre}, theme: {theme}, num_ideas: {num_ideas}, custom_prompt: {custom_prompt}, user_language: {user_language}")

    try:
        task = GenerationTask.objects.get(id=task_id)
        task.status = 'running'
        task.started_at = timezone.now()
        task.celery_task_id = self.request.id
        task.save(update_fields=['status', 'started_at', 'celery_task_id'])

        project = NovelProject.objects.get(id=project_id)

        update_task_progress(task_id, 17, "Generating plot ideas...")

        # Start incremental progress updates (17% -> 85%, +5% every 2 seconds)
        progress_updater = ProgressUpdater(task_id, 17, 85, increment=5, interval=2)
        progress_updater.start("Generating plot ideas...")

        try:
            ideas = BrainstormService.generate_ideas(
                project,
                genre=genre,
                theme=theme,
                num_ideas=num_ideas,
                custom_prompt=custom_prompt,
                use_context=False,  # Skip context retrieval for faster generation
                user_language=user_language
            )
            logger.info(f"Brainstorm task generated {len(ideas)} ideas")
        finally:
            progress_updater.stop()

        update_task_progress(task_id, 90, "Finalizing ideas...")

        task.result_data = {'ideas': ideas}
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.progress = 100
        task.save()

        # Track API performance
        if task.started_at and task.completed_at:
            duration = (task.completed_at - task.started_at).total_seconds()
            APIPerformanceMetric.objects.create(
                api_type='brainstorm',
                duration_seconds=duration,
                input_params={'num_ideas': num_ideas, 'theme': theme or ''},
                success=True
            )

        update_task_progress(task_id, 100, "Complete!")

        return {'ideas': ideas}

    except Exception as exc:
        logger.error(f"Brainstorm task failed: {exc}")
        task = GenerationTask.objects.get(id=task_id)
        task.status = 'failed'
        task.error_message = str(exc)
        task.save()

        # Broadcast error to WebSocket BEFORE retrying
        update_task_progress(task_id, task.progress, f"Error: {str(exc)}")

        # Only retry if we haven't exhausted retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying brainstorm task, attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=exc, countdown=60)
        else:
            # Final failure after all retries exhausted
            logger.error(f"Brainstorm task {task_id} failed after {self.max_retries} retries")
            raise


@shared_task(bind=True, max_retries=3)
def write_chapter_task(self, task_id, project_id, chapter_outline_id, writing_style='literary', language='English', target_word_count=3000):
    """Write a chapter asynchronously."""
    logger.info(f"Write chapter task started - task_id: {task_id}, project_id: {project_id}, "
                f"outline_id: {chapter_outline_id}, language: {language}, writing_style: {writing_style}")
    try:
        task = GenerationTask.objects.get(id=task_id)
        task.status = 'running'
        task.started_at = timezone.now()
        task.celery_task_id = self.request.id
        task.save(update_fields=['status', 'started_at', 'celery_task_id'])

        # Get project with error handling
        try:
            project = NovelProject.objects.get(id=project_id)
        except NovelProject.DoesNotExist:
            error_msg = f"Project {project_id} not found"
            logger.error(error_msg)
            task.status = 'failed'
            task.error_message = error_msg
            task.save()
            update_task_progress(task_id, 0, f"Error: {error_msg}")
            return

        # Get outline with specific error handling
        try:
            outline = ChapterOutline.objects.get(id=chapter_outline_id, project=project)
            logger.info(f"Found ChapterOutline: {outline.id} - Title: {outline.title}")
        except ChapterOutline.DoesNotExist:
            error_msg = f"Chapter outline {chapter_outline_id} not found for project {project_id}"
            logger.error(error_msg)
            task.status = 'failed'
            task.error_message = error_msg
            task.save()
            update_task_progress(task_id, 0, f"Error: {error_msg}")
            return

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

        update_task_progress(task_id, 17, "Generating chapter content...")

        # Start incremental progress updates (17% -> 75%, +5% every 2 seconds)
        progress_updater = ProgressUpdater(task_id, 17, 75, increment=5, interval=2)
        progress_updater.start("Generating chapter content...")

        try:
            logger.info(f"Calling WritingService.write_chapter with language='{language}'")
            chapter_data = WritingService.write_chapter(
                project,
                outline_data,
                writing_style=writing_style,
                language=language,
                target_word_count=target_word_count
            )

            # Log the response structure for debugging
            logger.info(f"WritingService returned data with keys: {chapter_data.keys() if isinstance(chapter_data, dict) else 'Not a dict'}")

            # Validate response structure
            required_keys = ['chapter_number', 'title', 'content', 'word_count']
            missing_keys = [k for k in required_keys if k not in chapter_data]
            if missing_keys:
                raise ValueError(f"Invalid chapter data returned, missing keys: {missing_keys}")

            # Check if content contains an error message (from AI)
            if isinstance(chapter_data.get('content'), dict):
                if 'error' in chapter_data['content']:
                    raise ValueError(f"AI returned error: {chapter_data['content']['error']}")
                # Content shouldn't be a dict, log warning
                logger.warning(f"Chapter content is a dict, not a string: {chapter_data['content']}")

            # Log if content is in Chinese
            content = chapter_data.get('content', '')
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in content[:500] if char)
            logger.info(f"Chapter content generated - Language requested: {language}, Contains Chinese: {has_chinese}")

        except Exception as e:
            logger.error(f"WritingService.write_chapter failed: {e}", exc_info=True)
            raise
        finally:
            progress_updater.stop()

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
            'word_count': chapter_data['word_count'],
            'content': chapter_data['content'],  # Include content in result
            'title': chapter_data['title']
        }
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.progress = 100
        task.save()

        # Track API performance
        if task.started_at and task.completed_at:
            duration = (task.completed_at - task.started_at).total_seconds()
            APIPerformanceMetric.objects.create(
                api_type='chapter',
                duration_seconds=duration,
                input_params={'target_word_count': target_word_count, 'writing_style': writing_style},
                success=True
            )

        update_task_progress(task_id, 100, "Chapter complete!")

        return {'chapter_id': str(chapter.id)}

    except Exception as exc:
        logger.error(f"Write chapter task failed: {exc}")
        task = GenerationTask.objects.get(id=task_id)
        task.status = 'failed'
        task.error_message = str(exc)
        task.save()

        # Broadcast error to WebSocket BEFORE retrying
        update_task_progress(task_id, task.progress, f"Error: {str(exc)}")

        # Only retry if we haven't exhausted retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying write chapter task, attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=exc, countdown=60)
        else:
            # Final failure after all retries exhausted
            logger.error(f"Write chapter task {task_id} failed after {self.max_retries} retries")
            raise


@shared_task(bind=True, max_retries=3, time_limit=180, soft_time_limit=150)
def create_outline_task(self, task_id, project_id, num_chapters=20, user_language='en'):
    """Create chapter outline asynchronously.

    Time limits: 150s soft limit (raises exception), 180s hard limit (kills task).
    """
    logger.info(f"Create Outline task started - task_id: {task_id}, project_id: {project_id}, "
               f"num_chapters: {num_chapters}, user_language: {user_language}")

    try:
        task = GenerationTask.objects.get(id=task_id)
        task.status = 'running'
        task.started_at = timezone.now()
        task.celery_task_id = self.request.id
        task.save(update_fields=['status', 'started_at', 'celery_task_id'])

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

        update_task_progress(task_id, 17, f"Generating {num_chapters} chapter outline...")

        # Start incremental progress updates (17% -> 75%, +5% every 2 seconds)
        progress_updater = ProgressUpdater(task_id, 17, 75, increment=5, interval=2)
        progress_updater.start(f"Generating {num_chapters} chapter outline...")

        try:
            outline = OutlineService.create_outline(project, plot_data, num_chapters, user_language=user_language)
            logger.info(f"Create Outline task generated outline with {len(outline.get('chapters', []))} chapters")
        finally:
            progress_updater.stop()

        update_task_progress(task_id, 80, "Saving outline...")

        # Get highest existing chapter number to append new outlines
        existing_outlines = ChapterOutline.objects.filter(project=project).order_by('-number')
        starting_number = existing_outlines.first().number + 1 if existing_outlines.exists() else 1

        # Adjust chapter numbers to append after existing outlines
        for chapter_data in outline['chapters']:
            chapter_data['number'] = starting_number + (chapter_data['number'] - 1)

        # Save chapter outlines to database with progress updates
        total_chapters = len(outline['chapters'])
        for i, chapter_data in enumerate(outline['chapters'], 1):
            ChapterOutline.objects.create(
                project=project,
                number=chapter_data['number'],
                title=chapter_data.get('title', f"Chapter {chapter_data['number']}"),
                pov=chapter_data.get('pov', ''),
                setting=chapter_data.get('setting', ''),
                events=chapter_data.get('events', ''),
                character_development=chapter_data.get('character_development', ''),
                pacing=chapter_data.get('pacing', 'medium'),
                story_beats=chapter_data.get('story_beats', '')
            )

            # Update progress every 3 chapters or on last chapter
            if i % 3 == 0 or i == total_chapters:
                progress = 80 + int((i / total_chapters) * 15)
                update_task_progress(task_id, progress, f"Saved {i}/{total_chapters} chapters...")

        update_task_progress(task_id, 95, "Finalizing...")

        task.result_data = {'num_chapters': len(outline['chapters'])}
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.progress = 100
        task.save()

        # Track API performance
        if task.started_at and task.completed_at:
            duration = (task.completed_at - task.started_at).total_seconds()
            APIPerformanceMetric.objects.create(
                api_type='outline',
                duration_seconds=duration,
                input_params={'num_chapters': num_chapters},
                success=True
            )

        update_task_progress(task_id, 100, "Outline complete!")

        return {'num_chapters': len(outline['chapters'])}

    except SoftTimeLimitExceeded:
        logger.error(f"Create outline task timed out after 150 seconds")
        task = GenerationTask.objects.get(id=task_id)
        task.status = 'failed'
        task.error_message = f"Outline generation timed out. Try generating fewer chapters (you requested {num_chapters})."
        task.save()

        # Broadcast error to WebSocket
        update_task_progress(task_id, task.progress, task.error_message)
        raise
    except Exception as exc:
        logger.error(f"Create outline task failed: {exc}")
        task = GenerationTask.objects.get(id=task_id)
        task.status = 'failed'
        task.error_message = str(exc)
        task.save()

        # Broadcast error to WebSocket BEFORE retrying
        update_task_progress(task_id, task.progress, f"Error: {str(exc)}")

        # Only retry if we haven't exhausted retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying outline task, attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=exc, countdown=60)
        else:
            # Final failure after all retries exhausted
            logger.error(f"Outline task {task_id} failed after {self.max_retries} retries")
            raise


@shared_task(bind=True, max_retries=3, time_limit=120, soft_time_limit=100)
def regenerate_single_outline_task(self, task_id, project_id, chapter_number, user_language='en'):
    """Regenerate a single chapter outline asynchronously.

    Time limits: 100s soft limit (raises exception), 120s hard limit (kills task).
    """
    try:
        task = GenerationTask.objects.get(id=task_id)
        task.status = 'running'
        task.started_at = timezone.now()
        task.celery_task_id = self.request.id
        task.save(update_fields=['status', 'started_at', 'celery_task_id'])

        project = NovelProject.objects.get(id=project_id)

        # Get plot data
        if not hasattr(project, 'plot'):
            raise ValueError("Project must have a plot before regenerating outline")

        plot_data = {
            'title': project.plot.premise,
            'genre': project.plot.genre,
            'premise': project.plot.premise,
            'themes': project.plot.themes,
            'conflict': project.plot.conflict,
            'structure': project.plot.structure,
            'arc': project.plot.arc
        }

        update_task_progress(task_id, 17, f"Regenerating chapter {chapter_number} outline...")

        # Get existing outlines for context
        all_outlines = list(project.chapter_outlines.all().order_by('number'))
        total_chapters = len(all_outlines)

        # Start incremental progress updates (17% -> 75%, +5% every 2 seconds)
        progress_updater = ProgressUpdater(task_id, 17, 75, increment=5, interval=2)
        progress_updater.start(f"Regenerating chapter {chapter_number} outline...")

        try:
            # Generate new outline for this chapter
            outline = OutlineService.create_outline(project, plot_data, total_chapters, user_language=user_language)
        finally:
            progress_updater.stop()

        update_task_progress(task_id, 80, "Saving outline...")

        # Find and update the specific chapter outline
        if chapter_number <= len(outline['chapters']):
            chapter_data = outline['chapters'][chapter_number - 1]
            ChapterOutline.objects.update_or_create(
                project=project,
                number=chapter_number,
                defaults={
                    'title': chapter_data.get('title', f"Chapter {chapter_number}"),
                    'pov': chapter_data.get('pov', ''),
                    'setting': chapter_data.get('setting', ''),
                    'events': chapter_data.get('events', ''),
                    'character_development': chapter_data.get('character_development', ''),
                    'pacing': chapter_data.get('pacing', 'medium'),
                    'story_beats': chapter_data.get('story_beats', '')
                }
            )
        else:
            raise ValueError(f"Generated outline doesn't include chapter {chapter_number}")

        update_task_progress(task_id, 95, "Finalizing...")

        task.result_data = {'chapter_number': chapter_number}
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.progress = 100
        task.save()

        update_task_progress(task_id, 100, "Outline regenerated!")

        return {'chapter_number': chapter_number}

    except SoftTimeLimitExceeded:
        logger.error(f"Regenerate outline task timed out after 100 seconds")
        task = GenerationTask.objects.get(id=task_id)
        task.status = 'failed'
        task.error_message = "Outline regeneration timed out. Please try again."
        task.save()

        # Broadcast error to WebSocket
        update_task_progress(task_id, task.progress, task.error_message)
        raise
    except Exception as exc:
        logger.error(f"Regenerate outline task failed: {exc}")
        task = GenerationTask.objects.get(id=task_id)
        task.status = 'failed'
        task.error_message = str(exc)
        task.save()

        # Broadcast error to WebSocket BEFORE retrying
        update_task_progress(task_id, task.progress, f"Error: {str(exc)}")

        # Only retry if we haven't exhausted retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying regenerate outline task, attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=exc, countdown=60)
        else:
            # Final failure after all retries exhausted
            logger.error(f"Regenerate outline task {task_id} failed after {self.max_retries} retries")
            raise


@shared_task(bind=True, max_retries=3)
def score_novel_task(self, task_id, project_id):
    """Score novel asynchronously."""
    try:
        task = GenerationTask.objects.get(id=task_id)
        task.status = 'running'
        task.started_at = timezone.now()
        task.celery_task_id = self.request.id
        task.save(update_fields=['status', 'started_at', 'celery_task_id'])

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

        update_task_progress(task_id, 17, "Analyzing content...")

        # Get chapters
        for chapter in project.chapters.all()[:5]:  # Sample first 5 chapters
            novel_data['chapters'].append({
                'chapter_number': chapter.chapter_number,
                'content': chapter.content,
                'word_count': chapter.word_count
            })

        update_task_progress(task_id, 60, "Scoring novel...")

        # Start incremental progress updates (60% -> 85%, +5% every 2 seconds)
        progress_updater = ProgressUpdater(task_id, 60, 85, increment=5, interval=2)
        progress_updater.start("Scoring novel...")

        try:
            score_report = ScoringService.score_novel(project, novel_data)
        finally:
            progress_updater.stop()

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
        task = GenerationTask.objects.get(id=task_id)
        task.status = 'failed'
        task.error_message = str(exc)
        task.save()

        # Broadcast error to WebSocket BEFORE retrying
        update_task_progress(task_id, task.progress, f"Error: {str(exc)}")

        # Only retry if we haven't exhausted retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying score novel task, attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=exc, countdown=60)
        else:
            # Final failure after all retries exhausted
            logger.error(f"Score novel task {task_id} failed after {self.max_retries} retries")
            raise
