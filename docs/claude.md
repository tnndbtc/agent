# Novel Writing Agent - Complete Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Quick Start Guide](#quick-start-guide)
5. [Module Documentation](#module-documentation)
6. [Workflow Examples](#workflow-examples)
7. [API Reference](#api-reference)
8. [Configuration](#configuration)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Novel Writing Agent is an AI-powered assistant built with LangChain that helps authors create complete novels through an intelligent, step-by-step workflow. It uses OpenAI's GPT models, ChromaDB for persistent memory, and provides a comprehensive suite of tools for every stage of novel writing.

### Key Capabilities

- **Brainstorming**: Generate multiple plot ideas based on genre, theme, and constraints
- **Plot Development**: Create detailed three-act structures with subplots and key scenes
- **Character Creation**: Generate complex characters with depth, flaws, and arcs
- **World-Building**: Design settings, magic systems, and cultural elements
- **Outlining**: Generate chapter-by-chapter outlines with scene breakdowns
- **Writing**: Generate chapters, scenes, dialogue, and descriptions
- **Editing**: Improve style, pacing, grammar, and dialogue
- **Consistency**: Verify character traits, settings, and timelines
- **Scoring**: Rate novels with adjustable criteria weights
- **Export**: Output in multiple languages and formats

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│                  (CLI / API / Future Web)                │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────┐
│                  Core Orchestration                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Context    │  │  Long-Term   │  │   Example    │  │
│  │   Manager    │  │    Memory    │  │   Manager    │  │
│  │              │  │  (ChromaDB)  │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────┐
│                  Generation Modules                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Brainstorming│  │Plot Generator│  │  Character   │  │
│  │              │  │              │  │  Generator   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Setting    │  │   Outliner   │  │   Chapter    │  │
│  │  Generator   │  │              │  │   Writer     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────┐
│              Quality & Output Modules                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    Editor    │  │ Consistency  │  │    Scorer    │  │
│  │              │  │   Checker    │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐                                       │
│  │   Exporter   │                                       │
│  │ (Multi-lang) │                                       │
│  └──────────────┘                                       │
└───────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Input** → CLI or API
2. **Context Retrieval** → Context Manager queries Long-Term Memory
3. **Generation** → Module generates content using LLM + context
4. **Storage** → Result stored in Long-Term Memory
5. **Output** → Result returned to user / exported

### Memory System

The Long-Term Memory system uses ChromaDB (vector database) to store:
- Character profiles
- Plot structures
- Settings and world-building
- Chapter content
- Outlines and relationships

All stored data is:
- **Searchable**: Semantic search using embeddings
- **Retrievable**: Context-aware retrieval for each task
- **Persistent**: Survives across sessions

---

## Installation & Setup

### Prerequisites

- Python 3.12 or higher
- OpenAI API key
- 2GB+ free disk space (for vector database)

### Step 1: Install Dependencies

```bash
cd /home/tnnd/data/code/agent
pip install -r requirements.txt
```

Dependencies include:
- `langchain` (core orchestration)
- `langchain-openai` (OpenAI integration)
- `langchain-community` (vector stores)
- `chromadb` (vector database)
- `tiktoken` (tokenization)
- `rich` (terminal UI)

### Step 2: Configure API Key

Option 1 - Environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Option 2 - Edit config file:
```python
# novel_agent/config/settings.py
OPENAI_API_KEY = "your-api-key-here"
```

### Step 3: Verify Installation

```bash
python test_installation.py
```

Expected output:
```
✓ ALL TESTS PASSED!
The Novel Writing Agent is ready to use!
```

---

## Quick Start Guide

### Method 1: Interactive CLI

```bash
python main.py
```

Follow the menu to:
1. Start new novel (complete workflow)
2. Use individual modules
3. Export and score your work

### Method 2: Example Workflow

```bash
python example_workflow.py
```

This demonstrates all features end-to-end:
- Brainstorms 3 plot ideas
- Creates full plot structure
- Generates protagonist, antagonist, supporting characters
- Builds primary setting
- Creates 10-chapter outline
- Writes Chapter 1
- Edits for style
- Checks consistency
- Scores the chapter
- Exports to file

### Method 3: Programmatic Usage

```python
from novel_agent.memory.long_term_memory import LongTermMemory
from novel_agent.memory.context_manager import ContextManager
from novel_agent.modules import BrainstormingModule

# Initialize
memory = LongTermMemory()
context = ContextManager(memory)
brainstormer = BrainstormingModule(context)

# Generate ideas
ideas = brainstormer.generate_plot_ideas(
    genre="Fantasy",
    theme="Redemption",
    num_ideas=3
)

print(f"Generated {len(ideas)} plot ideas")
for idea in ideas:
    print(f"- {idea['title']}: {idea['premise']}")
```

---

## Module Documentation

### 1. BrainstormingModule

**Purpose**: Generate creative plot ideas

**Methods**:
- `generate_plot_ideas(genre, theme, num_ideas)` - Generate multiple ideas
- `refine_plot_idea(idea, feedback)` - Refine based on feedback
- `expand_plot_idea(idea)` - Expand into detailed structure
- `brainstorm_with_constraints(must_have, must_avoid)` - Constrained generation

**Example**:
```python
ideas = brainstormer.generate_plot_ideas(
    genre="Science Fiction",
    theme="Identity",
    num_ideas=5
)
```

### 2. PlotGenerator

**Purpose**: Create detailed plot structures

**Methods**:
- `create_full_plot(idea)` - Create three-act structure
- `generate_subplots(main_plot, num)` - Create subplots
- `identify_key_scenes(plot)` - Identify crucial scenes

**Example**:
```python
plot = plot_gen.create_full_plot(selected_idea)
subplots = plot_gen.generate_subplots(plot, num_subplots=2)
```

### 3. CharacterGenerator

**Purpose**: Generate and manage characters

**Methods**:
- `create_protagonist(plot, num_options)` - Generate protagonist options
- `create_antagonist(plot, protagonist)` - Create opposing force
- `create_supporting_characters(plot, protagonist, roles)` - Supporting cast
- `develop_character_relationships(characters)` - Map relationships

**Example**:
```python
protagonists = char_gen.create_protagonist(plot, num_options=3)
protagonist = protagonists[0]  # User selects

antagonist = char_gen.create_antagonist(plot, protagonist)

supporting = char_gen.create_supporting_characters(
    plot, protagonist, ["mentor", "sidekick", "love interest"]
)
```

### 4. SettingGenerator

**Purpose**: Build worlds and settings

**Methods**:
- `create_primary_setting(plot)` - Main setting
- `create_secondary_locations(setting, num)` - Additional locations
- `develop_magic_system(plot)` - Fantasy/sci-fi systems
- `create_cultural_elements(setting)` - Culture and customs

**Example**:
```python
setting = setting_gen.create_primary_setting(plot)
locations = setting_gen.create_secondary_locations(setting, num_locations=5)
magic = setting_gen.develop_magic_system(plot)
```

### 5. OutlinerModule

**Purpose**: Create chapter outlines

**Methods**:
- `create_chapter_outline(plot, num_chapters)` - Full outline
- `refine_chapter(chapter_num, outline, feedback)` - Refine chapter
- `generate_scene_breakdown(chapter)` - Break into scenes
- `check_outline_pacing(outline)` - Analyze pacing

**Example**:
```python
outline = outliner.create_chapter_outline(plot, num_chapters=20)
scenes = outliner.generate_scene_breakdown(outline['chapters'][0])
pacing = outliner.check_outline_pacing(outline)
```

### 6. ChapterWriter

**Purpose**: Write novel content

**Methods**:
- `write_chapter(outline, style, language)` - Complete chapter
- `write_paragraph(context, previous, style)` - Single paragraph
- `write_dialogue(characters, context, purpose)` - Dialogue scene
- `write_description(subject, type, mood)` - Descriptive passage
- `continue_from_draft(content, outline)` - Continue existing

**Example**:
```python
chapter = writer.write_chapter(
    chapter_outline=outline['chapters'][0],
    writing_style="literary",
    language="English"
)

dialogue = writer.write_dialogue(
    characters=["Alice", "Bob"],
    context="They meet in a dark alley",
    purpose="Reveal Bob's secret"
)
```

### 7. EditorModule

**Purpose**: Edit and refine content

**Methods**:
- `edit_for_style(content, target_style)` - Style improvements
- `edit_for_pacing(content, context)` - Pacing adjustments
- `edit_for_grammar(content)` - Grammar/mechanics
- `improve_dialogue(dialogue, characters)` - Dialogue enhancement
- `strengthen_opening(opening, genre)` - Improve hooks
- `compress_text(content, target_reduction)` - Tighten prose

**Example**:
```python
style_edit = editor.edit_for_style(
    chapter['content'],
    target_style="literary"
)

grammar_check = editor.edit_for_grammar(chapter['content'])
```

### 8. ConsistencyChecker

**Purpose**: Maintain story coherence

**Methods**:
- `check_character_consistency(content)` - Character traits
- `check_setting_consistency(content, setting)` - World-building
- `check_timeline_consistency(chapters)` - Timeline
- `check_plot_consistency(content)` - Plot points
- `generate_consistency_report(novel_data)` - Full report
- `suggest_fix(issue, context)` - Fix suggestions

**Example**:
```python
char_issues = checker.check_character_consistency(chapter['content'])
setting_issues = checker.check_setting_consistency(
    chapter['content'],
    chapter_setting="City of Avalon"
)
report = checker.generate_consistency_report(novel_data)
```

### 9. NovelScorer

**Purpose**: Score and evaluate novels

**Methods**:
- `score_novel(novel_data)` - Complete novel scoring
- `score_chapter(chapter_data)` - Single chapter
- `update_weights(new_weights)` - Adjust category weights
- `add_category(name, weight)` - Add scoring category
- `format_score_table(report)` - Format results

**Example**:
```python
# Default scoring
scorer = NovelScorer()
report = scorer.score_novel(novel_data)

# Custom weights
custom_scorer = NovelScorer(custom_categories={
    "Plot": 40,
    "Characters": 30,
    "Writing": 30
})

print(scorer.format_score_table(report))
```

### 10. NovelExporter

**Purpose**: Export to various formats

**Methods**:
- `export_to_text(novel_data, language, filename)` - Text export
- `export_chapter(chapter_data, language)` - Single chapter
- `export_outline(outline_data)` - Outline only
- `export_character_profiles(characters)` - Character sheets
- `export_complete_package(novel_data, language)` - Everything

**Example**:
```python
# Export complete novel
path = exporter.export_to_text(
    novel_data,
    language="English",
    filename="my_novel.txt"
)

# Export complete package
files = exporter.export_complete_package(
    novel_data,
    language="Chinese"
)
```

---

## Workflow Examples

### Complete Novel Workflow

```python
from novel_agent.memory.long_term_memory import LongTermMemory
from novel_agent.memory.context_manager import ContextManager
from novel_agent.modules import *
from novel_agent.output import *

# Initialize
memory = LongTermMemory()
context = ContextManager(memory)
example_mgr = ExampleManager()

# All modules
brainstormer = BrainstormingModule(context)
plot_gen = PlotGenerator(context, memory)
char_gen = CharacterGenerator(context, memory)
setting_gen = SettingGenerator(context, memory)
outliner = OutlinerModule(context, memory)
writer = ChapterWriter(context, memory, example_mgr)
editor = EditorModule(example_mgr)
checker = ConsistencyChecker(context, memory)
exporter = NovelExporter()
scorer = NovelScorer()

# Step 1: Brainstorm
ideas = brainstormer.generate_plot_ideas(genre="Fantasy", num_ideas=3)
selected = ideas[0]  # User choice

# Step 2: Develop plot
plot = plot_gen.create_full_plot(selected)

# Step 3: Create characters
protagonists = char_gen.create_protagonist(plot, num_options=3)
protagonist = protagonists[0]
antagonist = char_gen.create_antagonist(plot, protagonist)
supporting = char_gen.create_supporting_characters(
    plot, protagonist, ["mentor", "sidekick"]
)

# Step 4: Build world
setting = setting_gen.create_primary_setting(plot)
locations = setting_gen.create_secondary_locations(setting, num_locations=3)

# Step 5: Outline
outline = outliner.create_chapter_outline(plot, num_chapters=20)

# Step 6: Write chapters
chapters = []
for i in range(3):  # First 3 chapters
    chapter = writer.write_chapter(
        outline['chapters'][i],
        writing_style="literary",
        language="English"
    )
    chapters.append(chapter)

    # Edit each chapter
    style_edit = editor.edit_for_style(chapter['content'])
    if style_edit['revised']:
        chapter['content'] = style_edit['revised']

# Step 7: Check consistency
novel_data = {
    'title': plot['title'],
    'plot': plot,
    'characters': [protagonist, antagonist] + supporting,
    'settings': [setting] + locations,
    'outline': outline,
    'chapters': chapters
}

consistency_report = checker.generate_consistency_report(novel_data)

# Step 8: Score
score_report = scorer.score_novel(novel_data)
print(scorer.format_score_table(score_report))

# Step 9: Export
exported = exporter.export_complete_package(novel_data, language="English")
print(f"Novel exported to: {exported['novel']}")
```

### Quick Chapter Generation

```python
# Write a standalone chapter
from novel_agent.modules import ChapterWriter
from novel_agent.memory import LongTermMemory, ContextManager
from novel_agent.data import ExampleManager

memory = LongTermMemory()
context = ContextManager(memory)
examples = ExampleManager()
writer = ChapterWriter(context, memory, examples)

chapter_outline = {
    'number': 1,
    'title': 'The Beginning',
    'pov': 'Third person',
    'setting': 'A dark forest',
    'events': 'The hero discovers a mysterious artifact',
    'character_development': 'Hero overcomes fear',
    'pacing': 'medium'
}

chapter = writer.write_chapter(
    chapter_outline,
    writing_style="commercial",
    language="English"
)

print(f"Chapter complete: {chapter['word_count']} words")
```

---

## API Reference

### Memory System

#### LongTermMemory

```python
memory = LongTermMemory(collection_name="my_novel")

# Store data
memory.store_character(character_dict)
memory.store_plot(plot_dict)
memory.store_chapter(chapter_dict)
memory.store_setting(setting_dict)
memory.store_outline(outline_dict)

# Retrieve data
characters = memory.get_all_characters()
plot = memory.get_plot_summary()
chapters = memory.get_all_chapters()

# Search
results = memory.retrieve_context(query="brave warrior", k=5)
filtered = memory.retrieve_context(
    query="magic system",
    k=3,
    filter_type="setting"
)

# Clear
memory.clear_memory()  # Use with caution!
```

#### ContextManager

```python
context = ContextManager(memory)

# Build context for tasks
context_text = context.build_context_for_task(
    task_type="writing",  # brainstorm, character, writing, editing, consistency
    query="chapter 1",
    k=5
)

# Update current context
context.update_current_context('plot', plot_data)
current_plot = context.get_current_context('plot')

# Get full story context
story = context.get_full_story_context()
summary = context.format_context_summary()
```

### Example Manager

```python
examples = ExampleManager()

# Add examples
examples.add_good_example(
    content="Brilliant dialogue example...",
    category="dialogue",
    description="Natural conversation with subtext"
)

examples.add_bad_example(
    content="Terrible info dump...",
    category="exposition",
    description="Too much telling, not showing",
    issues=["info dump", "no subtlety", "boring"]
)

# Retrieve examples
good_dialogue = examples.get_good_examples(category="dialogue", limit=5)
bad_exposition = examples.get_bad_examples(category="exposition")

# Statistics
stats = examples.get_statistics()
categories = examples.get_categories(is_good=True)

# Create comparison prompt
comparison = examples.create_comparison_prompt(
    category="dialogue",
    num_examples=3
)
```

---

## Configuration

### Settings File

Edit `novel_agent/config/settings.py`:

```python
# API Configuration
OPENAI_API_KEY = "your-key-here"

# Model Configuration
MODEL_NAME = "gpt-4o-mini"  # or "gpt-4", "gpt-4-turbo"
TEMPERATURE = 0.7           # 0.0-1.0, higher = more creative
MAX_TOKENS = 2000           # Max tokens per generation

# Directories
BASE_DIR = Path(__file__).parent.parent
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
SUPPORTED_LANGUAGES = [
    "English", "Chinese", "French",
    "Spanish", "German", "Japanese"
]
```

### Adjust Scoring Weights

```python
from novel_agent.output import NovelScorer

# Method 1: Initialize with custom weights
scorer = NovelScorer(custom_categories={
    "Plot": 35,
    "Characters": 25,
    "Writing": 25,
    "Pacing": 15
})

# Method 2: Update existing scorer
scorer.update_weights({
    "Story/Plot": 35,
    "Character Development": 25
})

# Method 3: Add/remove categories
scorer.add_category("Pacing", 10)
scorer.remove_category("Emotional Impact / Engagement")
```

### Temperature Settings

Different modules use different temperatures:

- **Brainstorming**: 0.7 (base)
- **Character Generation**: 0.8 (more creative)
- **Chapter Writing**: 0.9 (most creative)
- **Editing**: 0.5 (more focused)
- **Consistency Checking**: 0.4 (most analytical)
- **Scoring**: 0.4 (most consistent)

---

## Best Practices

### 1. Memory Management

**DO**:
- Use meaningful collection names for different novels
- Store all major story elements (characters, plot, settings)
- Regularly query memory for consistency

**DON'T**:
- Store incomplete or placeholder data
- Mix multiple novels in same collection
- Clear memory without backing up

### 2. Prompt Engineering

**DO**:
- Provide specific, detailed requirements
- Give examples of desired style/tone
- Iterate with feedback loops

**DON'T**:
- Be vague or overly broad
- Expect perfection on first generation
- Ignore the refinement methods

### 3. Workflow Optimization

**DO**:
- Follow the natural workflow: brainstorm → plot → characters → outline → write
- Use the example manager to improve quality over time
- Run consistency checks after every few chapters

**DON'T**:
- Skip the outlining phase
- Write entire novels without checkpoints
- Ignore consistency issues

### 4. Quality Control

**DO**:
- Edit each chapter after writing
- Check consistency regularly
- Use scoring to identify weak areas
- Store good/bad examples as you find them

**DON'T**:
- Generate without reviewing
- Trust AI blindly
- Skip the editing phase

### 5. Cost Management

**DO**:
- Use lower-cost models for testing (gpt-4o-mini)
- Cache and reuse generated content
- Batch similar operations

**DON'T**:
- Regenerate unnecessarily
- Use GPT-4 for simple tasks
- Forget to monitor API usage

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Error**: `ModuleNotFoundError: No module named 'langchain.schema'`

**Solution**: Update imports to use `langchain_core`:
```python
# Old
from langchain.schema import Document

# New
from langchain_core.documents import Document
```

#### 2. ChromaDB Errors

**Error**: `sqlite3.OperationalError: database is locked`

**Solution**: Only one instance can access the database at a time. Close other instances or use different collection names.

#### 3. API Rate Limits

**Error**: `RateLimitError: Rate limit exceeded`

**Solution**:
- Add delays between API calls
- Use lower-cost models
- Implement exponential backoff

```python
import time

for chapter in chapters:
    result = writer.write_chapter(chapter)
    time.sleep(2)  # 2-second delay
```

#### 4. Memory/Context Issues

**Error**: Context not retrieving expected information

**Solution**:
- Verify data was stored correctly
- Check collection name
- Increase `k` parameter for more results
- Use specific queries

```python
# More specific
results = memory.retrieve_context(
    query="protagonist warrior brave sword",
    k=10,
    filter_type="character"
)
```

#### 5. Poor Quality Output

**Problem**: Generated content is low quality

**Solutions**:
- Add good examples to example manager
- Provide more detailed prompts/context
- Increase temperature for creativity
- Use iterative refinement
- Try different models (GPT-4 for better quality)

### Debug Mode

Enable detailed logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Your code here
```

### Getting Help

1. Check the error message and traceback
2. Verify API key and quotas
3. Review the logs
4. Test with simple examples
5. Check ChromaDB status

---

## Advanced Usage

### Custom Module Creation

Create your own module:

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from novel_agent.config import OPENAI_API_KEY, MODEL_NAME

class MyCustomModule:
    def __init__(self, context_manager, memory):
        self.context_manager = context_manager
        self.memory = memory
        self.llm = ChatOpenAI(
            model=MODEL_NAME,
            temperature=0.7,
            openai_api_key=OPENAI_API_KEY
        )

    def my_custom_method(self, input_data):
        # Get relevant context
        context = self.context_manager.build_context_for_task(
            "custom_task",
            input_data
        )

        # Generate with LLM
        messages = [
            SystemMessage(content="You are a helpful assistant..."),
            HumanMessage(content=f"Context: {context}\n\nTask: {input_data}")
        ]

        response = self.llm.invoke(messages)

        # Store result
        # self.memory.store_...

        return response.content
```

### Batch Processing

Process multiple novels:

```python
def process_novel_batch(novel_specs):
    for spec in novel_specs:
        # Create separate memory for each novel
        memory = LongTermMemory(collection_name=spec['name'])
        context = ContextManager(memory)

        # Process novel
        # ... workflow code ...

        # Export
        exporter.export_complete_package(novel_data, spec['language'])
```

### Custom Scoring System

Implement domain-specific scoring:

```python
class MyCustomScorer(NovelScorer):
    def __init__(self):
        custom_categories = {
            "Historical Accuracy": 25,
            "Period Dialogue": 20,
            "Setting Detail": 25,
            "Plot": 20,
            "Writing Quality": 10
        }
        super().__init__(custom_categories=custom_categories)

    def score_historical_accuracy(self, novel_data):
        # Custom scoring logic
        pass
```

---

## API Performance Tracking System

### Overview

The Novel Writing Agent includes an intelligent API performance tracking system that monitors the duration of AI-powered operations and provides real-time progress estimation to users. This system consists of two main components:

1. **APIPerformanceMetric Model**: Stores historical performance data
2. **Progress Bar System**: Displays real-time progress with intelligent time estimation

### APIPerformanceMetric Model

#### Purpose

The `APIPerformanceMetric` model tracks the execution time of AI generation tasks to provide accurate duration estimates for future operations. This data helps:

- Provide realistic time estimates to users
- Display intelligent progress bars
- Identify performance bottlenecks
- Monitor system health

#### Database Schema

Located in `novels/models.py`:

```python
class APIPerformanceMetric(models.Model):
    """Track API call performance for duration estimation."""

    API_TYPE_CHOICES = [
        ('brainstorm', 'Idea Generation'),
        ('plot', 'Plot and Characters Generation'),
        ('outline', 'Outlines Generation'),
        ('chapter', 'Chapter Generation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    api_type = models.CharField(max_length=20, choices=API_TYPE_CHOICES, db_index=True)
    duration_seconds = models.FloatField(help_text="How long the API call took in seconds")
    input_params = models.JSONField(default=dict, blank=True, help_text="e.g., num_chapters, word_count")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    success = models.BooleanField(default=True, help_text="Whether the API call succeeded")
```

**Fields**:
- `id`: Unique identifier (UUID)
- `api_type`: Type of operation (brainstorm, plot, outline, chapter)
- `duration_seconds`: How long the operation took in seconds
- `input_params`: Optional parameters like word count, number of chapters
- `created_at`: Timestamp when the metric was recorded
- `success`: Whether the operation completed successfully

#### Auto-Cleanup Mechanism

The model automatically maintains a maximum of **50 records per API type** to prevent database bloat:

```python
def save(self, *args, **kwargs):
    """Save and maintain max 50 records per API type."""
    super().save(*args, **kwargs)

    # Get records beyond the 50th (ordered by newest first)
    old_records = APIPerformanceMetric.objects.filter(
        api_type=self.api_type
    ).order_by('-created_at')[50:]

    if old_records:
        old_ids = [r.id for r in old_records]
        APIPerformanceMetric.objects.filter(id__in=old_ids).delete()
```

This ensures:
- Recent performance data is always available
- Database size remains manageable
- Statistics reflect current system performance

#### Recording Metrics

Metrics are automatically recorded after each AI operation completes:

**Example - Celery Task (Asynchronous)**:

```python
# In novels/tasks.py - brainstorm_ideas_task
start_time = time.time()

try:
    # ... AI generation logic ...

    # Record successful completion
    duration = time.time() - start_time
    APIPerformanceMetric.objects.create(
        api_type='brainstorm',
        duration_seconds=duration,
        input_params={'num_ideas': num_ideas, 'genre': genre, 'theme': theme},
        success=True
    )
except Exception as e:
    # Record failure
    duration = time.time() - start_time
    APIPerformanceMetric.objects.create(
        api_type='brainstorm',
        duration_seconds=duration,
        success=False
    )
    raise
```

**Example - Synchronous API (Plot Generation)**:

```python
# In novels/views.py - create_plot
start_time = time.time()

try:
    # ... AI generation logic ...

    duration = time.time() - start_time
    APIPerformanceMetric.objects.create(
        api_type='plot',
        duration_seconds=duration,
        input_params={'idea_title': idea_data.get('title')},
        success=True
    )
except Exception as e:
    duration = time.time() - start_time
    APIPerformanceMetric.objects.create(
        api_type='plot',
        duration_seconds=duration,
        success=False
    )
    raise
```

#### Performance Statistics API

The system provides a dedicated endpoint to retrieve average duration statistics:

**Endpoint**: `GET /api/tasks/performance-stats/`

**Response**:
```json
{
    "brainstorm": {
        "display_name": "Idea Generation",
        "average_duration_seconds": 28.45,
        "sample_size": 23
    },
    "plot": {
        "display_name": "Plot and Characters Generation",
        "average_duration_seconds": 18.32,
        "sample_size": 15
    },
    "outline": {
        "display_name": "Outlines Generation",
        "average_duration_seconds": 62.18,
        "sample_size": 41
    },
    "chapter": {
        "display_name": "Chapter Generation",
        "average_duration_seconds": 47.56,
        "sample_size": 38
    }
}
```

**Implementation** (in `novels/views.py`):

```python
@action(detail=False, methods=['get'], url_path='performance-stats')
def performance_stats(self, request):
    """Get average duration estimates for each API type."""
    from django.db.models import Avg, Count

    stats = {}
    for api_type, display_name in APIPerformanceMetric.API_TYPE_CHOICES:
        metrics = APIPerformanceMetric.objects.filter(
            api_type=api_type,
            success=True  # Only successful calls
        ).aggregate(
            avg_duration=Avg('duration_seconds'),
            count=Count('id')
        )

        stats[api_type] = {
            'display_name': display_name,
            'average_duration_seconds': round(metrics['avg_duration'] or 30.0, 2),
            'sample_size': metrics['count']
        }

    return Response(stats)
```

**Features**:
- Only considers successful operations
- Provides display-friendly names
- Returns sample size for confidence assessment
- Defaults to 30 seconds if no data available

---

## Progress Bar System

### Overview

The progress bar system provides real-time visual feedback during AI generation operations. It uses the APIPerformanceMetric data to intelligently estimate completion time and update progress accordingly.

### Visual Design

The progress bars use a consistent, modern design across all operations:

- **Purple gradient fill**: Linear gradient from `#4f46e5` to `#7c3aed`
- **Rounded corners**: 15px border radius
- **Height**: 30px
- **Percentage display**: Shown inside the progress bar
- **Status text**: Below the progress bar

### Implementation Architecture

#### 1. CSS Styling (Global)

Located in `frontend/templates/novels/project_detail.html`:

```css
.progress-container {
    margin: 1.5rem 0;
    display: none;  /* Hidden by default */
}

.progress-bar {
    width: 100%;
    height: 30px;
    background: #e5e7eb;  /* Light gray background */
    border-radius: 15px;
    overflow: hidden;
    position: relative;
}

.progress-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
    border-radius: 15px;
    transition: width 0.3s ease;
    width: 0%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: 0.875rem;
}

.progress-text {
    margin-top: 0.5rem;
    text-align: center;
    color: #6b7280;
    font-size: 0.875rem;
}
```

**Important**: The CSS is **global** (not scoped to any container), allowing progress bars to work in any section of the page.

#### 2. HTML Structure

Each operation has its own progress bar with unique IDs:

```html
<!-- Example: Write Chapter Progress Bar -->
<div id="writeChapterProgressContainer-{{ outline.id }}"
     class="progress-container"
     style="display: none; margin-bottom: 1rem;">
    <div class="progress-bar">
        <div id="writeChapterProgressBarFill-{{ outline.id }}"
             class="progress-bar-fill">0%</div>
    </div>
    <div id="writeChapterProgressText-{{ outline.id }}"
         class="progress-text">Saving idea and creating plot & characters...</div>
</div>

<button class="btn btn-sm btn-primary"
        onclick="writeChapterFromOutline('{{ outline.id }}')"
        id="writeChapterBtn-{{ outline.id }}">
    Write This Chapter
</button>
```

**Key Points**:
- Each progress bar has a unique ID based on the operation context (e.g., `outline.id`, `outline.number`)
- Container starts hidden (`display: none`)
- Button has an ID for enabling/disabling during progress

#### 3. JavaScript Progress Management

Each operation type has three management functions:

**a) Start Progress Bar**

```javascript
async function writeChapterFromOutline(outlineId) {
    // User input...

    try {
        // Get estimated duration for chapter API
        const estimatedDuration = await getEstimatedDuration('chapter');
        startWriteChapterProgressBar(outlineId, estimatedDuration);

        // Make API request...
    } catch (err) {
        resetWriteChapterProgressBar(outlineId);
    }
}

function startWriteChapterProgressBar(outlineId, estimatedDuration = null) {
    const progressContainer = document.getElementById(`writeChapterProgressContainer-${outlineId}`);
    const progressBarFill = document.getElementById(`writeChapterProgressBarFill-${outlineId}`);
    const writeChapterBtn = document.getElementById(`writeChapterBtn-${outlineId}`);

    if (progressContainer) {
        // Show progress bar
        progressContainer.style.display = 'block';

        // Disable button
        if (writeChapterBtn) {
            writeChapterBtn.disabled = true;
            writeChapterBtn.style.opacity = '0.6';
        }

        writeChapterCurrentProgress[outlineId] = 0;

        // Calculate intelligent increment
        let increment = 5; // Default: 5% every 2 seconds
        if (estimatedDuration) {
            // Calculate increment to reach 95% by estimated time
            increment = Math.max(1, Math.min(95 / (estimatedDuration / 2), 10));
        }

        // Update progress every 2 seconds
        writeChapterProgressIntervals[outlineId] = setInterval(() => {
            if (writeChapterCurrentProgress[outlineId] < 95) {
                writeChapterCurrentProgress[outlineId] += increment;
                if (writeChapterCurrentProgress[outlineId] > 95) {
                    writeChapterCurrentProgress[outlineId] = 95;
                }
                progressBarFill.style.width = writeChapterCurrentProgress[outlineId] + '%';
                progressBarFill.textContent = Math.round(writeChapterCurrentProgress[outlineId]) + '%';
            }
        }, 2000); // Update every 2 seconds
    }
}
```

**b) Complete Progress Bar**

```javascript
function completeWriteChapterProgressBar(outlineId) {
    const progressBarFill = document.getElementById(`writeChapterProgressBarFill-${outlineId}`);

    if (writeChapterProgressIntervals[outlineId]) {
        clearInterval(writeChapterProgressIntervals[outlineId]);
    }

    writeChapterCurrentProgress[outlineId] = 100;
    if (progressBarFill) {
        progressBarFill.style.width = '100%';
        progressBarFill.textContent = '100%';
    }
}
```

**c) Reset Progress Bar**

```javascript
function resetWriteChapterProgressBar(outlineId) {
    const progressContainer = document.getElementById(`writeChapterProgressContainer-${outlineId}`);
    const progressBarFill = document.getElementById(`writeChapterProgressBarFill-${outlineId}`);
    const writeChapterBtn = document.getElementById(`writeChapterBtn-${outlineId}`);

    // Clear intervals
    if (writeChapterProgressIntervals[outlineId]) {
        clearInterval(writeChapterProgressIntervals[outlineId]);
        delete writeChapterProgressIntervals[outlineId];
    }

    if (writeChapterPollingIntervals[outlineId]) {
        clearInterval(writeChapterPollingIntervals[outlineId]);
        delete writeChapterPollingIntervals[outlineId];
    }

    // Hide and reset
    if (progressContainer) {
        progressContainer.style.display = 'none';
        writeChapterCurrentProgress[outlineId] = 0;

        if (progressBarFill) {
            progressBarFill.style.width = '0%';
            progressBarFill.textContent = '0%';
        }

        // Re-enable button
        if (writeChapterBtn) {
            writeChapterBtn.disabled = false;
            writeChapterBtn.style.opacity = '1';
        }
    }
}
```

#### 4. Intelligent Increment Calculation

The progress bar uses a smart algorithm to reach 95% completion by the estimated time:

```javascript
// If estimated duration is 60 seconds:
// increment = 95 / (60 / 2) = 95 / 30 = 3.17% per update
// At 2-second intervals, it will reach 95% in ~60 seconds

let increment = 5; // Default fallback
if (estimatedDuration) {
    increment = Math.max(1, Math.min(95 / (estimatedDuration / 2), 10));
}
```

**Formula Breakdown**:
- `estimatedDuration / 2`: Number of 2-second intervals
- `95 / intervals`: Percentage to add each interval to reach 95%
- `Math.max(1, ...)`: Ensure at least 1% per update
- `Math.min(..., 10)`: Cap at 10% per update for very short tasks

**Why 95% and not 100%?**
- Prevents the bar from completing before the actual task
- Last 5% completes only when server confirms success
- Provides better user experience (no premature completion)

#### 5. Task Status Polling

The progress bar integrates with task polling to complete when the server finishes:

```javascript
// Poll task status every 2 seconds
writeChapterPollingIntervals[outlineId] = setInterval(async () => {
    try {
        const task = await apiRequest(`/api/tasks/${response.task_id}/`);

        if (task.status === 'completed') {
            clearInterval(writeChapterPollingIntervals[outlineId]);
            completeWriteChapterProgressBar(outlineId);  // Jump to 100%
            showToast('Chapter written successfully!', 'success');
            setTimeout(() => window.location.reload(), 1500);
        } else if (task.status === 'failed') {
            clearInterval(writeChapterPollingIntervals[outlineId]);
            resetWriteChapterProgressBar(outlineId);  // Hide and reset
            showToast('Failed to write chapter', 'error');
        }
    } catch (error) {
        clearInterval(writeChapterPollingIntervals[outlineId]);
        resetWriteChapterProgressBar(outlineId);
        showToast('Error checking task status', 'error');
    }
}, 2000);
```

### Progress Bar Implementations

Currently implemented for:

1. **Generate Ideas** (Brainstorm page)
   - Button: "Generate Ideas"
   - API Type: `brainstorm`
   - ID Pattern: `brainstormProgressContainer`

2. **Save Idea and Continue** (Manual Input section)
   - Button: "Save Idea and continue"
   - API Type: `plot`
   - ID Pattern: `manualProgressContainer`

3. **Create Outline** (Chapters tab)
   - Button: "Create Outline"
   - API Type: `outline`
   - ID Pattern: `outlineProgressContainer`

4. **Regenerate Outline** (Per chapter)
   - Button: "Regenerate"
   - API Type: `outline`
   - ID Pattern: `regenerateProgressContainer-{chapterNumber}`

5. **Write This Chapter** (Per outline)
   - Button: "Write This Chapter"
   - API Type: `chapter`
   - ID Pattern: `writeChapterProgressContainer-{outlineId}`

### Frontend Caching

The performance stats are cached on the frontend to reduce API calls:

```javascript
// In frontend/static/js/api.js
let performanceStatsCache = null;
let lastFetchTime = null;
const CACHE_DURATION = 60000; // 1 minute

async function getPerformanceStats(forceRefresh = false) {
    const now = Date.now();

    // Return cached data if fresh
    if (!forceRefresh && performanceStatsCache && lastFetchTime &&
        (now - lastFetchTime < CACHE_DURATION)) {
        return performanceStatsCache;
    }

    try {
        const stats = await apiRequest('/api/tasks/performance-stats/');
        performanceStatsCache = stats;
        lastFetchTime = now;
        return stats;
    } catch (error) {
        // Fallback defaults if API fails
        return {
            'brainstorm': { average_duration_seconds: 30 },
            'plot': { average_duration_seconds: 20 },
            'outline': { average_duration_seconds: 60 },
            'chapter': { average_duration_seconds: 45 }
        };
    }
}

async function getEstimatedDuration(apiType) {
    const stats = await getPerformanceStats();
    return stats[apiType]?.average_duration_seconds || 30;
}
```

**Benefits**:
- Reduces server load
- Faster progress bar initialization
- Graceful fallback if API fails
- 1-minute cache is fresh enough for estimates

### Adding Progress Bars to New Operations

To add a progress bar to a new operation:

1. **Add Progress Bar HTML**:
```html
<div id="myOperationProgressContainer-{{ unique_id }}" class="progress-container" style="display: none;">
    <div class="progress-bar">
        <div id="myOperationProgressBarFill-{{ unique_id }}" class="progress-bar-fill">0%</div>
    </div>
    <div id="myOperationProgressText-{{ unique_id }}" class="progress-text">Processing...</div>
</div>
```

2. **Add JavaScript State Variables**:
```javascript
let myOperationProgressIntervals = {};
let myOperationCurrentProgress = {};
let myOperationPollingIntervals = {};
```

3. **Create Management Functions**:
```javascript
function startMyOperationProgressBar(uniqueId, estimatedDuration) { ... }
function completeMyOperationProgressBar(uniqueId) { ... }
function resetMyOperationProgressBar(uniqueId) { ... }
```

4. **Update Operation Function**:
```javascript
async function myOperation(uniqueId) {
    const estimatedDuration = await getEstimatedDuration('my_api_type');
    startMyOperationProgressBar(uniqueId, estimatedDuration);

    // Make API call and poll status...
}
```

5. **Record Performance Metrics** (Backend):
```python
start_time = time.time()
try:
    # ... operation logic ...
    APIPerformanceMetric.objects.create(
        api_type='my_api_type',
        duration_seconds=time.time() - start_time,
        success=True
    )
except Exception as e:
    APIPerformanceMetric.objects.create(
        api_type='my_api_type',
        duration_seconds=time.time() - start_time,
        success=False
    )
    raise
```

---

## Roadmap

### Planned Features

- [ ] Web interface (Flask/FastAPI)
- [ ] PDF/EPUB export formats
- [ ] Microsoft Word (.docx) export
- [ ] Collaborative writing support
- [ ] Version control for drafts
- [ ] Advanced plotting tools (Save the Cat, Story Circle)
- [ ] Style transfer from favorite authors
- [ ] Automated fact-checking
- [ ] Character voice training
- [ ] Scene visualization
- [ ] Publishing workflow integration

### Contributing

To contribute:
1. Fork the repository
2. Create feature branch
3. Implement with tests
4. Submit pull request

---

## License

This project is for educational and creative purposes.

---

## Acknowledgments

- **LangChain**: LLM orchestration framework
- **OpenAI**: GPT models for generation
- **ChromaDB**: Vector storage for memory
- **Rich**: Terminal UI library

---

## Contact & Support

For issues, questions, or suggestions:
- Check this documentation first
- Review troubleshooting section
- Test with minimal examples
- Provide error messages and traceback

---

**Happy Writing! 📚✨**

*Generated with Novel Writing Agent v1.0*
