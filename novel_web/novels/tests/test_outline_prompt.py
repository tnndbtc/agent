"""
Test to verify that outline generation prompts explicitly require exact chapter counts.

This test should FAIL with the current code and PASS after the fix.
"""

import pytest
from unittest.mock import patch, Mock
from novels.services import OutlineService


@pytest.mark.django_db
class TestOutlinePromptExplicitness:
    """Test that outline prompts explicitly state the required number of chapters."""

    def test_outline_prompt_includes_exact_count_requirement(self, test_project):
        """
        Test that outline generation prompt explicitly requires exact chapter count.

        This test should FAIL with current code because the prompt uses vague wording
        like "For each chapter outline" instead of "exactly N chapters".
        """
        from langchain_core.messages import HumanMessage, SystemMessage

        # Mock ChatOpenAI to capture the actual prompt sent
        captured_messages = []

        def mock_invoke(messages):
            """Capture messages and return mock response."""
            captured_messages.extend(messages)

            # Return mock response
            mock_response = Mock()
            mock_response.content = '[{"number": 1, "title": "Test Chapter", "summary": "Test", "events": "Test events", "pacing": "medium", "setting": "Test", "word_count_target": 3000}]'
            mock_response.response_metadata = {
                'token_usage': {
                    'prompt_tokens': 100,
                    'completion_tokens': 50,
                    'total_tokens': 150
                }
            }
            return mock_response

        with patch('langchain_openai.ChatOpenAI') as mock_chat_class:
            # Create mock instance
            mock_instance = Mock()
            mock_instance.invoke = Mock(side_effect=mock_invoke)
            mock_chat_class.return_value = mock_instance

            # Call OutlineService.create_outline with num_chapters=1
            plot_data = {
                # Removed 'premise' - deprecated field
                'themes': 'Testing, Quality Assurance',
                'conflict': 'Bugs vs Developers'
            }

            OutlineService.create_outline(
                project=test_project,
                plot_data=plot_data,
                num_chapters=1,
                user_language='en'
            )

        # Extract the user message content (should be HumanMessage)
        user_message = None
        for msg in captured_messages:
            if isinstance(msg, HumanMessage) or (hasattr(msg, '__class__') and msg.__class__.__name__ == 'HumanMessage'):
                user_message = msg.content
                break

        assert user_message is not None, "No HumanMessage found in captured messages"

        print("\n" + "="*80)
        print("CAPTURED PROMPT:")
        print("="*80)
        print(user_message)
        print("="*80 + "\n")

        # Test 1: Should NOT contain vague "for each" wording
        # This assertion should FAIL with current code
        assert "For each chapter outline, provide" not in user_message, \
            "FAIL: Prompt uses vague 'For each chapter outline' wording instead of explicit count"

        # Test 2: Should NOT contain generic numbering pattern
        # This assertion should FAIL with current code
        assert "number: Chapter number (1, 2, 3, ...)" not in user_message, \
            "FAIL: Prompt shows generic numbering pattern instead of specific count requirement"

        # Test 3: Should contain explicit "exactly 1" requirement
        # This assertion should FAIL with current code
        user_message_lower = user_message.lower()
        has_explicit_count = (
            "exactly 1 chapter outline" in user_message_lower or
            "must create exactly 1" in user_message_lower or
            "you must create exactly 1" in user_message_lower
        )
        assert has_explicit_count, \
            "FAIL: Prompt must explicitly state 'exactly 1 chapter outline' or similar"

        # Test 4: Should require exact array size in JSON format instruction
        # This assertion should FAIL with current code
        has_exact_array_requirement = (
            "array with exactly 1" in user_message_lower or
            "json array with exactly 1" in user_message_lower or
            "exactly 1 chapter object" in user_message_lower
        )
        assert has_exact_array_requirement, \
            "FAIL: Prompt must explicitly require 'array with exactly 1 object' in format instruction"

    def test_outline_prompt_with_multiple_chapters(self, test_project):
        """
        Test that outline generation prompt works correctly for multiple chapters.

        This test verifies the same explicit requirements for num_chapters=3.
        """
        from langchain_core.messages import HumanMessage

        captured_messages = []

        def mock_invoke(messages):
            captured_messages.extend(messages)
            mock_response = Mock()
            mock_response.content = '[{"number": 1, "title": "Ch1", "summary": "Test", "events": "Test events 1", "pacing": "medium", "setting": "Test", "word_count_target": 3000}, {"number": 2, "title": "Ch2", "summary": "Test", "events": "Test events 2", "pacing": "medium", "setting": "Test", "word_count_target": 3000}, {"number": 3, "title": "Ch3", "summary": "Test", "events": "Test events 3", "pacing": "medium", "setting": "Test", "word_count_target": 3000}]'
            mock_response.response_metadata = {'token_usage': {'prompt_tokens': 100, 'completion_tokens': 150, 'total_tokens': 250}}
            return mock_response

        with patch('langchain_openai.ChatOpenAI') as mock_chat_class:
            mock_instance = Mock()
            mock_instance.invoke = Mock(side_effect=mock_invoke)
            mock_chat_class.return_value = mock_instance

            OutlineService.create_outline(
                project=test_project,
                plot_data={'themes': 'Test themes', 'conflict': 'Test conflict'},
                num_chapters=3,
                user_language='en'
            )

        user_message = None
        for msg in captured_messages:
            if isinstance(msg, HumanMessage) or (hasattr(msg, '__class__') and msg.__class__.__name__ == 'HumanMessage'):
                user_message = msg.content
                break

        assert user_message is not None

        user_message_lower = user_message.lower()

        # Should contain "exactly 3" somewhere
        assert "exactly 3" in user_message_lower, \
            "FAIL: Prompt must explicitly state 'exactly 3' for num_chapters=3"

        # Should mention "3 chapter outlines" or similar
        has_plural_explicit = (
            "exactly 3 chapter outlines" in user_message_lower or
            "must create exactly 3" in user_message_lower or
            "create exactly 3" in user_message_lower
        )
        assert has_plural_explicit, \
            "FAIL: Prompt must use explicit phrasing like 'exactly 3 chapter outlines'"
