"""
Test for project detail view template rendering.
This test reproduces the template syntax error in project_detail.html.
"""
import uuid
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.template.exceptions import TemplateSyntaxError
from novels.models import NovelProject, Plot, Act, Chapter, ChapterOutline


class TestProjectDetailView(TestCase):
    """Test the project detail view renders correctly."""

    def setUp(self):
        """Set up test data."""
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

        # Create a test project
        self.project = NovelProject.objects.create(
            user=self.user,
            title="Test Novel",
            target_language='en',
            chroma_collection_name=f"test_{uuid.uuid4().hex[:8]}"
        )

        # Create plot and acts
        self.plot = Plot.objects.create(project=self.project)
        self.act1 = Act.objects.create(
            plot=self.plot,
            act_number=1,
            subject="SETUP",
            description="The beginning of the story"
        )
        self.act2 = Act.objects.create(
            plot=self.plot,
            act_number=2,
            subject="CONFRONTATION",
            description="The middle conflict"
        )

        # Create outlines associated with acts
        self.outline1 = ChapterOutline.objects.create(
            project=self.project,
            act=self.act1,
            number=1,
            title="Chapter 1 Outline",
            pov="Main Character",
            setting="City",
            events="Opening events",
            pacing="slow"
        )

        self.outline2 = ChapterOutline.objects.create(
            project=self.project,
            act=self.act2,
            number=2,
            title="Chapter 2 Outline",
            pov="Secondary Character",
            setting="Forest",
            events="Conflict events",
            pacing="fast"
        )

        # Create chapters associated with outlines
        self.chapter1 = Chapter.objects.create(
            project=self.project,
            outline=self.outline1,
            chapter_number=1,
            title="Chapter 1",
            content="Chapter 1 content here...",
            word_count=500,
            is_draft=True
        )

        self.chapter2 = Chapter.objects.create(
            project=self.project,
            outline=self.outline2,
            chapter_number=2,
            title="Chapter 2",
            content="Chapter 2 content here...",
            word_count=600,
            is_draft=False
        )

        # Create an orphan chapter (no outline, created directly)
        self.chapter3 = Chapter.objects.create(
            project=self.project,
            outline=None,  # No outline - created directly
            chapter_number=3,
            title="Chapter 3 - Direct",
            content="Chapter 3 content created directly...",
            word_count=450,
            is_draft=True
        )

    def test_project_detail_view_renders(self):
        """Test that the project detail view renders without template syntax errors."""
        # URL needs language prefix because of i18n_patterns
        url = f'/en/project/{self.project.id}/'

        # This should reproduce the template syntax error
        # The error occurs because of missing {% endwith %} tags in the template
        try:
            response = self.client.get(url)

            # If the template has syntax errors, Django will raise TemplateSyntaxError
            # Check if response was successful
            self.assertEqual(response.status_code, 200)

            # Check that the context contains expected data
            self.assertEqual(response.context['project'], self.project)
            self.assertTrue(response.context['has_plot'])
            self.assertEqual(len(response.context['chapters']), 3)
            self.assertEqual(len(response.context['outlines']), 2)

            # Check that chapters are displayed in the response
            self.assertContains(response, "Chapter 1")
            self.assertContains(response, "Chapter 2")
            self.assertContains(response, "Chapter 3 - Direct")

            # Check that acts are displayed
            self.assertContains(response, "Act 1: SETUP")
            self.assertContains(response, "Act 2: CONFRONTATION")

            # Check that the "Other Chapters" section appears for orphan chapters
            # The text might be translated, so let's check for the chapter itself
            # which should be in the "Other Chapters" section
            self.assertIn("Chapter 3 - Direct", response.content.decode())

            # Verify the template rendered successfully
            print("✓ Template rendered successfully without syntax errors")

        except TemplateSyntaxError as e:
            # Expected error due to missing endwith tags
            print(f"✗ Template syntax error detected (as expected): {e}")
            # Re-raise to make the test fail and show the error
            raise

    def test_project_detail_view_with_no_acts(self):
        """Test project detail view when there are no acts (flat chapter display)."""
        # Create a project without acts
        project_no_acts = NovelProject.objects.create(
            user=self.user,
            title="Novel Without Acts",
            target_language='en',
            chroma_collection_name=f"test_{uuid.uuid4().hex[:8]}"
        )

        # Create chapters without acts/outlines
        Chapter.objects.create(
            project=project_no_acts,
            chapter_number=1,
            title="Standalone Chapter",
            content="Content...",
            word_count=400,
            is_draft=True
        )

        url = f'/en/project/{project_no_acts.id}/'

        try:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Standalone Chapter")
            print("✓ Template renders correctly for projects without acts")
        except TemplateSyntaxError as e:
            print(f"✗ Template syntax error: {e}")
            raise

    def test_project_detail_view_with_empty_project(self):
        """Test project detail view with no chapters or outlines."""
        empty_project = NovelProject.objects.create(
            user=self.user,
            title="Empty Novel",
            target_language='en',
            chroma_collection_name=f"test_{uuid.uuid4().hex[:8]}"
        )

        url = f'/en/project/{empty_project.id}/'

        try:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "No chapters written yet")
            print("✓ Template renders correctly for empty projects")
        except TemplateSyntaxError as e:
            print(f"✗ Template syntax error: {e}")
            raise