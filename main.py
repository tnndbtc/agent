#!/usr/bin/env python3
"""Main entry point for the Novel Writing Agent."""
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# OpenAI API key MUST be set via environment variable
if 'OPENAI_API_KEY' not in os.environ:
    print("\n" + "=" * 80)
    print("ERROR: OPENAI_API_KEY environment variable is not set!")
    print("=" * 80)
    print("\nPlease set your OpenAI API key before running this application:")
    print("  export OPENAI_API_KEY=your-api-key-here")
    print("\nOr add it to your .env file in the project root:")
    print("  OPENAI_API_KEY=your-api-key-here")
    print("=" * 80)
    sys.exit(1)

from novel_agent.cli import main

if __name__ == "__main__":
    main()
