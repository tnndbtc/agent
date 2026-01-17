"""Service layer for Novel Writing Agent integration."""
import logging
from django.conf import settings
from pathlib import Path

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

logger = logging.getLogger(__name__)


def get_language_name(locale_code):
    """
    Convert Django locale code to readable language name for prompts.

    Args:
        locale_code: Django language code (e.g., 'en', 'zh-hans', 'es')

    Returns:
        Human-readable language name (e.g., 'English', 'Simplified Chinese', 'Spanish')
    """
    language_map = {
        'en': 'English',
        'zh-hans': 'Simplified Chinese',
        'zh-hant': 'Traditional Chinese',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'ja': 'Japanese',
        'ko': 'Korean',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'ar': 'Arabic',
    }
    return language_map.get(locale_code, 'English')


def add_language_instruction(custom_prompt, target_language):
    """
    Add language generation instruction to custom prompt.

    Args:
        custom_prompt: Existing custom prompt (can be None)
        target_language: Target language name (e.g., 'Simplified Chinese')

    Returns:
        Modified prompt with language instruction
    """
    if not target_language or target_language == 'English':
        return custom_prompt

    language_instruction = f"\n\nIMPORTANT: Generate all content in {target_language}. All text, names, descriptions, and narrative elements should be written in {target_language}."

    if custom_prompt:
        return custom_prompt + language_instruction
    else:
        return language_instruction.strip()


class ProjectService:
    """Service for managing a novel project with AI modules."""

    def __init__(self, project):
        """
        Initialize service for a specific project.

        Args:
            project: NovelProject instance
        """
        self.project = project

        # Initialize memory with project-specific collection
        # Use Django settings VECTOR_STORE_DIR to avoid permission issues
        self.memory = LongTermMemory(
            collection_name=project.chroma_collection_name,
            vector_store_dir=settings.NOVEL_AGENT['VECTOR_STORE_DIR']
        )

        # Initialize context manager
        self.context_manager = ContextManager(self.memory)

        # Initialize example manager (could be per-user or global)
        examples_dir = settings.NOVEL_AGENT['EXAMPLES_DIR'] / f"user_{project.user.id}"
        examples_dir.mkdir(parents=True, exist_ok=True)
        self.example_manager = ExampleManager()

    def get_brainstormer(self):
        """Get brainstorming module."""
        return BrainstormingModule(self.context_manager)

    def get_plot_generator(self):
        """Get plot generator module."""
        return PlotGenerator(self.context_manager, self.memory)

    def get_character_generator(self):
        """Get character generator module."""
        return CharacterGenerator(self.context_manager, self.memory)

    def get_setting_generator(self):
        """Get setting generator module."""
        return SettingGenerator(self.context_manager, self.memory)

    def get_outliner(self):
        """Get outliner module."""
        return OutlinerModule(self.context_manager, self.memory)

    def get_writer(self):
        """Get chapter writer module."""
        return ChapterWriter(self.context_manager, self.memory, self.example_manager)

    def get_editor(self):
        """Get editor module."""
        return EditorModule(self.example_manager)

    def get_consistency_checker(self):
        """Get consistency checker module."""
        return ConsistencyChecker(self.context_manager, self.memory)

    def get_exporter(self):
        """Get novel exporter."""
        output_dir = settings.NOVEL_AGENT['OUTPUT_DIR'] / f"project_{self.project.id.hex}"
        output_dir.mkdir(parents=True, exist_ok=True)
        return NovelExporter(output_dir=output_dir)

    def get_scorer(self, custom_categories=None):
        """Get novel scorer."""
        return NovelScorer(custom_categories=custom_categories)


