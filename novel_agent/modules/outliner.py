"""Chapter outlining module for structuring the novel."""
import logging
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from novel_agent.config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE
from novel_agent.memory.context_manager import ContextManager
from novel_agent.memory.long_term_memory import LongTermMemory

logger = logging.getLogger(__name__)


class OutlinerModule:
    """Creates detailed chapter outlines for novels."""

    def __init__(self, context_manager: ContextManager, memory: LongTermMemory):
        """
        Initialize the outliner module.

        Args:
            context_manager: ContextManager instance
            memory: LongTermMemory instance
        """
        self.context_manager = context_manager
        self.memory = memory
        self.llm = ChatOpenAI(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            openai_api_key=OPENAI_API_KEY
        )

    def create_chapter_outline(
        self,
        plot: Dict[str, Any],
        num_chapters: int = 20,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a complete chapter-by-chapter outline.

        Args:
            plot: Plot structure
            num_chapters: Number of chapters to outline
            language: Optional language for generation (e.g., 'Simplified Chinese')

        Returns:
            Complete outline dictionary
        """
        logger.info(f"OutlinerModule.create_chapter_outline - num_chapters: {num_chapters}, "
                   f"plot_title: {plot.get('title', 'Untitled')}, language: {language}")

        # Get all relevant context
        characters = self.memory.get_all_characters()
        settings = self.memory.retrieve_by_type("setting", k=5)

        system_message = """You are an expert story outliner creating detailed chapter outlines.
Each chapter should advance the plot, develop characters, and maintain pacing.
Consider the three-act structure when distributing chapters."""

        char_summary = "\n".join([
            f"- {c.page_content.split(':')[1].split('Age')[0].strip() if ':' in c.page_content else 'Character'}: {c.metadata.get('name', 'Unknown')}"
            for c in characters[:5]
        ])

        user_prompt = f"""Create a {num_chapters}-chapter outline for this novel:

Title: {plot.get('title', 'Untitled')}
Premise: {plot.get('premise', '')}
Plot Structure: {plot.get('structure', '')}

Characters:
{char_summary}

For each chapter provide:
- Chapter number and title
- POV character (if applicable)
- Setting/location
- Plot events (what happens)
- Character development (how characters change)
- Pacing notes (slow/medium/fast)
- Story beats (which major plot points occur)

Consider:
- Act 1: Chapters 1-{num_chapters // 4} (setup)
- Act 2: Chapters {num_chapters // 4 + 1}-{3 * num_chapters // 4} (confrontation)
- Act 3: Chapters {3 * num_chapters // 4 + 1}-{num_chapters} (resolution)

Format each chapter as:
---
CHAPTER [number]: [Title]
POV: [character name]
Setting: [location]
Events: [what happens - 3-4 sentences]
Character Development: [how characters grow/change]
Pacing: [slow/medium/fast]
Story Beats: [which major plot points]
---"""

        # Add language instruction if specified
        if language and language != 'English':
            user_prompt += f"\n\nIMPORTANT: Generate all content in {language}. All text, names, descriptions, and narrative elements should be written in {language}."
            logger.info(f"OutlinerModule - Added language instruction for: {language}")

        logger.info(f"OutlinerModule - Sending prompt to OpenAI requesting {num_chapters} chapters with language: {language}")
        logger.debug(f"OutlinerModule - User prompt: {user_prompt[:500]}")

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        logger.info(f"OutlinerModule - Received response from OpenAI (length: {len(response.content)})")
        logger.debug(f"OutlinerModule - Response content: {response.content[:500]}")

        chapters = self._parse_chapter_outline(response.content)
        logger.info(f"OutlinerModule - Parsed {len(chapters)} chapters from response (requested: {num_chapters})")

        # Validate and limit chapters to requested number
        if len(chapters) > num_chapters:
            logger.warning(f"OutlinerModule - AI generated {len(chapters)} chapters but only {num_chapters} were requested. Truncating to {num_chapters}.")
            chapters = chapters[:num_chapters]
        elif len(chapters) < num_chapters:
            logger.warning(f"OutlinerModule - AI generated only {len(chapters)} chapters but {num_chapters} were requested.")

        logger.info(f"OutlinerModule - Final chapter count after validation: {len(chapters)}")

        outline = {
            'title': plot.get('title', 'Untitled'),
            'num_chapters': num_chapters,
            'chapters': chapters
        }

        # Store in memory
        self.memory.store_outline(outline)
        self.context_manager.update_current_context('outline', outline)

        return outline

    def refine_chapter(
        self,
        chapter_number: int,
        chapter_outline: Dict[str, Any],
        feedback: str
    ) -> Dict[str, Any]:
        """
        Refine a specific chapter outline based on feedback.

        Args:
            chapter_number: Chapter number
            chapter_outline: Current chapter outline
            feedback: User feedback

        Returns:
            Refined chapter outline
        """
        system_message = """You are refining a chapter outline based on feedback.
Maintain consistency with the overall story while incorporating the changes."""

        user_prompt = f"""Refine this chapter outline:

Chapter {chapter_number}: {chapter_outline.get('title', 'Untitled')}
Current outline:
{self._format_chapter(chapter_outline)}

User feedback: {feedback}

Provide the refined chapter in the same format."""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        refined_chapters = self._parse_chapter_outline(response.content)

        return refined_chapters[0] if refined_chapters else chapter_outline

    def generate_scene_breakdown(self, chapter_outline: Dict[str, Any], language: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Break down a chapter into individual scenes.

        Args:
            chapter_outline: Chapter outline dictionary
            language: Optional language for generation (e.g., 'Simplified Chinese')

        Returns:
            List of scene dictionaries
        """
        logger.info(f"OutlinerModule.generate_scene_breakdown - chapter: {chapter_outline.get('number', 'Unknown')}, "
                   f"language: {language}")

        system_message = """You are breaking down a chapter into individual scenes.
Each scene should have a clear purpose and move the story forward."""

        user_prompt = f"""Break down this chapter into 3-5 individual scenes:

Chapter {chapter_outline.get('number', 1)}: {chapter_outline.get('title', 'Untitled')}
Events: {chapter_outline.get('events', '')}

For each scene provide:
- Scene number
- Setting/location
- Characters present
- What happens (2-3 sentences)
- Purpose (why this scene matters)
- Emotional tone

Format each as:
---
SCENE [number]
Setting: [location]
Characters: [list]
Action: [what happens]
Purpose: [why it matters]
Tone: [emotional tone]
---"""

        # Add language instruction if specified
        if language and language != 'English':
            user_prompt += f"\n\nIMPORTANT: Generate all content in {language}. All text, names, descriptions, and narrative elements should be written in {language}."
            logger.info(f"OutlinerModule.generate_scene_breakdown - Added language instruction for: {language}")

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        scenes = self._parse_scenes(response.content)

        return scenes

    def check_outline_pacing(self, outline: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the outline for pacing issues.

        Args:
            outline: Complete outline dictionary

        Returns:
            Pacing analysis dictionary
        """
        system_message = """You are analyzing story pacing.
Identify potential issues with pacing and suggest improvements."""

        chapters_summary = "\n".join([
            f"Chapter {ch.get('number', i+1)}: {ch.get('title', 'Untitled')} - {ch.get('pacing', 'unknown')} pace"
            for i, ch in enumerate(outline.get('chapters', []))
        ])

        user_prompt = f"""Analyze the pacing of this {outline.get('num_chapters', 0)}-chapter outline:

{chapters_summary}

Provide:
- Overall pacing assessment
- Potential problem areas (e.g., too slow, rushed, uneven)
- Specific chapters that may need adjustment
- Recommendations for improvement

Format as:
Overall: [assessment]
Problems: [issues]
Problem Chapters: [list]
Recommendations: [suggestions]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        analysis = self._parse_pacing_analysis(response.content)

        return analysis

    def _parse_chapter_outline(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse chapter outline response."""
        chapters = []
        current_chapter = {}
        current_field = None

        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()

            if line.startswith('CHAPTER ') and ':' in line:
                if current_chapter:
                    chapters.append(current_chapter)
                parts = line.split(':', 1)
                number_part = parts[0].replace('CHAPTER', '').strip()
                title = parts[1].strip() if len(parts) > 1 else 'Untitled'
                try:
                    number = int(number_part)
                except ValueError:
                    number = len(chapters) + 1
                current_chapter = {'number': number, 'title': title}
                current_field = 'title'
            elif line.startswith('POV:'):
                current_chapter['pov'] = line.replace('POV:', '').strip()
                current_field = 'pov'
            elif line.startswith('Setting:'):
                current_chapter['setting'] = line.replace('Setting:', '').strip()
                current_field = 'setting'
            elif line.startswith('Events:'):
                current_chapter['events'] = line.replace('Events:', '').strip()
                current_field = 'events'
            elif line.startswith('Character Development:'):
                current_chapter['character_development'] = line.replace('Character Development:', '').strip()
                current_field = 'character_development'
            elif line.startswith('Pacing:'):
                current_chapter['pacing'] = line.replace('Pacing:', '').strip()
                current_field = 'pacing'
            elif line.startswith('Story Beats:'):
                current_chapter['story_beats'] = line.replace('Story Beats:', '').strip()
                current_field = 'story_beats'
            elif current_field and line and not line.startswith(('---', 'CHAPTER', 'POV:', 'Setting:', 'Events:', 'Character', 'Pacing:', 'Story')):
                if current_field in current_chapter:
                    current_chapter[current_field] += ' ' + line

        if current_chapter:
            chapters.append(current_chapter)

        return chapters

    def _parse_scenes(self, response_text: str) -> List[Dict[str, str]]:
        """Parse scene breakdown response."""
        scenes = []
        current_scene = {}
        current_field = None

        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()

            if line.startswith('SCENE '):
                if current_scene:
                    scenes.append(current_scene)
                number = line.replace('SCENE', '').strip()
                current_scene = {'number': number}
                current_field = 'number'
            elif line.startswith('Setting:'):
                current_scene['setting'] = line.replace('Setting:', '').strip()
                current_field = 'setting'
            elif line.startswith('Characters:'):
                current_scene['characters'] = line.replace('Characters:', '').strip()
                current_field = 'characters'
            elif line.startswith('Action:'):
                current_scene['action'] = line.replace('Action:', '').strip()
                current_field = 'action'
            elif line.startswith('Purpose:'):
                current_scene['purpose'] = line.replace('Purpose:', '').strip()
                current_field = 'purpose'
            elif line.startswith('Tone:'):
                current_scene['tone'] = line.replace('Tone:', '').strip()
                current_field = 'tone'
            elif current_field and line and not line.startswith(('---', 'SCENE', 'Setting:', 'Characters:', 'Action:', 'Purpose:', 'Tone:')):
                if current_field in current_scene:
                    current_scene[current_field] += ' ' + line

        if current_scene:
            scenes.append(current_scene)

        return scenes

    def _parse_pacing_analysis(self, response_text: str) -> Dict[str, Any]:
        """Parse pacing analysis response."""
        analysis = {}
        current_field = None

        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()

            if line.startswith('Overall:'):
                analysis['overall'] = line.replace('Overall:', '').strip()
                current_field = 'overall'
            elif line.startswith('Problems:'):
                analysis['problems'] = line.replace('Problems:', '').strip()
                current_field = 'problems'
            elif line.startswith('Problem Chapters:'):
                analysis['problem_chapters'] = line.replace('Problem Chapters:', '').strip()
                current_field = 'problem_chapters'
            elif line.startswith('Recommendations:'):
                analysis['recommendations'] = line.replace('Recommendations:', '').strip()
                current_field = 'recommendations'
            elif current_field and line and not line.startswith(('Overall:', 'Problems:', 'Problem', 'Recommendations:')):
                if current_field in analysis:
                    analysis[current_field] += ' ' + line

        return analysis

    def _format_chapter(self, chapter: Dict[str, Any]) -> str:
        """Format a chapter outline for display."""
        return f"""POV: {chapter.get('pov', 'Unknown')}
Setting: {chapter.get('setting', 'Unknown')}
Events: {chapter.get('events', 'No events specified')}
Character Development: {chapter.get('character_development', 'None specified')}
Pacing: {chapter.get('pacing', 'Medium')}
Story Beats: {chapter.get('story_beats', 'None specified')}"""
