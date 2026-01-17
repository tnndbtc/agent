"""API views for Novel Writing Agent."""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

logger = logging.getLogger(__name__)

from .models import (
    NovelProject, Plot, Character, Setting,
    ChapterOutline, Chapter, Example, GenerationTask, APIPerformanceMetric
)
from .serializers import (
    NovelProjectSerializer, NovelProjectListSerializer,
    PlotSerializer, CharacterSerializer, SettingSerializer,
    ChapterOutlineSerializer, ChapterSerializer, ChapterListSerializer,
    ExampleSerializer, GenerationTaskSerializer,
    BrainstormRequestSerializer, CreatePlotRequestSerializer,
    CreateCharacterRequestSerializer, WriteChapterRequestSerializer,
    EditRequestSerializer, ScoreRequestSerializer
)
from .services import (
    BrainstormService, PlotService, CharacterService,
    SettingService, OutlineService, WritingService,
    EditingService, ConsistencyService, ScoringService, ExportService
)
from .tasks import brainstorm_ideas_task, write_chapter_task, create_outline_task, score_novel_task
from .permissions import IsOwner


class NovelProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for NovelProject model."""

    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = NovelProjectSerializer

    def get_queryset(self):
        return NovelProject.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return NovelProjectListSerializer
        return NovelProjectSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def brainstorm(self, request, pk=None):
        """Generate plot ideas."""
        project = self.get_object()
        serializer = BrainstormRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get user's language preference
        user_language = getattr(request, 'LANGUAGE_CODE', 'en')

        logger.info(f"Brainstorm API called - User: {request.user.username}, Project: {project.id}, "
                   f"Language: {user_language}, Input: {serializer.validated_data}")

        # Create generation task
        task = GenerationTask.objects.create(
            project=project,
            user=request.user,
            task_type='brainstorm',
            input_data=serializer.validated_data
        )

        # Start async task
        brainstorm_ideas_task.delay(
            task_id=str(task.id),
            project_id=str(project.id),
            user_language=user_language,
            **serializer.validated_data
        )

        return Response({
            'task_id': task.id,
            'status': 'Task started. Check status at /api/tasks/{id}/'
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'], url_path='save_manual_idea')
    def save_manual_idea(self, request, pk=None):
        """Save a manually entered idea."""
        project = self.get_object()
        idea_data = request.data.get('idea')

        if not idea_data or not idea_data.get('premise'):
            return Response(
                {'error': 'Idea premise is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create a completed generation task with the manual idea
        from django.utils import timezone
        task = GenerationTask.objects.create(
            project=project,
            user=request.user,
            task_type='brainstorm',
            status='completed',
            input_data={'manual': True},
            result_data={'ideas': [idea_data]},
            completed_at=timezone.now()
        )

        return Response({
            'message': 'Idea saved successfully',
            'task_id': task.id
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def create_plot(self, request, pk=None):
        """Create full plot structure and auto-generate protagonist and antagonist."""
        project = self.get_object()
        serializer = CreatePlotRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get user's language preference
        user_language = getattr(request, 'LANGUAGE_CODE', 'en')

        logger.info(f"Create Plot API called - User: {request.user.username}, Project: {project.id}, "
                   f"Language: {user_language}, Input: {serializer.validated_data}")

        # Delete old plot and characters first
        try:
            if hasattr(project, 'plot'):
                project.plot.delete()
                logger.info(f"Deleted old plot for project {project.id}")
        except Exception as e:
            logger.warning(f"Error deleting old plot: {e}")

        # Delete all existing characters for this project
        deleted_count = project.characters.all().delete()[0]
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} old characters for project {project.id}")

        # Track API performance
        start_time = timezone.now()

        plot_data = PlotService.create_full_plot(project, serializer.validated_data['idea_data'], user_language=user_language)

        # Save to database
        plot, created = Plot.objects.update_or_create(
            project=project,
            defaults={
                'premise': plot_data.get('premise', ''),
                'genre': plot_data.get('genre', ''),
                'themes': plot_data.get('themes', ''),
                'conflict': plot_data.get('conflict', ''),
                'structure': plot_data.get('structure', ''),
                'arc': plot_data.get('arc', '')
            }
        )

        # Auto-generate protagonist character
        character_plot_data = {
            'title': plot.premise,
            'genre': plot.genre,
            'premise': plot.premise,
            'themes': plot.themes
        }

        # Generate and save protagonist
        protagonist_options = CharacterService.create_protagonists(
            project, character_plot_data, num_options=1, user_language=user_language
        )

        protagonist_db = None
        if protagonist_options:
            protagonist_data = protagonist_options[0]
            protagonist_db = Character.objects.create(
                project=project,
                name=protagonist_data.get('name', ''),
                role='protagonist',
                age=protagonist_data.get('age', ''),
                background=protagonist_data.get('background', ''),
                personality=protagonist_data.get('personality', ''),
                motivation=protagonist_data.get('motivation') or protagonist_data.get('goals', ''),
                flaw=protagonist_data.get('flaw', ''),
                arc=protagonist_data.get('arc', ''),
                appearance=protagonist_data.get('appearance') or protagonist_data.get('physical_description', ''),
                relationships=protagonist_data.get('relationships', '')
            )

        # Auto-generate antagonist character
        antagonist_db = None
        if protagonist_db:
            protagonist_data_for_antagonist = {
                'name': protagonist_db.name,
                'background': protagonist_db.background,
                'personality': protagonist_db.personality,
                'goals': protagonist_db.motivation
            }

            antagonist_data = CharacterService.create_antagonist(
                project, character_plot_data, protagonist_data_for_antagonist, user_language=user_language
            )

            if antagonist_data:
                antagonist_db = Character.objects.create(
                    project=project,
                    name=antagonist_data.get('name', ''),
                    role='antagonist',
                    age=antagonist_data.get('age', ''),
                    background=antagonist_data.get('background', ''),
                    personality=antagonist_data.get('personality', ''),
                    motivation=antagonist_data.get('motivation') or antagonist_data.get('goals', ''),
                    flaw=antagonist_data.get('flaw', ''),
                    arc=antagonist_data.get('arc', ''),
                    appearance=antagonist_data.get('appearance') or antagonist_data.get('physical_description', ''),
                    relationships=antagonist_data.get('relationships', '')
                )

        # Track API performance
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        APIPerformanceMetric.objects.create(
            api_type='plot',
            duration_seconds=duration,
            input_params={},
            success=True
        )

        response_data = {
            'plot': PlotSerializer(plot).data,
            'message': 'Plot and characters (protagonist and antagonist) created successfully'
        }
        if protagonist_db:
            response_data['protagonist'] = CharacterSerializer(protagonist_db).data
        if antagonist_db:
            response_data['antagonist'] = CharacterSerializer(antagonist_db).data

        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def create_characters(self, request, pk=None):
        """Create characters."""
        project = self.get_object()
        serializer = CreateCharacterRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get user's language preference
        user_language = getattr(request, 'LANGUAGE_CODE', 'en')

        logger.info(f"Create Characters API called - User: {request.user.username}, Project: {project.id}, "
                   f"Language: {user_language}, Input: {serializer.validated_data}")

        if not hasattr(project, 'plot'):
            return Response(
                {'error': 'Project must have a plot before creating characters'},
                status=status.HTTP_400_BAD_REQUEST
            )

        plot_data = {
            'title': project.plot.premise,
            'genre': project.plot.genre,
            'premise': project.plot.premise,
            'themes': project.plot.themes
        }

        char_type = serializer.validated_data['character_type']
        num_options = serializer.validated_data.get('num_options', 3)

        if char_type == 'protagonist':
            characters_data = CharacterService.create_protagonists(
                project, plot_data, num_options, user_language=user_language
            )
        elif char_type == 'antagonist':
            # For antagonist, we need protagonist data - use first protagonist if exists
            protagonist_data = {}
            protagonists = project.characters.filter(role='protagonist').first()
            if protagonists:
                protagonist_data = {
                    'name': protagonists.name,
                    'background': protagonists.background,
                    'personality': protagonists.personality,
                    'motivation': protagonists.motivation
                }

            # Create single antagonist and wrap in list
            antagonist = CharacterService.create_antagonist(
                project, plot_data, protagonist_data, user_language=user_language
            )
            characters_data = [antagonist]
        elif char_type == 'supporting':
            # For supporting, use protagonist if exists
            protagonist_data = {}
            protagonists = project.characters.filter(role='protagonist').first()
            if protagonists:
                protagonist_data = {
                    'name': protagonists.name,
                    'background': protagonists.background,
                    'personality': protagonists.personality,
                    'motivation': protagonists.motivation
                }

            # Create supporting characters with common roles
            roles = ['sidekick', 'mentor', 'love_interest'][:num_options]
            supporting = CharacterService.create_supporting(
                project, plot_data, protagonist_data, roles, user_language=user_language
            )
            characters_data = supporting if isinstance(supporting, list) else [supporting]
        else:
            return Response(
                {'error': f'Unknown character type: {char_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({'characters': characters_data}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def save_character(self, request, pk=None):
        """Save a character to the project."""
        project = self.get_object()
        character_data = request.data.get('character')

        if not character_data:
            return Response(
                {'error': 'Character data is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the character
        character = Character.objects.create(
            project=project,
            name=character_data.get('name', ''),
            role=character_data.get('role', 'supporting'),
            age=character_data.get('age', ''),
            background=character_data.get('background', ''),
            personality=character_data.get('personality', ''),
            motivation=character_data.get('motivation') or character_data.get('goals', ''),
            flaw=character_data.get('flaw', ''),
            arc=character_data.get('arc', ''),
            appearance=character_data.get('appearance') or character_data.get('physical_description', ''),
            relationships=character_data.get('relationships', '')
        )

        return Response(CharacterSerializer(character).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def create_outline(self, request, pk=None):
        """Create chapter outline."""
        project = self.get_object()

        # Get user's language preference
        user_language = getattr(request, 'LANGUAGE_CODE', 'en')

        # Log raw request data for debugging
        logger.info(f"Create Outline API called - User: {request.user.username}, Project: {project.id}, "
                   f"Language: {user_language}, Raw request.data: {request.data}")

        num_chapters = int(request.data.get('num_chapters', 1))  # Default to 1 chapter if not specified

        logger.info(f"Create Outline - num_chapters parsed: {num_chapters}")

        # Create generation task
        task = GenerationTask.objects.create(
            project=project,
            user=request.user,
            task_type='outline',
            input_data={'num_chapters': num_chapters}
        )

        # Start async task
        create_outline_task.delay(
            task_id=str(task.id),
            project_id=str(project.id),
            num_chapters=num_chapters,
            user_language=user_language
        )

        return Response({
            'task_id': task.id,
            'status': 'Task started. Check status at /api/tasks/{id}/'
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'])
    def regenerate_chapter_outline(self, request, pk=None):
        """Regenerate a single chapter outline."""
        project = self.get_object()
        chapter_number = int(request.data.get('chapter_number')) if request.data.get('chapter_number') else None

        if not chapter_number:
            return Response(
                {'error': 'chapter_number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create generation task
        task = GenerationTask.objects.create(
            project=project,
            user=request.user,
            task_type='outline_single',
            input_data={'chapter_number': chapter_number}
        )

        # Get user's language preference
        user_language = getattr(request, 'LANGUAGE_CODE', 'en')

        # Start async task
        from .tasks import regenerate_single_outline_task
        regenerate_single_outline_task.delay(
            task_id=str(task.id),
            project_id=str(project.id),
            chapter_number=chapter_number,
            user_language=user_language
        )

        return Response({
            'task_id': task.id,
            'status': 'Task started. Check status at /api/tasks/{id}/'
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['delete'], url_path='delete_outline/(?P<outline_id>[^/.]+)')
    def delete_outline(self, request, pk=None, outline_id=None):
        """Delete a chapter outline and renumber subsequent outlines."""
        from django.db import transaction

        project = self.get_object()
        outline = get_object_or_404(ChapterOutline, id=outline_id, project=project)
        deleted_number = outline.number

        with transaction.atomic():
            # Delete the outline
            outline.delete()

            # Renumber all subsequent outlines
            subsequent_outlines = ChapterOutline.objects.filter(
                project=project,
                number__gt=deleted_number
            ).order_by('number')

            for outline in subsequent_outlines:
                outline.number -= 1
                outline.save(update_fields=['number'])

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def write_chapter(self, request, pk=None):
        """Write a chapter."""
        project = self.get_object()
        serializer = WriteChapterRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Convert UUID to string for JSON serialization
        validated_data = serializer.validated_data.copy()
        chapter_outline_id = validated_data['chapter_outline_id']

        # Validate that the ChapterOutline exists and belongs to this project
        try:
            outline = ChapterOutline.objects.get(
                id=chapter_outline_id,
                project=project
            )
            logger.info(f"Found ChapterOutline: {outline.id} - Title: {outline.title}")
        except ChapterOutline.DoesNotExist:
            logger.error(f"ChapterOutline {chapter_outline_id} not found for project {project.id}")
            return Response({
                'error': f'Chapter outline {chapter_outline_id} not found or does not belong to this project'
            }, status=status.HTTP_404_NOT_FOUND)

        validated_data['chapter_outline_id'] = str(chapter_outline_id)

        # If language not specified in request, use user's UI language preference
        if 'language' not in validated_data or not validated_data['language']:
            from novels.services import get_language_name
            user_language_code = getattr(request, 'LANGUAGE_CODE', 'en')
            validated_data['language'] = get_language_name(user_language_code)

        logger.info(f"Write Chapter API called - User: {request.user.username}, Project: {project.id}, "
                   f"Outline: {outline.title}, Language: {validated_data.get('language')}, Input: {validated_data}")

        # Create generation task
        task = GenerationTask.objects.create(
            project=project,
            user=request.user,
            task_type='chapter',
            input_data=validated_data
        )

        # Start async task
        write_chapter_task.delay(
            task_id=str(task.id),
            project_id=str(project.id),
            **validated_data
        )

        return Response({
            'task_id': task.id,
            'status': 'Task started. Check status at /api/tasks/{id}/'
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'])
    def score(self, request, pk=None):
        """Score the novel."""
        project = self.get_object()

        # Create generation task
        task = GenerationTask.objects.create(
            project=project,
            user=request.user,
            task_type='score',
            input_data={}
        )

        # Start async task
        score_novel_task.delay(
            task_id=str(task.id),
            project_id=str(project.id)
        )

        return Response({
            'task_id': task.id,
            'status': 'Task started. Check status at /api/tasks/{id}/'
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """Export novel as downloadable file."""
        from django.http import FileResponse
        import os

        project = self.get_object()
        language = request.query_params.get('language', 'English')

        # Gather novel data
        novel_data = {
            'title': project.title,
            'genre': project.genre,
            'author': request.user.get_full_name() or request.user.username,
            'chapters': []
        }

        for chapter in project.chapters.all().order_by('chapter_number'):
            novel_data['chapters'].append({
                'chapter_number': chapter.chapter_number,
                'title': chapter.title,
                'content': chapter.content,
                'word_count': chapter.word_count
            })

        file_path = ExportService.export_novel(project, novel_data, language)

        # Return file as download
        if os.path.exists(file_path):
            response = FileResponse(
                open(file_path, 'rb'),
                content_type='text/plain',
                as_attachment=True,
                filename=f"{project.title.replace(' ', '_')}.txt"
            )
            return response
        else:
            return Response({
                'error': 'Export file not found'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='view_text')
    def view_text(self, request, pk=None):
        """View novel text online."""
        project = self.get_object()
        language = request.query_params.get('language', 'English')

        # Gather novel data
        novel_data = {
            'title': project.title,
            'genre': project.genre,
            'author': request.user.get_full_name() or request.user.username,
            'chapters': []
        }

        for chapter in project.chapters.all().order_by('chapter_number'):
            novel_data['chapters'].append({
                'chapter_number': chapter.chapter_number,
                'title': chapter.title,
                'content': chapter.content,
                'word_count': chapter.word_count
            })

        # Build full text
        full_text = f"{project.title}\n"
        full_text += f"by {request.user.get_full_name() or request.user.username}\n"
        full_text += f"Genre: {project.genre}\n"
        full_text += "=" * 80 + "\n\n"

        for chapter in novel_data['chapters']:
            full_text += f"Chapter {chapter['chapter_number']}: {chapter['title']}\n"
            full_text += "-" * 80 + "\n\n"
            full_text += chapter['content']
            full_text += "\n\n" + "=" * 80 + "\n\n"

        return Response({
            'title': project.title,
            'author': request.user.get_full_name() or request.user.username,
            'genre': project.genre,
            'full_text': full_text,
            'total_word_count': project.total_word_count,
            'chapter_count': len(novel_data['chapters'])
        }, status=status.HTTP_200_OK)


class ChapterViewSet(viewsets.ModelViewSet):
    """ViewSet for Chapter model."""

    permission_classes = [IsAuthenticated]
    serializer_class = ChapterSerializer

    def get_queryset(self):
        return Chapter.objects.filter(project__user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return ChapterListSerializer
        return ChapterSerializer

    def destroy(self, request, *args, **kwargs):
        """Delete a chapter and renumber subsequent chapters."""
        from django.db import transaction

        chapter = self.get_object()
        project = chapter.project
        deleted_number = chapter.chapter_number

        with transaction.atomic():
            # Delete the chapter
            response = super().destroy(request, *args, **kwargs)

            # Renumber all subsequent chapters
            subsequent_chapters = Chapter.objects.filter(
                project=project,
                chapter_number__gt=deleted_number
            ).order_by('chapter_number')

            for ch in subsequent_chapters:
                ch.chapter_number -= 1
                ch.save(update_fields=['chapter_number'])

        return response

    @action(detail=True, methods=['post'])
    def edit(self, request, pk=None):
        """Edit chapter content."""
        chapter = self.get_object()
        serializer = EditRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        edit_type = serializer.validated_data['edit_type']
        content = serializer.validated_data['content']

        if edit_type == 'style':
            result = EditingService.edit_for_style(
                chapter.project, content,
                serializer.validated_data.get('target_style', 'literary')
            )
        elif edit_type == 'grammar':
            result = EditingService.edit_for_grammar(chapter.project, content)
        else:
            return Response(
                {'error': 'Unsupported edit type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def consistency_check(self, request, pk=None):
        """Check chapter consistency."""
        chapter = self.get_object()

        result = ConsistencyService.check_chapter_consistency(
            chapter.project, chapter.content
        )

        return Response(result, status=status.HTTP_200_OK)


class GenerationTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for GenerationTask model."""

    permission_classes = [IsAuthenticated]
    serializer_class = GenerationTaskSerializer

    def get_queryset(self):
        return GenerationTask.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='performance-stats')
    def performance_stats(self, request):
        """Get average duration estimates for each API type."""
        from django.db.models import Avg, Count

        stats = {}
        for api_type, display_name in APIPerformanceMetric.API_TYPE_CHOICES:
            metrics = APIPerformanceMetric.objects.filter(
                api_type=api_type,
                success=True
            ).aggregate(
                avg_duration=Avg('duration_seconds'),
                count=Count('id')
            )

            stats[api_type] = {
                'display_name': display_name,
                'average_duration_seconds': round(metrics['avg_duration'] or 30.0, 2),
                'sample_size': metrics['count']
            }

        return Response(stats)


class ExampleViewSet(viewsets.ModelViewSet):
    """ViewSet for Example model."""

    permission_classes = [IsAuthenticated]
    serializer_class = ExampleSerializer

    def get_queryset(self):
        return Example.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
