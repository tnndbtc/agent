"""
Pytest configuration and fixtures for novel_web integration tests.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework.test import APIClient
from novels.models import NovelProject, Genre, GenreTranslation, ScoreCategory, ScoreCategoryTranslation, Example, ExampleScore
from novels.tests.mocks.openai_responses import get_mock_response_for_prompt


# ============================================================================
# Django and Database Configuration
# ============================================================================

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Configure Django settings for testing."""
    import tempfile
    from pathlib import Path

    # Use eager mode for Celery to run tasks synchronously
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True

    # Ensure we have a test OpenAI API key (won't be used due to mocking)
    if 'OPENAI_API_KEY' not in os.environ:
        os.environ['OPENAI_API_KEY'] = 'test-key-12345'

    settings.NOVEL_AGENT['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', 'test-key-12345')

    # Use temp directories for all file operations to avoid permission issues
    temp_vector_dir = Path(tempfile.mkdtemp(prefix='test_vector_stores_'))
    temp_examples_dir = Path(tempfile.mkdtemp(prefix='test_examples_'))
    temp_output_dir = Path(tempfile.mkdtemp(prefix='test_exports_'))

    settings.NOVEL_AGENT['VECTOR_STORE_DIR'] = temp_vector_dir
    settings.NOVEL_AGENT['EXAMPLES_DIR'] = temp_examples_dir
    settings.NOVEL_AGENT['OUTPUT_DIR'] = temp_output_dir


# ============================================================================
# User and Authentication Fixtures
# ============================================================================

