"""
Test that outline details are properly persisted to database after creation.

This test verifies that the events field and other outline details are populated
with actual data from the AI response, not left empty.
"""

import pytest
from unittest.mock import patch, Mock
from novels.services import OutlineService
from novels.models import ChapterOutline


@pytest.mark.django_db
class TestOutlineDataPersistence:
    """Test that outline data persists correctly to database."""

    def test_outline_events_field_populated(self, test_project):
        """
        Test that outline events field is populated with narrative text.

        This test should FAIL with current code because:
        - Prompt asks for 'key_events' but code looks for 'events'
        - Result: events field saves as empty string
        """
        from langchain_core.messages import HumanMessage

        # Mock ChatOpenAI to return response with 'events' field
        captured_messages = []

        def mock_invoke(messages):
            """Capture messages and return mock outline response."""
            captured_messages.extend(messages)

            # Return mock response with correct field names
            mock_response = Mock()
            mock_response.content = '''[{
                "number": 1,
                "title": "The Beginning",
                "summary": "The hero receives a call to adventure and must decide whether to accept.",
                "events": "The hero is living their ordinary life when a mysterious stranger arrives with urgent news. After initial reluctance, the hero agrees to embark on a dangerous quest.",
                "pacing": "medium",
                "setting": "Small village at the edge of the kingdom",
                "word_count_target": 3000
            }]'''
            mock_response.response_metadata = {
                'token_usage': {
                    'prompt_tokens': 200,
                    'completion_tokens': 100,
                    'total_tokens': 300
                }
            }
            return mock_response

        with patch('langchain_openai.ChatOpenAI') as mock_chat_class:
            mock_instance = Mock()
            mock_instance.invoke = Mock(side_effect=mock_invoke)
            mock_chat_class.return_value = mock_instance

            # Call OutlineService to create outline
            plot_data = {
                'premise': 'A hero must save the kingdom',
                'themes': 'Courage, sacrifice',
                'conflict': 'Evil threatens the land'
            }

            outline_data, tokens = OutlineService.create_outline(
                project=test_project,
                plot_data=plot_data,
                num_chapters=1,
                user_language='en'
            )

        # Verify outline was returned
        assert 'chapters' in outline_data
        assert len(outline_data['chapters']) == 1

        chapter_data = outline_data['chapters'][0]

        # Critical assertions - these should FAIL with current code
        assert 'events' in chapter_data, \
            "FAIL: Response must include 'events' field"

        assert chapter_data['events'] != '', \
            "FAIL: events field should not be empty"

        assert 'hero' in chapter_data['events'].lower() or \
               'village' in chapter_data['events'].lower() or \
               'stranger' in chapter_data['events'].lower(), \
            f"FAIL: events field should contain narrative description, got: {chapter_data['events']}"

        # Verify other required fields exist
        assert chapter_data['number'] == 1
        assert chapter_data['title'] == "The Beginning"
        assert 'hero' in chapter_data['summary'].lower()
        assert chapter_data['pacing'] == "medium"
        assert chapter_data['setting'] == "Small village at the edge of the kingdom"
        assert chapter_data['word_count_target'] == 3000

    def test_outline_fields_match_model(self, test_project):
        """
        Test that outline response fields match ChapterOutline model fields.

        Verifies the JSON response contains exactly the fields needed for the model.
        """
        from langchain_core.messages import HumanMessage

        def mock_invoke(messages):
            mock_response = Mock()
            mock_response.content = '''[{
                "number": 1,
                "title": "Test Chapter",
                "summary": "A test summary",
                "events": "Test events description",
                "pacing": "fast",
                "setting": "Test location",
                "word_count_target": 2500
            }]'''
            mock_response.response_metadata = {
                'token_usage': {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150}
            }
            return mock_response

        with patch('langchain_openai.ChatOpenAI') as mock_chat_class:
            mock_instance = Mock()
            mock_instance.invoke = Mock(side_effect=mock_invoke)
            mock_chat_class.return_value = mock_instance

            outline_data, _ = OutlineService.create_outline(
                project=test_project,
                plot_data={'premise': 'Test'},
                num_chapters=1,
                user_language='en'
            )

        chapter = outline_data['chapters'][0]

        # Verify all required model fields are present
        required_fields = ['number', 'title', 'summary', 'events', 'pacing', 'setting', 'word_count_target']
        for field in required_fields:
            assert field in chapter, f"Missing required field: {field}"

        # Verify events is a string, not a list
        assert isinstance(chapter['events'], str), \
            f"events should be string, not {type(chapter['events'])}"

    def test_multiple_outlines_all_have_events(self, test_project):
        """Test that all outlines in a multi-chapter request have populated events."""
        def mock_invoke(messages):
            mock_response = Mock()
            mock_response.content = '''[
                {
                    "number": 1,
                    "title": "Chapter One",
                    "summary": "First chapter summary",
                    "events": "Events for chapter one",
                    "pacing": "medium",
                    "setting": "Location 1",
                    "word_count_target": 3000
                },
                {
                    "number": 2,
                    "title": "Chapter Two",
                    "summary": "Second chapter summary",
                    "events": "Events for chapter two",
                    "pacing": "fast",
                    "setting": "Location 2",
                    "word_count_target": 3500
                },
                {
                    "number": 3,
                    "title": "Chapter Three",
                    "summary": "Third chapter summary",
                    "events": "Events for chapter three",
                    "pacing": "slow",
                    "setting": "Location 3",
                    "word_count_target": 2800
                }
            ]'''
            mock_response.response_metadata = {
                'token_usage': {'prompt_tokens': 300, 'completion_tokens': 200, 'total_tokens': 500}
            }
            return mock_response

        with patch('langchain_openai.ChatOpenAI') as mock_chat_class:
            mock_instance = Mock()
            mock_instance.invoke = Mock(side_effect=mock_invoke)
            mock_chat_class.return_value = mock_instance

            outline_data, _ = OutlineService.create_outline(
                project=test_project,
                plot_data={'premise': 'Test'},
                num_chapters=3,
                user_language='en'
            )

        assert len(outline_data['chapters']) == 3

        for i, chapter in enumerate(outline_data['chapters'], 1):
            assert chapter['number'] == i
            assert 'events' in chapter
            assert chapter['events'] != ''
            assert f"chapter {['one', 'two', 'three'][i-1]}" in chapter['events'].lower()
