"""Setting generator module for creating detailed world-building."""
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from novel_agent.config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE
from novel_agent.memory.context_manager import ContextManager
from novel_agent.memory.long_term_memory import LongTermMemory


class SettingGenerator:
    """Generates and manages world-building and settings for novels."""

    def __init__(self, context_manager: ContextManager, memory: LongTermMemory):
        """
        Initialize the setting generator.

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

    def create_primary_setting(self, plot: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create the primary setting for the story.

        Args:
            plot: Plot structure

        Returns:
            Primary setting dictionary
        """
        system_message = """You are a world-building expert creating immersive settings.
Create a vivid, believable world that enhances the story and themes."""

        user_prompt = f"""Create the primary setting for this story:

Title: {plot.get('title', 'Untitled')}
Genre: {plot.get('genre', '')}
Premise: {plot.get('premise', '')}
Themes: {plot.get('themes', '')}

Provide detailed information about:
- Location name
- Time period (historical, contemporary, future, or fantasy equivalent)
- Physical description (geography, climate, architecture)
- Culture and society
- Technology/magic level (if applicable)
- Political structure
- Economy
- Key locations within this setting
- Atmosphere and mood
- How the setting reflects the themes

Format as:
Location: [name]
Time Period: [period]
Physical: [description]
Culture: [culture and society]
Technology: [tech/magic level]
Politics: [political structure]
Economy: [economic system]
Key Locations: [list of important places]
Atmosphere: [mood and feel]
Thematic Connection: [how it reflects themes]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        setting = self._parse_setting(response.content)

        # Store in memory
        self.memory.store_setting(setting)

        return setting

    def create_secondary_locations(
        self,
        primary_setting: Dict[str, Any],
        num_locations: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Create secondary locations within the primary setting.

        Args:
            primary_setting: Primary setting dictionary
            num_locations: Number of secondary locations

        Returns:
            List of secondary location dictionaries
        """
        system_message = """You are creating detailed secondary locations.
Each location should be distinct and serve a purpose in the story."""

        user_prompt = f"""Create {num_locations} secondary locations within this primary setting:

Primary Setting: {primary_setting.get('location', 'Unknown')}
Time Period: {primary_setting.get('time_period', '')}
Culture: {primary_setting.get('culture', '')}

For each location provide:
- Location name
- Type (city, building, natural feature, etc.)
- Description (sensory details)
- Purpose in story
- Atmosphere
- Notable features

Format each as:
---
LOCATION [number]
Name: [name]
Type: [type]
Description: [detailed description]
Story Purpose: [why this location matters]
Atmosphere: [mood]
Features: [notable features]
---"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        locations = self._parse_locations(response.content)

        # Store each in memory
        for location in locations:
            self.memory.store_setting(location)

        return locations

    def develop_magic_system(self, plot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Develop a magic or technology system if applicable.

        Args:
            plot: Plot structure

        Returns:
            Magic/tech system dictionary or None
        """
        genre = plot.get('genre', '').lower()

        if 'fantasy' not in genre and 'sci-fi' not in genre and 'science fiction' not in genre:
            return None

        system_type = "magic" if 'fantasy' in genre else "technology"

        system_message = f"""You are creating a {system_type} system for a story.
Create clear rules and limitations to maintain consistency."""

        user_prompt = f"""Create a {system_type} system for this story:

Genre: {plot.get('genre', '')}
Premise: {plot.get('premise', '')}
Themes: {plot.get('themes', '')}

Provide:
- Name of the system
- How it works (fundamental principles)
- Rules and limitations
- Who can use it and how they learn
- Costs or consequences
- Rare or forbidden aspects
- How it affects society
- Role in the plot

Format as:
Name: [system name]
Principles: [how it works]
Rules: [rules and limitations]
Users: [who can use it]
Costs: [consequences]
Forbidden: [taboo aspects]
Societal Impact: [effect on society]
Plot Role: [importance to story]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        system = self._parse_system(response.content)

        return system

    def create_cultural_elements(self, setting: Dict[str, Any]) -> Dict[str, Any]:
        """
        Develop cultural elements for the setting.

        Args:
            setting: Setting dictionary

        Returns:
            Cultural elements dictionary
        """
        system_message = """You are developing rich cultural details.
Create believable customs, traditions, and social norms."""

        user_prompt = f"""Develop cultural elements for this setting:

Location: {setting.get('location', 'Unknown')}
Time Period: {setting.get('time_period', '')}
Society: {setting.get('culture', '')}

Provide:
- Social customs and etiquette
- Important traditions or festivals
- Religious or spiritual beliefs
- Art and entertainment
- Food and cuisine
- Language or dialect notes
- Social hierarchies
- Taboos or superstitions

