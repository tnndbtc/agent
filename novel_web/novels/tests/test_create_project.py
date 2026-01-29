"""
Project creation tests.

Tests project creation functionality via API.
"""

import pytest
from novels.models import NovelProject


@pytest.mark.integration
@pytest.mark.django_db
class TestProjectCreation:
    """Test project creation functionality."""

    def test_create_project_via_api(self, authenticated_client, test_user):
        """Test creating a project via API endpoint."""
        response = authenticated_client.post('/api/projects/', {
            'title': 'My Test Novel',
        })

        assert response.status_code == 201
        assert 'id' in response.data
        assert response.data['title'] == 'My Test Novel'

        # Verify project was created in database
        project = NovelProject.objects.get(id=response.data['id'])
        assert project.user == test_user
        assert project.title == 'My Test Novel'
        assert project.chroma_collection_name is not None

    def test_create_project_unauthenticated(self, api_client):
        """Test creating project fails without authentication."""
        response = api_client.post('/api/projects/', {
            'title': 'Unauthorized Novel',
        })

        # Accept both 401 Unauthorized and 403 Forbidden
        assert response.status_code in [401, 403]

    def test_create_poem_project(self, authenticated_client, test_user):
        """Test creating a poem project via API endpoint."""
        response = authenticated_client.post('/api/projects/', {
            'title': 'My Test Poem',
            'content_type': 'poem',
        })

        assert response.status_code == 201
        assert 'id' in response.data
        assert response.data['title'] == 'My Test Poem'
        assert response.data['content_type'] == 'poem'

        # Verify project was created in database
        project = NovelProject.objects.get(id=response.data['id'])
        assert project.user == test_user
        assert project.title == 'My Test Poem'
        assert project.content_type == 'poem'
        assert project.chroma_collection_name is not None

    def test_create_essay_project(self, authenticated_client, test_user):
        """Test creating an essay project via API endpoint."""
        response = authenticated_client.post('/api/projects/', {
            'title': 'My Test Essay',
            'content_type': 'essay',
        })

        assert response.status_code == 201
        assert 'id' in response.data
        assert response.data['title'] == 'My Test Essay'
        assert response.data['content_type'] == 'essay'

        # Verify project was created in database
        project = NovelProject.objects.get(id=response.data['id'])
        assert project.user == test_user
        assert project.title == 'My Test Essay'
        assert project.content_type == 'essay'
        assert project.chroma_collection_name is not None

    def test_create_sketch_project(self, authenticated_client, test_user):
        """Test creating a sketch project via API endpoint."""
        response = authenticated_client.post('/api/projects/', {
            'title': 'My Test Sketch',
            'content_type': 'sketch',
        })

        assert response.status_code == 201
        assert 'id' in response.data
        assert response.data['title'] == 'My Test Sketch'
        assert response.data['content_type'] == 'sketch'

        # Verify project was created in database
        project = NovelProject.objects.get(id=response.data['id'])
        assert project.user == test_user
        assert project.title == 'My Test Sketch'
        assert project.content_type == 'sketch'
        assert project.chroma_collection_name is not None

    def test_create_article_project(self, authenticated_client, test_user):
        """Test creating an article project via API endpoint."""
        response = authenticated_client.post('/api/projects/', {
            'title': 'My Test Article',
            'content_type': 'article',
        })

        assert response.status_code == 201
        assert 'id' in response.data
        assert response.data['title'] == 'My Test Article'
        assert response.data['content_type'] == 'article'

        # Verify project was created in database
        project = NovelProject.objects.get(id=response.data['id'])
        assert project.user == test_user
        assert project.title == 'My Test Article'
        assert project.content_type == 'article'
        assert project.chroma_collection_name is not None
