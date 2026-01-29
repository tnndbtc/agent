"""
Test content generation from idea for Poem, Essay, Sketch, and Article content types.

This verifies the workflow where:
1. User creates a project for a specific content type
2. User enters idea data and clicks "Save Idea and continue"
3. The generate_content API is called
4. ContentPiece is created with the generated content
5. Page reload shows the content in the Overview tab
"""
import pytest
from django.test import Client
from novels.models import NovelProject, ContentPiece


@pytest.fixture
def test_poem_project(db, test_user):
    """Create a test poem project."""
    return NovelProject.objects.create(
        user=test_user,
        title='Test Poem Project',
        content_type='poem',
        status='draft'
    )


@pytest.fixture
def test_essay_project(db, test_user):
    """Create a test essay project."""
    return NovelProject.objects.create(
        user=test_user,
        title='Test Essay Project',
        content_type='essay',
        status='draft'
    )


@pytest.fixture
def test_sketch_project(db, test_user):
    """Create a test sketch project."""
    return NovelProject.objects.create(
        user=test_user,
        title='Test Sketch Project',
        content_type='sketch',
        status='draft'
    )


@pytest.fixture
def test_article_project(db, test_user):
    """Create a test article project."""
    return NovelProject.objects.create(
        user=test_user,
        title='Test Article Project',
        content_type='article',
        status='draft'
    )


