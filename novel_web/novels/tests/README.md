# Novel Web Integration Tests

## Overview

This directory contains integration tests for the novel_web Django application. These tests validate the complete workflow from user authentication through chapter generation, with all OpenAI API calls mocked using hardcoded responses.

## Test Coverage

The integration tests cover the following scenarios as specified in the requirements:

1. **User Login** - User registration and authentication
2. **Create Project** - Novel project creation via API
3. **Create Idea** - Brainstorming and idea generation
4. **Auto Generate Plot and Characters** - Plot creation with automatic character generation
5. **Auto Generate 3 Outlines** - Chapter outline generation
6. **Auto Generate 3 Chapters** - Chapter writing from outlines
7. **Complete End-to-End Workflow** - Full novel creation workflow

## Directory Structure

```
tests/
├── __init__.py
├── README.md (this file)
├── conftest.py              # Pytest fixtures and configuration
├── test_integration.py      # Main integration test suite
└── mocks/
    ├── __init__.py
    └── openai_responses.py  # Mock OpenAI response generator
```

## Running the Tests

### Quick Start (Recommended)

Use the automated test runner that handles everything:

```bash
cd /home/tnnd/data/code/agent/novel_web/novels/tests
./run_test.sh
```

This single command will:
- Install all dependencies
- Set environment variables
- Verify installation
- Run all tests

### Script Options

```bash
./run_test.sh                        # Run all tests
./run_test.sh --skip-install         # Skip dependency installation
./run_test.sh -v                     # Verbose output
./run_test.sh --coverage             # Generate coverage report
./run_test.sh --test TestClassName   # Run specific test class
./run_test.sh --help                 # Show all options
```

### Manual Setup (Advanced)

1. Install dependencies:
   ```bash
   pip install -r novel_web/requirements-web.txt
   pip install -r novel_web/novels/tests/requirements.txt
   ```

2. Set environment variables and run:
   ```bash
   cd /home/tnnd/data/code/agent
   export DJANGO_SETTINGS_MODULE=novel_web.settings
   export OPENAI_API_KEY=test-key-123
   python3 -m pytest novel_web/novels/tests/test_integration.py -v
   ```

### Run Specific Test Class

```bash
python3 -m pytest novel_web/novels/tests/test_integration.py::TestProjectCreation -v
```

### Run With Coverage

```bash
python3 -m pytest novel_web/novels/tests/test_integration.py --cov=novels --cov-report=html
```

## Test Configuration

### Pytest Configuration

The `pytest.ini` file in the project root configures:
- Django settings module
- Test discovery patterns
- Output verbosity
- Test markers (integration, unit)

### Fixtures

Key fixtures defined in `conftest.py`:

- `test_user` - Creates a test user account
- `api_client` - DRF APIClient instance
- `authenticated_client` - Pre-authenticated API client
- `test_project` - Creates a test novel project
- `mock_openai_chat` - Mocks ChatOpenAI for LLM calls
- `mock_openai_embeddings` - Mocks OpenAIEmbeddings for vector store
- `mock_chroma` - Mocks ChromaDB vector database
- `mock_all_openai` - Combined mock for all OpenAI services

## Mock OpenAI Responses

All OpenAI API calls are mocked to return hardcoded responses. This ensures:

✅ **No real API calls** - No API costs during testing
✅ **Deterministic results** - Tests produce consistent results
✅ **Fast execution** - Tests run quickly without network latency
✅ **No API key required** - Can run tests without valid OpenAI credentials

### Mock Response Strategy

The `get_mock_response_for_prompt()` function in `mocks/openai_responses.py` examines the prompt text and returns appropriate mock responses:

- **Brainstorm prompts** → Returns 1-3 simple plot ideas
- **Plot creation** → Returns JSON with 3-act structure
- **Character creation** → Returns JSON with character details
- **Outline generation** → Returns chapter outline data
- **Chapter writing** → Returns generated chapter text (~100 words)

### Celery Configuration for Tests

Tests run Celery tasks synchronously using:

