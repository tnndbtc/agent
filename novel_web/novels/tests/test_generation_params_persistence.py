"""Test temperature and top_p persistence in ContentPiece."""
import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from novels.models import NovelProject, ContentPiece, Idea
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestGenerationParamsPersistence:
    """Test that temperature and top_p values persist across requests."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_authenticate(user=self.user)

    def test_poem_temperature_top_p_saved_and_retrieved(self):
        """Test that custom temperature/top_p values are saved to ContentPiece and can be retrieved."""
        # Create a poem project
        project = NovelProject.objects.create(
            user=self.user,
            title='Test Poem',
            content_type='poem'
        )

        # Generate content with custom temperature and top_p
        idea_data = {
            'theme': 'nature',
            'style': 'haiku',
            'word_count': 50
        }

        response = self.client.post(
            f'/api/projects/{project.id}/generate_content/',
            {
                'idea_data': idea_data,
                'temperature': 0.9,
                'top_p': 0.8
            },
            format='json'
        )

        assert response.status_code == 201
        assert 'content_piece' in response.data

        # Verify ContentPiece was created with correct generation parameters
        content_piece = ContentPiece.objects.get(project=project)
        assert content_piece.generation_temperature == Decimal('0.9')
        assert content_piece.generation_top_p == Decimal('0.8')

        # Verify generation_params endpoint returns the saved values
        params_response = self.client.get(f'/api/projects/{project.id}/generation_params/')
        assert params_response.status_code == 200
        assert params_response.data['generation_temperature'] == Decimal('0.9')
        assert params_response.data['generation_top_p'] == Decimal('0.8')

    def test_essay_temperature_top_p_saved_and_retrieved(self):
        """Test that custom temperature/top_p values are saved for essays."""
        # Create an essay project
        project = NovelProject.objects.create(
            user=self.user,
            title='Test Essay',
            content_type='essay'
        )

        # Generate content with different custom values
        idea_data = {
            'topic': 'climate change',
            'argument': 'need for action',
            'word_count': 500
        }

        response = self.client.post(
            f'/api/projects/{project.id}/generate_content/',
            {
                'idea_data': idea_data,
                'temperature': 0.6,
                'top_p': 0.9
            },
            format='json'
        )

        assert response.status_code == 201

        # Verify saved values
        content_piece = ContentPiece.objects.get(project=project)
        assert content_piece.generation_temperature == Decimal('0.6')
        assert content_piece.generation_top_p == Decimal('0.9')

        # Verify API returns correct values
        params_response = self.client.get(f'/api/projects/{project.id}/generation_params/')
        assert params_response.status_code == 200
        assert params_response.data['generation_temperature'] == Decimal('0.6')
        assert params_response.data['generation_top_p'] == Decimal('0.9')

    def test_generation_params_null_for_new_project(self):
        """Test that generation_params returns null for projects without content."""
        # Create a project without generating content
        project = NovelProject.objects.create(
            user=self.user,
            title='New Project',
            content_type='poem'
        )

        # Query generation params - should return null
        params_response = self.client.get(f'/api/projects/{project.id}/generation_params/')
        assert params_response.status_code == 200
        assert params_response.data['generation_temperature'] is None
        assert params_response.data['generation_top_p'] is None

    def test_generation_params_update_on_regeneration(self):
        """Test that regenerating content with different params updates the saved values."""
        # Create a project and generate initial content
        project = NovelProject.objects.create(
            user=self.user,
            title='Test Article',
            content_type='article'
        )

        idea_data = {
            'headline': 'Breaking News',
            'angle': 'investigative',
            'word_count': 400
        }

        # First generation with temp=0.7, top_p=1.0
        response1 = self.client.post(
            f'/api/projects/{project.id}/generate_content/',
            {
                'idea_data': idea_data,
                'temperature': 0.7,
                'top_p': 1.0
            },
            format='json'
        )
        assert response1.status_code == 201

        # Verify first values
        content_piece = ContentPiece.objects.get(project=project)
        assert content_piece.generation_temperature == Decimal('0.7')
        assert content_piece.generation_top_p == Decimal('1.0')

        # Regenerate with different params: temp=0.4, top_p=0.8
        response2 = self.client.post(
            f'/api/projects/{project.id}/generate_content/',
            {
                'idea_data': idea_data,
                'temperature': 0.4,
                'top_p': 0.8
            },
            format='json'
        )
        assert response2.status_code == 201

        # Verify updated values
        content_piece.refresh_from_db()
        assert content_piece.generation_temperature == Decimal('0.4')
        assert content_piece.generation_top_p == Decimal('0.8')

        # Verify API returns updated values
        params_response = self.client.get(f'/api/projects/{project.id}/generation_params/')
        assert params_response.status_code == 200
        assert params_response.data['generation_temperature'] == Decimal('0.4')
        assert params_response.data['generation_top_p'] == Decimal('0.8')

    def test_content_piece_serializer_includes_generation_params(self):
        """Test that ContentPieceSerializer includes generation_temperature and generation_top_p."""
        # Create project and generate content
        project = NovelProject.objects.create(
            user=self.user,
            title='Test Sketch',
            content_type='sketch'
        )

        idea_data = {
            'subject': 'urban landscape',
            'perspective': 'first person',
            'word_count': 300
        }

        response = self.client.post(
            f'/api/projects/{project.id}/generate_content/',
            {
                'idea_data': idea_data,
                'temperature': 0.8,
                'top_p': 0.9
            },
            format='json'
        )

        assert response.status_code == 201

        # Verify serializer includes the fields
        content_piece_data = response.data['content_piece']
        assert 'generation_temperature' in content_piece_data
        assert 'generation_top_p' in content_piece_data
        assert content_piece_data['generation_temperature'] == '0.8'
        assert content_piece_data['generation_top_p'] == '0.9'

    def test_generation_params_requires_authentication(self):
        """Test that unauthenticated requests cannot access generation_params."""
        project = NovelProject.objects.create(
            user=self.user,
            title='Test Project',
            content_type='poem'
        )

        # Logout
        self.client.force_authenticate(user=None)

        # Try to access generation params
        response = self.client.get(f'/api/projects/{project.id}/generation_params/')
        assert response.status_code == 403  # DRF returns 403 for unauthenticated requests

    def test_generation_params_returns_null_for_novel_projects(self):
        """Test that generation_params returns null for novel projects (which don't use ContentPiece)."""
        # Create a novel project
        project = NovelProject.objects.create(
            user=self.user,
            title='Test Novel',
            content_type='novel'
        )

        # Query generation params - should return null since novels don't use ContentPiece
        params_response = self.client.get(f'/api/projects/{project.id}/generation_params/')
        assert params_response.status_code == 200
        assert params_response.data['generation_temperature'] is None
        assert params_response.data['generation_top_p'] is None
