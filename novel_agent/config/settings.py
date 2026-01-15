"""Configuration settings for the Novel Writing Agent."""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "DEFAULT")

# Model Configuration
MODEL_NAME = "gpt-4o-mini"
TEMPERATURE = 0.7
MAX_TOKENS = 2000

# Memory Configuration
MEMORY_DIR = BASE_DIR / "memory"
VECTOR_STORE_DIR = MEMORY_DIR / "vector_store"
EXAMPLES_DIR = BASE_DIR / "data" / "examples"
OUTPUT_DIR = BASE_DIR / "output"

# Scoring Configuration
SCORING_CATEGORIES = {
    "Story/Plot": 30,
    "Character Development": 20,
    "World-Building / Setting": 15,
    "Writing Style / Language": 20,
    "Dialogue & Interactions": 10,
    "Emotional Impact / Engagement": 5
}

# Language Support
SUPPORTED_LANGUAGES = ["English", "Chinese", "French", "Spanish", "German", "Japanese"]

# Create necessary directories
for directory in [MEMORY_DIR, VECTOR_STORE_DIR, EXAMPLES_DIR, OUTPUT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