class BrainstormService:
    """Service for brainstorming operations."""

    @staticmethod
    def generate_ideas(project, genre=None, theme=None, num_ideas=3, custom_prompt=None, use_context=False, user_language='en'):
        """
        Generate plot ideas.

        Args:
            use_context: Whether to use existing context from memory (default: False for faster generation)
            user_language: User's preferred language code (e.g., 'en', 'zh-hans')

        Returns:
            List of idea dictionaries
        """
        service = ProjectService(project)
        brainstormer = service.get_brainstormer()

        # Add language instruction to prompt
        target_language = get_language_name(user_language)
        logger.info(f"BrainstormService.generate_ideas - user_language: {user_language}, "
                   f"target_language: {target_language}, genre: {genre}, theme: {theme}, num_ideas: {num_ideas}")

        custom_prompt = add_language_instruction(custom_prompt, target_language)
        logger.info(f"BrainstormService - custom_prompt after language instruction: {custom_prompt[:200] if custom_prompt else None}")

        ideas = brainstormer.generate_plot_ideas(
            genre=genre,
            theme=theme,
            num_ideas=num_ideas,
            custom_prompt=custom_prompt,
            use_context=use_context
        )

        logger.info(f"BrainstormService generated {len(ideas)} ideas")
        return ideas

    @staticmethod
    def refine_idea(project, idea_data, feedback):
        """Refine a plot idea based on feedback."""
        service = ProjectService(project)
        brainstormer = service.get_brainstormer()

        refined = brainstormer.refine_plot_idea(idea_data, feedback)
        return refined

    @staticmethod
    def expand_idea(project, idea_data):
        """Expand a plot idea into detailed structure."""
        service = ProjectService(project)
        brainstormer = service.get_brainstormer()

        expanded = brainstormer.expand_plot_idea(idea_data)
        return expanded


class PlotService:
    """Service for plot operations."""

    @staticmethod
    def create_full_plot(project, idea_data, user_language='en'):
        """Create a complete plot structure."""
        service = ProjectService(project)
        plot_gen = service.get_plot_generator()

        # Pass language to plot generator
        target_language = get_language_name(user_language)
        logger.info(f"PlotService.create_full_plot - user_language: {user_language}, target_language: {target_language}")

        plot = plot_gen.create_full_plot(idea_data, language=target_language)
        logger.info("PlotService.create_full_plot - Successfully generated plot with language support")
        return plot

    @staticmethod
    def generate_subplots(project, main_plot, num_subplots=2, user_language='en'):
        """Generate subplots."""
        service = ProjectService(project)
        plot_gen = service.get_plot_generator()

        target_language = get_language_name(user_language)
        logger.info(f"PlotService.generate_subplots - user_language: {user_language}, target_language: {target_language}")

        subplots = plot_gen.generate_subplots(main_plot, num_subplots, language=target_language)
        logger.info("PlotService.generate_subplots - Successfully generated subplots with language support")
        return subplots


class CharacterService:
    """Service for character operations."""

    @staticmethod
    def create_protagonists(project, plot_data, num_options=3, user_language='en'):
        """Generate protagonist options."""
        service = ProjectService(project)
        char_gen = service.get_character_generator()

        target_language = get_language_name(user_language)
        logger.info(f"CharacterService.create_protagonists - user_language: {user_language}, "
                   f"target_language: {target_language}, num_options: {num_options}")

        protagonists = char_gen.create_protagonist(plot_data, num_options, language=target_language)
        logger.info(f"CharacterService.create_protagonists - Successfully generated {len(protagonists)} protagonists with language support")
        return protagonists

    @staticmethod
    def create_antagonist(project, plot_data, protagonist_data, user_language='en'):
        """Create an antagonist."""
        service = ProjectService(project)
        char_gen = service.get_character_generator()

        target_language = get_language_name(user_language)
        logger.info(f"CharacterService.create_antagonist - user_language: {user_language}, "
                   f"target_language: {target_language}")

        antagonist = char_gen.create_antagonist(plot_data, protagonist_data, language=target_language)
        logger.info("CharacterService.create_antagonist - Successfully generated antagonist with language support")
        return antagonist

    @staticmethod
    def create_supporting(project, plot_data, protagonist_data, roles, user_language='en'):
        """Create supporting characters."""
        service = ProjectService(project)
        char_gen = service.get_character_generator()

        target_language = get_language_name(user_language)
        logger.info(f"CharacterService.create_supporting - user_language: {user_language}, "
                   f"target_language: {target_language}, roles: {roles}")

        supporting = char_gen.create_supporting_characters(
            plot_data, protagonist_data, roles, language=target_language
        )
        logger.info(f"CharacterService.create_supporting - Successfully generated {len(supporting)} supporting characters with language support")
        return supporting


class SettingService:
    """Service for setting operations."""

    @staticmethod
    def create_primary_setting(project, plot_data):
        """Create primary setting."""
        service = ProjectService(project)
        setting_gen = service.get_setting_generator()

        setting = setting_gen.create_primary_setting(plot_data)
        return setting

    @staticmethod
    def create_secondary_locations(project, primary_setting, num_locations=3):
        """Create secondary locations."""
        service = ProjectService(project)
        setting_gen = service.get_setting_generator()

        locations = setting_gen.create_secondary_locations(
            primary_setting, num_locations
        )
        return locations


