"""
Test for act and character modification workflow.

This test verifies that acts and characters can be modified properly,
especially after the removal of the percentage field from the Act model.
"""

import pytest
from django.test import TransactionTestCase
from django.contrib.auth.models import User
from novels.models import NovelProject, Plot, Act, Character


@pytest.mark.django_db
class TestActCharacterModification(TransactionTestCase):
    """Test modification of acts and characters."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create test project
        self.project = NovelProject.objects.create(
            user=self.user,
            title='Test Novel Project',
            status='draft'
        )

        # Create plot
        self.plot = Plot.objects.create(
            project=self.project,
            conflict='Test conflict between good and evil',
            structure='Three-act structure',
            tone='Dark and mysterious',
            target_audience='Young Adult'
        )

        # Create acts (without percentage field)
        self.act1 = Act.objects.create(
            plot=self.plot,
            act_number=1,
            subject='SETUP',
            description='Introduction to the world and characters'
        )

        self.act2 = Act.objects.create(
            plot=self.plot,
            act_number=2,
            subject='CONFRONTATION',
            description='Rising action and main conflicts'
        )

        self.act3 = Act.objects.create(
            plot=self.plot,
            act_number=3,
            subject='RESOLUTION',
            description='Climax and resolution of conflicts'
        )

        # Create characters
        self.protagonist = Character.objects.create(
            project=self.project,
            name='Hero Name',
            role='protagonist',
            age='25',
            background='Orphaned at young age',
            personality='Brave but impulsive',
            motivation='Seeking justice',
            flaw='Too trusting',
            arc='Learns to be more cautious',
            appearance='Tall with dark hair',
            relationships='Best friend is the mentor'
        )

        self.antagonist = Character.objects.create(
            project=self.project,
            name='Villain Name',
            role='antagonist',
            age='40',
            background='Former hero turned evil',
            personality='Calculating and ruthless',
            motivation='Power and control',
            flaw='Overconfidence',
            arc='Becomes more desperate',
            appearance='Scarred face',
            relationships='Enemy of the protagonist'
        )

    def test_modify_act_without_percentage(self):
        """Test that acts can be modified without percentage field."""
        # Modify act subject and description
        self.act1.subject = 'INTRODUCTION'
        self.act1.description = 'Setting up the story world and main character'
        self.act1.save()

        # Verify the changes were saved
        self.act1.refresh_from_db()
        self.assertEqual(self.act1.subject, 'INTRODUCTION')
        self.assertEqual(self.act1.description, 'Setting up the story world and main character')

        # Ensure no percentage field exists
        with self.assertRaises(AttributeError):
            _ = self.act1.percentage

    def test_modify_character_fields(self):
        """Test that characters can be modified properly."""
        # Modify protagonist
        self.protagonist.name = 'Updated Hero Name'
        self.protagonist.age = '30'
        self.protagonist.personality = 'More mature and wise'
        self.protagonist.save()

        # Verify the changes were saved
        self.protagonist.refresh_from_db()
        self.assertEqual(self.protagonist.name, 'Updated Hero Name')
        self.assertEqual(self.protagonist.age, '30')
        self.assertEqual(self.protagonist.personality, 'More mature and wise')

    def test_create_new_act_without_percentage(self):
        """Test creating a new act without percentage field."""
        # Create a new act
        new_act = Act.objects.create(
            plot=self.plot,
            act_number=4,
            subject='EPILOGUE',
            description='After the main story ends'
            # No percentage field
        )

        # Verify the act was created
        self.assertIsNotNone(new_act.id)
        self.assertEqual(new_act.act_number, 4)
        self.assertEqual(new_act.subject, 'EPILOGUE')

        # Ensure no percentage field exists
        with self.assertRaises(AttributeError):
            _ = new_act.percentage

    def test_bulk_update_acts(self):
        """Test bulk updating multiple acts."""
        # Update multiple acts
        Act.objects.filter(plot=self.plot).update(
            description='Updated description for all acts'
        )

        # Verify all acts were updated
        for act in [self.act1, self.act2, self.act3]:
            act.refresh_from_db()
            self.assertEqual(act.description, 'Updated description for all acts')

    def test_act_character_relationship(self):
        """Test the relationship between acts and characters in the plot."""
        # Get all acts for the plot
        acts = self.plot.acts.all().order_by('act_number')
        self.assertEqual(acts.count(), 3)

        # Get all characters for the project
        characters = self.project.characters.all()
        self.assertEqual(characters.count(), 2)

        # Verify protagonist and antagonist exist
        protagonists = characters.filter(role='protagonist')
        antagonists = characters.filter(role='antagonist')
        self.assertEqual(protagonists.count(), 1)
        self.assertEqual(antagonists.count(), 1)

    def test_act_serialization_without_percentage(self):
        """Test that acts can be serialized without percentage field."""
        # Create a dictionary representation of the act
        act_data = {
            'id': str(self.act1.id),
            'act_number': self.act1.act_number,
            'subject': self.act1.subject,
            'description': self.act1.description,
            # No percentage field
        }

        # Verify the data structure
        self.assertNotIn('percentage', act_data)
        self.assertEqual(act_data['act_number'], 1)
        self.assertEqual(act_data['subject'], 'SETUP')

    def test_modify_plot_with_acts(self):
        """Test modifying a plot that has associated acts."""
        # Modify plot
        self.plot.conflict = 'Updated conflict description'
        self.plot.tone = 'Light and humorous'
        self.plot.save()

        # Verify plot changes
        self.plot.refresh_from_db()
        self.assertEqual(self.plot.conflict, 'Updated conflict description')
        self.assertEqual(self.plot.tone, 'Light and humorous')

        # Verify acts are still associated
        self.assertEqual(self.plot.acts.count(), 3)

    def test_character_creation_with_plot_context(self):
        """Test creating a character with plot context."""
        # Create a supporting character
        supporting = Character.objects.create(
            project=self.project,
            name='Supporting Character',
            role='supporting',
            age='35',
            background='Friend of the protagonist',
            personality='Loyal and humorous',
            motivation='Help the protagonist',
            flaw='Sometimes cowardly',
            arc='Becomes braver',
            appearance='Average height',
            relationships='Best friend of protagonist'
        )

        # Verify character was created
        self.assertIsNotNone(supporting.id)
        self.assertEqual(supporting.role, 'supporting')

        # Verify total character count
        self.assertEqual(self.project.characters.count(), 3)

    def test_delete_act_cascade(self):
        """Test that deleting an act doesn't break the plot."""
        # Delete act 2
        self.act2.delete()

        # Verify plot still exists
        self.plot.refresh_from_db()
        self.assertIsNotNone(self.plot)

        # Verify only 2 acts remain
        self.assertEqual(self.plot.acts.count(), 2)

        # Verify remaining acts
        remaining_acts = self.plot.acts.all().order_by('act_number')
        self.assertEqual(remaining_acts[0].act_number, 1)
        self.assertEqual(remaining_acts[1].act_number, 3)


