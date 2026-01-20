"""Tests for AI text modification feature."""
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from novels.models import UserPrompt, NovelProject, Chapter, ChapterOutline, Plot
from unittest.mock import patch, MagicMock


@pytest.fixture
def user(db):
    """Create test user."""
    return User.objects.create_user(username='testuser', password='testpass123')


@pytest.fixture
def auth_client(user):
    """Create authenticated API client."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def project(user):
    """Create test project."""
    return NovelProject.objects.create(
        user=user,
        title='Test Novel',
        genre_text='Fantasy'
    )


@pytest.mark.django_db
class TestAIModificationAPI:
    """Test AI text modification endpoints."""

    @patch('langchain_openai.ChatOpenAI')
    def test_modify_text_success(self, mock_openai, auth_client):
        """Test successful text modification."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.content = "The brave hero stormed dramatically into the chamber."
        mock_response.response_metadata = {
            'token_usage': {
                'prompt_tokens': 50,
                'completion_tokens': 20,
                'total_tokens': 70
            }
        }
        mock_openai.return_value.invoke.return_value = mock_response

        response = auth_client.post('/api/ai-modifications/modify-text/', {
            'original_text': 'The hero walked into the room.',
            'user_prompt': 'Make it more dramatic',
            'content_type': 'chapter'
        }, format='json')

        assert response.status_code == 200
        assert 'modified_text' in response.data
        assert 'token_usage' in response.data
        assert response.data['token_usage']['total_tokens'] == 70
        assert response.data['modified_text'] == "The brave hero stormed dramatically into the chamber."

    def test_modify_text_missing_prompt(self, auth_client):
        """Test validation for missing prompt."""
        response = auth_client.post('/api/ai-modifications/modify-text/', {
            'original_text': 'Some text',
            'user_prompt': '',  # Empty prompt
            'content_type': 'chapter'
        }, format='json')

        assert response.status_code == 400

    def test_modify_text_missing_original_text(self, auth_client):
        """Test validation for missing original text."""
        response = auth_client.post('/api/ai-modifications/modify-text/', {
            'original_text': '',
            'user_prompt': 'Make it better',
            'content_type': 'chapter'
        }, format='json')

        assert response.status_code == 400

    def test_modify_text_invalid_content_type(self, auth_client):
        """Test validation for invalid content type."""
        response = auth_client.post('/api/ai-modifications/modify-text/', {
            'original_text': 'Some text',
            'user_prompt': 'Make it better',
            'content_type': 'invalid_type'
        }, format='json')

        assert response.status_code == 400

    @patch('langchain_openai.ChatOpenAI')
    def test_modify_text_with_save_prompt(self, mock_openai, auth_client, user):
        """Test saving custom prompt during modification."""
        mock_response = MagicMock()
        mock_response.content = "Modified text"
        mock_response.response_metadata = {
            'token_usage': {
                'prompt_tokens': 10,
                'completion_tokens': 5,
                'total_tokens': 15
            }
        }
        mock_openai.return_value.invoke.return_value = mock_response

        response = auth_client.post('/api/ai-modifications/modify-text/', {
            'original_text': 'Original text',
            'user_prompt': 'Custom modification',
            'content_type': 'plot',
            'save_prompt': True,
            'prompt_name': 'My Custom Prompt'
        }, format='json')

        assert response.status_code == 200
        assert 'saved_prompt' in response.data
        assert response.data['saved_prompt']['name'] == 'My Custom Prompt'

        # Verify prompt was saved
        prompt = UserPrompt.objects.get(user=user, name='My Custom Prompt')
        assert prompt.prompt_text == 'Custom modification'
        assert prompt.usage_count == 0

    @patch('langchain_openai.ChatOpenAI')
    def test_modify_text_update_existing_prompt(self, mock_openai, auth_client, user):
        """Test updating an existing saved prompt."""
        # Create existing prompt
        UserPrompt.objects.create(
            user=user,
            name='Existing Prompt',
            prompt_text='Old text'
        )

        mock_response = MagicMock()
        mock_response.content = "Modified text"
        mock_response.response_metadata = {
            'token_usage': {
                'prompt_tokens': 10,
                'completion_tokens': 5,
                'total_tokens': 15
            }
        }
        mock_openai.return_value.invoke.return_value = mock_response

        response = auth_client.post('/api/ai-modifications/modify-text/', {
            'original_text': 'Original text',
            'user_prompt': 'New text',
            'content_type': 'plot',
            'save_prompt': True,
            'prompt_name': 'Existing Prompt'
        }, format='json')

        assert response.status_code == 200

        # Verify prompt was updated
        prompt = UserPrompt.objects.get(user=user, name='Existing Prompt')
        assert prompt.prompt_text == 'New text'

    @patch('langchain_openai.ChatOpenAI')
    def test_modify_text_with_saved_prompt_id(self, mock_openai, auth_client, user):
        """Test using a saved prompt by ID."""
        # Create saved prompt
        saved_prompt = UserPrompt.objects.create(
            user=user,
            name='Dramatic',
            prompt_text='Make it more dramatic and intense',
            usage_count=5
        )

        mock_response = MagicMock()
        mock_response.content = "Modified text with drama"
        mock_response.response_metadata = {
            'token_usage': {
                'prompt_tokens': 10,
                'completion_tokens': 5,
                'total_tokens': 15
            }
        }
        mock_openai.return_value.invoke.return_value = mock_response

        response = auth_client.post('/api/ai-modifications/modify-text/', {
            'original_text': 'Original text',
            'user_prompt': 'This will be ignored',
            'content_type': 'chapter',
            'saved_prompt_id': str(saved_prompt.id)
        }, format='json')

        assert response.status_code == 200

        # Verify usage count incremented
        saved_prompt.refresh_from_db()
        assert saved_prompt.usage_count == 6

    def test_modify_text_invalid_saved_prompt_id(self, auth_client):
        """Test using non-existent saved prompt ID."""
        import uuid
        fake_id = uuid.uuid4()

        response = auth_client.post('/api/ai-modifications/modify-text/', {
            'original_text': 'Original text',
            'user_prompt': 'Ignored',
            'content_type': 'chapter',
            'saved_prompt_id': str(fake_id)
        }, format='json')

        assert response.status_code == 404

    def test_get_preset_prompts(self, auth_client):
        """Test getting preset prompts."""
        response = auth_client.get('/api/ai-modifications/preset-prompts/')

        assert response.status_code == 200
        assert len(response.data) == 5
        assert any(p['id'] == 'dramatic' for p in response.data)
        assert any(p['id'] == 'simplify' for p in response.data)
        assert any(p['id'] == 'detail' for p in response.data)
        assert any(p['id'] == 'shorter' for p in response.data)
        assert any(p['id'] == 'clarity' for p in response.data)

    def test_modify_text_requires_authentication(self):
        """Test that unauthenticated requests are rejected."""
        client = APIClient()  # No authentication

        response = client.post('/api/ai-modifications/modify-text/', {
            'original_text': 'Text',
            'user_prompt': 'Modify',
            'content_type': 'chapter'
        }, format='json')

        assert response.status_code in [401, 403]


