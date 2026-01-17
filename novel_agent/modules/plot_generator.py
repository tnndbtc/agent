"""Plot generator module for creating detailed plot structures."""
import logging
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from novel_agent.config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE
from novel_agent.memory.context_manager import ContextManager
from novel_agent.memory.long_term_memory import LongTermMemory

logger = logging.getLogger(__name__)


class PlotGenerator:
    """Generates and manages plot structures for novels."""

    def __init__(self, context_manager: ContextManager, memory: LongTermMemory):
        """
        Initialize the plot generator.

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

    def create_full_plot(self, plot_idea: Dict[str, Any], language: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a comprehensive plot structure from a plot idea.

        Args:
            plot_idea: Basic plot idea dictionary
            language: Optional language for generation (e.g., 'Simplified Chinese')

        Returns:
            Complete plot structure
        """
        logger.info(f"PlotGenerator.create_full_plot - language: {language}, plot_title: {plot_idea.get('title', 'Untitled')}")

        system_message = """You are an expert plot architect for novels.
Create a comprehensive three-act plot structure that will sustain a full-length novel.
Be specific and provide enough detail for a writer to follow."""

        user_prompt = f"""Based on this plot idea, create a detailed three-act structure:

Title: {plot_idea.get('title', 'Untitled')}
Premise: {plot_idea.get('premise', '')}
Conflict: {plot_idea.get('conflict', '')}
Genre: {plot_idea.get('genre', 'General Fiction')}
Themes: {plot_idea.get('themes', '')}

IMPORTANT: The plot structure must be AT LEAST 2 paragraphs or 200 words in total length.

Create a detailed structure with:

ACT 1 - SETUP (25% of story):
- Opening scene
- Introduction of protagonist and world
- Inciting incident
- First plot point (major turning point)

ACT 2 - CONFRONTATION (50% of story):
- Rising action and complications
- Midpoint (major twist or revelation)
- Protagonist's lowest point
- Second plot point (final push into Act 3)

ACT 3 - RESOLUTION (25% of story):
- Climax
- Resolution
- Denouement

For each section, provide 2-3 sentences of specific plot details.
Ensure the entire plot structure is comprehensive and detailed, with at least 200 words total."""

        # Add language instruction if specified
        if language and language != 'English':
            user_prompt += f"\n\nIMPORTANT: Generate all content in {language}. All text, names, descriptions, and narrative elements should be written in {language}."
            logger.info(f"PlotGenerator - Added language instruction for: {language}")

        logger.info(f"PlotGenerator - Sending prompt to OpenAI with language: {language}")
        logger.debug(f"PlotGenerator - Full prompt: {user_prompt[:500]}")

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        logger.info(f"PlotGenerator - Received response from OpenAI (length: {len(response.content)})")
        logger.debug(f"PlotGenerator - Response preview: {response.content[:500]}")

        plot_structure = {
            'title': plot_idea.get('title', 'Untitled'),
            'genre': plot_idea.get('genre', ''),
            'premise': plot_idea.get('premise', ''),
            'themes': plot_idea.get('themes', ''),
            'conflict': plot_idea.get('conflict', ''),
            'structure': response.content
        }

        # Store in long-term memory
        self.memory.store_plot(plot_structure)
        self.context_manager.update_current_context('plot', plot_structure)

        return plot_structure

    def generate_subplots(self, main_plot: Dict[str, Any], num_subplots: int = 2, language: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Generate subplots that complement the main plot.

        Args:
            main_plot: Main plot structure
            num_subplots: Number of subplots to generate
            language: Optional language for generation (e.g., 'Simplified Chinese')

        Returns:
            List of subplot dictionaries
        """
        logger.info(f"PlotGenerator.generate_subplots - language: {language}, num_subplots: {num_subplots}")

        system_message = """You are a plot expert creating compelling subplots.
Subplots should complement and enhance the main plot, not distract from it.
They should intersect with the main plot at key moments."""

        user_prompt = f"""Main plot:
Title: {main_plot.get('title', 'Untitled')}
Premise: {main_plot.get('premise', '')}
Themes: {main_plot.get('themes', '')}

Generate {num_subplots} subplots that:
1. Support or contrast with the main themes
2. Develop secondary characters
3. Add depth and complexity
4. Resolve by the story's end

For each subplot provide:
- Subplot title
- Description (2-3 sentences)
- How it connects to main plot
- Resolution

Format as:
---
SUBPLOT [number]
Title: [title]
Description: [description]
Connection: [connection to main plot]
Resolution: [how it resolves]
---"""

        # Add language instruction if specified
        if language and language != 'English':
            user_prompt += f"\n\nIMPORTANT: Generate all content in {language}. All text, names, descriptions, and narrative elements should be written in {language}."
            logger.info(f"PlotGenerator.generate_subplots - Added language instruction for: {language}")

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        subplots = self._parse_subplots(response.content)

        return subplots

    def identify_key_scenes(self, plot: Dict[str, Any], language: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Identify key scenes that must be included in the novel.

        Args:
            plot: Plot structure
            language: Optional language for generation (e.g., 'Simplified Chinese')

        Returns:
            List of key scene descriptions
        """
        logger.info(f"PlotGenerator.identify_key_scenes - language: {language}")

        system_message = """You are a story structure expert identifying crucial scenes.
Key scenes are the pivotal moments that drive the plot forward and must be included."""

        user_prompt = f"""Based on this plot:

{plot.get('structure', plot.get('premise', ''))}

Identify 10-15 key scenes that are essential to the story. For each scene provide:
- Scene name
- Where it occurs in the story (Act 1/2/3, percentage)
- What happens (2-3 sentences)
- Why it's crucial

Format as:
---
SCENE [number]
Name: [scene name]
Placement: [Act and approximate percentage]
What Happens: [description]
Importance: [why crucial]
---"""

        # Add language instruction if specified
        if language and language != 'English':
            user_prompt += f"\n\nIMPORTANT: Generate all content in {language}. All text, names, descriptions, and narrative elements should be written in {language}."
            logger.info(f"PlotGenerator.identify_key_scenes - Added language instruction for: {language}")

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        scenes = self._parse_key_scenes(response.content)

        return scenes

    def _parse_subplots(self, response_text: str) -> List[Dict[str, str]]:
        """Parse subplot response into structured format."""
        subplots = []
        current_subplot = {}

        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()

            if line.startswith('Title:'):
                if current_subplot:
                    subplots.append(current_subplot)
                current_subplot = {'title': line.replace('Title:', '').strip()}
            elif line.startswith('Description:'):
                current_subplot['description'] = line.replace('Description:', '').strip()
            elif line.startswith('Connection:'):
                current_subplot['connection'] = line.replace('Connection:', '').strip()
            elif line.startswith('Resolution:'):
                current_subplot['resolution'] = line.replace('Resolution:', '').strip()

        if current_subplot:
            subplots.append(current_subplot)

        return subplots

    def _parse_key_scenes(self, response_text: str) -> List[Dict[str, str]]:
        """Parse key scenes response into structured format."""
        scenes = []
        current_scene = {}

        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()

            if line.startswith('Name:'):
                if current_scene:
                    scenes.append(current_scene)
                current_scene = {'name': line.replace('Name:', '').strip()}
            elif line.startswith('Placement:'):
                current_scene['placement'] = line.replace('Placement:', '').strip()
            elif line.startswith('What Happens:'):
                current_scene['description'] = line.replace('What Happens:', '').strip()
            elif line.startswith('Importance:'):
                current_scene['importance'] = line.replace('Importance:', '').strip()

        if current_scene:
            scenes.append(current_scene)

        return scenes
