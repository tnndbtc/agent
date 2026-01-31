"""API views for Novel Writing Agent."""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

logger = logging.getLogger(__name__)

from .models import (
    NovelProject, Plot, Act, Character, Setting,
    Chapter, Example, GenerationTask, APIPerformanceMetric,
    ScoreCategory, ScoreCategoryTranslation, ExampleScore,
    UserProfile, UserPrompt,
    SystemPolicy, AgentRole, WritingStyle, WritingTechnique
)
from .serializers import (
    NovelProjectSerializer, NovelProjectListSerializer,
    PlotSerializer, ActSerializer, CharacterSerializer, SettingSerializer,
    ChapterSerializer, ChapterListSerializer,
    ExampleSerializer, GenerationTaskSerializer,
    CreatePlotRequestSerializer,
    CreateCharacterRequestSerializer, WriteChapterRequestSerializer,
    EditRequestSerializer, ScoreRequestSerializer,
    ScoreCategorySerializer, ScoreCategoryTranslationSerializer, ExampleScoreSerializer,
    UserPromptSerializer, AIModificationRequestSerializer, AIModificationResponseSerializer,
    SystemPolicySerializer, AgentRoleSerializer,
    WritingStyleSerializer, WritingTechniqueSerializer
)
from .services import (
    PlotService, CharacterService,
    SettingService, WritingService,
    EditingService, ConsistencyService, ScoringService, ExportService,
    ProjectService, AIModificationService
)
from .prompt_assembly import get_language_name
from .tasks import write_chapter_task, score_novel_task
from .permissions import IsOwner
from .ai_client import generate_theme_from_idea


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
        # Auto-assign matching writing style based on content_type
        content_type = serializer.validated_data.get('content_type')
        default_style = serializer.validated_data.get('default_style')

        # Only auto-assign if no style was explicitly provided
        if not default_style and content_type:
            from .models import WritingStyle
            # Find the system style matching this content_type
            matching_style = WritingStyle.objects.filter(
                is_system=True,
                content_type=content_type
            ).first()

            if matching_style:
                serializer.validated_data['default_style'] = matching_style

        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def create_plot(self, request, pk=None):
        """Create full plot structure and auto-generate protagonist and antagonist."""
        project = self.get_object()
        serializer = CreatePlotRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get user's language preference
        user_language = getattr(request, 'LANGUAGE_CODE', 'en')

        logger.info("=" * 80)
        logger.info("CREATE PLOT API - INPUT PROMPT")
        logger.info(f"User: {request.user.username}, Project: {project.id}, Language: {user_language}")
        # logger.info(f"Input Data: {serializer.validated_data}")
        logger.info(f"CREATE PLOT API - INPUT DATA: {serializer.validated_data}")
        logger.info("=" * 80)

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

        # Get optional temperature and top_p from request
        temperature = request.data.get('temperature')
        top_p = request.data.get('top_p')

        # Convert to float if provided
        if temperature is not None:
            try:
                temperature = float(temperature)
            except (ValueError, TypeError):
                temperature = None

        if top_p is not None:
            try:
                top_p = float(top_p)
            except (ValueError, TypeError):
                top_p = None

        # Track API performance
        start_time = timezone.now()

        # Accumulate token usage from all AI calls
        total_tokens_used = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0
        }

        logger.info("-" * 80)
        logger.info("Calling PlotService.create_full_plot...")
        plot_data, plot_tokens = PlotService.create_full_plot(
            project,
            serializer.validated_data['idea_data'],
            user_language=user_language,
            temperature=temperature,
            top_p=top_p
        )
        logger.info("-" * 80)
        logger.info("CREATE PLOT API - RESPONSE")
        logger.info(f"Generated Plot Data: {plot_data}")
        logger.info("-" * 80)

        # Accumulate plot tokens
        if plot_tokens:
            total_tokens_used['prompt_tokens'] += plot_tokens.get('prompt_tokens', 0)
            total_tokens_used['completion_tokens'] += plot_tokens.get('completion_tokens', 0)
            total_tokens_used['total_tokens'] += plot_tokens.get('total_tokens', 0)
            logger.info(f"Plot generation tokens: {plot_tokens}")

        # Save idea to Idea model
        from .models import Idea
        Idea.objects.update_or_create(
            project=project,
            defaults={
                'idea_data': serializer.validated_data['idea_data'],
                'content_type': 'novel'
            }
        )

        # Save to database
        # Note: genre is now a ForeignKey to Genre model, not a text field
        # If project has a genre, copy it to the plot; otherwise leave as None
        defaults = {
            # Removed 'premise' - deprecated field that caused pollution
            # Removed 'themes' - no longer generating themes separately
            'conflict': plot_data.get('conflict', ''),
            'structure': plot_data.get('structure', ''),
            'arc': plot_data.get('arc', '')
        }

        plot, created = Plot.objects.update_or_create(
            project=project,
            defaults=defaults
        )

        # Save acts from structured data or parse from text as fallback
        from .models import Act
        acts_data = []

        # First, try to use structured acts from plot generation (new JSON format)
        if plot_data.get('acts'):
            acts_data = plot_data['acts']
            logger.info(f"Using {len(acts_data)} structured acts from plot generation response")
        # Fallback: parse acts from plot structure text (old format or if structured output failed)
        elif plot.structure:
            acts_data = PlotService.parse_acts(plot.structure)
            logger.info(f"Parsed {len(acts_data)} acts from plot structure text (fallback)")

        # Create act records if we have acts data
        if acts_data:
            # Delete old acts for this plot (in case of regeneration)
            plot.acts.all().delete()

            # Create new act records
            for act_data in acts_data:
                Act.objects.create(
                    plot=plot,
                    act_number=act_data['act_number'],
                    subject=act_data['subject'],
                    # percentage field removed in migration 0023
                    description=act_data['description']
                )
                logger.info(f"Created Act {act_data['act_number']}: {act_data['subject']}")
        else:
            logger.warning(f"No acts data available for plot {plot.id}")

        # Store plot in ChromaDB memory
        try:
            service = ProjectService(project)
            service.memory.store_plot({
                'title': project.title,  # Use project title instead of deprecated premise
                # Removed 'premise' key - deprecated field
                'conflict': plot.conflict,
                # Removed 'theme' key - themes no longer generated
                'arc': plot.arc,
                'structure': plot.structure
            })
            logger.info(f"Stored plot in ChromaDB memory for project {project.id}")
        except Exception as e:
            logger.warning(f"Failed to store plot in ChromaDB memory: {e}")

        # Check if characters were generated in the plot response
        characters_from_plot = plot_data.get('characters', [])
        protagonist_db = None
        antagonist_db = None

        if characters_from_plot:
            # Save characters from the plot response (single API call approach)
            logger.info(f"Found {len(characters_from_plot)} characters in plot response")
            for char_data in characters_from_plot:
                role = char_data.get('role', '').lower()
                if role == 'protagonist' and not protagonist_db:
                    protagonist_db = Character.objects.create(
                        project=project,
                        name=char_data.get('name', ''),
                        role='protagonist',
                        age=char_data.get('age', ''),
                        background=char_data.get('background', ''),
                        personality=char_data.get('personality', ''),
                        motivation=char_data.get('motivation', ''),
                        flaw=char_data.get('flaw', ''),
                        arc=char_data.get('arc', ''),
                        appearance=char_data.get('appearance', ''),
                        relationships=char_data.get('relationships', '')
                    )
                    logger.info(f"Created protagonist '{protagonist_db.name}' from plot response")
                elif role == 'antagonist' and not antagonist_db:
                    antagonist_db = Character.objects.create(
                        project=project,
                        name=char_data.get('name', ''),
                        role='antagonist',
                        age=char_data.get('age', ''),
                        background=char_data.get('background', ''),
                        personality=char_data.get('personality', ''),
                        motivation=char_data.get('motivation', ''),
                        flaw=char_data.get('flaw', ''),
                        arc=char_data.get('arc', ''),
                        appearance=char_data.get('appearance', ''),
                        relationships=char_data.get('relationships', '')
                    )
                    logger.info(f"Created antagonist '{antagonist_db.name}' from plot response")

        # If no characters in plot response, fall back to generating separately (backward compatibility)
        if not protagonist_db:
            logger.info("No characters in plot response, generating separately for backward compatibility")
            character_plot_data = {
                'title': project.title,  # Use project title instead of deprecated premise
                # Removed 'premise' key - deprecated field
                # Removed 'themes' key - themes no longer generated
                'conflict': plot.conflict  # More specific than premise
            }

            # Generate and save protagonist
            logger.info("-" * 80)
            logger.info("Generating protagonist character...")
            protagonist_options, protagonist_tokens = CharacterService.create_protagonists(
                project, character_plot_data, num_options=1, user_language=user_language
            )
            logger.info(f"Protagonist generated: {protagonist_options}")
            logger.info("-" * 80)
            # Accumulate protagonist tokens
            if protagonist_tokens:
                total_tokens_used['prompt_tokens'] += protagonist_tokens.get('prompt_tokens', 0)
                total_tokens_used['completion_tokens'] += protagonist_tokens.get('completion_tokens', 0)
                total_tokens_used['total_tokens'] += protagonist_tokens.get('total_tokens', 0)
                logger.info(f"Protagonist generation tokens: {protagonist_tokens}")

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

                # Store protagonist in ChromaDB memory
                try:
                    service = ProjectService(project)
                    service.memory.store_character({
                        'name': protagonist_db.name,
                        'age': protagonist_db.age,
                        'role': protagonist_db.role,
                        'personality': protagonist_db.personality,
                        'background': protagonist_db.background,
                        'appearance': protagonist_db.appearance,
                        'motivations': protagonist_db.motivation,
                        'flaw': protagonist_db.flaw,
                        'arc': protagonist_db.arc,
                        'relationships': protagonist_db.relationships
                    })
                    logger.info(f"Stored protagonist '{protagonist_db.name}' in ChromaDB memory for project {project.id}")
                except Exception as e:
                    logger.warning(f"Failed to store protagonist in ChromaDB memory: {e}")

        # Auto-generate antagonist character if protagonist exists but no antagonist yet
        if protagonist_db and not antagonist_db:
            protagonist_data_for_antagonist = {
                'name': protagonist_db.name,
                'background': protagonist_db.background,
                'personality': protagonist_db.personality,
                'goals': protagonist_db.motivation
            }

            logger.info("-" * 80)
            logger.info("Generating antagonist character...")
            antagonist_data, antagonist_tokens = CharacterService.create_antagonist(
                project, plot_data, protagonist_data_for_antagonist, user_language=user_language
            )
            logger.info(f"Antagonist generated: {antagonist_data}")
            logger.info("-" * 80)
            # Accumulate antagonist tokens
            if antagonist_tokens:
                total_tokens_used['prompt_tokens'] += antagonist_tokens.get('prompt_tokens', 0)
                total_tokens_used['completion_tokens'] += antagonist_tokens.get('completion_tokens', 0)
                total_tokens_used['total_tokens'] += antagonist_tokens.get('total_tokens', 0)
                logger.info(f"Antagonist generation tokens: {antagonist_tokens}")

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

                # Store antagonist in ChromaDB memory
                try:
                    service = ProjectService(project)
                    service.memory.store_character({
                        'name': antagonist_db.name,
                        'age': antagonist_db.age,
                        'role': antagonist_db.role,
                        'personality': antagonist_db.personality,
                        'background': antagonist_db.background,
                        'appearance': antagonist_db.appearance,
                        'motivations': antagonist_db.motivation,
                        'flaw': antagonist_db.flaw,
                        'arc': antagonist_db.arc,
                        'relationships': antagonist_db.relationships
                    })
                    logger.info(f"Stored antagonist '{antagonist_db.name}' in ChromaDB memory for project {project.id}")
                except Exception as e:
                    logger.warning(f"Failed to store antagonist in ChromaDB memory: {e}")

        # Save token usage to user profile
        if total_tokens_used and request.user.is_authenticated:
            try:
                profile, created = UserProfile.objects.get_or_create(user=request.user)
                profile.add_tokens(
                    prompt_tokens=total_tokens_used.get('prompt_tokens', 0),
                    completion_tokens=total_tokens_used.get('completion_tokens', 0),
                    total_tokens=total_tokens_used.get('total_tokens', 0)
                )
                logger.info(f"Saved create_plot tokens to user {request.user.username}: {total_tokens_used}")
            except Exception as e:
                logger.error(f"Failed to save create_plot tokens to user profile: {e}")

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
            'message': 'Plot and characters (protagonist and antagonist) created successfully',
            'token_usage': total_tokens_used
        }
        if protagonist_db:
            response_data['protagonist'] = CharacterSerializer(protagonist_db).data
        if antagonist_db:
            response_data['antagonist'] = CharacterSerializer(antagonist_db).data

        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='generate_content')
    def generate_content(self, request, pk=None):
        """Generate complete content for poem/essay/sketch/article (one-shot generation)."""
        project = self.get_object()

        # Only allow for non-novel content types
        if project.content_type == 'novel':
            return Response(
                {'error': 'Use create_plot and write_chapter for novel projects'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get user's language preference
        user_language = getattr(request, 'LANGUAGE_CODE', 'en')

        logger.info("=" * 80)
        logger.info("GENERATE CONTENT API - INPUT")
        logger.info(f"User: {request.user.username}, Project: {project.id}")
        logger.info(f"Content Type: {project.content_type}, Language: {user_language}")
        logger.info(f"Input Data: {request.data}")
        logger.info("=" * 80)

        # Get idea data from request
        idea_data = request.data.get('idea_data', {})

        # Get optional temperature and top_p from request
        temperature = request.data.get('temperature')
        top_p = request.data.get('top_p')

        # Convert to float if provided
        if temperature is not None:
            try:
                temperature = float(temperature)
            except (ValueError, TypeError):
                temperature = None

        if top_p is not None:
            try:
                top_p = float(top_p)
            except (ValueError, TypeError):
                top_p = None

        # Track API performance
        start_time = timezone.now()

        try:
            # Generate content using ContentGenerationService
            from .services import ContentGenerationService
            content_dict, token_usage = ContentGenerationService.generate_content(
                project=project,
                idea_data=idea_data,
                user_language=user_language,
                temperature=temperature,
                top_p=top_p
            )

            logger.info("-" * 80)
            logger.info("GENERATE CONTENT API - RESPONSE")
            logger.info(f"Generated Content: title={content_dict.get('title')}, words={content_dict.get('word_count')}")
            logger.info(f"Token Usage: {token_usage}")
            logger.info("-" * 80)

            # Save idea to Idea model
            from .models import Idea
            Idea.objects.update_or_create(
                project=project,
                defaults={
                    'idea_data': idea_data,
                    'content_type': project.content_type
                }
            )

            # Save to ContentPiece model
            from .models import ContentPiece
            content_piece, created = ContentPiece.objects.update_or_create(
                project=project,
                defaults={
                    'title': content_dict.get('title', ''),
                    'content': content_dict.get('content', ''),
                    'word_count': content_dict.get('word_count', 0),
                    'structure_template_id': content_dict.get('structure_template_id'),
                    'sections_data': content_dict.get('sections_data', {}),
                    'generation_temperature': temperature,
                    'generation_top_p': top_p
                }
            )

            # Update project word count
            project.total_word_count = content_dict.get('word_count', 0)
            project.save()

            # Track tokens for user
            if token_usage and request.user:
                from .models import UserProfile
                profile, _ = UserProfile.objects.get_or_create(user=request.user)
                profile.add_tokens(**token_usage)

            # Record API performance
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()
            from .models import APIPerformanceMetric
            APIPerformanceMetric.objects.create(
                api_type='content_generation',
                duration_seconds=duration,
                success=True
            )

            logger.info(f"Content generation completed in {duration:.2f}s")

            # Serialize response
            from .serializers import ContentPieceSerializer
            response_data = {
                'content_piece': ContentPieceSerializer(content_piece).data,
                'message': f'{project.get_content_type_display()} created successfully',
                'token_usage': token_usage
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            logger.error(f"Content generation error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in content generation: {str(e)}", exc_info=True)

            # Record failed API call
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()
            from .models import APIPerformanceMetric
            APIPerformanceMetric.objects.create(
                api_type='content_generation',
                duration_seconds=duration,
                success=False
            )

            return Response(
                {'error': 'An error occurred while generating content'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['patch'], url_path='content_piece')
    def update_content_piece(self, request, pk=None):
        """Update content piece (poem/essay/sketch/article) after AI modification or manual editing."""
        project = self.get_object()

        # Ensure project is not a novel (novels use chapters, not content pieces)
        if project.content_type == 'novel':
            return Response(
                {'error': 'Novels use chapters, not content pieces'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get content from request
        new_content = request.data.get('content')
        if not new_content:
            return Response(
                {'error': 'Content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if content piece exists
        if not hasattr(project, 'content_piece'):
            return Response(
                {'error': 'No content piece exists for this project'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update content piece
        content_piece = project.content_piece
        content_piece.content = new_content

        # Recalculate word count
        content_piece.word_count = len(new_content.split())
        content_piece.save()

        # Return updated content piece
        from .serializers import ContentPieceSerializer
        return Response({
            'message': 'Content updated successfully',
            'content_piece': ContentPieceSerializer(content_piece).data,
            'word_count': content_piece.word_count
        })

    @action(detail=True, methods=['get'], url_path='generation_params')
    def get_generation_params(self, request, pk=None):
        """Get generation parameters (temperature, top_p) from the last content generation."""
        project = self.get_object()

        # For non-novel projects, check ContentPiece
        if project.content_type != 'novel' and hasattr(project, 'content_piece'):
            content_piece = project.content_piece
            return Response({
                'generation_temperature': content_piece.generation_temperature,
                'generation_top_p': content_piece.generation_top_p
            })

        # Return None if no data available
        return Response({
            'generation_temperature': None,
            'generation_top_p': None
        })

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
            'title': project.title,  # Use project title instead of deprecated premise
            # Removed 'premise' key - deprecated field
            'themes': project.plot.themes,
            'conflict': project.plot.conflict  # More specific than premise
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
    def write_chapter(self, request, pk=None):
        """Write a chapter."""
        project = self.get_object()
        serializer = WriteChapterRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Convert UUID to string for JSON serialization
        validated_data = serializer.validated_data.copy()
        act_id = validated_data.get('act_id')

        # Validate act exists
        try:
            act = Act.objects.get(
                id=act_id,
                plot__project=project
            )
            logger.info(f"Found Act: {act.id} - Subject: {act.subject} for chapter creation")
        except Act.DoesNotExist:
            logger.error(f"Act {act_id} not found for project {project.id}")
            return Response({
                'error': f'Act {act_id} not found or does not belong to this project'
            }, status=status.HTTP_404_NOT_FOUND)

        # Convert example_id UUID to string for JSON serialization (if present)
        if 'example_id' in validated_data and validated_data['example_id'] is not None:
            validated_data['example_id'] = str(validated_data['example_id'])

        # If language not specified in request, use user's UI language preference
        if 'language' not in validated_data or not validated_data['language']:
            user_language_code = getattr(request, 'LANGUAGE_CODE', 'en')
            validated_data['language'] = get_language_name(user_language_code)

        # Log the API call
        logger.info(f"Write Chapter API called - User: {request.user.username}, Project: {project.id}, "
                   f"Act ID: {act_id}, Language: {validated_data.get('language')}, Input: {validated_data}")

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
        full_text += "=" * 80 + "\n\n"

        for chapter in novel_data['chapters']:
            full_text += f"Chapter {chapter['chapter_number']}: {chapter['title']}\n"
            full_text += "-" * 80 + "\n\n"
            full_text += chapter['content']
            full_text += "\n\n" + "=" * 80 + "\n\n"

        return Response({
            'title': project.title,
            'author': request.user.get_full_name() or request.user.username,
            'full_text': full_text,
            'total_word_count': project.total_word_count,
            'chapter_count': len(novel_data['chapters'])
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='update_plot')
    def update_plot(self, request, pk=None):
        """Update plot fields."""
        project = self.get_object()

        # Check if plot exists
        if not hasattr(project, 'plot'):
            return Response(
                {'error': 'No plot exists for this project'},
                status=status.HTTP_404_NOT_FOUND
            )

        plot = project.plot

        # Update allowed fields
        allowed_fields = ['themes', 'structure', 'conflict']  # Removed 'premise' - deprecated
        updated = False

        for field in allowed_fields:
            if field in request.data:
                setattr(plot, field, request.data[field])
                updated = True

        if updated:
            plot.save()
            logger.info(f"Updated plot for project {project.id}: {list(request.data.keys())}")
            return Response({'message': 'Plot updated successfully'}, status=status.HTTP_200_OK)

        return Response(
            {'error': 'No valid fields provided for update'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['patch'], url_path='update_character/(?P<character_id>[^/.]+)')
    def update_character(self, request, pk=None, character_id=None):
        """Update character fields."""
        project = self.get_object()

        # Get the character
        character = get_object_or_404(Character, id=character_id, project=project)

        # Update allowed fields
        allowed_fields = ['name', 'background', 'personality', 'motivation', 'relationships']
        updated = False

        for field in allowed_fields:
            if field in request.data:
                setattr(character, field, request.data[field])
                updated = True

        if updated:
            character.save()
            logger.info(f"Updated character {character.id} for project {project.id}: {list(request.data.keys())}")
            return Response(CharacterSerializer(character).data, status=status.HTTP_200_OK)

        return Response(
            {'error': 'No valid fields provided for update'},
            status=status.HTTP_400_BAD_REQUEST
        )


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
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['public', 'is_good', 'category']

    def get_queryset(self):
        """Return user's own examples and all public examples."""
        return Example.objects.filter(
            Q(public=True) | Q(user=self.request.user)
        ).select_related('user').prefetch_related(
            'scores__category__translations'
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Override create to add detailed error logging."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Example creation failed. Request data: {request.data}")
            logger.error(f"Validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['post'], url_path='generate-scores')
    def generate_scores(self, request):
        """Generate AI scores for example content."""
        content = request.data.get('content')
        category = request.data.get('category')  # Optional

        if not content:
            return Response(
                {'error': 'Content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get user's language preference
        user_language = getattr(request, 'LANGUAGE_CODE', 'en')

        # Create generation task
        task = GenerationTask.objects.create(
            project=None,  # Not project-specific
            user=request.user,
            task_type='example_scoring',
            input_data={
                'content': content,
                'category': category,
                'language': user_language
            }
        )

        # Start async task
        from .tasks import generate_example_scores_task
        generate_example_scores_task.delay(
            task_id=str(task.id),
            content=content,
            category=category,
            user_language=user_language
        )

        return Response({
            'task_id': str(task.id),
            'status': 'Task started'
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'], url_path='suggest-metadata')
    def suggest_metadata(self, request):
        """Suggest title, category, and locale for example content using OpenAI."""
        from .ai_client import LoggingOpenAIClient
        import json

        content = request.data.get('content', '')
        if not content:
            return Response(
                {'error': 'Content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get available choices
        category_choices = [choice[0] for choice in Example.CATEGORY_CHOICES]
        locale_choices = [choice[0] for choice in Example.LOCALE_CHOICES]

        try:
            ai_client = LoggingOpenAIClient()

            prompt = f"""Analyze the following writing example and suggest appropriate metadata.

Content:
{content[:1000]}

Please suggest:
1. A short one-line title (max 100 characters)
2. Category - choose EXACTLY ONE from this list: {', '.join(category_choices)}
3. Locale/Language - choose EXACTLY ONE from this list: {', '.join(locale_choices)}

IMPORTANT: You must respond with ONLY a valid JSON object in this exact format, with no additional text before or after and no markdown formatting:
{{
    "title": "your suggested title here",
    "category": "one of the categories from the list",
    "locale": "one of the locales from the list"
}}
"""

            messages = [
                {"role": "system", "content": "You are a metadata suggestion assistant for writing examples."},
                {"role": "user", "content": prompt}
            ]

            # Use chat_completion_with_json for automatic JSON parsing and token extraction
            suggestions, token_usage = ai_client.chat_completion_with_json(
                messages=messages,
                model="gpt-4o-mini",
                temperature=0.3
            )

            # Log token usage in web container
            logger.info(f"suggest_metadata - Token usage: {token_usage}")

            # Save token usage to user profile
            if token_usage and request.user.is_authenticated:
                try:
                    profile, created = UserProfile.objects.get_or_create(user=request.user)
                    profile.add_tokens(
                        prompt_tokens=token_usage.get('prompt_tokens', 0),
                        completion_tokens=token_usage.get('completion_tokens', 0),
                        total_tokens=token_usage.get('total_tokens', 0)
                    )
                    logger.info(f"suggest_metadata - Saved tokens to user {request.user.username}: {token_usage}")
                except Exception as e:
                    logger.error(f"suggest_metadata - Failed to save tokens to user profile: {e}")

            # Validate and clean suggestions with case-insensitive matching
            suggested_category = suggestions.get('category', '')
            validated_category = ''
            if suggested_category:
                # Case-insensitive lookup
                suggested_lower = suggested_category.lower()
                for choice in category_choices:
                    if choice.lower() == suggested_lower:
                        validated_category = choice  # Use the canonical lowercase value
                        break

            suggested_locale = suggestions.get('locale', 'English')
            validated_locale = 'English'
            if suggested_locale:
                # Case-insensitive lookup
                suggested_lower = suggested_locale.lower()
                for choice in locale_choices:
                    if choice.lower() == suggested_lower:
                        validated_locale = choice  # Use the canonical value
                        break

            result = {
                'title': suggestions.get('title', '')[:200],  # Max 200 chars
                'category': validated_category,
                'locale': validated_locale,
                'token_usage': token_usage
            }

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error suggesting metadata: {str(e)}")
            return Response(
                {'error': f'Failed to generate suggestions: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='scores')
    def create_score(self, request, pk=None):
        """Create a score for this example."""
        example = self.get_object()

        # Verify the user owns this example or it's public
        if example.user != request.user and not example.public:
            return Response(
                {'error': 'You do not have permission to score this example'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ExampleScoreSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(example=example)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ExampleScoreViewSet(viewsets.ModelViewSet):
    """ViewSet for ExampleScore model."""

    permission_classes = [IsAuthenticated]
    serializer_class = ExampleScoreSerializer

    def get_queryset(self):
        """Return scores for examples the user can access."""
        return ExampleScore.objects.filter(
            Q(example__public=True) | Q(example__user=self.request.user)
        ).select_related('example', 'category')

    def perform_create(self, serializer):
        """Create score - example must be set in request data."""
        serializer.save()

    def perform_update(self, serializer):
        """Update score - verify permissions."""
        score = self.get_object()
        if score.example.user != self.request.user:
            raise PermissionError("You don't have permission to update this score")
        serializer.save()


class ScoreCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for ScoreCategory model."""

    permission_classes = [IsAuthenticated]
    serializer_class = ScoreCategorySerializer

    def get_queryset(self):
        """Return accessible categories (public + user's private)."""
        return ScoreCategory.objects.filter(
            Q(public=True) | Q(created_by=self.request.user)
        ).prefetch_related('translations').distinct()

    def perform_create(self, serializer):
        """Create category with current user as creator."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Only allow users to update their own non-system categories."""
        instance = self.get_object()
        if instance.is_system:
            raise serializers.ValidationError("Cannot modify system categories")
        if instance.created_by != self.request.user:
            raise serializers.ValidationError("Cannot modify another user's category")
        serializer.save()

    def perform_destroy(self, instance):
        """Only allow users to delete their own non-system categories."""
        if instance.is_system:
            raise serializers.ValidationError("Cannot delete system categories")
        if instance.created_by != self.request.user:
            raise serializers.ValidationError("Cannot delete another user's category")
        instance.delete()


class ActViewSet(viewsets.ModelViewSet):
    """ViewSet for Act model."""

    permission_classes = [IsAuthenticated]
    serializer_class = ActSerializer

    def get_queryset(self):
        """Return acts for plots that belong to user's projects."""
        return Act.objects.filter(plot__project__user=self.request.user)

    def perform_update(self, serializer):
        """Only allow users to update acts from their own projects."""
        instance = self.get_object()
        if instance.plot.project.user != self.request.user:
            raise serializers.ValidationError("Cannot modify acts from another user's project")
        serializer.save()


class UserPromptViewSet(viewsets.ModelViewSet):
    """ViewSet for UserPrompt model - managing saved prompts."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserPromptSerializer

    def get_queryset(self):
        """Return prompts belonging to the current user."""
        return UserPrompt.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Create prompt with current user as owner."""
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """Only allow users to update their own prompts."""
        instance = self.get_object()
        if instance.user != self.request.user:
            raise serializers.ValidationError("Cannot modify another user's prompt")
        serializer.save()

    def perform_destroy(self, instance):
        """Only allow users to delete their own prompts."""
        if instance.user != self.request.user:
            raise serializers.ValidationError("Cannot delete another user's prompt")
        instance.delete()


class AIModificationViewSet(viewsets.ViewSet):
    """ViewSet for AI text modification operations."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='modify-text')
    def modify_text(self, request):
        """
        Modify selected text using AI with a custom prompt.

        Expected POST data:
        {
            "original_text": "The text to modify",
            "user_prompt": "Make it more dramatic",
            "content_type": "character",  // optional: plot, act, character, chapter, text
            "save_prompt": false,  // optional: whether to save the prompt
            "prompt_name": "Make dramatic",  // required if save_prompt=true
            "saved_prompt_id": "uuid"  // optional: use a saved prompt instead of user_prompt
        }
        """
        serializer = AIModificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user = request.user

        # Handle saved prompt usage
        if data.get('saved_prompt_id'):
            try:
                saved_prompt = UserPrompt.objects.get(
                    id=data['saved_prompt_id'],
                    user=user
                )
                user_prompt = saved_prompt.prompt_text
                saved_prompt.increment_usage()
                logger.info(f"Using saved prompt '{saved_prompt.name}' (ID: {saved_prompt.id})")
            except UserPrompt.DoesNotExist:
                return Response(
                    {'error': 'Saved prompt not found or does not belong to you'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            user_prompt = data['user_prompt']

        # Call AI modification service
        try:
            result = AIModificationService.modify_text_selection(
                user=user,
                original_text=data['original_text'],
                user_prompt=user_prompt,
                content_type=data.get('content_type', 'text')
            )

            # Save prompt if requested
            saved_prompt_obj = None
            if data.get('save_prompt') and data.get('prompt_name'):
                # Check if a prompt with this name already exists
                existing = UserPrompt.objects.filter(
                    user=user,
                    name=data['prompt_name']
                ).first()

                if existing:
                    # Update existing prompt
                    existing.prompt_text = user_prompt
                    existing.save()
                    saved_prompt_obj = existing
                    logger.info(f"Updated existing prompt '{data['prompt_name']}'")
                else:
                    # Create new prompt
                    saved_prompt_obj = UserPrompt.objects.create(
                        user=user,
                        name=data['prompt_name'],
                        prompt_text=user_prompt
                    )
                    logger.info(f"Created new saved prompt '{data['prompt_name']}'")

            # Add saved prompt to response if created
            if saved_prompt_obj:
                result['saved_prompt'] = UserPromptSerializer(saved_prompt_obj).data

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in AI modification: {e}", exc_info=True)
            return Response(
                {'error': f'Failed to modify text: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='preset-prompts')
    def preset_prompts(self, request):
        """Get preset prompts for quick modifications."""
        presets = [
            {'id': 'dramatic', 'name': 'Make more dramatic', 'prompt': 'Rewrite this text to be more dramatic and emotionally intense while maintaining the core meaning.'},
            {'id': 'simplify', 'name': 'Simplify language', 'prompt': 'Simplify the language in this text to make it clearer and easier to understand.'},
            {'id': 'detail', 'name': 'Add more detail', 'prompt': 'Expand this text with more vivid details and sensory descriptions.'},
            {'id': 'shorter', 'name': 'Make it shorter', 'prompt': 'Condense this text to be more concise while keeping the essential information.'},
            {'id': 'clarity', 'name': 'Improve clarity', 'prompt': 'Improve the clarity and readability of this text without changing its meaning.'},
        ]
        return Response(presets, status=status.HTTP_200_OK)


# ========================================
# Prompt Architecture ViewSets (5-Layer)
# ========================================

class SystemPolicyViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for SystemPolicy model - read-only access to system policies."""

    permission_classes = [IsAuthenticated]
    serializer_class = SystemPolicySerializer

    def get_queryset(self):
        """Return all active system policies with translations."""
        return SystemPolicy.objects.filter(is_active=True).prefetch_related('translations').order_by('priority', 'name_key')


class AgentRoleViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AgentRole model - read-only access to agent roles."""

    permission_classes = [IsAuthenticated]
    serializer_class = AgentRoleSerializer

    def get_queryset(self):
        """Return all active agent roles with translations."""
        return AgentRole.objects.filter(is_active=True).prefetch_related('translations').order_by('name_key')


class WritingStyleViewSet(viewsets.ModelViewSet):
    """ViewSet for WritingStyle model."""

    permission_classes = [IsAuthenticated]
    serializer_class = WritingStyleSerializer
    pagination_class = None

    def get_queryset(self):
        """Return accessible styles (system styles + public styles + user's private styles).

        Can be filtered by content_type query parameter to show only styles
        for that content type + generic styles (content_type=null).
        """
        queryset = WritingStyle.objects.filter(
            Q(is_system=True) | Q(public=True) | Q(created_by=self.request.user)
        )

        # Filter by content_type if provided
        content_type = self.request.query_params.get('content_type', None)
        if content_type:
            # Show styles matching this content_type OR generic styles (null)
            queryset = queryset.filter(
                Q(content_type=content_type) | Q(content_type__isnull=True)
            )

        return queryset.prefetch_related('translations').distinct()

    def perform_create(self, serializer):
        """Create style with current user as creator."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Only allow users to update their own non-system styles."""
        instance = self.get_object()
        if instance.is_system:
            raise serializers.ValidationError("Cannot modify system styles")
        if instance.created_by != self.request.user:
            raise serializers.ValidationError("Cannot modify another user's style")
        serializer.save()

    def perform_destroy(self, instance):
        """Only allow users to delete their own non-system styles."""
        if instance.is_system:
            raise serializers.ValidationError("Cannot delete system styles")
        if instance.created_by != self.request.user:
            raise serializers.ValidationError("Cannot delete another user's style")
        instance.delete()


class WritingTechniqueViewSet(viewsets.ModelViewSet):
    """ViewSet for WritingTechnique model."""

    permission_classes = [IsAuthenticated]
    serializer_class = WritingTechniqueSerializer
    pagination_class = None

    def get_queryset(self):
        """Return accessible techniques (system techniques + public techniques + user's private techniques)."""
        return WritingTechnique.objects.filter(
            Q(is_system=True) | Q(public=True) | Q(created_by=self.request.user)
        ).prefetch_related('translations').distinct()

    def perform_create(self, serializer):
        """Create technique with current user as creator."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Only allow users to update their own non-system techniques."""
        instance = self.get_object()
        if instance.is_system:
            raise serializers.ValidationError("Cannot modify system techniques")
        if instance.created_by != self.request.user:
            raise serializers.ValidationError("Cannot modify another user's technique")
        serializer.save()

    def perform_destroy(self, instance):
        """Only allow users to delete their own non-system techniques."""
        if instance.is_system:
            raise serializers.ValidationError("Cannot delete system techniques")
        if instance.created_by != self.request.user:
            raise serializers.ValidationError("Cannot delete another user's technique")
        instance.delete()