@pytest.mark.django_db(transaction=True)
class TestUserPromptAPI:
    """Test user prompt management endpoints."""

    @pytest.fixture(autouse=True)
    def clean_prompts(self, user):
        """Clean up user prompts before and after each test."""
        UserPrompt.objects.all().delete()
        yield
        UserPrompt.objects.all().delete()

    def test_create_user_prompt(self, auth_client, user):
        """Test creating a saved prompt."""
        response = auth_client.post('/api/user-prompts/', {
            'name': 'Make Epic',
            'prompt_text': 'Rewrite this to be epic and legendary'
        }, format='json')

        assert response.status_code == 201
        assert response.data['name'] == 'Make Epic'
        assert response.data['prompt_text'] == 'Rewrite this to be epic and legendary'
        assert response.data['usage_count'] == 0

        # Verify in database
        assert UserPrompt.objects.filter(user=user, name='Make Epic').exists()

    def test_list_user_prompts(self, auth_client, user):
        """Test listing user's prompts."""
        UserPrompt.objects.create(
            user=user,
            name='Test List Prompt 1',
            prompt_text='Text 1',
            usage_count=5
        )
        UserPrompt.objects.create(
            user=user,
            name='Test List Prompt 2',
            prompt_text='Text 2',
            usage_count=10
        )

        response = auth_client.get('/api/user-prompts/')

        assert response.status_code == 200
        # Handle paginated or list response
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 2

        # Find our test prompts in the response
        prompt_names = [p['name'] for p in data]
        assert 'Test List Prompt 1' in prompt_names
        assert 'Test List Prompt 2' in prompt_names

        # Check they're ordered by usage_count desc
        test_prompts = [p for p in data if p['name'].startswith('Test List Prompt')]
        assert len(test_prompts) == 2
        assert test_prompts[0]['name'] == 'Test List Prompt 2'  # Higher usage first
        assert test_prompts[0]['usage_count'] == 10
        assert test_prompts[1]['name'] == 'Test List Prompt 1'
        assert test_prompts[1]['usage_count'] == 5

    def test_get_single_user_prompt(self, auth_client, user):
        """Test retrieving a single prompt."""
        prompt = UserPrompt.objects.create(
            user=user,
            name='Test Prompt',
            prompt_text='Test text'
        )

        response = auth_client.get(f'/api/user-prompts/{prompt.id}/')

        assert response.status_code == 200
        assert response.data['name'] == 'Test Prompt'

    def test_update_user_prompt(self, auth_client, user):
        """Test updating a prompt."""
        prompt = UserPrompt.objects.create(
            user=user,
            name='Old Name',
            prompt_text='Old text'
        )

        response = auth_client.patch(f'/api/user-prompts/{prompt.id}/', {
            'name': 'New Name'
        }, format='json')

        assert response.status_code == 200
        prompt.refresh_from_db()
        assert prompt.name == 'New Name'
        assert prompt.prompt_text == 'Old text'  # Unchanged

    def test_delete_user_prompt(self, auth_client, user):
        """Test deleting a prompt."""
        prompt = UserPrompt.objects.create(
            user=user,
            name='To Delete',
            prompt_text='Text'
        )

        response = auth_client.delete(f'/api/user-prompts/{prompt.id}/')

        assert response.status_code == 204
        assert not UserPrompt.objects.filter(id=prompt.id).exists()

    def test_cannot_access_other_user_prompts(self, auth_client, user, db):
        """Test that users can only access their own prompts."""
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        other_prompt = UserPrompt.objects.create(
            user=other_user,
            name='Other User Prompt',
            prompt_text='Text'
        )

        # Try to get other user's prompt
        response = auth_client.get(f'/api/user-prompts/{other_prompt.id}/')
        assert response.status_code == 404

        # Try to list - should not see other user's prompts
        my_prompt = UserPrompt.objects.create(user=user, name='My Test Prompt', prompt_text='Text')
        response = auth_client.get('/api/user-prompts/')
        assert response.status_code == 200

        # Handle paginated or list response
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data

        # Verify our prompt is in the list
        prompt_names = [p['name'] for p in data]
        assert 'My Test Prompt' in prompt_names

        # Verify other user's prompt is NOT in the list
        assert 'Other User Prompt' not in prompt_names

        # Verify we can access our own prompt
        assert any(p['id'] == str(my_prompt.id) for p in data)

    def test_user_prompt_requires_authentication(self, db):
        """Test that unauthenticated requests are rejected."""
        client = APIClient()

        response = client.get('/api/user-prompts/')
        assert response.status_code in [401, 403]