```python
settings.CELERY_TASK_ALWAYS_EAGER = True
settings.CELERY_TASK_EAGER_PROPAGATES = True
```

This makes async tasks run immediately in the same process, simplifying testing.

## Test Results Summary

### Current Status

**Tests Run**: 15
**Passed**: 1
**Failed**: 14

### Known Issues and Fixes Needed

#### 1. Login URL 404 Errors

**Issue**: Login URLs return 404 because of i18n_patterns requiring language prefix.

**Fix**: Use language-aware URL resolution or hardcode language prefix:
```python
# Instead of reverse('novels:login')
response = client.post('/en-us/login/', ...)
```

#### 2. API Client Format

**Issue**: DRF APIClient fails with nested dictionaries in multipart form data.

**Fix**: Add `format='json'` to all API client POST requests:
```python
response = authenticated_client.post(
    f'/api/projects/{project_id}/create_plot/',
    {'idea_data': {...}},
    format='json'  # Add this
)
```

#### 3. Plot Model Fields

**Issue**: Tests use wrong field names (`title`, `main_conflict`) instead of actual fields (`premise`, `conflict`).

**Fix**: Use correct Plot model fields:
```python
Plot.objects.create(
    project=test_project,
    premise='Test premise',  # Not 'title'
    conflict='Test conflict'  # Not 'main_conflict'
)
```

#### 4. ChromaDB Permission Error

**Issue**: Celery tasks fail with permission denied when creating ChromaDB collections.

**Fix**: Configure test to use temp directory for vector store or mock more completely:
```python
@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    import tempfile
    settings.NOVEL_AGENT['VECTOR_STORE_DIR'] = tempfile.mkdtemp()
```

#### 5. Authentication Expectation

**Issue**: Unauthenticated API requests return 403 instead of expected 401.

**Fix**: Update assertion to accept 403:
```python
assert response.status_code in [401, 403]  # Both are valid
```

## Test Maintenance

### Adding New Tests

1. Add new test methods to existing test classes or create new classes
2. Use appropriate fixtures from `conftest.py`
3. Ensure all OpenAI calls are mocked
4. Follow naming convention: `test_<description>`
5. Add docstrings explaining what the test validates

### Updating Mocks

When adding new AI generation features:

1. Add new mock response method to `MockOpenAIResponses` class
2. Update `get_mock_response_for_prompt()` to handle new prompt patterns
3. Test that mocks return appropriate data structures

### Best Practices

- **Isolate tests**: Each test should be independent
- **Use fixtures**: Leverage pytest fixtures for setup
- **Mock external dependencies**: Never make real API calls in tests
- **Clear assertions**: Use descriptive assertion messages
- **Test both success and failure paths**: Include negative test cases

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

- Fast execution (< 30 seconds for all tests)
- No external dependencies (mocked APIs)
- Deterministic results (no flaky tests)
- Clear error messages for debugging

## Troubleshooting

### Common Issues

**Q: Tests fail with "No module named 'celery'"**
A: Install dependencies: `pip install -r requirements-web.txt`

**Q: Tests fail with ChromaDB permission errors**
A: Configure test to use temp directory or enhance mock coverage

**Q: Login tests return 404**
A: Use language-prefixed URLs (`/en-us/login/`) instead of reverse()

**Q: API tests fail with nested dict error**
A: Add `format='json'` to API client POST calls

## Future Improvements

- [ ] Fix all failing tests
- [ ] Add more edge case tests
- [ ] Increase test coverage to >80%
- [ ] Add performance benchmarks
- [ ] Integrate with CI/CD pipeline
- [ ] Add database transaction rollback for faster cleanup
- [ ] Mock ChromaDB more completely to avoid file system access

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all tests pass before committing
3. Update this README with new test scenarios
4. Add appropriate mocks for new AI features

## Contact

For questions about tests, see the main project documentation or check the test files for inline comments.

---

**Last Updated**: 2026-01-15
**Test Framework**: pytest-django 4.11.1
**Python Version**: 3.12+
**Django Version**: 5.0.1
