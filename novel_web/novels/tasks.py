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
from .models import GenerationTask, NovelProject, Chapter, APIPerformanceMetric, UserProfile
from .services import (
    PlotService, CharacterService,
    SettingService, WritingService,
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
def write_chapter_task(self, task_id, project_id, act_id, writing_style='literary', language='English', target_word_count=3000, example_id=None, iterative_mode=True, max_iterations_multiplier=3):
    """
    Write a chapter asynchronously with optional iterative quality improvement.

    Args:
        task_id: Generation task ID
        project_id: Novel project ID
        act_id: Act ID for chapter creation
        writing_style: Writing style (literary, commercial, etc.)
        language: Target language
        target_word_count: Target word count for the chapter
        example_id: Optional example ID for quality targeting
        iterative_mode: Whether to use iterative generation (default: True)
        max_iterations_multiplier: Maximum tokens as multiple of first iteration (default: 3)
    """
    logger.info(f"Write chapter task started - task_id: {task_id}, project_id: {project_id}, "
                f"act_id: {act_id}, language: {language}, writing_style: {writing_style}, "
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

        # Get act for chapter creation
        try:
            from .models import Act
            act = Act.objects.get(id=act_id, plot__project=project)
            logger.info(f"Found Act: {act.id} - Subject: {act.subject} for chapter creation")
        except Act.DoesNotExist:
            error_msg = f"Act {act_id} not found for project {project_id}"
            logger.error(error_msg)
            task.status = 'failed'
            task.error_message = error_msg
            task.save()
            update_task_progress(task_id, 0, f"Error: {error_msg}")
            return

        logger.info(f"Creating chapter from Act {act.act_number}: {act.subject}")

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
                chapter_data, token_usage = WritingService.write_chapter_from_act(
                    project,
                    act,
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
            if not chapter_data:
                raise ValueError("WritingService returned None or empty chapter data")

            required_keys = ['chapter_number', 'title', 'content', 'word_count']
            if not isinstance(chapter_data, dict):
                raise ValueError(f"Invalid chapter data type: expected dict, got {type(chapter_data)}")

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
            version=1,  # Explicit version in lookup
            defaults={
                'title': chapter_data['title'],
                'content': chapter_data['content'],
                'summary': chapter_data.get('summary', ''),
                'word_count': chapter_data['word_count'],
                'language': language,
                'writing_style': writing_style,
                'is_draft': True,
                'order_key': chapter_data.get('order_key')  # Add order_key for flexible ordering
            }
        )

        # Set act association
        logger.info(f"Setting act association for chapter {chapter.chapter_number} to act {act_id}")
        chapter.act_id = act_id
        chapter.save(update_fields=['act_id'])

        # Reorder all chapters by act to ensure proper sequencing
        WritingService.reorder_chapters_by_act(project)

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
                # Removed 'premise' - deprecated field
                # 'themes' removed - field removed in migration 0023
                'conflict': project.plot.conflict  # More specific than premise
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


@shared_task(bind=True, max_retries=10)
def poll_video_generation(self, content_piece_id, task_id):
    """
    Poll Runway API for video generation completion and download video when ready.
    Polls every 60 seconds for up to 10 minutes (10 retries).

    Args:
        content_piece_id: ContentPiece model ID
        task_id: Runway API task ID
    """
    from .models import ContentPiece
    from .ai_client import RunwayVideoClient
    from django.core.files.base import ContentFile
    from django.utils import timezone
    import time

    logger.info("=" * 80)
    logger.info("=== CELERY TASK STARTED: poll_video_generation ===")
    logger.info(f"Content Piece ID: {content_piece_id}")
    logger.info(f"Runway Task ID: {task_id}")
    logger.info(f"Retry count: {self.request.retries}")
    logger.info("=" * 80)

    # Check if this is a mock/test task - exit immediately to avoid log spam
    if task_id == "mock-task-id-for-testing":
        logger.info("Mock task detected - skipping polling to avoid log spam")
        logger.info("When ready to test with real API, uncomment the API calls in ai_client.py")
        logger.info("=" * 80)
        return

    logger.info(f"Polling video generation: content_piece={content_piece_id}, task={task_id}")

    try:
        content_piece = ContentPiece.objects.get(id=content_piece_id)
        runway_client = RunwayVideoClient()

        # Check video status
        status_result = runway_client.check_video_status(task_id)

        logger.info(f"Video status: {status_result['status']}, progress: {status_result.get('progress', 0)*100:.1f}%")

        # Update status
        content_piece.video_status = status_result['status']
        content_piece.save()

        if status_result['status'] == 'completed' and status_result.get('video_url'):
            # Video is ready - download it
            logger.info(f"Video completed, downloading from: {status_result['video_url'][:100]}...")

            video_content = runway_client.download_video(status_result['video_url'])

            # Save video file
            filename = f"content_{content_piece.project.id}_{task_id[:8]}.mp4"
            content_piece.video_file.save(
                filename,
                ContentFile(video_content),
                save=False
            )
            content_piece.video_status = 'completed'
            content_piece.video_generated_at = timezone.now()
            content_piece.save()

            logger.info(f"Video saved successfully: {filename}")

            # Broadcast completion to WebSocket for real-time frontend update
            channel_layer = get_channel_layer()
            if channel_layer:
                try:
                    async_to_sync(channel_layer.group_send)(
                        f'project_{content_piece.project.id}',
                        {
                            'type': 'video_complete',
                            'video_url': content_piece.video_file.url,
                            'status': 'completed',
                            'job_id': task_id
                        }
                    )
                    logger.info(f"✅ WebSocket broadcast sent to project_{content_piece.project.id}")
                except Exception as e:
                    logger.warning(f"Failed to broadcast WebSocket message: {e}")

        elif status_result['status'] == 'failed':
            # Video generation failed
            error_msg = status_result.get('error', 'Unknown error')
            logger.error(f"Video generation failed: {error_msg}")
            content_piece.video_status = 'failed'
            content_piece.save()

        elif status_result['status'] in ['queued', 'processing']:
            # Still processing - retry in 60 seconds
            logger.info(f"Video still processing, retrying in 60 seconds...")
            raise self.retry(countdown=60)

    except ContentPiece.DoesNotExist:
        logger.error(f"ContentPiece {content_piece_id} not found")
        raise

    except Exception as exc:
        logger.error(f"Video polling task failed: {exc}", exc_info=True)

        # Update status to failed
        try:
            content_piece = ContentPiece.objects.get(id=content_piece_id)
            content_piece.video_status = 'failed'
            content_piece.save()
        except:
            pass

        # Retry if we haven't exhausted retries (max 10 retries = 10 minutes)
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying video poll, attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=exc, countdown=60)
        else:
            logger.error(f"Video poll task failed after {self.max_retries} retries (10 minutes)")
            raise
