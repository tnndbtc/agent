"""API views for Novel Writing Agent."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import (
    NovelProject, Plot, Character, Setting,
    ChapterOutline, Chapter, Example, GenerationTask
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
            **serializer.validated_data
        )

        return Response({
            'task_id': task.id,
            'status': 'Task started. Check status at /api/tasks/{id}/'
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'])
    def create_plot(self, request, pk=None):
        """Create full plot structure."""
        project = self.get_object()
        serializer = CreatePlotRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plot_data = PlotService.create_full_plot(project, serializer.validated_data['idea_data'])

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

        return Response(PlotSerializer(plot).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def create_characters(self, request, pk=None):
        """Create characters."""
        project = self.get_object()
        serializer = CreateCharacterRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

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
                project, plot_data, num_options
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
                    'goals': protagonists.goals
                }

            # Create single antagonist and wrap in list
            antagonist = CharacterService.create_antagonist(
                project, plot_data, protagonist_data
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
                    'goals': protagonists.goals
                }

            # Create supporting characters with common roles
            roles = ['sidekick', 'mentor', 'love_interest'][:num_options]
            supporting = CharacterService.create_supporting(
                project, plot_data, protagonist_data, roles
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
        num_chapters = request.data.get('num_chapters', 20)

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
            num_chapters=num_chapters
        )

        return Response({
            'task_id': task.id,
            'status': 'Task started. Check status at /api/tasks/{id}/'
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'])
    def regenerate_chapter_outline(self, request, pk=None):
        """Regenerate a single chapter outline."""
        project = self.get_object()
        chapter_number = request.data.get('chapter_number')

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

        # Start async task
        from .tasks import regenerate_single_outline_task
        regenerate_single_outline_task.delay(
            task_id=str(task.id),
            project_id=str(project.id),
            chapter_number=chapter_number
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
        validated_data['chapter_outline_id'] = str(validated_data['chapter_outline_id'])

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
        """Export novel."""
        project = self.get_object()
        language = request.query_params.get('language', 'English')

        # Gather novel data
        novel_data = {
            'title': project.title,
            'genre': project.genre,
            'author': request.user.get_full_name() or request.user.username,
            'chapters': []
        }

        for chapter in project.chapters.all():
            novel_data['chapters'].append({
                'chapter_number': chapter.chapter_number,
                'title': chapter.title,
                'content': chapter.content,
                'word_count': chapter.word_count
            })

        file_path = ExportService.export_novel(project, novel_data, language)

        return Response({
            'file_path': file_path,
            'message': 'Novel exported successfully'
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


class ExampleViewSet(viewsets.ModelViewSet):
    """ViewSet for Example model."""

    permission_classes = [IsAuthenticated]
    serializer_class = ExampleSerializer

    def get_queryset(self):
        return Example.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
