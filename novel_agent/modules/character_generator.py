"""Character generator module for creating detailed character profiles."""
import logging
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from novel_agent.config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE
from novel_agent.memory.context_manager import ContextManager
from novel_agent.memory.long_term_memory import LongTermMemory

logger = logging.getLogger(__name__)


class CharacterGenerator:
    """Generates and manages character profiles for novels."""

    def __init__(self, context_manager: ContextManager, memory: LongTermMemory):
        """
        Initialize the character generator.

        Args:
            context_manager: ContextManager instance
            memory: LongTermMemory instance
        """
        self.context_manager = context_manager
        self.memory = memory
        self.llm = ChatOpenAI(
            model=MODEL_NAME,
            temperature=TEMPERATURE + 0.1,  # Slightly higher for more creative characters
            openai_api_key=OPENAI_API_KEY
        )

    def create_protagonist(self, plot: Dict[str, Any], num_options: int = 3, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate protagonist options based on the plot.

        Args:
            plot: Plot structure
            num_options: Number of protagonist options to generate
            language: Optional language for generation (e.g., 'Simplified Chinese')

        Returns:
            List of protagonist profile dictionaries
        """
        logger.info(f"CharacterGenerator.create_protagonist - language: {language}, num_options: {num_options}")

        system_message = """You are a character creation expert.
Create compelling, multi-dimensional protagonists that fit the story perfectly.
Each character should have depth, flaws, and a clear character arc."""

        user_prompt = f"""Based on this plot, create {num_options} different protagonist options:

Title: {plot.get('title', 'Untitled')}
Premise: {plot.get('premise', '')}
Genre: {plot.get('genre', '')}
Themes: {plot.get('themes', '')}
Conflict: {plot.get('conflict', '')}

For each protagonist provide:
- Name
- Age
- Brief background (2-3 sentences)
- Personality traits (3-4 key traits)
- Core motivation
- Fatal flaw
- Character arc (how they change)
- Why they're perfect for this story

Format each as:
---
PROTAGONIST [number]
Name: [name]
Age: [age]
Background: [background]
Personality: [traits]
Motivation: [core motivation]
Flaw: [fatal flaw]
Arc: [character arc]
Fit: [why perfect for story]
---"""

        # Add language instruction if specified
        if language and language != 'English':
            user_prompt += f"\n\nIMPORTANT: Generate all content in {language}. All text, names, descriptions, and narrative elements should be written in {language}."
            logger.info(f"CharacterGenerator - Added language instruction for: {language}")

        logger.info(f"CharacterGenerator - Sending prompt to OpenAI with language: {language}")

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        logger.info(f"CharacterGenerator - Received response from OpenAI (length: {len(response.content)})")

        protagonists = self._parse_characters(response.content)
        logger.info(f"CharacterGenerator - Parsed {len(protagonists)} protagonists")

        return protagonists

    def create_antagonist(self, plot: Dict[str, Any], protagonist: Dict[str, Any], language: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate an antagonist that complements the protagonist.

        Args:
            plot: Plot structure
            protagonist: Protagonist profile
            language: Optional language for generation (e.g., 'Simplified Chinese')

        Returns:
            Antagonist profile dictionary
        """
        logger.info(f"CharacterGenerator.create_antagonist - language: {language}")

        system_message = """You are a character creation expert specializing in compelling antagonists.
Create an antagonist who is not just evil, but has understandable motivations.
They should be a perfect foil to the protagonist."""

        context = self.context_manager.build_context_for_task("character", "antagonist")

        user_prompt = f"""Create a compelling antagonist for this story:

Plot: {plot.get('premise', '')}
Conflict: {plot.get('conflict', '')}

Protagonist:
Name: {protagonist.get('name', '')}
Motivation: {protagonist.get('motivation', '')}
Flaw: {protagonist.get('flaw', '')}

{context}

Create an antagonist with:
- Name
- Age
- Background (why they became antagonistic)
- Personality traits
- Motivations (what they want and why)
- Methods (how they pursue their goals)
- Relationship to protagonist
- Redeeming qualities (what makes them human)

Format as:
Name: [name]
Age: [age]
Background: [background]
Personality: [traits]
Motivation: [motivation]
Methods: [methods]
Relationship: [relationship to protagonist]
Humanity: [redeeming qualities]"""

        # Add language instruction if specified
        if language and language != 'English':
            user_prompt += f"\n\nIMPORTANT: Generate all content in {language}. All text, names, descriptions, and narrative elements should be written in {language}."
            logger.info(f"CharacterGenerator.create_antagonist - Added language instruction for: {language}")

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        logger.info(f"CharacterGenerator.create_antagonist - Received response from OpenAI")
        antagonist = self._parse_single_character(response.content)

        # Store in memory
        self.memory.store_character(antagonist)

        return antagonist

    def create_supporting_characters(
        self,
        plot: Dict[str, Any],
        protagonist: Dict[str, Any],
        roles: List[str],
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate supporting characters.

        Args:
            plot: Plot structure
            protagonist: Protagonist profile
            roles: List of roles needed (e.g., "mentor", "sidekick", "love interest")
            language: Optional language for generation (e.g., 'Simplified Chinese')

        Returns:
            List of supporting character profiles
        """
        logger.info(f"CharacterGenerator.create_supporting_characters - language: {language}, roles: {roles}")

        characters = []

        for role in roles:
            character = self._create_supporting_character(plot, protagonist, role, language)
            characters.append(character)
            # Store in memory
            self.memory.store_character(character)

        logger.info(f"CharacterGenerator - Created {len(characters)} supporting characters")
        return characters

    def _create_supporting_character(
        self,
        plot: Dict[str, Any],
        protagonist: Dict[str, Any],
        role: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a single supporting character."""
        system_message = f"""You are a character creation expert creating a {role} character.
Make them memorable and essential to the story, not just a stereotype."""

        context = self.context_manager.build_context_for_task("character", role)

        user_prompt = f"""Create a {role} character for this story:

Plot: {plot.get('premise', '')}
Genre: {plot.get('genre', '')}

Protagonist: {protagonist.get('name', '')}

{context}

Provide:
- Name
- Age
- Role: {role}
- Background
- Personality
- Relationship to protagonist
- How they help/hinder the story
- Character arc (if any)

Format as:
Name: [name]
Age: [age]
Role: {role}
Background: [background]
Personality: [personality]
Relationship: [relationship]
Story Function: [how they affect the story]
Arc: [character arc]"""

        # Add language instruction if specified
        if language and language != 'English':
            user_prompt += f"\n\nIMPORTANT: Generate all content in {language}. All text, names, descriptions, and narrative elements should be written in {language}."

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        character = self._parse_single_character(response.content)

        return character

    def develop_character_relationships(self, characters: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Map out relationships between all characters.

        Args:
            characters: List of all character profiles

        Returns:
            Dictionary mapping character pairs to relationship descriptions
        """
        system_message = """You are analyzing character relationships.
Create a relationship map showing how characters interact and relate to each other."""

        char_list = "\n".join([
            f"- {char.get('name', 'Unknown')} ({char.get('role', 'Unknown role')})"
            for char in characters
        ])

        user_prompt = f"""These are the characters in the story:

{char_list}

For each significant relationship between characters, describe:
- The nature of their relationship
- How it evolves over the story
- Key conflicts or bonds

Format as:
[Character A] & [Character B]: [relationship description]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        relationships = self._parse_relationships(response.content)

        return relationships

    def _parse_characters(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse multiple character profiles."""
        characters = []
        current_char = {}
        current_field = None

        # Define English and Chinese label mappings
        label_mappings = {
            'name': ['Name:', '姓名:', '名字:'],
            'age': ['Age:', '年龄:', '年齡:'],
            'background': ['Background:', '背景:', '经历:'],
            'personality': ['Personality:', '性格:', '个性:'],
            'motivation': ['Motivation:', '动机:', '目标:'],
            'flaw': ['Flaw:', '缺陷:', '弱点:'],
            'arc': ['Arc:', '成长:', '发展:'],
            'fit': ['Fit:', '适合:', '契合:'],
            'role': ['Role:', '角色:', '身份:']
        }

        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()

            # Check for field labels in both English and Chinese
            field_found = False
            for field, labels in label_mappings.items():
                for label in labels:
                    if line.startswith(label):
                        if current_char and field == 'name':
                            characters.append(current_char)
                            current_char = {}
                        current_char[field] = line.replace(label, '').strip()
                        current_field = field
                        field_found = True
                        break
                if field_found:
                    break

            # If no field label found, check for continuation or section markers
            if not field_found:
                if current_field and line and not line.startswith(('---', 'PROTAGONIST', 'CHARACTER', '主角', '反派', '配角')):
                    # Continue multi-line content
                    if current_field in current_char:
                        current_char[current_field] += ' ' + line

        if current_char:
            characters.append(current_char)

        return characters

    def _parse_single_character(self, response_text: str) -> Dict[str, Any]:
        """Parse a single character profile."""
        characters = self._parse_characters(response_text)
        return characters[0] if characters else {}

    def _parse_relationships(self, response_text: str) -> Dict[str, str]:
        """Parse relationship descriptions."""
        relationships = {}

        lines = response_text.split('\n')
        for line in lines:
            if '&' in line and ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    pair = parts[0].strip()
                    description = parts[1].strip()
                    relationships[pair] = description

        return relationships
