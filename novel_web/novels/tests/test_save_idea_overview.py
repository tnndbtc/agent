"""
Test that after creating plot/characters directly from idea,
the project detail page (Overview tab) renders the plot and characters.

This verifies the JS form handler properly reloads the page after plot creation.
"""
import re
import pytest
from django.test import Client
from novels.models import Plot, Character


@pytest.mark.integration
@pytest.mark.django_db
class TestSaveIdeaOverview:
    """Test the full flow: create plot directly from idea -> verify overview shows data."""

    def test_overview_shows_plot_and_characters_after_save_idea(
        self, authenticated_client, test_project, mock_all_openai
    ):
        """
        After creating plot/characters via API directly from idea,
        the project detail page should render plot and characters.
        """
        project = test_project

        # Step 1: Create plot and characters directly from idea (simplified workflow)
        idea_data = {
            'premise': 'A young wizard discovers a hidden world beneath the ocean.'
        }
        plot_response = authenticated_client.post(
            f'/api/projects/{project.id}/create_plot/',
            {
                'idea_data': {
                    'title': 'Ocean Wizard',
                    'premise': idea_data['premise'],
                    'conflict': 'Ancient sea creatures vs humanity',
                    'hook': 'A mysterious portal appears in the deep'
                }
            },
            format='json'
        )
        assert plot_response.status_code == 201
        assert 'plot' in plot_response.data
        assert 'protagonist' in plot_response.data
        assert 'antagonist' in plot_response.data

        # Step 2: Verify data exists in the database
        assert Plot.objects.filter(project=project).exists(), \
            "Plot should exist in DB after create_plot API call"
        assert Character.objects.filter(project=project, role='protagonist').exists(), \
            "Protagonist should exist in DB after create_plot API call"
        assert Character.objects.filter(project=project, role='antagonist').exists(), \
            "Antagonist should exist in DB after create_plot API call"

        # Step 3: Load the project detail page (simulates page reload)
        web_client = Client()
        web_client.login(username='testuser', password='testpass123')
        page_response = web_client.get(f'/en/project/{project.id}/')

        assert page_response.status_code == 200

        # Step 4: Verify the page context includes plot and characters
        assert page_response.context['has_plot'] is True, \
            "Page context should have has_plot=True after plot creation"
        characters = list(page_response.context['characters'])
        assert len(characters) >= 2, \
            f"Page context should have at least 2 characters, got {len(characters)}"

        # Step 5: Verify the HTML contains character and plot content
        content = page_response.content.decode()
        protagonist = Character.objects.get(project=project, role='protagonist')
        antagonist = Character.objects.get(project=project, role='antagonist')

        assert protagonist.name in content, \
            f"Protagonist name '{protagonist.name}' should appear in rendered HTML"
        assert antagonist.name in content, \
            f"Antagonist name '{antagonist.name}' should appear in rendered HTML"

    def test_js_reloads_page_after_plot_creation(
        self, authenticated_client, test_project, mock_all_openai
    ):
        """
        Verifies that the JS handler for manualForm submit calls create_plot
        and triggers window.location.reload() after success.

        Without a reload, the server-rendered plot/characters sections
        (controlled by {% if has_plot %} and {% if characters %}) remain
        empty because the initial page was loaded without plot data.

        This test verifies the template's JS includes a page reload
        after the create_plot API call succeeds.
        """
        project = test_project

        # Load the project detail page to get the rendered JS
        web_client = Client()
        web_client.login(username='testuser', password='testpass123')
        page_response = web_client.get(f'/en/project/{project.id}/')
        assert page_response.status_code == 200

        html = page_response.content.decode()

        # Extract the JS block that handles the manualForm submit
        # Find the section from "manualForm.addEventListener('submit'" to the
        # closing of the event handler
        match = re.search(
            r"manualForm\.addEventListener\('submit'.*?create_plot.*?showToast\("
            r"[^)]*'success'\)(.*?)\}\s*catch",
            html,
            re.DOTALL
        )
        assert match is not None, \
            "Could not find manualForm submit handler with create_plot call in template JS"

        js_after_toast = match.group(1)

        # The bug: after showToast('...success'), the JS updates the idea
        # display but never reloads the page. Plot and characters sections
        # are server-rendered and won't update without a reload.
        assert 'window.location.reload()' in js_after_toast or \
               'location.reload()' in js_after_toast, \
            (
                "BUG REPRODUCED: After create_plot succeeds, the JS handler "
                "does not call window.location.reload(). The plot and characters "
                "sections are server-rendered ({% if has_plot %}, {% if characters %}) "
                "and will not appear without a page reload. "
                f"JS after success toast: {js_after_toast[:300]}"
            )
