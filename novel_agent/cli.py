"""Interactive CLI for the Novel Writing Agent."""
import sys
from typing import Dict, Any, List, Optional

from novel_agent.memory.long_term_memory import LongTermMemory
from novel_agent.memory.context_manager import ContextManager
from novel_agent.data.example_manager import ExampleManager
from novel_agent.modules import (
    BrainstormingModule,
    PlotGenerator,
    CharacterGenerator,
    SettingGenerator,
    ChapterWriter,
    EditorModule,
    ConsistencyChecker,
    OutlinerModule
)
from novel_agent.output import NovelExporter, NovelScorer


class NovelAgentCLI:
    """Interactive command-line interface for the Novel Writing Agent."""

    def __init__(self):
        """Initialize the CLI and all modules."""
        print("Initializing Novel Writing Agent...")

        # Initialize core systems
        self.memory = LongTermMemory()
        self.context_manager = ContextManager(self.memory)
        self.example_manager = ExampleManager()

        # Initialize modules
        self.brainstormer = BrainstormingModule(self.context_manager)
        self.plot_gen = PlotGenerator(self.context_manager, self.memory)
        self.char_gen = CharacterGenerator(self.context_manager, self.memory)
        self.setting_gen = SettingGenerator(self.context_manager, self.memory)
        self.outliner = OutlinerModule(self.context_manager, self.memory)
        self.writer = ChapterWriter(self.context_manager, self.memory, self.example_manager)
        self.editor = EditorModule(self.example_manager)
        self.checker = ConsistencyChecker(self.context_manager, self.memory)

        # Initialize output systems
        self.exporter = NovelExporter()
        self.scorer = NovelScorer()

        # Current project state
        self.current_project = {
            'title': None,
            'plot': None,
            'characters': [],
            'settings': [],
            'outline': None,
            'chapters': []
        }

        print("✓ Novel Writing Agent ready!\n")

    def run(self):
        """Run the main CLI loop."""
        print("=" * 80)
        print("NOVEL WRITING AGENT".center(80))
        print("AI-Powered Creative Writing Assistant".center(80))
        print("=" * 80)
        print()

        while True:
            self.show_main_menu()
            choice = input("\nEnter your choice: ").strip()

            if choice == '1':
                self.workflow_new_novel()
            elif choice == '2':
                self.brainstorm_ideas()
            elif choice == '3':
                self.create_characters()
            elif choice == '4':
                self.create_outline()
            elif choice == '5':
                self.write_chapters()
            elif choice == '6':
                self.edit_content()
            elif choice == '7':
                self.check_consistency()
            elif choice == '8':
                self.score_novel()
            elif choice == '9':
                self.export_novel()
            elif choice == '10':
                self.manage_examples()
            elif choice == '0':
                print("\nThank you for using Novel Writing Agent!")
                break
            else:
                print("\n❌ Invalid choice. Please try again.")

    def show_main_menu(self):
        """Display the main menu."""
        print("\n" + "=" * 80)
        print("MAIN MENU")
        print("=" * 80)
        print("1. Start New Novel (Complete Workflow)")
        print("2. Brainstorm Plot Ideas")
        print("3. Create Characters")
        print("4. Create Chapter Outline")
        print("5. Write Chapters")
        print("6. Edit & Refine")
        print("7. Check Consistency")
        print("8. Score Novel")
        print("9. Export Novel")
        print("10. Manage Examples (Good/Bad)")
        print("0. Exit")
        print("=" * 80)

    def workflow_new_novel(self):
        """Complete workflow for creating a new novel."""
        print("\n" + "=" * 80)
        print("NEW NOVEL WORKFLOW")
        print("=" * 80)

        # Step 1: Brainstorm
        print("\n--- Step 1: Brainstorming ---")
        genre = input("Genre (optional): ").strip() or None
        theme = input("Theme (optional): ").strip() or None

        print("\nGenerating plot ideas...")
        ideas = self.brainstormer.generate_plot_ideas(genre=genre, theme=theme, num_ideas=3)

        print("\nPlot Ideas:")
        for i, idea in enumerate(ideas, 1):
            print(f"\n{i}. {idea.get('title', 'Untitled')}")
            print(f"   Premise: {idea.get('premise', '')}")

        choice = int(input("\nSelect plot idea (1-3): ")) - 1
        selected_idea = ideas[choice]

        # Expand the plot
        print("\nExpanding plot idea...")
        plot = self.plot_gen.create_full_plot(selected_idea)
        self.current_project['plot'] = plot
        self.current_project['title'] = plot['title']

        print(f"\n✓ Plot created for: {plot['title']}")

        # Step 2: Characters
        print("\n--- Step 2: Creating Characters ---")
        print("Generating protagonist options...")
        protagonists = self.char_gen.create_protagonist(plot, num_options=3)

        print("\nProtagonist Options:")
        for i, prot in enumerate(protagonists, 1):
            print(f"\n{i}. {prot.get('name', 'Unknown')}")
            print(f"   {prot.get('background', '')[:100]}...")

        choice = int(input("\nSelect protagonist (1-3): ")) - 1
        protagonist = protagonists[choice]
        self.memory.store_character(protagonist)
        self.current_project['characters'].append(protagonist)

        print("\nGenerating antagonist...")
        antagonist = self.char_gen.create_antagonist(plot, protagonist)
        self.current_project['characters'].append(antagonist)

        print(f"✓ Created antagonist: {antagonist.get('name', 'Unknown')}")

        # Supporting characters
        roles = input("\nSupporting character roles (comma-separated, e.g., 'mentor,sidekick'): ").strip()
        if roles:
            role_list = [r.strip() for r in roles.split(',')]
            supporting = self.char_gen.create_supporting_characters(plot, protagonist, role_list)
            self.current_project['characters'].extend(supporting)
            print(f"✓ Created {len(supporting)} supporting characters")

        # Step 3: Settings
        print("\n--- Step 3: Creating World & Settings ---")
        print("Generating primary setting...")
        primary_setting = self.setting_gen.create_primary_setting(plot)
        self.current_project['settings'].append(primary_setting)
        print(f"✓ Created setting: {primary_setting.get('location', 'Unknown')}")

        # Step 4: Outline
        print("\n--- Step 4: Creating Chapter Outline ---")
        num_chapters = int(input("Number of chapters (default 20): ").strip() or "20")

        print(f"Generating {num_chapters}-chapter outline...")
        outline = self.outliner.create_chapter_outline(plot, num_chapters)
        self.current_project['outline'] = outline

        print(f"\n✓ Created outline with {len(outline['chapters'])} chapters")

        # Step 5: Write chapters
        print("\n--- Step 5: Writing Chapters ---")
        write_now = input("Start writing chapters now? (y/n): ").strip().lower()

        if write_now == 'y':
            chapters_to_write = input(f"How many chapters to write (1-{num_chapters}): ").strip()
            chapters_to_write = int(chapters_to_write) if chapters_to_write else 1

            for i in range(min(chapters_to_write, len(outline['chapters']))):
                print(f"\nWriting Chapter {i+1}...")
                chapter = self.writer.write_chapter(outline['chapters'][i])
                self.current_project['chapters'].append(chapter)
                print(f"✓ Chapter {i+1} complete ({chapter['word_count']} words)")

        print("\n" + "=" * 80)
        print("✓ NEW NOVEL WORKFLOW COMPLETE!")
        print("=" * 80)
        print(f"Title: {self.current_project['title']}")
        print(f"Characters: {len(self.current_project['characters'])}")
        print(f"Chapters Written: {len(self.current_project['chapters'])}/{num_chapters}")

    def brainstorm_ideas(self):
        """Brainstorm plot ideas."""
        print("\n--- Brainstorming ---")
        genre = input("Genre (optional): ").strip() or None
        theme = input("Theme (optional): ").strip() or None
        num_ideas = int(input("Number of ideas (default 3): ").strip() or "3")

        print("\nGenerating ideas...")
        ideas = self.brainstormer.generate_plot_ideas(genre=genre, theme=theme, num_ideas=num_ideas)

        print("\n" + "=" * 80)
        for i, idea in enumerate(ideas, 1):
            print(f"\nIDEA {i}: {idea.get('title', 'Untitled')}")
            print(f"Premise: {idea.get('premise', '')}")
            print(f"Conflict: {idea.get('conflict', '')}")
            print(f"Hook: {idea.get('hook', '')}")
            print("-" * 80)

    def create_characters(self):
        """Create characters."""
        print("\n--- Character Creation ---")
        # Implementation here
        print("Feature coming soon...")

    def create_outline(self):
        """Create chapter outline."""
        print("\n--- Chapter Outline ---")
        # Implementation here
        print("Feature coming soon...")

    def write_chapters(self):
        """Write chapters."""
        print("\n--- Chapter Writing ---")
        # Implementation here
        print("Feature coming soon...")

    def edit_content(self):
        """Edit and refine content."""
        print("\n--- Editing & Refinement ---")
        # Implementation here
        print("Feature coming soon...")

    def check_consistency(self):
        """Check consistency."""
        print("\n--- Consistency Check ---")
        if not self.current_project['chapters']:
            print("❌ No chapters to check. Write some chapters first.")
            return

        print("Checking consistency...")
        report = self.checker.generate_consistency_report(self.current_project)

        print("\n" + "=" * 80)
        print("CONSISTENCY REPORT")
        print("=" * 80)
        print(f"Overall: {report['overall_assessment']}")
        print(f"\nCharacter Issues: {len(report['character_issues'])}")
        print(f"Setting Issues: {len(report['setting_issues'])}")
        print(f"Plot Issues: {len(report['plot_issues'])}")
        print(f"Timeline Issues: {len(report['timeline_issues'])}")

    def score_novel(self):
        """Score the novel."""
        print("\n--- Novel Scoring ---")
        if not self.current_project['chapters']:
            print("❌ No chapters to score. Write some chapters first.")
            return

        print("Scoring novel...")
        score_report = self.scorer.score_novel(self.current_project)

        print("\n" + self.scorer.format_score_table(score_report))

    def export_novel(self):
        """Export the novel."""
        print("\n--- Export Novel ---")
        if not self.current_project['chapters']:
            print("❌ No chapters to export. Write some chapters first.")
            return

        print("\nExport Options:")
        print("1. Complete Package (all files)")
        print("2. Novel Text Only")
        print("3. Outline Only")

        choice = input("Choice: ").strip()

        language = input("Language (English/Chinese/French/Spanish): ").strip() or "English"

        if choice == '1':
            files = self.exporter.export_complete_package(self.current_project, language)
            print("\n✓ Exported complete package:")
            for name, path in files.items():
                print(f"  - {name}: {path}")
        elif choice == '2':
            path = self.exporter.export_to_text(self.current_project, language)
            print(f"\n✓ Exported novel to: {path}")
        elif choice == '3':
            if self.current_project['outline']:
                path = self.exporter.export_outline(self.current_project['outline'])
                print(f"\n✓ Exported outline to: {path}")
            else:
                print("❌ No outline to export.")

    def manage_examples(self):
        """Manage good/bad examples."""
        print("\n--- Example Management ---")
        print("1. Add Good Example")
        print("2. Add Bad Example")
        print("3. View Statistics")

        choice = input("Choice: ").strip()

        if choice == '3':
            stats = self.example_manager.get_statistics()
            print("\n" + "=" * 80)
            print("EXAMPLE STATISTICS")
            print("=" * 80)
            print(f"Good Examples: {stats['good_examples']['total']}")
            for cat, count in stats['good_examples']['by_category'].items():
                print(f"  - {cat}: {count}")
            print(f"\nBad Examples: {stats['bad_examples']['total']}")
            for cat, count in stats['bad_examples']['by_category'].items():
                print(f"  - {cat}: {count}")


def main():
    """Main entry point."""
    try:
        cli = NovelAgentCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
