#!/bin/bash
# Novel Web Integration Tests - Complete Test Runner
# This script installs dependencies, sets environment variables, and runs tests

set -e  # Exit on error

echo "======================================================="
echo "Novel Web Integration Tests - Complete Test Runner"
echo "======================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo "Script directory: $SCRIPT_DIR"
echo "Project root: $PROJECT_ROOT"
echo ""

# Parse command line arguments
SKIP_INSTALL=false
VERBOSE=false
COVERAGE=false
SPECIFIC_TEST=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-install)
            SKIP_INSTALL=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --test)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-install    Skip dependency installation"
            echo "  -v, --verbose     Run tests with verbose output"
            echo "  --coverage        Generate coverage report"
            echo "  --test CLASS      Run specific test class (e.g., TestUserAuthentication)"
            echo "  -h, --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                              # Run all tests"
            echo "  $0 --skip-install -v            # Skip install, run with verbose output"
            echo "  $0 --test TestProjectCreation   # Run specific test class"
            echo "  $0 --coverage                   # Run with coverage report"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Step 1: Install Dependencies (unless skipped)
if [ "$SKIP_INSTALL" = false ]; then
    echo "Step 1: Installing dependencies..."
    echo "---------------------------------------------------"

    # Check if we're in the right directory
    if [ ! -f "$SCRIPT_DIR/requirements.txt" ]; then
        echo -e "${RED}Error: requirements.txt not found${NC}"
        echo "Expected location: $SCRIPT_DIR/requirements.txt"
        exit 1
    fi

    # Install main application dependencies
    echo "Installing main application dependencies..."
    if [ -f "$PROJECT_ROOT/requirements-web.txt" ]; then
        pip install -q -r "$PROJECT_ROOT/requirements-web.txt"
        echo -e "${GREEN}✓ Main dependencies installed${NC}"
    else
        echo -e "${YELLOW}Warning: Main requirements file not found${NC}"
        echo "Location checked: $PROJECT_ROOT/requirements-web.txt"
    fi

    # Install test dependencies
    echo "Installing test dependencies..."
    pip install -q -r "$SCRIPT_DIR/requirements.txt"
    echo -e "${GREEN}✓ Test dependencies installed${NC}"
    echo ""
else
    echo "Step 1: Skipping dependency installation (--skip-install)"
    echo ""
fi

# Step 2: Set Environment Variables
echo "Step 2: Setting environment variables..."
echo "---------------------------------------------------"
export DJANGO_SETTINGS_MODULE=novel_web.settings
export OPENAI_API_KEY=test-key-123-not-used-mocked
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"
echo "OPENAI_API_KEY=$OPENAI_API_KEY"
echo "PYTHONPATH=$PYTHONPATH"
echo -e "${GREEN}✓ Environment variables set${NC}"
echo ""

# Step 3: Verify Installation
echo "Step 3: Verifying installation..."
echo "---------------------------------------------------"
cd "$PROJECT_ROOT"

python3 -c "import pytest; print(f'✓ pytest {pytest.__version__}')" 2>/dev/null || echo -e "${RED}✗ pytest not found${NC}"
python3 -c "import pytest_django; print(f'✓ pytest-django {pytest_django.__version__}')" 2>/dev/null || echo -e "${RED}✗ pytest-django not found${NC}"
python3 -c "import django; print(f'✓ Django {django.__version__}')" 2>/dev/null || echo -e "${RED}✗ Django not found${NC}"
python3 -c "import rest_framework; print(f'✓ DRF {rest_framework.__version__}')" 2>/dev/null || echo -e "${RED}✗ Django REST Framework not found${NC}"
python3 -c "import celery; print(f'✓ Celery {celery.__version__}')" 2>/dev/null || echo -e "${RED}✗ Celery not found${NC}"

echo ""

# Step 4: Run Tests
echo "Step 4: Running tests..."
echo "---------------------------------------------------"

# Build pytest command
PYTEST_CMD="python3 -m pytest novels/tests/test_integration.py"

# Add verbosity
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add coverage
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=novels --cov-report=html --cov-report=term-missing"
fi

# Add specific test
if [ -n "$SPECIFIC_TEST" ]; then
    PYTEST_CMD="$PYTEST_CMD::$SPECIFIC_TEST"
fi

# Add color output
PYTEST_CMD="$PYTEST_CMD --color=yes"

echo "Running command: $PYTEST_CMD"
echo ""

# Run the tests
if $PYTEST_CMD; then
    TEST_EXIT_CODE=0
else
    TEST_EXIT_CODE=$?
fi

echo ""
echo "======================================================="
echo "Test Run Complete"
echo "======================================================="
echo ""

# Step 5: Summary
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""

    if [ "$COVERAGE" = true ]; then
        echo "Coverage report generated:"
        echo "  HTML: htmlcov/index.html"
        echo ""
        echo "View coverage report:"
        echo "  xdg-open htmlcov/index.html  # Linux"
        echo "  open htmlcov/index.html      # macOS"
    fi
else
    echo -e "${RED}✗ Some tests failed (exit code: $TEST_EXIT_CODE)${NC}"
    echo ""
    echo "Troubleshooting tips:"
    echo "  1. Check the test output above for specific errors"
    echo "  2. Read README.md for known issues and solutions"
    echo "  3. Run with --verbose for more detailed output"
    echo "  4. Run specific failing test: $0 --test TestClassName"
fi

echo ""
echo "Additional commands:"
echo "  Run specific test:     $0 --test TestProjectCreation"
echo "  Run with coverage:     $0 --coverage"
echo "  Run verbose:           $0 -v"
echo "  Skip installation:     $0 --skip-install"
echo "  Show help:             $0 --help"
echo ""

exit $TEST_EXIT_CODE
