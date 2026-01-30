"""
Test to verify that chapter generation prompts explicitly emphasize act context.

This test ensures that when writing chapter content, the AI prompt clearly states
which act the chapter belongs to, preventing chapters from being written with
incorrect tone/pacing for their story position.

This test captures the actual prompts sent to the AI and verifies that act
information is properly emphasized.
"""

import pytest
from unittest.mock import patch, Mock
from novels.services import WritingService
from novels.models import Act, Plot


@pytest.mark.django_db
class TestChapterPromptActEmphasis:
    """Test that chapter generation prompts explicitly emphasize act context."""

    def test_chapter_prompt_includes_act_emphasis(self, test_project):
        """
        Test that chapter prompt includes explicit act emphasis in user message.

        This test verifies the main act emphasis feature: the prompt should clearly
        state "THIS CHAPTER IS PART OF ACT X" to ensure the AI writes with appropriate
        tone and pacing for the story position.
        """
        # Setup: Create plot with acts
        plot = Plot.objects.create(
            project=test_project,
            conflict='Protagonist must overcome inner doubts to save their world'
        )

        act = Act.objects.create(
            plot=plot,
            act_number=1,
            subject='SETUP',
            description='Introduction to the protagonist and their ordinary world. Establish the status quo before the inciting incident disrupts everything.'
        )

        # Mock OpenAI to capture messages
        captured_messages = []

        def mock_create(**kwargs):
            """Capture messages and return mock response."""
            captured_messages.append(kwargs.get('messages', []))

            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"title": "The Ordinary World", "content": "Test chapter content here. This is the generated story text."}'
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 500
            mock_response.usage.completion_tokens = 200
            mock_response.usage.total_tokens = 700
            return mock_response

        with patch('novels.ai_client.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_client.chat.completions.create = Mock(side_effect=mock_create)
            mock_openai_class.return_value = mock_client

            # Call WritingService.write_chapter_from_act
            WritingService.write_chapter_from_act(
                project=test_project,
                act=act,
                language='English'
            )

        # Extract ALL messages and combine content (5-message format spreads across roles)
        all_content = []
        for messages_list in captured_messages:
            for msg in messages_list:
                if msg.get('content'):
                    all_content.append(msg['content'])

        assert all_content, "No messages found in captured messages"

        # Combine all message content for searching
        combined_content = "\n".join(all_content)

        print("\n" + "="*80)
        print("CAPTURED CHAPTER GENERATION PROMPT (ALL MESSAGES):")
        print("="*80)
        print(combined_content)
        print("="*80 + "\n")

        # Critical assertions - verify act emphasis exists
        assert "**Current Act (for this chapter):**" in combined_content, \
            "FAIL: Prompt must include '**Current Act (for this chapter):**' header"

        assert "Act 1 (SETUP)" in combined_content, \
            "FAIL: Prompt must include 'Act 1 (SETUP)'"

        # percentage field removed in migration 0023

        assert "Introduction to the protagonist and their ordinary world" in combined_content, \
            "FAIL: Prompt must include full act description"

    def test_chapter_prompt_includes_all_act_details(self, test_project):
        """
        Test that all required act details appear in the chapter generation prompt.

        Verifies that act number, subject, and description are all
        included to provide complete context for the AI.
        """
        # Setup: Create plot with Act 2
        plot = Plot.objects.create(
            project=test_project,
            conflict='Heroes face escalating obstacles'
        )

        act = Act.objects.create(
            plot=plot,
            act_number=2,
            subject='CONFRONTATION',
            description='Rising action and complications. The protagonist faces challenges that test their resolve and force growth.'
        )

        # Mock OpenAI
        captured_messages = []

        def mock_create(**kwargs):
            captured_messages.append(kwargs.get('messages', []))
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"title": "The Darkest Hour", "content": "Chapter content..."}'
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 400
            mock_response.usage.completion_tokens = 300
            mock_response.usage.total_tokens = 700
            return mock_response

        with patch('novels.ai_client.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_client.chat.completions.create = Mock(side_effect=mock_create)
            mock_openai_class.return_value = mock_client

            WritingService.write_chapter_from_act(
                project=test_project,
                act=act,
                language='English'
            )

        # Extract ALL messages and combine content (5-message format spreads across roles)
        all_content = []
        for messages_list in captured_messages:
            for msg in messages_list:
                if msg.get('content'):
                    all_content.append(msg['content'])

        assert all_content, "No messages found in captured messages"

        # Combine all message content for searching
        combined_content = "\n".join(all_content)

        # Verify each detail individually for clear error messages
        assert "Act 2" in combined_content, \
            "FAIL: Prompt must include 'Act 2' (act number)"

        assert "CONFRONTATION" in combined_content, \
            "FAIL: Prompt must include 'CONFRONTATION' (act subject)"

        # percentage field removed in migration 0023

        assert "Rising action and complications" in combined_content, \
            "FAIL: Prompt must include act description text"

        assert "challenges that test their resolve" in combined_content, \
            "FAIL: Prompt must include complete act description"

    def test_chapter_prompt_with_multiple_acts_shows_current_act(self, test_project):
        """
        Test that when project has multiple acts, the prompt emphasizes the CURRENT act.

        This ensures chapters are written with the correct tone for their position
        in the story, not confused with other acts.
        """
        # Setup: Create plot with all 3 acts
        plot = Plot.objects.create(
            project=test_project,
            conflict='Hero must save the world'
        )

        act1 = Act.objects.create(
            plot=plot,
            act_number=1,
            subject='SETUP',
            description='Ordinary world and call to adventure'
        )

        act2 = Act.objects.create(
            plot=plot,
            act_number=2,
            subject='CONFRONTATION',
            description='Tests, allies, enemies, and approach'
        )

        act3 = Act.objects.create(
            plot=plot,
            act_number=3,
            subject='RESOLUTION',
            description='Climax and return home'
        )

        # Mock OpenAI
        captured_messages = []

        def mock_create(**kwargs):
            captured_messages.append(kwargs.get('messages', []))
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"title": "The Final Battle", "content": "Final battle content..."}'
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 600
            mock_response.usage.completion_tokens = 500
            mock_response.usage.total_tokens = 1100
            return mock_response

        with patch('novels.ai_client.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_client.chat.completions.create = Mock(side_effect=mock_create)
            mock_openai_class.return_value = mock_client

            # Write chapter from Act 3 (final act)
            WritingService.write_chapter_from_act(
                project=test_project,
                act=act3,
                language='English'
            )

        # Extract ALL messages and combine content (5-message format spreads across roles)
        all_content = []
        for messages_list in captured_messages:
            for msg in messages_list:
                if msg.get('content'):
                    all_content.append(msg['content'])

        assert all_content, "No messages found in captured messages"

        # Combine all message content for searching
        combined_content = "\n".join(all_content)

        # Should emphasize Act 3 (CURRENT act), not Act 1 or Act 2
        assert "Act 3 (RESOLUTION)" in combined_content, \
            "FAIL: Prompt must emphasize Act 3 (current act for this chapter)"

        assert "Climax and return home" in combined_content, \
            "FAIL: Prompt must include Act 3 description"

        # Should NOT emphasize other acts in the main act emphasis section
        # (They may appear in story structure context, but not in the emphasis header)
        combined_lines = combined_content.split('\n')
        act_emphasis_section = []
        in_emphasis = False
        for line in combined_lines:
            if "**Current Act (for this chapter):**" in line:
                in_emphasis = True
            if in_emphasis:
                act_emphasis_section.append(line)
                if line.strip() == '' and len(act_emphasis_section) > 3:
                    break

        act_emphasis_text = '\n'.join(act_emphasis_section)
        assert "Act 3" in act_emphasis_text, \
            "Act emphasis section must mention Act 3"

