#!/usr/bin/env python3
"""Example workflow demonstrating the Novel Writing Agent capabilities."""
import os
import sys

# Set OpenAI API key - MUST be set via environment variable
# os.environ["OPENAI_API_KEY"] = "DEFAULT"  # Uncomment and set your key, or export OPENAI_API_KEY=your-key
if "OPENAI_API_KEY" not in os.environ:
    raise ValueError("OPENAI_API_KEY environment variable must be set. Export it before running this script.")

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


def main():
    """Run example workflow."""
    print("=" * 80)
    print("NOVEL WRITING AGENT - EXAMPLE WORKFLOW")
    print("=" * 80)

    # Initialize systems
    print("\n1. Initializing systems...")
    memory = LongTermMemory()
    context_manager = ContextManager(memory)
    example_manager = ExampleManager()

    # Initialize modules
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

    print("✓ Systems initialized")

    # Step 1: Brainstorm
    print("\n2. Brainstorming plot ideas...")
    ideas = brainstormer.generate_plot_ideas(
        genre="Fantasy",
        theme="Redemption",
        num_ideas=3
    )

    print(f"✓ Generated {len(ideas)} plot ideas")
    print(f"\nSelected: {ideas[0].get('title', 'Untitled')}")
    print(f"Premise: {ideas[0].get('premise', '')[:100]}...")

    # Step 2: Create full plot
    print("\n3. Creating detailed plot structure...")
    plot = plot_gen.create_full_plot(ideas[0])
    print(f"✓ Plot created: {plot['title']}")

    # Step 3: Create protagonist
    print("\n4. Creating protagonist...")
    protagonists = char_gen.create_protagonist(plot, num_options=2)
    protagonist = protagonists[0]
    print(f"✓ Protagonist: {protagonist.get('name', 'Unknown')}")

    # Step 4: Create antagonist
    print("\n5. Creating antagonist...")
    antagonist = char_gen.create_antagonist(plot, protagonist)
    print(f"✓ Antagonist: {antagonist.get('name', 'Unknown')}")

    # Step 5: Create supporting characters
    print("\n6. Creating supporting characters...")
    supporting = char_gen.create_supporting_characters(
        plot, protagonist, ["mentor", "sidekick"]
    )
    print(f"✓ Created {len(supporting)} supporting characters")

    # Step 6: Create setting
    print("\n7. Creating world and settings...")
    primary_setting = setting_gen.create_primary_setting(plot)
    print(f"✓ Primary setting: {primary_setting.get('location', 'Unknown')}")

    # Step 7: Create outline
    print("\n8. Creating chapter outline...")
    outline = outliner.create_chapter_outline(plot, num_chapters=10)
    print(f"✓ Created outline with {len(outline['chapters'])} chapters")

    # Step 8: Write first chapter
    print("\n9. Writing Chapter 1...")
    chapter1 = writer.write_chapter(
        outline['chapters'][0],
        writing_style="literary",
        language="English"
    )
    print(f"✓ Chapter 1 complete: {chapter1['word_count']} words")

    # Step 9: Edit chapter
    print("\n10. Editing Chapter 1 for style...")
    edit_results = editor.edit_for_style(chapter1['content'][:1000])
    print(f"✓ Editing complete: {len(edit_results['issues'])} issues found")

    # Step 10: Check consistency
    print("\n11. Checking consistency...")
    consistency = checker.check_character_consistency(chapter1['content'])
    print(f"✓ Consistency check: {len(consistency.get('issues', []))} issues found")

    # Step 11: Score chapter
    print("\n12. Scoring chapter...")
    chapter_score = scorer.score_chapter(chapter1)
    print(f"✓ Chapter score: {chapter_score['total_score']:.1f}/10.0 ({chapter_score['grade']})")

    # Step 12: Export
    print("\n13. Exporting novel...")
    novel_data = {
        'title': plot['title'],
        'genre': plot.get('genre', ''),
        'author': 'Novel Writing Agent',
        'plot': plot,
        'characters': [protagonist, antagonist] + supporting,
        'settings': [primary_setting],
        'outline': outline,
        'chapters': [chapter1]
    }

    exported_path = exporter.export_to_text(novel_data, language="English")
    print(f"✓ Exported to: {exported_path}")

    # Final summary
    print("\n" + "=" * 80)
    print("WORKFLOW COMPLETE!")
    print("=" * 80)
    print(f"Novel Title: {plot['title']}")
    print(f"Characters: {len(novel_data['characters'])}")
    print(f"Chapters: {len(novel_data['chapters'])}")
    print(f"Total Words: {chapter1['word_count']}")
    print(f"Chapter Score: {chapter_score['total_score']:.1f}/10.0")
    print(f"Output File: {exported_path}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
