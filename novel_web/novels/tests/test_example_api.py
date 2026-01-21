"""
Tests for Example API endpoints, specifically focusing on performance and query optimization.
"""

import pytest
from django.db import connection
from django.test.utils import override_settings
from novels.models import Example, ExampleScore


@pytest.mark.django_db
class TestExampleAPI:
    """Test Example API endpoints for functionality and performance."""

    def test_examples_list_endpoint_query_performance(self, authenticated_client, test_user, test_score_categories):
        """
        Test that examples list endpoint doesn't cause N+1 queries.

        This test should FAIL initially due to the total_score property
        calling self.scores.all() which ignores prefetched data.

        Expected behavior after fix:
        - Query count should be low (< 15) even with 30 examples
        - Should use prefetch_related data instead of making extra queries
        """
        # Create 30 examples (more than page size of 20)
        examples = []
        for i in range(30):
            example = Example.objects.create(
                user=test_user,
                public=True,
                is_good=True,
                category='opening',
                title=f'Good Example {i}',
                content=f'Test content for example {i}' * 50  # Make it substantial
            )
            examples.append(example)

            # Add scores for each category
            for category in test_score_categories.values():
                ExampleScore.objects.create(
                    example=example,
                    category=category,
                    weight=20,
                    score=7.0 + (i % 3)  # Vary scores: 7.0, 8.0, 9.0
                )

        # Test with query counting
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as queries:
            response = authenticated_client.get('/api/examples/?is_good=true')
            query_count = len(queries)

        # Assertions
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"

        # Verify response structure
        data = response.json()
        assert 'results' in data, "Response should have 'results' key (paginated response)"
        assert len(data['results']) == 20, f"Expected 20 results (first page), got {len(data['results'])}"

        # Verify total_score is calculated for all examples
        for example_data in data['results']:
            assert 'total_score' in example_data, "Example should have total_score field"
            assert example_data['total_score'] > 0, f"total_score should be > 0, got {example_data['total_score']}"
            assert 'scores' in example_data, "Example should have scores field"
            assert len(example_data['scores']) == 5, f"Expected 5 scores, got {len(example_data['scores'])}"

        # Critical performance assertion
        # Expected queries (rough estimate):
        # 1. Count query for pagination
        # 2. SELECT examples with select_related (user)
        # 3. Prefetch scores
        # 4. Prefetch categories for scores
        # Plus a few for authentication/session
        # Should be around 8-12 queries total
        print(f"\n{'='*80}")
        print(f"Query Performance Test Results:")
        print(f"Total queries executed: {query_count}")
        print(f"Examples returned: {len(data['results'])}")
        print(f"{'='*80}\n")

        assert query_count < 20, (
            f"Too many queries! Expected < 20, got {query_count}. "
            f"This indicates N+1 query problem. "
            f"The total_score property likely isn't using prefetched scores."
        )

    def test_examples_filter_by_is_good(self, authenticated_client, test_user):
        """Test filtering examples by is_good parameter."""
        # Create good and bad examples
        good_example = Example.objects.create(
            user=test_user,
            is_good=True,
            content='This is a good example',
            public=True,
            category='opening',
            title='Good Example'
        )

        bad_example = Example.objects.create(
            user=test_user,
            is_good=False,
            content='This is a bad example',
            public=True,
            category='opening',
            title='Bad Example'
        )

        # Test filtering for good examples
        response = authenticated_client.get('/api/examples/?is_good=true')
        assert response.status_code == 200

        results = response.json()['results'] if 'results' in response.json() else response.json()

        # Should only return good examples
        assert len(results) >= 1, "Should have at least 1 good example"
        assert all(ex['is_good'] for ex in results), "All results should have is_good=True"

        # Verify good example is in results
        titles = [ex['title'] for ex in results]
        assert 'Good Example' in titles, "Good example should be in results"
        assert 'Bad Example' not in titles, "Bad example should NOT be in results"

    def test_examples_list_requires_authentication(self, api_client):
        """Test that examples list endpoint requires authentication."""
        response = api_client.get('/api/examples/')
        # DRF returns 403 (Forbidden) instead of 401 (Unauthorized) when not authenticated
        assert response.status_code in [401, 403], "Should require authentication"

    def test_examples_filter_by_category(self, authenticated_client, test_user):
        """Test filtering examples by category."""
        # Create examples with different categories
        opening_example = Example.objects.create(
            user=test_user,
            public=True,
            is_good=True,
            category='opening',
            title='Opening Example',
            content='Opening content'
        )

        closing_example = Example.objects.create(
            user=test_user,
            public=True,
            is_good=True,
            category='ending',
            title='Ending Example',
            content='Ending content'
        )

        # Test filtering for opening category
        response = authenticated_client.get('/api/examples/?category=opening')
        assert response.status_code == 200

        results = response.json()['results'] if 'results' in response.json() else response.json()

        # Verify only opening examples returned
        assert len(results) >= 1, "Should have at least 1 opening example"
        assert all(ex['category'] == 'opening' for ex in results), "All results should be opening category"
