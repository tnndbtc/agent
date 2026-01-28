"""
Test that actually runs write_chapter_task and reproduces the production error.
Also tests the template rendering for chapter grouping by acts.
"""
import uuid
import logging
import re
from unittest.mock import patch, Mock, MagicMock
from django.test import TransactionTestCase, TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from novels.models import NovelProject, Plot, Act, Example, GenerationTask, Chapter
from novels.tasks import write_chapter_task
from io import StringIO


class TestWriteChapterTaskActual(TransactionTestCase):
    """Test that actually runs write_chapter_task to reproduce the bug."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='test', password='test')
        self.project = NovelProject.objects.create(
            user=self.user,
            title="Test Novel",
            target_language='en',
            chroma_collection_name=f"test_{uuid.uuid4().hex[:8]}"
        )
        self.plot = Plot.objects.create(project=self.project)
        self.act = Act.objects.create(
            plot=self.plot,
            act_number=1,
            subject="SETUP",
            description="Beginning"
        )
        self.example = Example.objects.create(
            category='opening',
            locale='English',
            title='Test',
            description='Test',
            content='Test content',
            is_good=True
        )

    @patch('langchain_openai.ChatOpenAI')  # Mock LangChain OpenAI
    @patch('novels.tasks.update_task_progress')
    def test_actual_task_execution_with_act_id(self, mock_update_progress, mock_chat_openai):
        """
        Actually run write_chapter_task with act_id to reproduce the bug.
        This test validates the complete workflow of creating chapters from Acts.
        """
        # Setup logging to capture the error
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(levelname)s %(name)s - %(message)s')
        handler.setFormatter(formatter)

        # Add handler to the tasks logger
        logger = logging.getLogger('novels.tasks')
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)

        # Mock the LangChain ChatOpenAI to return valid content
        from unittest.mock import MagicMock
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm

        # Mock the invoke method to return JSON formatted chapter content
        mock_response = MagicMock()
        mock_response.content = '{"title": "The Beginning", "content": "The story begins here with vivid descriptions and engaging dialogue."}'
        mock_response.response_metadata = {'token_usage': {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150}}
        mock_llm.invoke.return_value = mock_response

        # Create GenerationTask
        task = GenerationTask.objects.create(
            project=self.project,
            user=self.user,
            task_type='chapter',
            celery_task_id='test-celery-task-id',
            input_data={
                'act_id': str(self.act.id),
                'target_word_count': 100,
                'writing_style': 'literary',
                'example_id': str(self.example.id)
            }
        )

        print("\n=== Running write_chapter_task with act_id ===")

        try:
            # Call the task using Celery's apply method
            result = write_chapter_task.apply(
                args=[],
                kwargs={
                    'task_id': str(task.id),
                    'project_id': str(self.project.id),
                    'act_id': str(self.act.id),
                    'target_word_count': 100,
                    'writing_style': 'literary',
                    'example_id': str(self.example.id),
                    'language': 'English',
                    'iterative_mode': False  # Disable iterative mode for simpler test
                },
                throw=False  # Don't throw exceptions, return them
            )

            # Check the result
            if result.failed():
                print(f"✗ Task failed with error: {result.info}")
                # Check if it's the old AttributeError we were trying to fix
                if "'NoneType' object has no attribute" in str(result.info):
                    self.fail(f"The AttributeError bug still exists: {result.info}")
                else:
                    self.fail(f"Task failed with different error: {result.info}")
            else:
                print("✓ Task completed successfully - bug is fixed!")

        except Exception as e:
            print(f"✗ Unexpected error during task execution: {e}")
            raise
        finally:
            # Clean up logger
            logger.removeHandler(handler)

        # Check the log output
        log_output = log_capture.getvalue()
        print(f"\n=== Captured Log Output ===")
        print(log_output if log_output else "(No error logged)")
        print("===========================\n")

        # Check that no error messages are in logs (bug is fixed)
        if "Write chapter task failed" in log_output:
            print(f"✗ Found error in logs: {log_output}")
        else:
            print(f"✓ No error messages in logs - task ran cleanly")

        # Check task status
        task.refresh_from_db()
        print(f"Task status: {task.status}")
        print(f"Task error: {task.error_message}")

        # The task should complete successfully now that the bug is fixed
        self.assertEqual(task.status, 'completed',
                        f"Task should complete but has status: {task.status}, error: {task.error_message}")
        # Check for no error (either None or empty string)
        self.assertIn(task.error_message, [None, ''], "Task should complete without errors")

        # Verify that the chapter was created and associated with the act
        chapters = Chapter.objects.filter(project=self.project)
        self.assertEqual(chapters.count(), 1, "Should have created one chapter")

        chapter = chapters.first()
        self.assertIsNotNone(chapter, "Chapter should exist")
        self.assertEqual(chapter.act_id, self.act.id, "Chapter should be directly associated with the act")

        print(f"✓ Chapter created with direct act association: act_id={chapter.act_id}")

    @patch('langchain_openai.ChatOpenAI')
    @patch('novels.tasks.update_task_progress')
    def test_chapter_renumbering_with_existing_chapters(self, mock_update_progress, mock_chat_openai):
        """
        Test that creating a chapter for Act 1 after chapters for Acts 2 and 3 exist
        properly renumbers all chapters without unique constraint violations.

        This test reproduces the bug where:
        1. Chapter 1 exists for Act 1
        2. Chapter 2 exists for Act 2
        3. Chapter 3 exists for Act 3
        4. Create new chapter for Act 1 → should become Chapter 2
        5. Renumbering should work without constraint violations
        """
        print("\n=== Testing Chapter Renumbering with Existing Chapters ===")

        # Create Act 2 and Act 3
        act2 = Act.objects.create(
            plot=self.plot,
            act_number=2,
            subject="CONFLICT",
            description="Rising action"
        )
        act3 = Act.objects.create(
            plot=self.plot,
            act_number=3,
            subject="RESOLUTION",
            description="Climax and ending"
        )

        # Mock the LangChain ChatOpenAI
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm

        # Mock response for chapter generation
        def create_mock_response(title):
            mock_response = MagicMock()
            mock_response.content = f'{{"title": "{title}", "content": "Chapter content for {title}"}}'
            mock_response.response_metadata = {'token_usage': {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150}}
            return mock_response

        mock_llm.invoke.return_value = create_mock_response("First Chapter")

        # Step 1: Create Chapter 1 for Act 1
        print("\nStep 1: Creating Chapter 1 for Act 1")
        task1 = GenerationTask.objects.create(
            project=self.project,
            user=self.user,
            task_type='chapter',
            celery_task_id='test-task-1',
            input_data={'act_id': str(self.act.id)}
        )

        result1 = write_chapter_task.apply(
            kwargs={
                'task_id': str(task1.id),
                'project_id': str(self.project.id),
                'act_id': str(self.act.id),
                'target_word_count': 100,
                'writing_style': 'literary',
                'example_id': str(self.example.id),
                'language': 'English',
                'iterative_mode': False
            },
            throw=False
        )

        self.assertFalse(result1.failed(), f"Chapter 1 creation failed: {result1.info if result1.failed() else ''}")

        # Step 2: Create Chapter 2 for Act 2
        print("Step 2: Creating Chapter 2 for Act 2")
        mock_llm.invoke.return_value = create_mock_response("Second Chapter")

        task2 = GenerationTask.objects.create(
            project=self.project,
            user=self.user,
            task_type='chapter',
            celery_task_id='test-task-2',
            input_data={'act_id': str(act2.id)}
        )

        result2 = write_chapter_task.apply(
            kwargs={
                'task_id': str(task2.id),
                'project_id': str(self.project.id),
                'act_id': str(act2.id),
                'target_word_count': 100,
                'writing_style': 'literary',
                'example_id': str(self.example.id),
                'language': 'English',
                'iterative_mode': False
            },
            throw=False
        )

        self.assertFalse(result2.failed(), f"Chapter 2 creation failed: {result2.info if result2.failed() else ''}")

        # Step 3: Create Chapter 3 for Act 3
        print("Step 3: Creating Chapter 3 for Act 3")
        mock_llm.invoke.return_value = create_mock_response("Third Chapter")

        task3 = GenerationTask.objects.create(
            project=self.project,
            user=self.user,
            task_type='chapter',
            celery_task_id='test-task-3',
            input_data={'act_id': str(act3.id)}
        )

        result3 = write_chapter_task.apply(
            kwargs={
                'task_id': str(task3.id),
                'project_id': str(self.project.id),
                'act_id': str(act3.id),
                'target_word_count': 100,
                'writing_style': 'literary',
                'example_id': str(self.example.id),
                'language': 'English',
                'iterative_mode': False
            },
            throw=False
        )

        self.assertFalse(result3.failed(), f"Chapter 3 creation failed: {result3.info if result3.failed() else ''}")

        # Verify we have 3 chapters
        chapters_before = Chapter.objects.filter(project=self.project).order_by('chapter_number')
        print(f"\nChapters before creating 4th chapter:")
        for ch in chapters_before:
            print(f"  Chapter {ch.chapter_number} (order_key={ch.order_key}): {ch.title} - Act {ch.act.act_number if ch.act else 'None'}")

        self.assertEqual(chapters_before.count(), 3, "Should have 3 chapters before creating 4th")

        # Step 4: Create another chapter for Act 1 - THIS SHOULD TRIGGER THE BUG
        print("\nStep 4: Creating another chapter for Act 1 (should be inserted as Chapter 2)")
        mock_llm.invoke.return_value = create_mock_response("Fourth Chapter for Act 1")

        task4 = GenerationTask.objects.create(
            project=self.project,
            user=self.user,
            task_type='chapter',
            celery_task_id='test-task-4',
            input_data={'act_id': str(self.act.id)}
        )

        result4 = write_chapter_task.apply(
            kwargs={
                'task_id': str(task4.id),
                'project_id': str(self.project.id),
                'act_id': str(self.act.id),
                'target_word_count': 100,
                'writing_style': 'literary',
                'example_id': str(self.example.id),
                'language': 'English',
                'iterative_mode': False
            },
            throw=False
        )

        # Check if it failed
        if result4.failed():
            print(f"✗ Chapter 4 creation failed (THIS IS THE BUG): {result4.info}")
            # Check if it's the constraint violation we expect
            error_msg = str(result4.info)
            if "duplicate key value violates unique constraint" in error_msg:
                print("✓ Successfully reproduced the unique constraint violation bug!")
                self.fail(f"BUG REPRODUCED: {error_msg}")
            else:
                self.fail(f"Chapter 4 creation failed with unexpected error: {result4.info}")
        else:
            print("✓ Chapter 4 created successfully - bug is fixed!")

        # Verify final state
        chapters_after = Chapter.objects.filter(project=self.project).order_by('order_key')
        print(f"\nFinal chapters (ordered by order_key):")
        for ch in chapters_after:
            print(f"  Chapter {ch.chapter_number} (order_key={ch.order_key}): {ch.title} - Act {ch.act.act_number if ch.act else 'None'}")

        # Verify we have 4 chapters
        self.assertEqual(chapters_after.count(), 4, "Should have 4 chapters after creating all")

        # Verify chapter numbers are sequential
        chapter_numbers = [ch.chapter_number for ch in chapters_after]
        self.assertEqual(chapter_numbers, [1, 2, 3, 4], "Chapter numbers should be sequential 1-4")

        # Verify chapters are in correct act order
        act_numbers = [ch.act.act_number if ch.act else 0 for ch in chapters_after]
        self.assertEqual(act_numbers, [1, 1, 2, 3], "Chapters should be ordered by act: 1, 1, 2, 3")

        print("✓ All assertions passed - chapters properly renumbered!")


class TestActChapterGroupingBug(TestCase):
    """Test that reproduces the Act 2 chapter grouping bug in template rendering."""

    def setUp(self):
        """Set up test data with two acts."""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')  # Use login instead of force_login

        self.project = NovelProject.objects.create(
            user=self.user,
            title="Test Novel for Grouping",
            target_language='en',
            chroma_collection_name=f"test_{uuid.uuid4().hex[:8]}"
        )

        self.plot = Plot.objects.create(project=self.project)

        # Create Act 1
        self.act1 = Act.objects.create(
            plot=self.plot,
            act_number=1,
            subject="Introduction",
            description="Setting the scene"
        )

        # Create Act 2
        self.act2 = Act.objects.create(
            plot=self.plot,
            act_number=2,
            subject="Rising Action",
            description="Building tension"
        )

        # Create example for chapter generation
        self.example = Example.objects.create(
            category='opening',
            locale='English',
            title='Test Example',
            description='Test description',
            content='Example content for testing',
            is_good=True
        )

    def test_chapter_grouping_by_acts(self):
        """Test that chapters are correctly grouped under their assigned acts in the template."""

        # Create multiple chapters assigned to different acts
        chapter1_act1 = Chapter.objects.create(
            project=self.project,
            act=self.act1,  # Assigned to Act 1
            chapter_number=1,
            title="First Chapter for Act 1",
            content="This chapter belongs to Act 1",
            word_count=100,
            language='English',
            writing_style='literary'
        )

        chapter2_act2 = Chapter.objects.create(
            project=self.project,
            act=self.act2,  # Assigned to Act 2
            chapter_number=2,
            title="Chapter for Act 2",
            content="This chapter belongs to Act 2",
            word_count=100,
            language='English',
            writing_style='literary'
        )

        chapter3_act1 = Chapter.objects.create(
            project=self.project,
            act=self.act1,  # Another chapter for Act 1
            chapter_number=3,
            title="Second Chapter for Act 1",
            content="This also belongs to Act 1",
            word_count=100,
            language='English',
            writing_style='literary'
        )

        # Debug: Verify database state
        print("\n=== DATABASE STATE ===")
        print(f"Act 1 ID: {self.act1.id} (type: {type(self.act1.id).__name__})")
        print(f"Act 2 ID: {self.act2.id} (type: {type(self.act2.id).__name__})")
        print(f"Chapter 1: act_id={chapter1_act1.act_id} -> Act {chapter1_act1.act.act_number if chapter1_act1.act else 'None'}")
        print(f"Chapter 2: act_id={chapter2_act2.act_id} -> Act {chapter2_act2.act.act_number if chapter2_act2.act else 'None'}")
        print(f"Chapter 3: act_id={chapter3_act1.act_id} -> Act {chapter3_act1.act.act_number if chapter3_act1.act else 'None'}")

        # Test the database relationships are correct
        self.assertEqual(chapter1_act1.act_id, self.act1.id,
                        f"Chapter 1 should have act_id={self.act1.id}, but has {chapter1_act1.act_id}")
        self.assertEqual(chapter2_act2.act_id, self.act2.id,
                        f"Chapter 2 should have act_id={self.act2.id}, but has {chapter2_act2.act_id}")
        self.assertEqual(chapter3_act1.act_id, self.act1.id,
                        f"Chapter 3 should have act_id={self.act1.id}, but has {chapter3_act1.act_id}")

        # Fetch the project detail page (handle i18n URL patterns)
        from django.utils import translation
        translation.activate('en')
        url = reverse('novels:project_detail', kwargs={'pk': self.project.id})
        response = self.client.get(url, follow=True)  # Follow redirects if any

        # Check response status
        self.assertEqual(response.status_code, 200,
                        f"Expected status 200, got {response.status_code}. Content: {response.content[:500]}")

        # Extract the HTML content
        html_content = response.content.decode('utf-8')

        # Save HTML for debugging
        with open('/tmp/test_chapter_grouping.html', 'w') as f:
            f.write(html_content)
        print("\nHTML saved to /tmp/test_chapter_grouping.html for debugging")

        # Helper function to find chapters in a specific act section
        def find_chapters_in_act_section(html, act_number):
            """Find all chapter titles that appear in a specific act's section."""
            # Look for the act section with data-act-id
            pattern = rf'data-act-id="{act_number}".*?(?=data-act-id="|Other Chapters|$)'
            match = re.search(pattern, html, re.DOTALL)

            if match:
                section_html = match.group(0)
                # Extract chapter titles from this section
                chapter_pattern = r'<h4>(.*?)</h4>'
                chapters = re.findall(chapter_pattern, section_html)
                return chapters
            return []

        # Find chapters grouped under each act
        chapters_under_act1 = find_chapters_in_act_section(html_content, 1)
        chapters_under_act2 = find_chapters_in_act_section(html_content, 2)

        print("\n=== TEMPLATE RENDERING RESULT ===")
        print(f"Chapters found under Act 1: {chapters_under_act1}")
        print(f"Chapters found under Act 2: {chapters_under_act2}")

        # Check if act sections exist in the HTML at all
        has_act1_section = f'data-act-id="1"' in html_content or 'Act 1:' in html_content
        has_act2_section = f'data-act-id="2"' in html_content or 'Act 2:' in html_content

        print(f"\nAct 1 section exists in HTML: {has_act1_section}")
        print(f"Act 2 section exists in HTML: {has_act2_section}")

        # Alternative: Look for chapters by searching for their proximity to act headers
        def find_chapter_after_act_header(html, chapter_title):
            """Find which act header appears before a chapter."""
            chapter_pos = html.find(chapter_title)
            if chapter_pos == -1:
                return None

            # Look backwards for the nearest Act header
            before_chapter = html[:chapter_pos]
            act_matches = list(re.finditer(r'Act (\d+):', before_chapter))
            if act_matches:
                last_match = act_matches[-1]
                return int(last_match.group(1))
            return None

        # Check where each chapter appears
        chapter1_appears_after_act = find_chapter_after_act_header(html_content, "First Chapter for Act 1")
        chapter2_appears_after_act = find_chapter_after_act_header(html_content, "Chapter for Act 2")
        chapter3_appears_after_act = find_chapter_after_act_header(html_content, "Second Chapter for Act 1")

        print(f"\n=== CHAPTER POSITIONS RELATIVE TO ACT HEADERS ===")
        print(f"'First Chapter for Act 1' appears after Act {chapter1_appears_after_act}")
        print(f"'Chapter for Act 2' appears after Act {chapter2_appears_after_act}")
        print(f"'Second Chapter for Act 1' appears after Act {chapter3_appears_after_act}")

        # MAIN ASSERTIONS - This is what we're actually testing
        # Chapters 1 and 3 should appear under Act 1
        # Chapter 2 should appear under Act 2

        error_msg = f"""
        Chapter grouping is incorrect!
        Expected:
          - Act 1 should contain: 'First Chapter for Act 1', 'Second Chapter for Act 1'
          - Act 2 should contain: 'Chapter for Act 2'

        Actual:
          - Chapters under Act 1: {chapters_under_act1}
          - Chapters under Act 2: {chapters_under_act2}

        Chapter positions relative to act headers:
          - 'First Chapter for Act 1' appears after Act {chapter1_appears_after_act}
          - 'Chapter for Act 2' appears after Act {chapter2_appears_after_act}
          - 'Second Chapter for Act 1' appears after Act {chapter3_appears_after_act}
        """

        # Test using proximity to act headers (more reliable than section parsing)
        self.assertEqual(chapter1_appears_after_act, 1,
                        f"Chapter 1 (for Act 1) appears after Act {chapter1_appears_after_act}, expected Act 1")
        self.assertEqual(chapter2_appears_after_act, 2,
                        f"Chapter 2 (for Act 2) appears after Act {chapter2_appears_after_act}, expected Act 2")
        self.assertEqual(chapter3_appears_after_act, 1,
                        f"Chapter 3 (for Act 1) appears after Act {chapter3_appears_after_act}, expected Act 1")

