"""
Test for idea display functionality in project detail view.
This test verifies that saved ideas are correctly displayed in the textarea.
"""
import uuid
from django.test import TestCase, Client
from django.contrib.auth.models import User
from novels.models import NovelProject, Idea


class TestIdeaDisplay(TestCase):
    """Test that ideas are correctly displayed in the 'Enter Your Idea' textarea."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_novel_idea_display(self):
        """Test that novel premise is displayed in textarea."""
        # Create a novel project
        project = NovelProject.objects.create(
            user=self.user,
            title="Test Novel",
            content_type='novel',
            target_language='en',
            chroma_collection_name=f"test_{uuid.uuid4().hex[:8]}"
        )

        # Create an idea for the project
        idea_text = "A young wizard discovers they are the chosen one."
        Idea.objects.create(
            project=project,
            idea_data={'premise': idea_text},
            content_type='novel'
        )

        # Get the project detail page
        url = f'/en/project/{project.id}/'
        response = self.client.get(url)

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that has_idea is True in context
        self.assertTrue(response.context['has_idea'])

        # Check that the textarea contains the idea text
        self.assertContains(response, idea_text)

        # Check that the textarea has the correct structure
        self.assertContains(response, 'id="manual_premise"')

        print("✓ Novel idea displays correctly in textarea")

    def test_poem_idea_display(self):
        """Test that poem theme is displayed in textarea."""
        # Create a poem project
        project = NovelProject.objects.create(
            user=self.user,
            title="Test Poem",
            content_type='poem',
            target_language='en',
            chroma_collection_name=f"test_{uuid.uuid4().hex[:8]}"
        )

        # Create an idea for the project
        theme_text = "The beauty of nature in autumn"
        Idea.objects.create(
            project=project,
            idea_data={'theme': theme_text, 'style_notes': ''},
            content_type='poem'
        )

        # Get the project detail page
        url = f'/en/project/{project.id}/'
        response = self.client.get(url)

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that has_idea is True in context
        self.assertTrue(response.context['has_idea'])

        # Check that the textarea contains the theme text
        self.assertContains(response, theme_text)

        print("✓ Poem theme displays correctly in textarea")

    def test_essay_idea_display(self):
        """Test that essay thesis is displayed in textarea."""
        # Create an essay project
        project = NovelProject.objects.create(
            user=self.user,
            title="Test Essay",
            content_type='essay',
            target_language='en',
            chroma_collection_name=f"test_{uuid.uuid4().hex[:8]}"
        )

        # Create an idea for the project
        thesis_text = "Technology has revolutionized modern education"
        Idea.objects.create(
            project=project,
            idea_data={'thesis': thesis_text, 'template': 'Five-Paragraph Essay', 'key_points': []},
            content_type='essay'
        )

        # Get the project detail page
        url = f'/en/project/{project.id}/'
        response = self.client.get(url)

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that has_idea is True in context
        self.assertTrue(response.context['has_idea'])

        # Check that the textarea contains the thesis text
        self.assertContains(response, thesis_text)

        print("✓ Essay thesis displays correctly in textarea")

    def test_sketch_idea_display(self):
        """Test that sketch observation is displayed in textarea."""
        # Create a sketch project
        project = NovelProject.objects.create(
            user=self.user,
            title="Test Sketch",
            content_type='sketch',
            target_language='en',
            chroma_collection_name=f"test_{uuid.uuid4().hex[:8]}"
        )

        # Create an idea for the project
        observation_text = "A busy coffee shop on a rainy morning"
        Idea.objects.create(
            project=project,
            idea_data={'observation': observation_text, 'scene_notes': ''},
            content_type='sketch'
        )

        # Get the project detail page
        url = f'/en/project/{project.id}/'
        response = self.client.get(url)

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that has_idea is True in context
        self.assertTrue(response.context['has_idea'])

        # Check that the textarea contains the observation text
        self.assertContains(response, observation_text)

        print("✓ Sketch observation displays correctly in textarea")

    def test_article_idea_display(self):
        """Test that article headline is displayed in textarea."""
        # Create an article project
        project = NovelProject.objects.create(
            user=self.user,
            title="Test Article",
            content_type='article',
            target_language='en',
            chroma_collection_name=f"test_{uuid.uuid4().hex[:8]}"
        )

        # Create an idea for the project
        headline_text = "New breakthrough in renewable energy technology"
        Idea.objects.create(
            project=project,
            idea_data={'headline': headline_text, 'facts': [], 'angle': ''},
            content_type='article'
        )

        # Get the project detail page
        url = f'/en/project/{project.id}/'
        response = self.client.get(url)

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that has_idea is True in context
        self.assertTrue(response.context['has_idea'])

        # Check that the textarea contains the headline text
        self.assertContains(response, headline_text)

        print("✓ Article headline displays correctly in textarea")

    def test_project_without_idea(self):
        """Test that projects without ideas show an empty textarea."""
        # Create a project without an idea
        project = NovelProject.objects.create(
            user=self.user,
            title="Test Project Without Idea",
            content_type='novel',
            target_language='en',
            chroma_collection_name=f"test_{uuid.uuid4().hex[:8]}"
        )

        # Get the project detail page
        url = f'/en/project/{project.id}/'
        response = self.client.get(url)

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that has_idea is False in context
        self.assertFalse(response.context['has_idea'])

        # Check that the textarea is present (for user to enter new idea)
        self.assertContains(response, 'id="manual_premise"')

        print("✓ Projects without ideas show empty textarea correctly")

    def test_idea_context_variable(self):
        """Test that the context includes has_idea variable."""
        # Create a project with an idea
        project = NovelProject.objects.create(
            user=self.user,
            title="Test Project",
            content_type='novel',
            target_language='en',
            chroma_collection_name=f"test_{uuid.uuid4().hex[:8]}"
        )

        Idea.objects.create(
            project=project,
            idea_data={'premise': 'Test premise'},
            content_type='novel'
        )

        url = f'/en/project/{project.id}/'
        response = self.client.get(url)

        # Verify the context variable exists
        self.assertIn('has_idea', response.context)
        self.assertTrue(response.context['has_idea'])

        # Verify project object is accessible
        self.assertEqual(response.context['project'], project)

        print("✓ Context variables are correctly set")
