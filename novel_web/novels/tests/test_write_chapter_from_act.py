"""
Test that actually runs write_chapter_task and reproduces the production error.
"""
import uuid
import logging
from unittest.mock import patch, Mock, MagicMock
from django.test import TransactionTestCase
from django.contrib.auth.models import User
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

        # Mock the invoke method to return chapter content
        mock_response = MagicMock()
        mock_response.content = "Chapter 1: The Beginning\n\nThe story begins here with vivid descriptions and engaging dialogue."
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
        self.assertIsNone(chapter.outline, "Chapter should not have an outline when created from act")

        print(f"✓ Chapter created with direct act association: act_id={chapter.act_id}")