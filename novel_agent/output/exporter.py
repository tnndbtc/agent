"""Novel exporter for multi-language output."""
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from novel_agent.config import OUTPUT_DIR, SUPPORTED_LANGUAGES


class NovelExporter:
    """Exports novels to various formats and languages."""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the exporter.

        Args:
            output_dir: Output directory (defaults to config OUTPUT_DIR)
        """
        self.output_dir = output_dir or OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_to_text(
        self,
        novel_data: Dict[str, Any],
        language: str = "English",
        filename: Optional[str] = None
    ) -> str:
        """
        Export novel to a text file.

        Args:
            novel_data: Dictionary containing novel data
            language: Target language
            filename: Optional custom filename

        Returns:
            Path to exported file
        """
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Language {language} not supported. Supported: {SUPPORTED_LANGUAGES}")

        # Generate filename if not provided
        if not filename:
            title = novel_data.get('title', 'Untitled')
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_title}_{language}_{timestamp}.txt"

        output_path = self.output_dir / filename

        # Format the novel content
        content = self._format_novel_text(novel_data, language)

        # Write to file with appropriate encoding
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(output_path)

    def export_chapter(
        self,
        chapter_data: Dict[str, Any],
        language: str = "English",
        filename: Optional[str] = None
    ) -> str:
        """
        Export a single chapter to a text file.

        Args:
            chapter_data: Chapter dictionary
            language: Target language
            filename: Optional custom filename

        Returns:
            Path to exported file
        """
        if not filename:
            chapter_num = chapter_data.get('chapter_number', 1)
            title = chapter_data.get('title', 'Untitled')
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"Chapter_{chapter_num}_{safe_title}_{language}.txt"

        output_path = self.output_dir / filename

        content = self._format_chapter_text(chapter_data, language)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(output_path)

    def export_outline(
        self,
        outline_data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        Export novel outline to a text file.

        Args:
            outline_data: Outline dictionary
            filename: Optional custom filename

        Returns:
            Path to exported file
        """
        if not filename:
            title = outline_data.get('title', 'Untitled')
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{safe_title}_Outline.txt"

        output_path = self.output_dir / filename

        content = self._format_outline_text(outline_data)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(output_path)

    def export_character_profiles(
        self,
        characters: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """
        Export character profiles to a text file.

        Args:
            characters: List of character dictionaries
            filename: Optional custom filename

        Returns:
            Path to exported file
        """
        if not filename:
            filename = f"Character_Profiles_{datetime.now().strftime('%Y%m%d')}.txt"

        output_path = self.output_dir / filename

        content = self._format_character_profiles(characters)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(output_path)

    def export_complete_package(
        self,
        novel_data: Dict[str, Any],
        language: str = "English"
    ) -> Dict[str, str]:
        """
        Export complete novel package with all components.

        Args:
            novel_data: Complete novel data
            language: Target language

        Returns:
            Dictionary mapping component names to file paths
        """
        title = novel_data.get('title', 'Untitled')
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create package directory
        package_dir = self.output_dir / f"{safe_title}_{timestamp}"
        package_dir.mkdir(parents=True, exist_ok=True)

        exported_files = {}

        # Export main novel
        novel_path = package_dir / f"{safe_title}_{language}.txt"
        with open(novel_path, 'w', encoding='utf-8') as f:
            f.write(self._format_novel_text(novel_data, language))
        exported_files['novel'] = str(novel_path)

        # Export outline
        if novel_data.get('outline'):
            outline_path = package_dir / "Outline.txt"
            with open(outline_path, 'w', encoding='utf-8') as f:
                f.write(self._format_outline_text(novel_data['outline']))
            exported_files['outline'] = str(outline_path)

        # Export character profiles
        if novel_data.get('characters'):
            chars_path = package_dir / "Characters.txt"
            with open(chars_path, 'w', encoding='utf-8') as f:
                f.write(self._format_character_profiles(novel_data['characters']))
            exported_files['characters'] = str(chars_path)

        # Export individual chapters
        chapters_dir = package_dir / "Chapters"
        chapters_dir.mkdir(exist_ok=True)

        if novel_data.get('chapters'):
            for chapter in novel_data['chapters']:
                chapter_num = chapter.get('chapter_number', 1)
                chapter_path = chapters_dir / f"Chapter_{chapter_num:02d}.txt"
                with open(chapter_path, 'w', encoding='utf-8') as f:
                    f.write(self._format_chapter_text(chapter, language))
                exported_files[f'chapter_{chapter_num}'] = str(chapter_path)

        # Export metadata
        metadata_path = package_dir / "Metadata.txt"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.write(self._format_metadata(novel_data))
        exported_files['metadata'] = str(metadata_path)

        return exported_files

    def _format_novel_text(self, novel_data: Dict[str, Any], language: str) -> str:
        """Format complete novel as text."""
        lines = []

        # Title and metadata
        title = novel_data.get('title', 'Untitled Novel')
        author = novel_data.get('author', 'AI Generated')

        lines.append("=" * 80)
        lines.append(title.center(80))
        lines.append(f"by {author}".center(80))
        lines.append("=" * 80)
        lines.append("")
        lines.append("")

        # Chapters
        chapters = novel_data.get('chapters', [])
        for i, chapter in enumerate(chapters):
            if i > 0:
                lines.append("\n\n\n")

            lines.append("=" * 80)
            chapter_title = f"Chapter {chapter.get('chapter_number', i+1)}: {chapter.get('title', 'Untitled')}"
            lines.append(chapter_title.center(80))
            lines.append("=" * 80)
            lines.append("")
            lines.append("")

            content = chapter.get('content', '')
            lines.append(content)

        # Footer
        lines.append("\n\n")
        lines.append("=" * 80)
        lines.append(f"Generated with Novel Writing Agent".center(80))
        lines.append(f"Language: {language}".center(80))
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}".center(80))
        lines.append("=" * 80)

        return "\n".join(lines)

    def _format_chapter_text(self, chapter_data: Dict[str, Any], language: str) -> str:
        """Format chapter as text."""
        lines = []

        chapter_num = chapter_data.get('chapter_number', 1)
        title = chapter_data.get('title', 'Untitled')

        lines.append("=" * 80)
        lines.append(f"Chapter {chapter_num}: {title}".center(80))
        lines.append("=" * 80)
        lines.append("")
        lines.append("")

        content = chapter_data.get('content', '')
        lines.append(content)

        lines.append("")
        lines.append("")
        lines.append("-" * 80)
        lines.append(f"Word count: {chapter_data.get('word_count', len(content.split()))}".center(80))
        lines.append(f"Language: {language}".center(80))
        lines.append("-" * 80)

        return "\n".join(lines)

    def _format_outline_text(self, outline_data: Dict[str, Any]) -> str:
        """Format outline as text."""
        lines = []

        title = outline_data.get('title', 'Untitled')
        lines.append("=" * 80)
        lines.append(f"Outline: {title}".center(80))
        lines.append("=" * 80)
        lines.append("")

        chapters = outline_data.get('chapters', [])
        for chapter in chapters:
            lines.append(f"\nChapter {chapter.get('number', '?')}: {chapter.get('title', 'Untitled')}")
            lines.append("-" * 40)
            if chapter.get('pov'):
                lines.append(f"POV: {chapter['pov']}")
            if chapter.get('setting'):
                lines.append(f"Setting: {chapter['setting']}")
            if chapter.get('events'):
                lines.append(f"Events: {chapter['events']}")
            if chapter.get('pacing'):
                lines.append(f"Pacing: {chapter['pacing']}")
            lines.append("")

        return "\n".join(lines)

    def _format_character_profiles(self, characters: List[Dict[str, Any]]) -> str:
        """Format character profiles as text."""
        lines = []

        lines.append("=" * 80)
        lines.append("CHARACTER PROFILES".center(80))
        lines.append("=" * 80)
        lines.append("")

        for character in characters:
            lines.append("\n" + "=" * 80)
            lines.append(character.get('name', 'Unknown').center(80))
            lines.append("=" * 80)
            lines.append("")

            for key, value in character.items():
                if key != 'name' and value:
                    lines.append(f"{key.replace('_', ' ').title()}: {value}")

            lines.append("")

        return "\n".join(lines)

    def _format_metadata(self, novel_data: Dict[str, Any]) -> str:
        """Format metadata as text."""
        lines = []

        lines.append("=" * 80)
        lines.append("NOVEL METADATA".center(80))
        lines.append("=" * 80)
        lines.append("")

        metadata_fields = ['title', 'genre', 'author', 'language', 'word_count', 'chapter_count']

        for field in metadata_fields:
            if field in novel_data:
                lines.append(f"{field.replace('_', ' ').title()}: {novel_data[field]}")

        lines.append("")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Generator: Novel Writing Agent v1.0")

        return "\n".join(lines)
