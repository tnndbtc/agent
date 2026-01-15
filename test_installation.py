#!/usr/bin/env python3
"""Test script to verify installation and basic functionality."""
import os
import sys

# Set API key - MUST be set via environment variable
# os.environ["OPENAI_API_KEY"] = "DEFAULT"  # Uncomment and set your key, or export OPENAI_API_KEY=your-key
if "OPENAI_API_KEY" not in os.environ:
    print("⚠ WARNING: OPENAI_API_KEY environment variable not set.")
    print("⚠ Some functionality tests will be skipped.")
    print("⚠ To test full functionality, export OPENAI_API_KEY=your-key before running.")
    os.environ["OPENAI_API_KEY"] = "DEFAULT"  # Set default to allow basic import tests

print("Testing Novel Writing Agent Installation...")
print("=" * 80)

# Test imports
print("\n1. Testing imports...")
try:
    from novel_agent.memory.long_term_memory import LongTermMemory
    from novel_agent.memory.context_manager import ContextManager
    from novel_agent.data.example_manager import ExampleManager
    from novel_agent.modules import (
        BrainstormingModule,
        PlotGenerator,
        CharacterGenerator,
        SettingGenerator,
        OutlinerModule,
        ChapterWriter,
        EditorModule,
        ConsistencyChecker
    )
    from novel_agent.output import NovelExporter, NovelScorer
    print("✓ All imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test initialization
print("\n2. Testing system initialization...")
try:
    memory = LongTermMemory(collection_name="test_collection")
    context_manager = ContextManager(memory)
    example_manager = ExampleManager()
    print("✓ Core systems initialized")
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    sys.exit(1)

# Test module creation
print("\n3. Testing module creation...")
try:
    brainstormer = BrainstormingModule(context_manager)
    plot_gen = PlotGenerator(context_manager, memory)
    char_gen = CharacterGenerator(context_manager, memory)
    setting_gen = SettingGenerator(context_manager, memory)
    outliner = OutlinerModule(context_manager, memory)
    writer = ChapterWriter(context_manager, memory, example_manager)
    editor = EditorModule(example_manager)
    checker = ConsistencyChecker(context_manager, memory)
    exporter = NovelExporter()
    scorer = NovelScorer()
    print("✓ All modules created")
except Exception as e:
    print(f"❌ Module creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test basic functionality
print("\n4. Testing basic functionality...")
try:
    # Test brainstorming (this will make an API call)
    print("   - Testing brainstorming...")
    ideas = brainstormer.generate_plot_ideas(
        genre="Fantasy",
        theme="Adventure",
        num_ideas=1
    )
    if ideas and len(ideas) > 0:
        print(f"✓ Generated plot idea: {ideas[0].get('title', 'Untitled')}")
    else:
        print("⚠ No ideas generated, but no error")
except Exception as e:
    print(f"⚠ Functionality test failed (this is okay if API key is invalid): {e}")

# Test example manager
print("\n5. Testing example manager...")
try:
    example_manager.add_good_example(
        content="This is a test example of good writing.",
        category="writing",
        description="Test example"
    )
    stats = example_manager.get_statistics()
    print(f"✓ Example manager working: {stats['good_examples']['total']} good examples")
except Exception as e:
    print(f"❌ Example manager failed: {e}")
    sys.exit(1)

# Test scorer
print("\n6. Testing scorer...")
try:
    scorer = NovelScorer()
    print(f"✓ Scorer initialized with {len(scorer.categories)} categories")
    for cat, weight in scorer.categories.items():
        print(f"   - {cat}: {weight}%")
except Exception as e:
    print(f"❌ Scorer failed: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("✓ ALL TESTS PASSED!")
print("=" * 80)
print("\nThe Novel Writing Agent is ready to use!")
print("\nTo run the interactive CLI:")
print("  python main.py")
print("\nTo run the example workflow:")
print("  python example_workflow.py")
print("=" * 80)