Format as:
Customs: [social customs]
Traditions: [festivals and ceremonies]
Beliefs: [religious/spiritual]
Arts: [art and entertainment]
Cuisine: [food culture]
Language: [linguistic notes]
Hierarchy: [social structure]
Taboos: [forbidden things]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        culture = self._parse_culture(response.content)

        return culture

    def _parse_setting(self, response_text: str) -> Dict[str, Any]:
        """Parse setting response into structured format."""
        setting = {}
        current_field = None

        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()

            if line.startswith('Location:'):
                setting['location'] = line.replace('Location:', '').strip()
                current_field = 'location'
            elif line.startswith('Time Period:'):
                setting['time_period'] = line.replace('Time Period:', '').strip()
                current_field = 'time_period'
            elif line.startswith('Physical:'):
                setting['description'] = line.replace('Physical:', '').strip()
                current_field = 'description'
            elif line.startswith('Culture:'):
                setting['culture'] = line.replace('Culture:', '').strip()
                current_field = 'culture'
            elif line.startswith('Technology:'):
                setting['technology'] = line.replace('Technology:', '').strip()
                current_field = 'technology'
            elif line.startswith('Politics:'):
                setting['politics'] = line.replace('Politics:', '').strip()
                current_field = 'politics'
            elif line.startswith('Economy:'):
                setting['economy'] = line.replace('Economy:', '').strip()
                current_field = 'economy'
            elif line.startswith('Key Locations:'):
                setting['important_locations'] = line.replace('Key Locations:', '').strip()
                current_field = 'important_locations'
            elif line.startswith('Atmosphere:'):
                setting['atmosphere'] = line.replace('Atmosphere:', '').strip()
                current_field = 'atmosphere'
            elif line.startswith('Thematic Connection:'):
                setting['thematic_connection'] = line.replace('Thematic Connection:', '').strip()
                current_field = 'thematic_connection'
            elif current_field and line and not line.startswith(('---', 'Location:', 'Time', 'Physical:', 'Culture:', 'Technology:', 'Politics:', 'Economy:', 'Key', 'Atmosphere:', 'Thematic')):
                # Continue multi-line content
                if current_field in setting:
                    setting[current_field] += ' ' + line

        return setting

    def _parse_locations(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse secondary locations."""
        locations = []
        current_location = {}
        current_field = None

        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()

            if line.startswith('Name:'):
                if current_location:
                    locations.append(current_location)
                current_location = {'location': line.replace('Name:', '').strip()}
                current_field = 'location'
            elif line.startswith('Type:'):
                current_location['type'] = line.replace('Type:', '').strip()
                current_field = 'type'
            elif line.startswith('Description:'):
                current_location['description'] = line.replace('Description:', '').strip()
                current_field = 'description'
            elif line.startswith('Story Purpose:'):
                current_location['purpose'] = line.replace('Story Purpose:', '').strip()
                current_field = 'purpose'
            elif line.startswith('Atmosphere:'):
                current_location['atmosphere'] = line.replace('Atmosphere:', '').strip()
                current_field = 'atmosphere'
            elif line.startswith('Features:'):
                current_location['features'] = line.replace('Features:', '').strip()
                current_field = 'features'
            elif current_field and line and not line.startswith(('---', 'LOCATION', 'Name:', 'Type:', 'Description:', 'Story', 'Atmosphere:', 'Features:')):
                if current_field in current_location:
                    current_location[current_field] += ' ' + line

        if current_location:
            locations.append(current_location)

        return locations

    def _parse_system(self, response_text: str) -> Dict[str, Any]:
        """Parse magic/tech system."""
        system = {}
        current_field = None

        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()

            field_mappings = {
                'Name:': 'name',
                'Principles:': 'principles',
                'Rules:': 'rules',
                'Users:': 'users',
                'Costs:': 'costs',
                'Forbidden:': 'forbidden',
                'Societal Impact:': 'impact',
                'Plot Role:': 'plot_role'
            }

            for prefix, field in field_mappings.items():
                if line.startswith(prefix):
                    system[field] = line.replace(prefix, '').strip()
                    current_field = field
                    break
            else:
                if current_field and line and not any(line.startswith(p) for p in field_mappings.keys()):
                    system[current_field] += ' ' + line

        return system

    def _parse_culture(self, response_text: str) -> Dict[str, Any]:
        """Parse cultural elements."""
        culture = {}
        current_field = None

        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()

            field_mappings = {
                'Customs:': 'customs',
                'Traditions:': 'traditions',
                'Beliefs:': 'beliefs',
                'Arts:': 'arts',
                'Cuisine:': 'cuisine',
                'Language:': 'language',
                'Hierarchy:': 'hierarchy',
                'Taboos:': 'taboos'
            }

            for prefix, field in field_mappings.items():
                if line.startswith(prefix):
                    culture[field] = line.replace(prefix, '').strip()
                    current_field = field
                    break
            else:
                if current_field and line and not any(line.startswith(p) for p in field_mappings.keys()):
                    culture[current_field] += ' ' + line

        return culture
