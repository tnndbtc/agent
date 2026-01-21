"""Celery tasks for async AI generation operations."""
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.db import models
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import threading
import time
from .models import GenerationTask, NovelProject, Chapter, ChapterOutline, APIPerformanceMetric, UserProfile
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
            ideas, token_usage = BrainstormService.generate_ideas(
                project,
                genre=genre,
                theme=theme,
                num_ideas=num_ideas,
                custom_prompt=custom_prompt,
                use_context=False,  # Skip context retrieval for faster generation
                user_language=user_language
            )
            logger.info(f"Brainstorm task generated {len(ideas)} ideas, tokens: {token_usage}")

            # Save token usage to user profile
            if token_usage and task.user:
                try:
                    profile, created = UserProfile.objects.get_or_create(user=task.user)
                    profile.add_tokens(
                        prompt_tokens=token_usage.get('prompt_tokens', 0),
                        completion_tokens=token_usage.get('completion_tokens', 0),
                        total_tokens=token_usage.get('total_tokens', 0)
                    )
                    logger.info(f"Saved brainstorm tokens to user {task.user.username}: {token_usage}")
                except Exception as e:
                    logger.error(f"Failed to save brainstorm tokens to user profile: {e}")
        finally:
            progress_updater.stop()

        update_task_progress(task_id, 90, "Finalizing ideas...")

        task.result_data = {
            'ideas': ideas,
            'token_usage': token_usage
        }
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

        return {
            'ideas': ideas,
            'token_usage': token_usage
        }

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
def write_chapter_task(self, task_id, project_id, chapter_outline_id, writing_style='literary', language='English', target_word_count=3000, example_id=None, iterative_mode=True, max_iterations_multiplier=3):
    """
    Write a chapter asynchronously with optional iterative quality improvement.

    Args:
        task_id: Generation task ID
        project_id: Novel project ID
        chapter_outline_id: Chapter outline ID
        writing_style: Writing style (literary, commercial, etc.)
        language: Target language
        target_word_count: Target word count for the chapter
        example_id: Optional example ID for quality targeting
        iterative_mode: Whether to use iterative generation (default: True)
        max_iterations_multiplier: Maximum tokens as multiple of first iteration (default: 3)
    """
    logger.info(f"Write chapter task started - task_id: {task_id}, project_id: {project_id}, "
                f"outline_id: {chapter_outline_id}, language: {language}, writing_style: {writing_style}, "
                f"example_id: {example_id}, iterative_mode: {iterative_mode}")
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

        # Load example metadata if example_id provided (metadata only, NO content!)
        example_metadata = None
        target_total_score = None
        if example_id and iterative_mode:
            try:
                from .models import Example
                example = Example.objects.prefetch_related('scores__category').get(id=example_id)

                # Extract ONLY metadata (NO content!)
                example_metadata = {
                    'category': example.category,
                    'total_score': float(example.total_score),
                    'scores': [
                        {
                            'category_name': str(score.category),
                            'score': float(score.score),
                            'weight': score.weight
                        }
                        for score in example.scores.all()
                    ]
                }
                target_total_score = float(example.total_score)
                logger.info(f"Loaded example metadata (NO content): category={example_metadata['category']}, "
                           f"target_score={target_total_score}")
            except Exception as e:
                logger.warning(f"Failed to load example {example_id}: {e}. Continuing without example.")
                example_metadata = None
                iterative_mode = False

        update_task_progress(task_id, 17, "Generating chapter content...")

        # Start incremental progress updates (17% -> 75%, +5% every 2 seconds)
        progress_updater = ProgressUpdater(task_id, 17, 75, increment=5, interval=2)
        progress_updater.start("Generating chapter content...")

        # Initialize iteration variables
        iteration = 1
        cumulative_tokens = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
        first_iteration_tokens = 0
        max_total_tokens = 0
        best_chapter_data = None
        best_score = 0
        previous_scores = None
        iteration_history = []  # Store each iteration's scores

        try:
            # Iterative generation loop
            while True:
                iteration_msg = f"Iteration {iteration}" if iterative_mode and example_metadata else "Generating chapter content"
                logger.info(f"{iteration_msg} - Calling WritingService.write_chapter with language='{language}'")

                # Pass example_metadata (NO content!), iteration, and previous_scores
                chapter_data, token_usage = WritingService.write_chapter(
                    project,
                    outline_data,
                    writing_style=writing_style,
                    language=language,
                    target_word_count=target_word_count,
                    example_metadata=example_metadata,
                    iteration=iteration,
                    previous_scores=previous_scores
                )

                # Accumulate tokens
                if token_usage:
                    cumulative_tokens['prompt_tokens'] += token_usage.get('prompt_tokens', 0)
                    cumulative_tokens['completion_tokens'] += token_usage.get('completion_tokens', 0)
                    cumulative_tokens['total_tokens'] += token_usage.get('total_tokens', 0)

                # Track first iteration tokens for budget
                if iteration == 1:
                    first_iteration_tokens = token_usage.get('total_tokens', 0)
                    max_total_tokens = first_iteration_tokens * max_iterations_multiplier
                    logger.info(f"First iteration used {first_iteration_tokens} tokens. "
                               f"Max budget: {max_total_tokens} tokens ({max_iterations_multiplier}x)")

                # If not in iterative mode or no example, use this result and break
                if not iterative_mode or not example_metadata:
                    best_chapter_data = chapter_data
                    logger.info("Non-iterative mode - using generated content")
                    break

                # Score the generated content
                from .services import ExampleScoringService
                content = chapter_data.get('content', '')
                logger.info(f"Iteration {iteration} - Scoring generated content (length: {len(content)})")

                try:
                    scores_by_name, scoring_tokens = ExampleScoringService.generate_scores(
                        content=content,
                        category=example_metadata.get('category'),
                        user_language=language
                    )

                    # Accumulate scoring tokens
                    if scoring_tokens:
                        cumulative_tokens['prompt_tokens'] += scoring_tokens.get('prompt_tokens', 0)
                        cumulative_tokens['completion_tokens'] += scoring_tokens.get('completion_tokens', 0)
                        cumulative_tokens['total_tokens'] += scoring_tokens.get('total_tokens', 0)

                    # Calculate total score (weighted average)
                    total_score = sum(scores_by_name.values()) / len(scores_by_name) if scores_by_name else 0
                    logger.info(f"Iteration {iteration} - Score: {total_score:.1f}/10 (Target: {target_total_score:.1f}/10)")
                    logger.info(f"Iteration {iteration} - Category scores: {scores_by_name}")

                    # Record this iteration's results
                    iteration_data = {
                        'iteration': iteration,
                        'total_score': round(total_score, 1),
                        'target_score': round(target_total_score, 1),
                        'scores': {cat_name: round(score, 1) for cat_name, score in scores_by_name.items()},
                        'is_best': False
                    }
                    iteration_history.append(iteration_data)

                    # Track best result
                    if total_score > best_score:
                        best_score = total_score
                        best_chapter_data = chapter_data
                        # Mark this iteration as best
                        for iter_data in iteration_history:
                            iter_data['is_best'] = (iter_data['iteration'] == iteration)
                        logger.info(f"Iteration {iteration} - New best score: {best_score:.1f}/10")

                    # Check if we met the target score
                    if total_score >= target_total_score:
                        logger.info(f"Iteration {iteration} - Target score achieved! "
                                   f"({total_score:.1f} >= {target_total_score:.1f})")
                        break

                    # Check if we've exceeded token budget
                    if cumulative_tokens['total_tokens'] >= max_total_tokens:
                        logger.info(f"Iteration {iteration} - Token budget reached "
                                   f"({cumulative_tokens['total_tokens']} >= {max_total_tokens})")
                        break

                    # Prepare for next iteration with gap analysis
                    # Build target scores map from example metadata
                    target_scores_map = {}
                    if example_metadata and 'scores' in example_metadata:
                        target_scores_map = {
                            score['category_name']: score['score']
                            for score in example_metadata['scores']
                        }

                    previous_scores = {
                        'total': total_score,
                        'target_total': target_total_score if example_metadata else 0,
                        'by_category': [
                            {
                                'category_name': cat_name,
                                'score': score,
                                'target_score': target_scores_map.get(cat_name, target_total_score if example_metadata else 0)
                            }
                            for cat_name, score in scores_by_name.items()
                        ]
                    }

                    iteration += 1
                    update_task_progress(task_id, min(17 + iteration * 10, 70),
                                       f"Iteration {iteration} - Improving quality...")
                    logger.info(f"Starting iteration {iteration} with gap analysis")

                except Exception as e:
                    logger.error(f"Iteration {iteration} - Scoring failed: {e}. Using current result.")
                    if best_chapter_data is None:
                        best_chapter_data = chapter_data
                    break

            # Use best result from all iterations
            chapter_data = best_chapter_data
            token_usage = cumulative_tokens

            # Save token usage to user profile
            if token_usage and token_usage.get('total_tokens', 0) > 0:
                logger.info(f"Saving token usage to UserProfile: {token_usage}")
                user_profile, _ = UserProfile.objects.get_or_create(user=project.user)
                user_profile.total_tokens += token_usage.get('total_tokens', 0)
                user_profile.prompt_tokens += token_usage.get('prompt_tokens', 0)
                user_profile.completion_tokens += token_usage.get('completion_tokens', 0)
                user_profile.save()

            # Log the response structure for debugging
            logger.info(f"WritingService returned data with keys: {chapter_data.keys() if isinstance(chapter_data, dict) else 'Not a dict'}")
            logger.info(f"Token usage: {token_usage}")

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
            'title': chapter_data['title'],
            'token_usage': token_usage,  # Include token usage for frontend display
            'iterations': iteration if iterative_mode and example_metadata else 1,  # Number of iterations performed
            'best_score': best_score if iterative_mode and example_metadata else None,  # Best score achieved
            'target_score': target_total_score if iterative_mode and example_metadata else None,  # Target score
            'iteration_history': iteration_history if iterative_mode and example_metadata else []  # Per-iteration score breakdown
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
def create_outline_task(self, task_id, project_id, num_chapters=1, act_id=None, user_language='en'):
    """Create chapter outline asynchronously.

    Args:
        task_id: ID of the GenerationTask
        project_id: ID of the NovelProject
        num_chapters: Number of chapter outlines to generate
        act_id: Optional ID of Act to associate outlines with
        user_language: Language for generation

    Time limits: 150s soft limit (raises exception), 180s hard limit (kills task).
    """
    logger.info(f"Create Outline task started - task_id: {task_id}, project_id: {project_id}, "
               f"num_chapters: {num_chapters}, act_id: {act_id}, user_language: {user_language}")

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
            'premise': project.plot.premise,
            'themes': project.plot.themes,
            'conflict': project.plot.conflict,
            'structure': project.plot.structure,
            'arc': project.plot.arc
        }

        # Fetch act if act_id is provided (key feature: include act context)
        act = None
        if act_id:
            from .models import Act
            try:
                act = Act.objects.get(id=act_id, plot=project.plot)
                logger.info(f"Fetched Act {act.act_number}: {act.subject} for outline generation")

                # KEY: Add act information to plot_data so it's included in the prompt
                plot_data['act_context'] = {
                    'act_number': act.act_number,
                    'subject': act.subject,
                    'percentage': act.percentage,
                    'description': act.description
                }
                logger.info(f"Including act context in outline generation: {act.subject} ({act.percentage}%)")
            except Act.DoesNotExist:
                logger.error(f"Act {act_id} not found for project {project_id}")
                act = None

        # Retrieve the original brainstorm idea for richer context
        idea_data = None
        try:
            brainstorm_tasks = GenerationTask.objects.filter(
                project=project,
                task_type='brainstorm',
                status='completed'
            ).order_by('-created_at')

            if brainstorm_tasks.exists():
                result = brainstorm_tasks.first().result_data
                if result and 'ideas' in result and len(result['ideas']) > 0:
                    # Use the first idea (or the one that was selected for plot creation)
                    idea_data = result['ideas'][0]
                    logger.info(f"Retrieved original brainstorm idea for outline generation: {idea_data.get('title', 'Untitled')}")
        except Exception as e:
            logger.warning(f"Failed to retrieve original brainstorm idea: {e}")

        update_task_progress(task_id, 17, f"Generating {num_chapters} chapter outline...")

        # Start incremental progress updates (17% -> 75%, +5% every 2 seconds)
        progress_updater = ProgressUpdater(task_id, 17, 75, increment=5, interval=2)
        progress_updater.start(f"Generating {num_chapters} chapter outline...")

        try:
            outline, token_usage = OutlineService.create_outline(project, plot_data, num_chapters, user_language=user_language, idea_data=idea_data)
            logger.info(f"Create Outline task generated outline with {len(outline.get('chapters', []))} chapters, tokens: {token_usage}")
        finally:
            progress_updater.stop()

        update_task_progress(task_id, 80, "Saving outline...")

        from decimal import Decimal

        # Get all existing outlines for global order_key calculation
        all_existing_outlines = ChapterOutline.objects.filter(project=project)
        max_order_key = all_existing_outlines.aggregate(
            max_key=models.Max('order_key')
        )['max_key'] or Decimal('0')

        # Get existing numbers for this specific act (or unassigned if act is None)
        # This ensures each act has its own numbering starting from 1
        if act:
            existing_outlines_in_act = ChapterOutline.objects.filter(project=project, act=act)
        else:
            existing_outlines_in_act = ChapterOutline.objects.filter(project=project, act__isnull=True)
        existing_numbers = set(existing_outlines_in_act.values_list('number', flat=True))

        # Find available numbers (gaps first, then append)
        def find_available_numbers(existing_numbers, count):
            """Find 'count' available numbers, preferring gaps over appending."""
            available = []

            if existing_numbers:
                max_num = max(existing_numbers)
                # Find gaps first
                for i in range(1, max_num + 1):
                    if i not in existing_numbers:
                        available.append(i)
                        if len(available) == count:
                            return available

                # Append after max if not enough gaps
                for i in range(max_num + 1, max_num + count + 1):
                    available.append(i)
                    if len(available) == count:
                        return available
            else:
                # No existing outlines, start from 1
                available = list(range(1, count + 1))

            return available

        total_chapters = len(outline['chapters'])
        available_numbers = find_available_numbers(existing_numbers, total_chapters)

        logger.info(f"Create Outline task - Saving {total_chapters} chapters to database (requested: {num_chapters})")
        logger.info(f"Create Outline task - Assigning numbers: {available_numbers}")

        # Assign numbers and order_keys
        for i, chapter_data in enumerate(outline['chapters']):
            chapter_data['number'] = available_numbers[i]
            chapter_data['order_key'] = max_order_key + Decimal(str(i + 1))

        # Save chapter outlines to database with progress updates
        for i, chapter_data in enumerate(outline['chapters'], 1):
            chapter_title = chapter_data.get('title', f"Chapter {chapter_data['number']}")
            logger.debug(f"Create Outline task - Saving chapter {i}/{total_chapters}: {chapter_title} (number={chapter_data['number']}, order_key={chapter_data['order_key']})")
            ChapterOutline.objects.create(
                project=project,
                act=act,  # Associate with act if provided
                number=chapter_data['number'],
                order_key=chapter_data['order_key'],
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

        # Save token usage to user profile
        if token_usage and task.user:
            try:
                profile, created = UserProfile.objects.get_or_create(user=task.user)
                profile.add_tokens(
                    prompt_tokens=token_usage.get('prompt_tokens', 0),
                    completion_tokens=token_usage.get('completion_tokens', 0),
                    total_tokens=token_usage.get('total_tokens', 0)
                )
                logger.info(f"Saved outline tokens to user {task.user.username}: {token_usage}")
            except Exception as e:
                logger.error(f"Failed to save outline tokens to user profile: {e}")

        task.result_data = {
            'num_chapters': len(outline['chapters']),
            'token_usage': token_usage
        }
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
            outline, token_usage = OutlineService.create_outline(project, plot_data, total_chapters, user_language=user_language)

            # Save token usage to user profile
            if token_usage and token_usage.get('total_tokens', 0) > 0:
                logger.info(f"Saving token usage to UserProfile: {token_usage}")
                user_profile, _ = UserProfile.objects.get_or_create(user=project.user)
                user_profile.total_tokens += token_usage.get('total_tokens', 0)
                user_profile.prompt_tokens += token_usage.get('prompt_tokens', 0)
                user_profile.completion_tokens += token_usage.get('completion_tokens', 0)
                user_profile.save()
        finally:
            progress_updater.stop()

        update_task_progress(task_id, 80, "Saving outline...")

        # Find and update the specific chapter outline
        if chapter_number <= len(outline['chapters']):
            chapter_data = outline['chapters'][chapter_number - 1]

            # Get existing outline to preserve order_key
            from decimal import Decimal
            existing_outline = ChapterOutline.objects.filter(
                project=project,
                number=chapter_number
            ).first()

            if existing_outline:
                # Update existing outline, preserving order_key
                existing_outline.title = chapter_data.get('title', f"Chapter {chapter_number}")
                existing_outline.pov = chapter_data.get('pov', '')
                existing_outline.setting = chapter_data.get('setting', '')
                existing_outline.events = chapter_data.get('events', '')
                existing_outline.character_development = chapter_data.get('character_development', '')
                existing_outline.pacing = chapter_data.get('pacing', 'medium')
                existing_outline.story_beats = chapter_data.get('story_beats', '')
                existing_outline.save()
            else:
                # Create new outline with appropriate order_key
                max_order_key = ChapterOutline.objects.filter(
                    project=project
                ).aggregate(max_key=models.Max('order_key'))['max_key'] or Decimal('0')

                ChapterOutline.objects.create(
                    project=project,
                    number=chapter_number,
                    order_key=max_order_key + Decimal('1'),
                    title=chapter_data.get('title', f"Chapter {chapter_number}"),
                    pov=chapter_data.get('pov', ''),
                    setting=chapter_data.get('setting', ''),
                    events=chapter_data.get('events', ''),
                    character_development=chapter_data.get('character_development', ''),
                    pacing=chapter_data.get('pacing', 'medium'),
                    story_beats=chapter_data.get('story_beats', '')
                )
        else:
            raise ValueError(f"Generated outline doesn't include chapter {chapter_number}")

        update_task_progress(task_id, 95, "Finalizing...")

        task.result_data = {
            'chapter_number': chapter_number,
            'token_usage': token_usage
        }
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.progress = 100
        task.save()

        update_task_progress(task_id, 100, "Outline regenerated!")

        return {'chapter_number': chapter_number, 'token_usage': token_usage}

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


@shared_task(bind=True, max_retries=3)
def generate_example_scores_task(self, task_id, content, category=None, user_language='en'):
    """Generate AI scores for example content."""
    logger.info(f"Example scoring task started - task_id: {task_id}, "
               f"content_length: {len(content)}, category: {category}")

    try:
        task = GenerationTask.objects.get(id=task_id)
        task.status = 'running'
        task.started_at = timezone.now()
        task.celery_task_id = self.request.id
        task.save(update_fields=['status', 'started_at', 'celery_task_id'])

        update_task_progress(task_id, 10, "Analyzing example content...")

        # Start progress updater (10% -> 85%)
        progress_updater = ProgressUpdater(task_id, 10, 85, increment=5, interval=2)
        progress_updater.start("Evaluating writing quality...")

        try:
            # Import service
            from .services import ExampleScoringService

            # Generate scores (returns scores and token_usage)
            scores, token_usage = ExampleScoringService.generate_scores(
                content=content,
                category=category,
                user_language=user_language
            )

            logger.info(f"Generated scores: {scores}, tokens: {token_usage}")

            # Save token usage to user profile
            if token_usage and task.user:
                try:
                    profile, created = UserProfile.objects.get_or_create(user=task.user)
                    profile.add_tokens(
                        prompt_tokens=token_usage.get('prompt_tokens', 0),
                        completion_tokens=token_usage.get('completion_tokens', 0),
                        total_tokens=token_usage.get('total_tokens', 0)
                    )
                    logger.info(f"Saved scoring tokens to user {task.user.username}: {token_usage}")
                except Exception as e:
                    logger.error(f"Failed to save scoring tokens to user profile: {e}")
        finally:
            progress_updater.stop()

        update_task_progress(task_id, 90, "Finalizing scores...")

        task.result_data = {
            'scores': scores,
            'token_usage': token_usage
        }
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.progress = 100
        task.save()

        update_task_progress(task_id, 100, "Complete!")

        return {
            'scores': scores,
            'token_usage': token_usage
        }

    except Exception as exc:
        logger.error(f"Example scoring task failed: {exc}", exc_info=True)
        task = GenerationTask.objects.get(id=task_id)
        task.status = 'failed'
        task.error_message = str(exc)
        task.save()

        # Broadcast error to WebSocket
        update_task_progress(task_id, task.progress, f"Error: {str(exc)}")

        # Only retry if we haven't exhausted retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying example scoring task, attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=exc, countdown=60)
        else:
            logger.error(f"Example scoring task {task_id} failed after {self.max_retries} retries")
            raise