@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def api_client():
    """Create a DRF API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, test_user):
    """Create an authenticated API client."""
    api_client.force_authenticate(user=test_user)
    return api_client


# ============================================================================
# Genre Fixtures
# ============================================================================

@pytest.fixture
def test_genres(db):
    """Create test genres with translations."""
    genres = {}

    # Create Fantasy genre
    fantasy_genre = Genre.objects.create(name_key='fantasy', public=True)
    GenreTranslation.objects.create(genre=fantasy_genre, language_code='en', name='Fantasy')
    GenreTranslation.objects.create(genre=fantasy_genre, language_code='zh-hans', name='奇幻')
    genres['fantasy'] = fantasy_genre

    # Create Science Fiction genre
    scifi_genre = Genre.objects.create(name_key='sci_fi', public=True)
    GenreTranslation.objects.create(genre=scifi_genre, language_code='en', name='Science Fiction')
    GenreTranslation.objects.create(genre=scifi_genre, language_code='zh-hans', name='科幻')
    genres['sci_fi'] = scifi_genre

    # Create Mystery genre
    mystery_genre = Genre.objects.create(name_key='mystery', public=True)
    GenreTranslation.objects.create(genre=mystery_genre, language_code='en', name='Mystery')
    GenreTranslation.objects.create(genre=mystery_genre, language_code='zh-hans', name='悬疑')
    genres['mystery'] = mystery_genre

    return genres


# ============================================================================
# ScoreCategory Fixtures
# ============================================================================

@pytest.fixture
def test_score_categories(db):
    """Create test score categories with translations."""
    categories = {}

    # Create Plot category
    plot_cat = ScoreCategory.objects.create(
        name='plot',
        public=True,
        is_system=True,
        default_weight=25,
        order=1
    )
    ScoreCategoryTranslation.objects.create(category=plot_cat, language_code='en', name='Plot')
    ScoreCategoryTranslation.objects.create(category=plot_cat, language_code='zh-hans', name='情节')
    categories['plot'] = plot_cat

    # Create Character Development category
    char_cat = ScoreCategory.objects.create(
        name='character_development',
        public=True,
        is_system=True,
        default_weight=20,
        order=2
    )
    ScoreCategoryTranslation.objects.create(category=char_cat, language_code='en', name='Character Development')
    ScoreCategoryTranslation.objects.create(category=char_cat, language_code='zh-hans', name='人物发展')
    categories['character_development'] = char_cat

    # Create Pacing category
    pacing_cat = ScoreCategory.objects.create(
        name='pacing',
        public=True,
        is_system=True,
        default_weight=20,
        order=3
    )
    ScoreCategoryTranslation.objects.create(category=pacing_cat, language_code='en', name='Pacing')
    ScoreCategoryTranslation.objects.create(category=pacing_cat, language_code='zh-hans', name='节奏')
    categories['pacing'] = pacing_cat

    # Create Dialogue category
    dialogue_cat = ScoreCategory.objects.create(
        name='dialogue',
        public=True,
        is_system=True,
        default_weight=15,
        order=4
    )
    ScoreCategoryTranslation.objects.create(category=dialogue_cat, language_code='en', name='Dialogue')
    ScoreCategoryTranslation.objects.create(category=dialogue_cat, language_code='zh-hans', name='对话')
    categories['dialogue'] = dialogue_cat

    # Create Description category
    desc_cat = ScoreCategory.objects.create(
        name='description',
        public=True,
        is_system=True,
        default_weight=20,
        order=5
    )
    ScoreCategoryTranslation.objects.create(category=desc_cat, language_code='en', name='Description')
    ScoreCategoryTranslation.objects.create(category=desc_cat, language_code='zh-hans', name='描写')
    categories['description'] = desc_cat

    return categories


# ============================================================================
# Example Fixtures
# ============================================================================

@pytest.fixture
def test_example(db, test_user, test_genres, test_score_categories):
    """Create a test example with scores."""
    # Create example
    example = Example.objects.create(
        user=test_user,
        genre=test_genres['fantasy'],
        public=True,
        is_good=True,
        category='opening',
        title='Excellent Fantasy Opening',
        locale='English',
        content='''The wind howled through the ancient forest, carrying with it whispers of forgotten magic.
Aria pressed her back against the gnarled oak, her breath coming in short gasps as she clutched
the amulet her grandmother had given her. Behind her, she could hear them—the Shadow Hunters,
relentless in their pursuit. But she wouldn't give up. Not when she was so close to finding the truth
about her parents' disappearance. With trembling fingers, she traced the runes on the amulet,
and it began to glow with a soft blue light.''',
        description='Strong opening with immediate tension, character introduction, and mystery setup.',
        metadata={'source': 'test', 'author': 'test'}
    )

    # Create scores for each category
    ExampleScore.objects.create(
        example=example,
        category=test_score_categories['plot'],
        weight=25,
        score=8.5
    )
    ExampleScore.objects.create(
        example=example,
        category=test_score_categories['character_development'],
        weight=20,
        score=7.0
    )
    ExampleScore.objects.create(
        example=example,
        category=test_score_categories['pacing'],
        weight=20,
        score=9.0
    )
    ExampleScore.objects.create(
        example=example,
        category=test_score_categories['dialogue'],
        weight=15,
        score=6.0
    )
    ExampleScore.objects.create(
        example=example,
        category=test_score_categories['description'],
        weight=20,
        score=8.0
    )

    return example


# ============================================================================
# Project Fixtures
# ============================================================================

@pytest.fixture
def test_project(db, test_user, test_genres):
    """Create a test project."""
    return NovelProject.objects.create(
        user=test_user,
        title='Test Novel Project',
        genre=test_genres['fantasy'],
        status='draft'
    )


# ============================================================================
# OpenAI/LangChain Mocking Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def mock_openai_chat():
    """
    Mock ChatOpenAI at all usage points in novel_agent modules.
    Returns appropriate responses based on prompt content.
    """
    # Create mock instance
    mock_instance = Mock()

    # Mock the invoke method
    def mock_invoke(messages):
        # Extract the actual prompt text from messages
        prompt_text = ""
        if isinstance(messages, list):
            for msg in messages:
                if hasattr(msg, 'content'):
                    prompt_text += msg.content + " "
                elif isinstance(msg, dict) and 'content' in msg:
                    prompt_text += msg['content'] + " "
                elif isinstance(msg, str):
                    prompt_text += msg + " "
        elif isinstance(messages, str):
            prompt_text = messages
        elif hasattr(messages, 'content'):
            prompt_text = messages.content

        # Get appropriate mock response
        response_content = get_mock_response_for_prompt(prompt_text)

        # Create mock response object with proper response_metadata
        mock_response = Mock()
        mock_response.content = response_content
        # Mock token usage metadata (mimics real OpenAI response structure)
        mock_response.response_metadata = {
            'token_usage': {
                'prompt_tokens': 100,
                'completion_tokens': 200,
                'total_tokens': 300
            },
            'model_name': 'gpt-4o-mini',
            'finish_reason': 'stop'
        }
        return mock_response

    mock_instance.invoke = Mock(side_effect=mock_invoke)

    # Patch ChatOpenAI at every usage point (where it's imported, not where it's defined)
    with patch('novel_agent.modules.brainstorming.ChatOpenAI', return_value=mock_instance), \
         patch('novel_agent.modules.plot_generator.ChatOpenAI', return_value=mock_instance), \
         patch('novel_agent.modules.character_generator.ChatOpenAI', return_value=mock_instance), \
         patch('novel_agent.modules.outliner.ChatOpenAI', return_value=mock_instance), \
         patch('novel_agent.modules.chapter_writer.ChatOpenAI', return_value=mock_instance), \
         patch('novel_agent.modules.editor.ChatOpenAI', return_value=mock_instance), \
         patch('novel_agent.modules.consistency_checker.ChatOpenAI', return_value=mock_instance), \
         patch('novel_agent.modules.setting_generator.ChatOpenAI', return_value=mock_instance):
        yield mock_instance


@pytest.fixture(autouse=True)
def mock_openai_embeddings():
    """Mock OpenAIEmbeddings at usage point in long_term_memory."""
    mock_instance = Mock()

    # Mock embed_documents and embed_query
    mock_instance.embed_documents = Mock(return_value=[[0.1] * 1536])  # Standard embedding size
    mock_instance.embed_query = Mock(return_value=[0.1] * 1536)

    # Patch at usage point, not at source
    with patch('novel_agent.memory.long_term_memory.OpenAIEmbeddings', return_value=mock_instance):
        yield mock_instance


@pytest.fixture(autouse=True)
def mock_chroma():
    """Mock ChromaDB vector store at usage point in long_term_memory."""
    mock_instance = Mock()

    # Mock vector store methods
    mock_instance.add_documents = Mock(return_value=['doc1', 'doc2'])
    mock_instance.similarity_search = Mock(return_value=[])
    mock_instance.similarity_search_with_score = Mock(return_value=[])
    mock_instance.delete_collection = Mock()

    mock_chroma_class = Mock()
    mock_chroma_class.return_value = mock_instance
    mock_chroma_class.from_documents = Mock(return_value=mock_instance)

    # Patch at usage point, not at source
    with patch('novel_agent.memory.long_term_memory.Chroma', mock_chroma_class):
        yield mock_instance


@pytest.fixture(autouse=True)
def mock_channel_layer():
    """Mock Django Channels layer for WebSocket testing."""
    with patch('novels.tasks.get_channel_layer') as mock_get_channel:
        mock_layer = MagicMock()
        mock_layer.group_send = MagicMock()
        mock_get_channel.return_value = mock_layer
        yield mock_layer


@pytest.fixture(autouse=True)
def mock_example_scorer():
    """Mock ExampleScorer for scoring generated content."""
    mock_scorer = Mock()

    # Mock score_example to return realistic scores
    def mock_score_example(content, categories, category_hint=None):
        """Return mock scores for each category."""
        scores = {
            'Plot': 6.5,
            'Character Development': 5.0,
            'Pacing': 6.0,
            'Dialogue': 4.0,
            'Description': 8.5
        }
        # Only return scores for categories that were requested
        filtered_scores = {k: v for k, v in scores.items() if k in categories}

        # Mock token usage
        token_usage = {
            'prompt_tokens': 386,
            'completion_tokens': 86,
            'total_tokens': 472
        }
        return filtered_scores, token_usage

    mock_scorer.score_example = Mock(side_effect=mock_score_example)

    # Patch ExampleScorer from novel_agent.output (where it's imported)
    with patch('novel_agent.output.ExampleScorer', return_value=mock_scorer):
        yield mock_scorer


# ============================================================================
# Combined Mock Fixture for Full Integration Tests
# ============================================================================

@pytest.fixture
def mock_all_openai(mock_openai_chat, mock_openai_embeddings, mock_chroma, mock_channel_layer, mock_example_scorer):
    """
    Combined fixture that mocks all OpenAI and related services.
    Use this for integration tests to ensure no real API calls are made.
    """
    return {
        'chat': mock_openai_chat,
        'embeddings': mock_openai_embeddings,
        'chroma': mock_chroma,
        'channel_layer': mock_channel_layer,
        'scorer': mock_example_scorer
    }


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def create_idea_data():
    """Factory fixture to create brainstorm idea data."""
    def _create_data(num_ideas=1, genre='Fantasy', theme='Adventure'):
        return {
            'genre': genre,
            'theme': theme,
            'num_ideas': num_ideas
        }
    return _create_data


@pytest.fixture
def create_plot_data():
    """Factory fixture to create plot data."""
    def _create_data(title='Test Plot'):
        return {
            'idea_data': {
                'title': title,
                'premise': 'A hero saves the world',
                'conflict': 'Good vs Evil',
                'hook': 'An exciting beginning'
            }
        }
    return _create_data


@pytest.fixture
def create_outline_data():
    """Factory fixture to create outline request data."""
    def _create_data(num_chapters=3):
        return {
            'num_chapters': num_chapters
        }
    return _create_data


@pytest.fixture
def create_chapter_data():
    """Factory fixture to create chapter writing request data."""
    def _create_data(chapter_outline_id, word_count=100):
        return {
            'chapter_outline_id': chapter_outline_id,
            'writing_style': 'literary',
            'language': 'English',
            'target_word_count': word_count
        }
    return _create_data
