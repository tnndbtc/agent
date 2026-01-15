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

        if char_type == 'protagonist':
            characters_data = CharacterService.create_protagonists(
                project, plot_data, serializer.validated_data.get('num_options', 3)
            )
        else:
            return Response(
                {'error': 'Only protagonist creation supported via API. Use service methods for others.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({'characters': characters_data}, status=status.HTTP_200_OK)

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
    def write_chapter(self, request, pk=None):
        """Write a chapter."""
        project = self.get_object()
        serializer = WriteChapterRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create generation task
        task = GenerationTask.objects.create(
            project=project,
            user=request.user,
            task_type='chapter',
            input_data=serializer.validated_data
        )

        # Start async task
        write_chapter_task.delay(
            task_id=str(task.id),
            project_id=str(project.id),
            **serializer.validated_data
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
