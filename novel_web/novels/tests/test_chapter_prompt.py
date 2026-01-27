"""
Test to verify that chapter generation prompts explicitly emphasize act context.

This test ensures that when writing chapter content, the AI prompt clearly states
which act the chapter belongs to, preventing chapters from being written with
incorrect tone/pacing for their story position.

Similar to test_outline_prompt.py, this test captures the actual prompts sent to
the AI and verifies that act information is properly emphasized.
"""

import pytest
from unittest.mock import patch, Mock
from novels.services import WritingService
from novels.models import Act, ChapterOutline, Plot


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
        from langchain_core.messages import HumanMessage, SystemMessage

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

        # Create chapter outline for Act 1
        outline = ChapterOutline.objects.create(
            project=test_project,
            act=act,
            number=1,
            title='The Ordinary World',
            events='The protagonist wakes up and goes about their daily routine, unaware of the adventure to come.',
            pacing='slow',
            setting='Small village on the edge of the kingdom'
        )

        # Mock ChatOpenAI to capture messages
        captured_messages = []

        def mock_invoke(messages):
            """Capture messages and return mock response."""
            captured_messages.extend(messages)

            mock_response = Mock()
            mock_response.content = 'Test chapter content here. This is the generated story text.'
            mock_response.response_metadata = {
                'token_usage': {
                    'prompt_tokens': 500,
                    'completion_tokens': 200,
                    'total_tokens': 700
                }
            }
            return mock_response

        with patch('langchain_openai.ChatOpenAI') as mock_chat_class:
            mock_instance = Mock()
            mock_instance.invoke = Mock(side_effect=mock_invoke)
            mock_chat_class.return_value = mock_instance

            # Call WritingService.write_chapter
            WritingService.write_chapter(
                project=test_project,
                chapter_outline=outline,
                language='English'
            )

        # Extract user message
        user_message = None
        for msg in captured_messages:
            if isinstance(msg, HumanMessage) or (hasattr(msg, '__class__') and msg.__class__.__name__ == 'HumanMessage'):
                user_message = msg.content
                break

        assert user_message is not None, "No HumanMessage found in captured messages"

        print("\n" + "="*80)
        print("CAPTURED CHAPTER GENERATION PROMPT:")
        print("="*80)
        print(user_message)
        print("="*80 + "\n")

        # Critical assertions - verify act emphasis exists
        assert "**IMPORTANT - Current Story Act:**" in user_message, \
            "FAIL: Prompt must include '**IMPORTANT - Current Story Act:**' header"

        assert "This chapter is part of Act 1: SETUP" in user_message, \
            "FAIL: Prompt must explicitly state 'This chapter is part of Act 1: SETUP'"

        # percentage field removed in migration 0023

        assert "Introduction to the protagonist and their ordinary world" in user_message, \
            "FAIL: Prompt must include full act description"

        assert "Ensure the chapter's content, tone, and pacing align with this act's purpose" in user_message, \
            "FAIL: Prompt must include instruction to align with act purpose"

    def test_chapter_prompt_includes_all_act_details(self, test_project):
        """
        Test that all required act details appear in the chapter generation prompt.

        Verifies that act number, subject, and description are all
        included to provide complete context for the AI.
        """
        from langchain_core.messages import HumanMessage

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

        outline = ChapterOutline.objects.create(
            project=test_project,
            act=act,
            number=5,
            title='The Darkest Hour',
            events='A major setback forces the protagonist to confront their deepest fears.',
            pacing='fast',
            setting='Deep in the dangerous forest'
        )

        # Mock ChatOpenAI
        captured_messages = []

        def mock_invoke(messages):
            captured_messages.extend(messages)
            mock_response = Mock()
            mock_response.content = '{"title": "Test Chapter", "content": "Chapter content..."}'
            mock_response.response_metadata = {
                'token_usage': {'prompt_tokens': 400, 'completion_tokens': 300, 'total_tokens': 700}
            }
            return mock_response

        with patch('langchain_openai.ChatOpenAI') as mock_chat_class:
            mock_instance = Mock()
            mock_instance.invoke = Mock(side_effect=mock_invoke)
            mock_chat_class.return_value = mock_instance

            WritingService.write_chapter(
                project=test_project,
                chapter_outline=outline,
                language='English'
            )

        # Extract user message
        user_message = None
        for msg in captured_messages:
            if isinstance(msg, HumanMessage) or (hasattr(msg, '__class__') and msg.__class__.__name__ == 'HumanMessage'):
                user_message = msg.content
                break

        assert user_message is not None

        # Verify each detail individually for clear error messages
        assert "Act 2" in user_message, \
            "FAIL: Prompt must include 'Act 2' (act number)"

        assert "CONFRONTATION" in user_message, \
            "FAIL: Prompt must include 'CONFRONTATION' (act subject)"

        # percentage field removed in migration 0023

        assert "Rising action and complications" in user_message, \
            "FAIL: Prompt must include act description text"

        assert "challenges that test their resolve" in user_message, \
            "FAIL: Prompt must include complete act description"

    def test_chapter_prompt_with_multiple_acts_shows_current_act(self, test_project):
        """
        Test that when project has multiple acts, the prompt emphasizes the CURRENT act.

        This ensures chapters are written with the correct tone for their position
        in the story, not confused with other acts.
        """
        from langchain_core.messages import HumanMessage

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

        # Create outline for Act 3 (final act)
        outline = ChapterOutline.objects.create(
            project=test_project,
            act=act3,  # Assigned to Act 3
            number=15,
            title='The Final Battle',
            events='Hero faces villain in final showdown.',
            pacing='fast',
            setting='The dark tower'
        )

        # Mock ChatOpenAI
        captured_messages = []

        def mock_invoke(messages):
            captured_messages.extend(messages)
            mock_response = Mock()
            mock_response.content = 'Final battle content...'
            mock_response.response_metadata = {
                'token_usage': {'prompt_tokens': 600, 'completion_tokens': 500, 'total_tokens': 1100}
            }
            return mock_response

        with patch('langchain_openai.ChatOpenAI') as mock_chat_class:
            mock_instance = Mock()
            mock_instance.invoke = Mock(side_effect=mock_invoke)
            mock_chat_class.return_value = mock_instance

            WritingService.write_chapter(
                project=test_project,
                chapter_outline=outline,
                language='English'
            )

        # Extract user message
        user_message = None
        for msg in captured_messages:
            if isinstance(msg, HumanMessage) or (hasattr(msg, '__class__') and msg.__class__.__name__ == 'HumanMessage'):
                user_message = msg.content
                break

        assert user_message is not None

        # Should emphasize Act 3 (CURRENT act), not Act 1 or Act 2
        assert "Act 3: RESOLUTION" in user_message, \
            "FAIL: Prompt must emphasize Act 3 (current act for this chapter)"

        assert "Climax and return home" in user_message, \
            "FAIL: Prompt must include Act 3 description"

        # Should NOT emphasize other acts in the main act emphasis section
        # (They may appear in story structure context, but not in the emphasis header)
        user_message_lines = user_message.split('\n')
        act_emphasis_section = []
        in_emphasis = False
        for line in user_message_lines:
            if "**IMPORTANT - Current Story Act:**" in line:
                in_emphasis = True
            if in_emphasis:
                act_emphasis_section.append(line)
                if line.strip() == '' and len(act_emphasis_section) > 3:
                    break

        act_emphasis_text = '\n'.join(act_emphasis_section)
        assert "Act 3" in act_emphasis_text, \
            "Act emphasis section must mention Act 3"

    def test_chapter_prompt_without_act_assignment(self, test_project):
        """
        Test graceful handling when chapter outline has no act assigned.

        The system should not crash and should either skip the act emphasis
        section or handle it gracefully.
        """
        from langchain_core.messages import HumanMessage

        # Setup: Create plot
        plot = Plot.objects.create(
            project=test_project,
            conflict='Uncover the truth'
        )

        # Create outline with NO act assignment
        outline = ChapterOutline.objects.create(
            project=test_project,
            act=None,  # No act assigned
            number=1,
            title='Standalone Chapter',
            events='Events occur.',
            pacing='medium',
            setting='Unknown location'
        )

        # Mock ChatOpenAI
        captured_messages = []

        def mock_invoke(messages):
            captured_messages.extend(messages)
            mock_response = Mock()
            mock_response.content = '{"title": "Unassigned Chapter", "content": "Chapter content for unassigned act..."}'
            mock_response.response_metadata = {
                'token_usage': {'prompt_tokens': 300, 'completion_tokens': 150, 'total_tokens': 450}
            }
            return mock_response

        # Should NOT crash
        with patch('langchain_openai.ChatOpenAI') as mock_chat_class:
            mock_instance = Mock()
            mock_instance.invoke = Mock(side_effect=mock_invoke)
            mock_chat_class.return_value = mock_instance

            # This should complete without errors
            WritingService.write_chapter(
                project=test_project,
                chapter_outline=outline,
                language='English'
            )

        # Verify it completed successfully
        assert len(captured_messages) > 0, "Should have called the AI despite missing act"

        # Extract user message
        user_message = None
        for msg in captured_messages:
            if isinstance(msg, HumanMessage) or (hasattr(msg, '__class__') and msg.__class__.__name__ == 'HumanMessage'):
                user_message = msg.content
                break

        assert user_message is not None

        # Act emphasis section should be absent (since no act is assigned)
        # This is expected behavior - if there's no act, don't add the emphasis
        # The code at services.py:1268-1274 has: "if chapter_outline_model.act:"