@pytest.mark.integration
@pytest.mark.django_db
class TestWriteContentFromIdea:
    """Test the full flow: generate content from idea -> verify overview shows content."""

    def test_poem_generation_and_display(
        self, authenticated_client, test_poem_project, mock_all_openai
    ):
        """
        Test poem generation from idea and verify the content is displayed.
        """
        project = test_poem_project

        # Step 1: Generate poem content via API
        idea_data = {
            'theme': 'Autumn and the passage of time',
            'mood': 'Reflective and melancholic',
            'style': 'Free verse'
        }
        response = authenticated_client.post(
            f'/api/projects/{project.id}/generate_content/',
            {'idea_data': idea_data},
            format='json'
        )

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.data}"
        assert 'content_piece' in response.data
        assert 'token_usage' in response.data

        content_piece_data = response.data['content_piece']
        assert content_piece_data['title'] is not None
        assert content_piece_data['content'] is not None
        assert content_piece_data['word_count'] > 0

        # Step 2: Verify ContentPiece exists in database
        assert ContentPiece.objects.filter(project=project).exists(), \
            "ContentPiece should exist in DB after generate_content API call"

        content_piece = ContentPiece.objects.get(project=project)
        assert 'autumn' in content_piece.content.lower() or 'leaves' in content_piece.content.lower()

        # Step 3: Load the project detail page
        web_client = Client()
        web_client.login(username='testuser', password='testpass123')
        page_response = web_client.get(f'/en/project/{project.id}/')

        assert page_response.status_code == 200

        # Step 4: Verify the page context includes content_piece
        assert page_response.context['project'].content_type == 'poem'
        assert hasattr(page_response.context['project'], 'content_piece')

        # Step 5: Verify the HTML contains the poem content
        html = page_response.content.decode()
        assert content_piece.title in html, \
            f"Poem title '{content_piece.title}' should appear in rendered HTML"
        assert 'autumn' in html.lower() or 'leaves' in html.lower(), \
            "Poem content should appear in rendered HTML"

    def test_essay_generation_and_display(
        self, authenticated_client, test_essay_project, mock_all_openai
    ):
        """
        Test essay generation from idea and verify the content is displayed.
        """
        project = test_essay_project

        # Step 1: Generate essay content via API
        idea_data = {
            'topic': 'The impact of technology on modern society',
            'thesis': 'Technology has both benefits and challenges',
            'structure': 'argumentative',
            'target_length': 'medium'
        }
        response = authenticated_client.post(
            f'/api/projects/{project.id}/generate_content/',
            {'idea_data': idea_data},
            format='json'
        )

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.data}"
        assert 'content_piece' in response.data

        content_piece_data = response.data['content_piece']
        assert content_piece_data['title'] is not None
        assert content_piece_data['content'] is not None
        assert content_piece_data['word_count'] > 0

        # Step 2: Verify ContentPiece exists in database
        assert ContentPiece.objects.filter(project=project).exists()

        content_piece = ContentPiece.objects.get(project=project)
        assert 'technology' in content_piece.content.lower()

        # Step 3: Load the project detail page
        web_client = Client()
        web_client.login(username='testuser', password='testpass123')
        page_response = web_client.get(f'/en/project/{project.id}/')

        assert page_response.status_code == 200

        # Step 4: Verify the page context
        assert page_response.context['project'].content_type == 'essay'

        # Step 5: Verify the HTML contains the essay content
        html = page_response.content.decode()
        assert content_piece.title in html
        assert 'technology' in html.lower()

    def test_sketch_generation_and_display(
        self, authenticated_client, test_sketch_project, mock_all_openai
    ):
        """
        Test sketch generation from idea and verify the content is displayed.
        """
        project = test_sketch_project

        # Step 1: Generate sketch content via API
        idea_data = {
            'observation': 'A quiet coffee shop at dawn',
            'focus': 'The interaction between early morning customers',
            'mood': 'Peaceful and contemplative'
        }
        response = authenticated_client.post(
            f'/api/projects/{project.id}/generate_content/',
            {'idea_data': idea_data},
            format='json'
        )

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.data}"
        assert 'content_piece' in response.data

        content_piece_data = response.data['content_piece']
        assert content_piece_data['title'] is not None
        assert content_piece_data['content'] is not None
        assert content_piece_data['word_count'] > 0

        # Step 2: Verify ContentPiece exists in database
        assert ContentPiece.objects.filter(project=project).exists()

        content_piece = ContentPiece.objects.get(project=project)
        assert 'coffee' in content_piece.content.lower() or 'dawn' in content_piece.content.lower()

        # Step 3: Load the project detail page
        web_client = Client()
        web_client.login(username='testuser', password='testpass123')
        page_response = web_client.get(f'/en/project/{project.id}/')

        assert page_response.status_code == 200

        # Step 4: Verify the page context
        assert page_response.context['project'].content_type == 'sketch'

        # Step 5: Verify the HTML contains the sketch content
        html = page_response.content.decode()
        assert content_piece.title in html
        assert 'coffee' in html.lower() or 'dawn' in html.lower()

    def test_article_generation_and_display(
        self, authenticated_client, test_article_project, mock_all_openai
    ):
        """
        Test article generation from idea and verify the content is displayed.
        """
        project = test_article_project

        # Step 1: Generate article content via API
        idea_data = {
            'headline': 'Local community garden transforms neighborhood',
            'angle': 'Human interest story about community building',
            'sources': 'Interview with garden founder',
            'length': 'standard'
        }
        response = authenticated_client.post(
            f'/api/projects/{project.id}/generate_content/',
            {'idea_data': idea_data},
            format='json'
        )

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.data}"
        assert 'content_piece' in response.data

        content_piece_data = response.data['content_piece']
        assert content_piece_data['title'] is not None
        assert content_piece_data['content'] is not None
        assert content_piece_data['word_count'] > 0

        # Step 2: Verify ContentPiece exists in database
        assert ContentPiece.objects.filter(project=project).exists()

        content_piece = ContentPiece.objects.get(project=project)
        assert 'garden' in content_piece.content.lower() or 'community' in content_piece.content.lower()

        # Step 3: Load the project detail page
        web_client = Client()
        web_client.login(username='testuser', password='testpass123')
        page_response = web_client.get(f'/en/project/{project.id}/')

        assert page_response.status_code == 200

        # Step 4: Verify the page context
        assert page_response.context['project'].content_type == 'article'

        # Step 5: Verify the HTML contains the article content
        html = page_response.content.decode()
        assert content_piece.title in html
        assert 'garden' in html.lower() or 'community' in html.lower()

    def test_novel_project_rejects_generate_content(
        self, authenticated_client, test_project, mock_all_openai
    ):
        """
        Test that novel projects cannot use generate_content endpoint.
        They should use create_plot instead.
        """
        project = test_project  # This is a novel project (default content_type)

        # Attempt to generate content for a novel project
        idea_data = {'premise': 'A test premise'}
        response = authenticated_client.post(
            f'/api/projects/{project.id}/generate_content/',
            {'idea_data': idea_data},
            format='json'
        )

        assert response.status_code == 400
        assert 'error' in response.data
        assert 'create_plot' in response.data['error'].lower()

    def test_content_piece_word_count_calculated(
        self, authenticated_client, test_poem_project, mock_all_openai
    ):
        """
        Test that word count is properly calculated for generated content.
        """
        project = test_poem_project

        idea_data = {'theme': 'Nature', 'mood': 'Peaceful'}
        response = authenticated_client.post(
            f'/api/projects/{project.id}/generate_content/',
            {'idea_data': idea_data},
            format='json'
        )

        assert response.status_code == 201

        content_piece = ContentPiece.objects.get(project=project)
        # Calculate expected word count
        expected_word_count = len(content_piece.content.split())
        assert content_piece.word_count == expected_word_count