@pytest.mark.django_db
class TestAIModificationService:
    """Test the service layer directly."""

    @patch('langchain_openai.ChatOpenAI')
    def test_modify_text_selection_service(self, mock_openai, user):
        """Test the service method directly."""
        from novels.services import AIModificationService

        mock_response = MagicMock()
        mock_response.content = "Enhanced text with dramatic flair"
        mock_response.response_metadata = {
            'token_usage': {
                'prompt_tokens': 30,
                'completion_tokens': 10,
                'total_tokens': 40
            }
        }
        mock_openai.return_value.invoke.return_value = mock_response

        result = AIModificationService.modify_text_selection(
            user=user,
            original_text="Original text",
            user_prompt="Add dramatic flair",
            content_type="character"
        )

        assert result['modified_text'] == "Enhanced text with dramatic flair"
        assert result['original_text'] == "Original text"
        assert result['user_prompt'] == "Add dramatic flair"
        assert result['token_usage']['total_tokens'] == 40
        assert result['token_usage']['prompt_tokens'] == 30
        assert result['token_usage']['completion_tokens'] == 10

    @patch('langchain_openai.ChatOpenAI')
    def test_content_type_specific_instructions(self, mock_openai, user):
        """Test that different content types get appropriate system messages."""
        from novels.services import AIModificationService

        mock_response = MagicMock()
        mock_response.content = "Modified"
        mock_response.response_metadata = {
            'token_usage': {
                'prompt_tokens': 10,
                'completion_tokens': 5,
                'total_tokens': 15
            }
        }
        mock_llm = mock_openai.return_value
        mock_llm.invoke.return_value = mock_response

        # Test with 'character' content type
        AIModificationService.modify_text_selection(
            user=user,
            original_text="Text",
            user_prompt="Modify",
            content_type="character"
        )

        # Verify the system message included character-specific instruction
        call_args = mock_llm.invoke.call_args[0][0]
        system_msg = call_args[0].content
        assert "character" in system_msg.lower()

    @patch('langchain_openai.ChatOpenAI')
    def test_all_content_types(self, mock_openai, user):
        """Test all content types have instructions."""
        from novels.services import AIModificationService

        mock_response = MagicMock()
        mock_response.content = "Modified"
        mock_response.response_metadata = {
            'token_usage': {
                'prompt_tokens': 10,
                'completion_tokens': 5,
                'total_tokens': 15
            }
        }
        mock_openai.return_value.invoke.return_value = mock_response

        content_types = ['plot', 'act', 'character', 'outline', 'chapter', 'text']

        for content_type in content_types:
            result = AIModificationService.modify_text_selection(
                user=user,
                original_text="Test text",
                user_prompt="Modify",
                content_type=content_type
            )
            assert result['modified_text'] == "Modified"