class OutlineService:
    """Service for outline operations."""

    @staticmethod
    def create_outline(project, plot_data, num_chapters=1, user_language='en'):
        """Create chapter outline."""
        logger.info(f"OutlineService.create_outline - project: {project.id}, num_chapters: {num_chapters}, "
                   f"user_language: {user_language}")

        service = ProjectService(project)
        outliner = service.get_outliner()

        target_language = get_language_name(user_language)
        logger.info(f"OutlineService - target_language: {target_language}")

        outline = outliner.create_chapter_outline(plot_data, num_chapters, language=target_language)
        logger.info(f"OutlineService created outline with language parameter, chapters: {len(outline.get('chapters', []))}")

        return outline

    @staticmethod
    def generate_scene_breakdown(project, chapter_outline, user_language='en'):
        """Break down a chapter into scenes."""
        service = ProjectService(project)
        outliner = service.get_outliner()

        target_language = get_language_name(user_language)
        logger.info(f"OutlineService.generate_scene_breakdown - user_language: {user_language}, "
                   f"target_language: {target_language}, chapter: {chapter_outline.get('number', 'Unknown')}")

        scenes = outliner.generate_scene_breakdown(chapter_outline, language=target_language)
        logger.info(f"OutlineService.generate_scene_breakdown - Successfully generated {len(scenes)} scenes with language support")
        return scenes


class WritingService:
    """Service for writing operations."""

    @staticmethod
    def write_chapter(project, chapter_outline, writing_style='literary', language='English', target_word_count=3000):
        """Write a complete chapter."""
        service = ProjectService(project)
        writer = service.get_writer()

        chapter = writer.write_chapter(
            chapter_outline,
            writing_style=writing_style,
            language=language,
            target_word_count=target_word_count
        )
        return chapter

    @staticmethod
    def write_dialogue(project, characters, context, purpose, language='English'):
        """Write a dialogue scene."""
        service = ProjectService(project)
        writer = service.get_writer()

        dialogue = writer.write_dialogue(characters, context, purpose, language)
        return dialogue


class EditingService:
    """Service for editing operations."""

    @staticmethod
    def edit_for_style(project, content, target_style='literary'):
        """Edit content for style."""
        service = ProjectService(project)
        editor = service.get_editor()

        result = editor.edit_for_style(content, target_style)
        return result

    @staticmethod
    def edit_for_grammar(project, content):
        """Check and correct grammar."""
        service = ProjectService(project)
        editor = service.get_editor()

        result = editor.edit_for_grammar(content)
        return result

    @staticmethod
    def improve_dialogue(project, dialogue, character_names):
        """Improve dialogue."""
        service = ProjectService(project)
        editor = service.get_editor()

        result = editor.improve_dialogue(dialogue, character_names)
        return result


class ConsistencyService:
    """Service for consistency checking."""

    @staticmethod
    def check_chapter_consistency(project, chapter_content):
        """Check chapter for consistency issues."""
        service = ProjectService(project)
        checker = service.get_consistency_checker()

        character_check = checker.check_character_consistency(chapter_content)
        return character_check

    @staticmethod
    def generate_full_report(project, novel_data):
        """Generate comprehensive consistency report."""
        service = ProjectService(project)
        checker = service.get_consistency_checker()

        report = checker.generate_consistency_report(novel_data)
        return report


class ScoringService:
    """Service for scoring operations."""

    @staticmethod
    def score_novel(project, novel_data, custom_categories=None):
        """Score a complete novel."""
        service = ProjectService(project)
        scorer = service.get_scorer(custom_categories)

        score_report = scorer.score_novel(novel_data)
        return score_report

    @staticmethod
    def score_chapter(project, chapter_data):
        """Score a single chapter."""
        service = ProjectService(project)
        scorer = service.get_scorer()

        score_report = scorer.score_chapter(chapter_data)
        return score_report


class ExportService:
    """Service for export operations."""

    @staticmethod
    def export_novel(project, novel_data, language='English'):
        """Export complete novel."""
        service = ProjectService(project)
        exporter = service.get_exporter()

        file_path = exporter.export_to_text(novel_data, language)
        return file_path

    @staticmethod
    def export_complete_package(project, novel_data, language='English'):
        """Export complete package with all files."""
        service = ProjectService(project)
        exporter = service.get_exporter()

        files = exporter.export_complete_package(novel_data, language)
        return files
