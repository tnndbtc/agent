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