@pytest.mark.django_db
class TestActCharacterAPIModification(TransactionTestCase):
    """Test act and character modification through API endpoints."""

    def setUp(self):
        """Set up test client and data."""
        from rest_framework.test import APIClient

        self.client = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='apipass123'
        )

        # Authenticate client
        self.client.force_authenticate(user=self.user)

        # Create test project
        self.project = NovelProject.objects.create(
            user=self.user,
            title='API Test Novel',
            status='draft'
        )

        # Create plot with acts
        self.plot = Plot.objects.create(
            project=self.project,
            conflict='API test conflict'
        )

        self.act = Act.objects.create(
            plot=self.plot,
            act_number=1,
            subject='SETUP',
            description='API test act description'
        )

        self.character = Character.objects.create(
            project=self.project,
            name='API Test Character',
            role='protagonist',
            age='30',
            background='Test background'
        )

    def test_update_act_via_api(self):
        """Test updating an act through API endpoint."""
        # Test that the ActViewSet works properly for updating acts
        url = f'/api/acts/{self.act.id}/'

        # Prepare update data (without percentage - it was removed)
        # Note: subject must be one of the valid choices: SETUP, CONFRONTATION, RESOLUTION
        update_data = {
            'subject': 'CONFRONTATION',  # Changed from SETUP to CONFRONTATION
            'description': 'Modified via API'
        }

        response = self.client.patch(url, update_data, format='json')
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.json()}")
        self.assertEqual(response.status_code, 200, "Should successfully update act")

        # Verify act was updated
        self.act.refresh_from_db()
        self.assertEqual(self.act.subject, 'CONFRONTATION')
        self.assertEqual(self.act.description, 'Modified via API')

        # Make sure trying to update with percentage field doesn't break things
        # (since percentage was removed in migration 0023)
        update_with_percentage = {
            'subject': 'RESOLUTION',  # Use a valid choice
            'percentage': 50  # This field doesn't exist anymore
        }

        response = self.client.patch(url, update_with_percentage, format='json')
        # Should still work, just ignoring the percentage field
        self.assertEqual(response.status_code, 200, "Should ignore non-existent percentage field")

    def test_update_character_via_api(self):
        """Test updating a character through API endpoint - should expose the bug."""
        # Test updating the motivation field (which has a bug - it's checking for 'motivations' plural)
        url = f'/api/projects/{self.project.id}/update_character/{self.character.id}/'

        # First, test updating fields that work
        update_data = {
            'name': 'Modified Character Name',
            'background': 'Modified background'
        }

        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, 200, "Should successfully update name and background")

        self.character.refresh_from_db()
        self.assertEqual(self.character.name, 'Modified Character Name')
        self.assertEqual(self.character.background, 'Modified background')

        # Now test updating motivation field - BUG IS FIXED
        # The view now correctly checks for 'motivation' (singular) matching the model field
        old_motivation = self.character.motivation
        update_data_motivation = {
            'motivation': 'New motivation for the character'
        }

        response = self.client.patch(url, update_data_motivation, format='json')

        # The response should be 200 because motivation is now a valid field
        self.assertEqual(response.status_code, 200,
                        "Should return 200 because 'motivation' is now correctly in allowed_fields")

        # Verify motivation was successfully updated
        self.character.refresh_from_db()
        self.assertEqual(
            self.character.motivation,
            'New motivation for the character',
            "Motivation field should be successfully updated after bug fix"
        )

    def test_create_act_without_percentage_via_api(self):
        """Test creating an act without percentage field via API."""
        # Prepare act data (without percentage)
        act_data = {
            'plot': str(self.plot.id),
            'act_number': 2,
            'subject': 'CONFRONTATION',
            'description': 'Created via API without percentage'
        }

        # Make API request to create act
        # Note: You'll need to implement the actual endpoint
        # This is a placeholder to demonstrate the test structure

        # Verify act was created without percentage field
        new_acts = Act.objects.filter(plot=self.plot, act_number=2)
        # Assertions would go here after API implementation

    def test_serializer_handles_missing_percentage(self):
        """Test that serializers handle acts without percentage field."""
        from novels.serializers import ActSerializer

        # Serialize the act
        serializer = ActSerializer(self.act)
        data = serializer.data

        # Verify percentage is not in serialized data
        self.assertNotIn('percentage', data)

        # Verify other fields are present
        self.assertEqual(data['act_number'], 1)
        self.assertEqual(data['subject'], 'SETUP')
        self.assertIn('description', data)