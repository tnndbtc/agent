"""Character generator module for creating detailed character profiles."""
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from novel_agent.config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE
from novel_agent.memory.context_manager import ContextManager
from novel_agent.memory.long_term_memory import LongTermMemory


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

    def create_protagonist(self, plot: Dict[str, Any], num_options: int = 3) -> List[Dict[str, Any]]:
        """
        Generate protagonist options based on the plot.

        Args:
            plot: Plot structure
            num_options: Number of protagonist options to generate

        Returns:
            List of protagonist profile dictionaries
        """
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

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        protagonists = self._parse_characters(response.content)

        return protagonists

    def create_antagonist(self, plot: Dict[str, Any], protagonist: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an antagonist that complements the protagonist.

        Args:
            plot: Plot structure
            protagonist: Protagonist profile

        Returns:
            Antagonist profile dictionary
        """
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

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        antagonist = self._parse_single_character(response.content)

        # Store in memory
        self.memory.store_character(antagonist)

        return antagonist

    def create_supporting_characters(
        self,
        plot: Dict[str, Any],
        protagonist: Dict[str, Any],
        roles: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate supporting characters.

        Args:
            plot: Plot structure
            protagonist: Protagonist profile
            roles: List of roles needed (e.g., "mentor", "sidekick", "love interest")

        Returns:
            List of supporting character profiles
        """
        characters = []

        for role in roles:
            character = self._create_supporting_character(plot, protagonist, role)
            characters.append(character)
            # Store in memory
            self.memory.store_character(character)

        return characters

    def _create_supporting_character(
        self,
        plot: Dict[str, Any],
        protagonist: Dict[str, Any],
        role: str
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

        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()

            if line.startswith('Name:'):
                if current_char:
                    characters.append(current_char)
                current_char = {'name': line.replace('Name:', '').strip()}
                current_field = 'name'
            elif line.startswith('Age:'):
                current_char['age'] = line.replace('Age:', '').strip()
                current_field = 'age'
            elif line.startswith('Background:'):
                current_char['background'] = line.replace('Background:', '').strip()
                current_field = 'background'
            elif line.startswith('Personality:'):
                current_char['personality'] = line.replace('Personality:', '').strip()
                current_field = 'personality'
            elif line.startswith('Motivation:'):
                current_char['motivation'] = line.replace('Motivation:', '').strip()
                current_field = 'motivation'
            elif line.startswith('Flaw:'):
                current_char['flaw'] = line.replace('Flaw:', '').strip()
                current_field = 'flaw'
            elif line.startswith('Arc:'):
                current_char['arc'] = line.replace('Arc:', '').strip()
                current_field = 'arc'
            elif line.startswith('Fit:'):
                current_char['fit'] = line.replace('Fit:', '').strip()
                current_field = 'fit'
            elif line.startswith('Role:'):
                current_char['role'] = line.replace('Role:', '').strip()
                current_field = 'role'
            elif current_field and line and not line.startswith(('---', 'PROTAGONIST', 'CHARACTER')):
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