@pytest.mark.django_db
class TestUserPromptModel:
    """Test UserPrompt model methods."""

    def test_increment_usage(self, user):
        """Test increment_usage method."""
        prompt = UserPrompt.objects.create(
            user=user,
            name='Test',
            prompt_text='Text',
            usage_count=0
        )

        prompt.increment_usage()
        assert prompt.usage_count == 1

        prompt.increment_usage()
        prompt.increment_usage()
        assert prompt.usage_count == 3

    def test_str_representation(self, user):
        """Test string representation."""
        prompt = UserPrompt.objects.create(
            user=user,
            name='Test Prompt',
            prompt_text='Text'
        )

        assert str(prompt) == "Test Prompt by testuser"

    def test_ordering(self, user):
        """Test that prompts are ordered by usage_count desc."""
        p1 = UserPrompt.objects.create(user=user, name='P1', prompt_text='T', usage_count=5)
        p2 = UserPrompt.objects.create(user=user, name='P2', prompt_text='T', usage_count=10)
        p3 = UserPrompt.objects.create(user=user, name='P3', prompt_text='T', usage_count=2)

        prompts = list(UserPrompt.objects.filter(user=user))
        assert prompts[0].name == 'P2'  # Highest usage
        assert prompts[1].name == 'P1'
        assert prompts[2].name == 'P3'  # Lowest usage
