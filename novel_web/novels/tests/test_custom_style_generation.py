"""
Test custom writing style content generation for 'other' content type.

This test reproduces the ImportError bug where get_language_name is imported
from the wrong module (novels.utils instead of novels.prompt_assembly) when
generating content with non-English custom writing styles.

The bug occurs at novels/services.py line 910:
    from .utils import get_language_name  # WRONG - should be from prompt_assembly

This test verifies the workflow:
1. User creates a project with content_type='other'
2. User creates a custom writing style with non-English language (zh-hans)
3. User selects the custom style and generates content
4. System should generate content using the custom style
"""
import pytest
import time
from django.test import Client
from novels.models import NovelProject, ContentPiece, CustomWritingStyle, CustomAgentRole


@pytest.fixture
def test_other_project(db, test_user):
    """Create a test 'other' content type project."""
    return NovelProject.objects.create(
        user=test_user,
        title='Test Custom Style Project',
        content_type='other',
        status='draft'
    )


@pytest.fixture
def chinese_custom_style(db, test_user):
    """Create a Chinese custom writing style."""
    return CustomWritingStyle.objects.create(
        user=test_user,
        created_at=int(time.time()),
        language_code='zh-hans',  # Chinese (Simplified) - triggers the bug
        style_name='诗意叙述',
        style_instruction='用优美的诗意语言写作，注重意境和情感表达。使用比喻和拟人等修辞手法。',
        sample='秋风起时，落叶纷飞，如同往事随风飘零...'
    )


@pytest.fixture
def chinese_custom_style_with_agent(db, test_user, chinese_custom_style):
    """Create a Chinese custom writing style with linked custom agent role."""
    agent_role = CustomAgentRole.objects.create(
        user=test_user,
        created_at=int(time.time()),
        language_code='zh-hans',
        role_name='诗意散文作家',
        role_instruction='你是一位擅长写诗意散文的作家，善于用细腻的笔触描绘情感和场景。',
        custom_style=chinese_custom_style
    )
    return chinese_custom_style


@pytest.fixture
def english_custom_style(db, test_user):
    """Create an English custom writing style."""
    return CustomWritingStyle.objects.create(
        user=test_user,
        created_at=int(time.time()),
        language_code='en',
        style_name='Hemingway Style',
        style_instruction='Write in short, declarative sentences. Use simple, direct language. Avoid flowery descriptions. Focus on action and dialogue.',
        sample='The sun was hot. The air was dry. He walked down the dusty road.'
    )


@pytest.mark.integration
@pytest.mark.django_db
class TestCustomStyleGeneration:
    """Test custom writing style content generation for 'other' content type."""

    def test_chinese_custom_style_generation(
        self, authenticated_client, test_other_project, chinese_custom_style,
        mock_all_openai, test_agent_roles
    ):
        """
        Test that custom style generation works with Chinese language.

        This test SHOULD FAIL with ImportError before the bug is fixed:
        ImportError: cannot import name 'get_language_name' from 'novels.utils'

        The error occurs because:
        1. custom_style.language_code = 'zh-hans' (not 'en')
        2. Code enters the if block: if effective_language != 'en'
        3. Tries to import: from .utils import get_language_name
        4. Function doesn't exist in utils.py (it's in prompt_assembly.py)
        """
        project = test_other_project

        # Generate content with Chinese custom style
        idea_data = {
            'idea': '写一段关于秋天月光的诗意描述',
            'word_count': 200,
            'custom_style_id': chinese_custom_style.id
        }

        # This will trigger the ImportError at services.py:910
        response = authenticated_client.post(
            f'/api/projects/{project.id}/generate_content/',
            {'idea_data': idea_data},
            format='json'
        )

        # Before fix: Should fail with 500 Internal Server Error (ImportError)
        # After fix: Should return 201 Created
        assert response.status_code == 201, \
            f"Expected 201, got {response.status_code}: {response.data}"
        assert 'content_piece' in response.data
        assert 'token_usage' in response.data

        content_piece_data = response.data['content_piece']
        assert content_piece_data['title'] is not None
        assert content_piece_data['content'] is not None
        assert content_piece_data['word_count'] > 0

        # Verify ContentPiece exists in database
        assert ContentPiece.objects.filter(project=project).exists(), \
            "ContentPiece should exist in DB after generate_content API call"

        content_piece = ContentPiece.objects.get(project=project)
        assert content_piece.content is not None
        assert content_piece.word_count > 0

    def test_chinese_custom_style_with_agent_role(
        self, authenticated_client, test_other_project,
        chinese_custom_style_with_agent, mock_all_openai, test_agent_roles
    ):
        """
        Test custom style generation with linked custom agent role.

        This also triggers the same ImportError because the language is zh-hans.
        """
        project = test_other_project

        idea_data = {
            'idea': '故国的秋',
            'word_count': 300,
            'custom_style_id': chinese_custom_style_with_agent.id
        }

        response = authenticated_client.post(
            f'/api/projects/{project.id}/generate_content/',
            {'idea_data': idea_data},
            format='json'
        )

        assert response.status_code == 201, \
            f"Expected 201, got {response.status_code}: {response.data}"
        assert 'content_piece' in response.data

        # Verify the custom agent role was used
        content_piece = ContentPiece.objects.get(project=project)
        assert content_piece.content is not None

    def test_english_custom_style_generation(
        self, authenticated_client, test_other_project, english_custom_style,
        mock_all_openai, test_agent_roles
    ):
        """
        Test that custom style generation works with English (no language conversion).

        This test should PASS even with the bug because:
        1. custom_style.language_code = 'en'
        2. Code skips the if block: if effective_language != 'en'
        3. Never tries to import get_language_name

        This demonstrates that the bug only affects non-English languages.
        """
        project = test_other_project

        idea_data = {
            'idea': 'Write about a man fishing on a boat at dawn',
            'word_count': 200,
            'custom_style_id': english_custom_style.id
        }

        response = authenticated_client.post(
            f'/api/projects/{project.id}/generate_content/',
            {'idea_data': idea_data},
            format='json'
        )

        # This should work even with the bug (language is 'en')
        assert response.status_code == 201, \
            f"Expected 201, got {response.status_code}: {response.data}"
        assert 'content_piece' in response.data

        content_piece = ContentPiece.objects.get(project=project)
        assert content_piece.content is not None

    def test_other_content_without_custom_style(
        self, authenticated_client, test_other_project, mock_all_openai, test_agent_roles
    ):
        """
        Test that 'other' content type works without custom style (fallback).

        This should work because when no custom_style_id is provided,
        the code uses standard prompt assembly and doesn't trigger the import.
        """
        project = test_other_project

        idea_data = {
            'idea': 'Write a short story about discovery',
            'word_count': 250
            # No custom_style_id provided
        }

        response = authenticated_client.post(
            f'/api/projects/{project.id}/generate_content/',
            {'idea_data': idea_data},
            format='json'
        )

        assert response.status_code == 201, \
            f"Expected 201, got {response.status_code}: {response.data}"
        assert 'content_piece' in response.data

        content_piece = ContentPiece.objects.get(project=project)
        assert content_piece.content is not None
