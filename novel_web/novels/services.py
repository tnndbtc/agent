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
from .prompt_assembly import get_language_name  # For services not yet refactored

logger = logging.getLogger(__name__)


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
    """Service for brainstorming operations using 5-layer prompt architecture."""

    @staticmethod
    def generate_ideas(project, genre=None, theme=None, num_ideas=3, custom_prompt=None, use_context=False, user_language='en'):
        """
        Generate plot ideas using 5-layer prompt architecture.

        Args:
            project: NovelProject instance
            genre: Optional genre string
            theme: Optional theme string
            num_ideas: Number of ideas to generate (default: 3)
            custom_prompt: Optional custom user prompt
            use_context: Whether to use existing project context (default: False for faster generation)
            user_language: User's preferred language code (e.g., 'en', 'zh-hans')

        Returns:
            tuple: (list of idea dictionaries, token_usage dict)
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from .prompt_assembly import PromptAssemblyService
        import json

        logger.info(f"BrainstormService.generate_ideas - language: {user_language}, genre: {genre}, theme: {theme}, num_ideas: {num_ideas}")

        # Build user prompt
        if not custom_prompt:
            custom_prompt = f"Generate {num_ideas} creative and unique plot ideas"
            if genre:
                custom_prompt += f" for the {genre} genre"
            if theme:
                custom_prompt += f" with the theme: {theme}"
            custom_prompt += f".\n\nYou MUST return a JSON array with the following structure:\n[\n    {{\n        \"title\": \"A compelling title for the story\",\n        \"premise\": \"A one-paragraph premise describing the main story (2-3 sentences)\",\n        \"hook\": \"What makes this story unique and interesting\"\n    }}\n]\n\nThe array MUST contain exactly {num_ideas} idea object(s).\n\nReturn ONLY the JSON array, no additional text or explanation."

        # Assemble full prompt using 5-layer architecture
        system_message, user_message = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='brainstormer',
            user_prompt=custom_prompt,
            project=project,
            language_code=user_language,
            context_type='brainstorm',
            include_context=use_context
        )

        # Call OpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

        try:
            response = llm.invoke([
                SystemMessage(content=system_message),
                HumanMessage(content=user_message)
            ])

            # Extract token usage
            token_usage = {
                'prompt_tokens': response.response_metadata.get('token_usage', {}).get('prompt_tokens', 0),
                'completion_tokens': response.response_metadata.get('token_usage', {}).get('completion_tokens', 0),
                'total_tokens': response.response_metadata.get('token_usage', {}).get('total_tokens', 0)
            }

            # Parse response - try JSON first, fall back to text parsing
            content = response.content.strip()
            try:
                # Try to parse as JSON
                if content.startswith('['):
                    ideas = json.loads(content)
                else:
                    # Extract JSON array from markdown code block
                    import re
                    json_match = re.search(r'```json\s*(\[.*?\])\s*```', content, re.DOTALL)
                    if json_match:
                        ideas = json.loads(json_match.group(1))
                    else:
                        # Fallback: convert text to simple structure
                        ideas = [{'title': f'Idea {i+1}', 'premise': content, 'hook': ''} for i in range(num_ideas)]
            except:
                # Fallback: convert text to simple structure
                ideas = [{'title': f'Idea {i+1}', 'premise': content, 'hook': ''} for i in range(num_ideas)]

            logger.info(f"BrainstormService generated {len(ideas)} ideas, tokens: {token_usage}")
            return ideas, token_usage

        except Exception as e:
            logger.error(f"Error generating ideas: {e}", exc_info=True)
            raise

    @staticmethod
    def refine_idea(project, idea_data, feedback):
        """Refine a plot idea based on feedback using 5-layer prompt architecture."""
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from .prompt_assembly import PromptAssemblyService
        import json

        user_prompt = f"""Refine the following plot idea based on user feedback:

**Original Idea:**
{json.dumps(idea_data, indent=2)}

**User Feedback:**
{feedback}

Provide the refined idea in the same JSON format with updated fields."""

        language_code = project.target_language if project else 'en'

        system_message, user_message = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='brainstormer',
            user_prompt=user_prompt,
            project=project,
            language_code=language_code,
            context_type='brainstorm',
            include_context=False
        )

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

        try:
            response = llm.invoke([
                SystemMessage(content=system_message),
                HumanMessage(content=user_message)
            ])

            content = response.content.strip()
            # Try to parse JSON
            try:
                if content.startswith('{'):
                    refined = json.loads(content)
                else:
                    import re
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                    if json_match:
                        refined = json.loads(json_match.group(1))
                    else:
                        refined = idea_data  # Fallback to original
            except:
                refined = idea_data

            return refined

        except Exception as e:
            logger.error(f"Error refining idea: {e}", exc_info=True)
            raise

    @staticmethod
    def expand_idea(project, idea_data):
        """Expand a plot idea into detailed structure using 5-layer prompt architecture."""
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from .prompt_assembly import PromptAssemblyService
        import json

        user_prompt = f"""Expand the following plot idea into a detailed story structure:

**Plot Idea:**
{json.dumps(idea_data, indent=2)}

Provide:
- Expanded premise (3-4 paragraphs)
- Main characters (protagonist, antagonist)
- Central conflict
- Story arc (beginning, middle, end)
- Key themes

Format as JSON."""

        language_code = project.target_language if project else 'en'

        system_message, user_message = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='brainstormer',
            user_prompt=user_prompt,
            project=project,
            language_code=language_code,
            context_type='brainstorm',
            include_context=True
        )

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

        try:
            response = llm.invoke([
                SystemMessage(content=system_message),
                HumanMessage(content=user_message)
            ])

            content = response.content.strip()
            # Try to parse JSON
            try:
                if content.startswith('{'):
                    expanded = json.loads(content)
                else:
                    import re
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                    if json_match:
                        expanded = json.loads(json_match.group(1))
                    else:
                        expanded = {'expanded_premise': content}
            except:
                expanded = {'expanded_premise': content}

            return expanded

        except Exception as e:
            logger.error(f"Error expanding idea: {e}", exc_info=True)
            raise


class PlotService:
    """Service for plot operations."""

    @staticmethod
    def create_full_plot(project, idea_data, user_language='en'):
        """
        Create a complete plot structure using 5-layer prompt architecture.

        Args:
            project: NovelProject instance
            idea_data: Dict with plot idea (title, premise, etc.)
            user_language: Language code (e.g., 'en', 'zh-hans')

        Returns:
            tuple: (plot_dict, token_usage)
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from .prompt_assembly import PromptAssemblyService
        import json

        logger.info(f"PlotService.create_full_plot - language: {user_language}")

        # Build user prompt requesting JSON format for reliable parsing
        user_prompt = f"""Create a detailed three-act plot structure based on this idea:

**Title:** {idea_data.get('title', 'Untitled')}
**Premise:** {idea_data.get('premise', '')}
**Hook:** {idea_data.get('hook', '')}

You MUST return a JSON object with the following structure:
{{
    "premise": "One-paragraph summary of the story",
    "genre": "Story genre",
    "themes": "Main themes (comma-separated)",
    "conflict": "Central conflict description",
    "arc": "Overall story arc",
    "acts": [
        {{
            "act_number": 1,
            "subject": "SETUP",
            "percentage": 25,
            "description": "Detailed description of Act 1 - introduce characters, world, and establish the status quo"
        }},
        {{
            "act_number": 2,
            "subject": "CONFRONTATION",
            "percentage": 50,
            "description": "Detailed description of Act 2 - rising action, complications, character growth through challenges"
        }},
        {{
            "act_number": 3,
            "subject": "RESOLUTION",
            "percentage": 25,
            "description": "Detailed description of Act 3 - climax and resolution of the conflict"
        }}
    ]
}}

Return ONLY the JSON object, no additional text or explanation."""

        # Assemble full prompt
        system_message, user_message = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='plotter',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='plot',
            include_context=False
        )

        # Call OpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

        try:
            response = llm.invoke([
                SystemMessage(content=system_message),
                HumanMessage(content=user_message)
            ])

            # Extract token usage
            token_usage = {
                'prompt_tokens': response.response_metadata.get('token_usage', {}).get('prompt_tokens', 0),
                'completion_tokens': response.response_metadata.get('token_usage', {}).get('completion_tokens', 0),
                'total_tokens': response.response_metadata.get('token_usage', {}).get('total_tokens', 0)
            }

            content = response.content.strip()

            # Parse JSON response
            # Try to extract JSON if there's surrounding text
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = content

            try:
                plot_json = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content: {content[:500]}")
                # Fallback to regex parsing for backward compatibility
                plot = {
                    'premise': '',
                    'genre': '',
                    'themes': '',
                    'conflict': '',
                    'structure': content,
                    'arc': '',
                    'acts': []
                }

                premise_match = re.search(r'Premise[:\s]+(.+?)(?=\n\n|\nGenre:|\Z)', content, re.DOTALL | re.IGNORECASE)
                if premise_match:
                    plot['premise'] = premise_match.group(1).strip()

                genre_match = re.search(r'Genre[:\s]+(.+?)(?=\n|\Z)', content, re.IGNORECASE)
                if genre_match:
                    plot['genre'] = genre_match.group(1).strip()

                themes_match = re.search(r'Themes?[:\s]+(.+?)(?=\n|\Z)', content, re.IGNORECASE)
                if themes_match:
                    plot['themes'] = themes_match.group(1).strip()

                conflict_match = re.search(r'Conflict[:\s]+(.+?)(?=\n\n|\nThree-Act|ACT|\Z)', content, re.DOTALL | re.IGNORECASE)
                if conflict_match:
                    plot['conflict'] = conflict_match.group(1).strip()

                arc_match = re.search(r'Arc[:\s]+(.+?)(?=\n\n|\Z)', content, re.DOTALL | re.IGNORECASE)
                if arc_match:
                    plot['arc'] = arc_match.group(1).strip()

                logger.warning("Used fallback regex parsing due to JSON parse error")
                logger.info(f"PlotService.create_full_plot - Generated plot (fallback), tokens: {token_usage}")
                return plot, token_usage

            # Build plot dict from JSON
            plot = {
                'premise': plot_json.get('premise', ''),
                'genre': plot_json.get('genre', ''),
                'themes': plot_json.get('themes', ''),
                'conflict': plot_json.get('conflict', ''),
                'arc': plot_json.get('arc', ''),
                'acts': plot_json.get('acts', []),
                'structure': json.dumps(plot_json, indent=2)  # Keep JSON as structure for legacy compatibility
            }

            # Validate that we have all required fields
            required_fields = ['premise', 'conflict', 'acts']
            missing_fields = [field for field in required_fields if not plot.get(field)]
            if missing_fields:
                logger.warning(f"Plot generation missing fields: {missing_fields}")

            # Ensure we have 3 acts
            if len(plot['acts']) != 3:
                logger.warning(f"Plot generation returned {len(plot['acts'])} acts instead of 3")

            logger.info(f"PlotService.create_full_plot - Generated plot with {len(plot['acts'])} acts, tokens: {token_usage}")
            return plot, token_usage

        except Exception as e:
            logger.error(f"Error creating plot: {e}", exc_info=True)
            raise

    @staticmethod
    def generate_subplots(project, main_plot, num_subplots=2, user_language='en'):
        """Generate subplots using 5-layer prompt architecture."""
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from .prompt_assembly import PromptAssemblyService

        logger.info(f"PlotService.generate_subplots - language: {user_language}, num: {num_subplots}")

        user_prompt = f"""Based on the main plot, generate {num_subplots} compelling subplots:

**Main Plot:**
{main_plot}

For each subplot provide:
- Title
- Description
- How it intersects with the main plot

Format as numbered list."""

        system_message, user_message = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='plotter',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='plot',
            include_context=True
        )

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

        try:
            response = llm.invoke([
                SystemMessage(content=system_message),
                HumanMessage(content=user_message)
            ])

            subplots = response.content.strip()
            logger.info("PlotService.generate_subplots - Successfully generated subplots")
            return subplots

        except Exception as e:
            logger.error(f"Error generating subplots: {e}", exc_info=True)
            raise

    @staticmethod
    def parse_acts(structure_text):
        """
        Parse acts from plot structure text.

        Args:
            structure_text: The plot structure text containing ACT markers

        Returns:
            list: List of dicts with keys: act_number, subject, percentage, description
        """
        import re

        logger.info(f"Parsing acts from structure text (length: {len(structure_text)})")

        acts = []

        # Pattern to match:
        # ACT 1 - SETUP (optional percentage)
        # ... content ...
        # ACT 2 - CONFRONTATION
        act_pattern = r'ACT\s+(\d+)\s*[-–]\s*(\w+)[^\n]*\n(.*?)(?=ACT\s+\d+|$)'

        matches = re.findall(act_pattern, structure_text, re.DOTALL | re.IGNORECASE)

        if not matches:
            logger.warning("No acts found in structure text using regex pattern")
            return acts

        # Default percentages for 3-act structure
        default_percentages = {1: 25, 2: 50, 3: 25}

        for match in matches:
            act_num_str, subject, description = match
            act_num = int(act_num_str)

            act_data = {
                'act_number': act_num,
                'subject': subject.upper().strip(),
                'percentage': default_percentages.get(act_num, 33),
                'description': description.strip()
            }

            acts.append(act_data)
            logger.info(f"Parsed Act {act_num}: {act_data['subject']} ({act_data['percentage']}%)")

        return acts


class CharacterService:
    """Service for character operations using 5-layer prompt architecture."""

    @staticmethod
    def create_protagonists(project, plot_data, num_options=3, user_language='en'):
        """Generate protagonist options using 5-layer prompt architecture.

        Returns:
            tuple: (protagonists, token_usage) where token_usage contains prompt_tokens, completion_tokens, total_tokens
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from .prompt_assembly import PromptAssemblyService
        import json
        import re

        logger.info(f"CharacterService.create_protagonists - project: {project.id}, num_options: {num_options}, user_language: {user_language}")

        # Build user prompt
        user_prompt = f"Create {num_options} protagonist character options for this story.\n\n"

        # Add plot data
        if plot_data:
            # Removed premise - deprecated field that caused pollution
            if plot_data.get('genre'):
                user_prompt += f"**Genre:** {plot_data['genre']}\n"
            if plot_data.get('themes'):
                user_prompt += f"**Themes:** {plot_data['themes']}\n"
            if plot_data.get('conflict'):
                user_prompt += f"**Conflict:** {plot_data['conflict']}\n"
            user_prompt += "\n"

        user_prompt += f"""You MUST return a JSON array with the following structure:
[
    {{
        "name": "Character's full name",
        "age": 25,
        "role": "protagonist",
        "background": "2-3 sentence background/backstory describing the character's past and how they came to this point",
        "personality": "Key personality traits (3-5 traits, comma-separated)",
        "goals": "Character's primary goals or motivations",
        "flaws": "Character's weaknesses or flaws",
        "arc": "How the character will develop/change through the story"
    }}
]

The array MUST contain exactly {num_options} protagonist character object(s).

Return ONLY the JSON array, no additional text or explanation."""

        # Assemble full prompt using 5-layer architecture
        system_message, user_message = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='character_creator',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='character',
            include_context=True
        )

        logger.info(f"Built character creation prompt: system={len(system_message)} chars, user={len(user_message)} chars")

        # Call OpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        response = llm.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ])

        # Extract token usage
        token_usage = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0
        }

        if hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
            usage = response.response_metadata['token_usage']
            token_usage = {
                'prompt_tokens': usage.get('prompt_tokens', 0),
                'completion_tokens': usage.get('completion_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0)
            }

        logger.info(f"OpenAI response received: {len(response.content)} chars, tokens: {token_usage}")

        # Parse JSON response
        content = response.content.strip()

        # Try to extract JSON if wrapped in markdown code blocks
        if '```json' in content:
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1).strip()
        elif '```' in content:
            json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1).strip()

        # Try direct JSON parsing
        try:
            protagonists = json.loads(content)
            if not isinstance(protagonists, list):
                logger.warning("Response is not a list, wrapping in list")
                protagonists = [protagonists]
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Content was: {content[:500]}...")
            # Return empty list
            protagonists = []

        logger.info(f"CharacterService.create_protagonists - Successfully generated {len(protagonists)} protagonists with token usage: {token_usage}")
        return protagonists, token_usage

    @staticmethod
    def create_antagonist(project, plot_data, protagonist_data, user_language='en'):
        """Create an antagonist using 5-layer prompt architecture.

        Returns:
            tuple: (antagonist, token_usage) where token_usage contains prompt_tokens, completion_tokens, total_tokens
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from .prompt_assembly import PromptAssemblyService
        import json
        import re

        logger.info(f"CharacterService.create_antagonist - project: {project.id}, user_language: {user_language}")

        # Build user prompt
        user_prompt = "Create an antagonist character for this story.\n\n"

        # Add plot data
        if plot_data:
            # Removed premise - deprecated field that caused pollution
            if plot_data.get('genre'):
                user_prompt += f"**Genre:** {plot_data['genre']}\n"
            if plot_data.get('conflict'):
                user_prompt += f"**Conflict:** {plot_data['conflict']}\n"
            user_prompt += "\n"

        # Add protagonist data for contrast
        if protagonist_data:
            user_prompt += "**Protagonist:**\n"
            if protagonist_data.get('name'):
                user_prompt += f"Name: {protagonist_data['name']}\n"
            if protagonist_data.get('personality'):
                user_prompt += f"Personality: {protagonist_data['personality']}\n"
            if protagonist_data.get('goals'):
                user_prompt += f"Goals: {protagonist_data['goals']}\n"
            user_prompt += "\n"

        user_prompt += """You MUST return a JSON object with the following structure:
{
    "name": "Character's full name",
    "age": 35,
    "role": "antagonist",
    "background": "2-3 sentence background/backstory describing the character's past and motivations",
    "personality": "Key personality traits that should contrast with protagonist (comma-separated)",
    "goals": "Character's goals that conflict with the protagonist's goals",
    "flaws": "Character's weaknesses or vulnerabilities",
    "relationship_to_protagonist": "How they relate to or oppose the protagonist"
}

Return ONLY the JSON object, no additional text or explanation."""

        # Assemble full prompt using 5-layer architecture
        system_message, user_message = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='character_creator',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='character',
            include_context=True
        )

        # Call OpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        response = llm.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ])

        # Extract token usage
        token_usage = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0
        }

        if hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
            usage = response.response_metadata['token_usage']
            token_usage = {
                'prompt_tokens': usage.get('prompt_tokens', 0),
                'completion_tokens': usage.get('completion_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0)
            }

        # Parse JSON response
        content = response.content.strip()

        # Try to extract JSON if wrapped in markdown code blocks
        if '```json' in content:
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1).strip()
        elif '```' in content:
            json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1).strip()

        # Try direct JSON parsing
        try:
            antagonist = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Content was: {content[:500]}...")
            antagonist = {}

        logger.info(f"CharacterService.create_antagonist - Successfully generated antagonist with token usage: {token_usage}")
        return antagonist, token_usage

    @staticmethod
    def create_supporting(project, plot_data, protagonist_data, roles, user_language='en'):
        """Create supporting characters using 5-layer prompt architecture.

        Returns:
            list: List of supporting characters (without token usage for backward compatibility)
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from .prompt_assembly import PromptAssemblyService
        import json
        import re

        logger.info(f"CharacterService.create_supporting - project: {project.id}, roles: {roles}, user_language: {user_language}")

        # Build user prompt
        user_prompt = f"Create {len(roles)} supporting characters with the following roles: {', '.join(roles)}.\n\n"

        # Add plot data
        if plot_data:
            # Removed premise - deprecated field that caused pollution
            if plot_data.get('genre'):
                user_prompt += f"**Genre:** {plot_data['genre']}\n"
            user_prompt += "\n"

        # Add protagonist data for context
        if protagonist_data:
            user_prompt += "**Protagonist:**\n"
            if protagonist_data.get('name'):
                user_prompt += f"Name: {protagonist_data['name']}\n"
            user_prompt += "\n"

        user_prompt += f"""You MUST return a JSON array with the following structure:
[
    {{
        "name": "Character's full name",
        "age": 30,
        "role": "The specific role (one of: {', '.join(roles)})",
        "background": "1-2 sentence background describing the character's past",
        "personality": "Key personality traits (comma-separated)",
        "relationship_to_protagonist": "How they relate to or support the protagonist"
    }}
]

The array MUST contain exactly {len(roles)} supporting character object(s), one for each role: {', '.join(roles)}.

Return ONLY the JSON array, no additional text or explanation."""

        # Assemble full prompt using 5-layer architecture
        system_message, user_message = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='character_creator',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='character',
            include_context=True
        )

        # Call OpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        response = llm.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ])

        # Parse JSON response
        content = response.content.strip()

        # Try to extract JSON if wrapped in markdown code blocks
        if '```json' in content:
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1).strip()
        elif '```' in content:
            json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1).strip()

        # Try direct JSON parsing
        try:
            supporting = json.loads(content)
            if not isinstance(supporting, list):
                logger.warning("Response is not a list, wrapping in list")
                supporting = [supporting]
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Content was: {content[:500]}...")
            supporting = []

        logger.info(f"CharacterService.create_supporting - Successfully generated {len(supporting)} supporting characters")
        return supporting


class SettingService:
    """Service for setting operations using 5-layer prompt architecture."""

    @staticmethod
    def create_primary_setting(project, plot_data, user_language='en'):
        """Create primary setting using 5-layer prompt architecture.

        Returns:
            dict: Primary setting data
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from .prompt_assembly import PromptAssemblyService
        import json
        import re

        logger.info(f"SettingService.create_primary_setting - project: {project.id}, user_language: {user_language}")

        # Build user prompt
        user_prompt = "Create the primary setting for this story.\n\n"

        # Add plot data
        if plot_data:
            # Removed premise - deprecated field that caused pollution
            if plot_data.get('genre'):
                user_prompt += f"**Genre:** {plot_data['genre']}\n"
            if plot_data.get('themes'):
                user_prompt += f"**Themes:** {plot_data['themes']}\n"
            user_prompt += "\n"

        user_prompt += """Create a detailed primary setting/location that fits the story. Provide:
- name: Setting/location name
- description: 2-3 paragraph detailed description
- atmosphere: The mood and feeling of the location
- key_features: List of 3-5 notable features or landmarks
- history: Brief history or background of the location (optional)
- significance: Why this location is important to the story

Format as JSON object."""

        # Assemble full prompt using 5-layer architecture
        system_message, user_message = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='setting_creator',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='plot',
            include_context=True
        )

        logger.info(f"Built setting creation prompt: system={len(system_message)} chars, user={len(user_message)} chars")

        # Call OpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        response = llm.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ])

        logger.info(f"OpenAI response received: {len(response.content)} chars")

        # Parse JSON response
        content = response.content.strip()

        # Try to extract JSON if wrapped in markdown code blocks
        if '```json' in content:
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1).strip()
        elif '```' in content:
            json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1).strip()

        # Try direct JSON parsing
        try:
            setting = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Content was: {content[:500]}...")
            setting = {}

        logger.info(f"SettingService.create_primary_setting - Successfully generated primary setting")
        return setting

    @staticmethod
    def create_secondary_locations(project, primary_setting, num_locations=3, user_language='en'):
        """Create secondary locations using 5-layer prompt architecture.

        Returns:
            list: List of secondary locations
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from .prompt_assembly import PromptAssemblyService
        import json
        import re

        logger.info(f"SettingService.create_secondary_locations - project: {project.id}, num_locations: {num_locations}, user_language: {user_language}")

        # Build user prompt
        user_prompt = f"Create {num_locations} secondary locations/settings for this story.\n\n"

        # Add primary setting context
        if primary_setting:
            user_prompt += "**Primary Setting:**\n"
            if primary_setting.get('name'):
                user_prompt += f"Name: {primary_setting['name']}\n"
            if primary_setting.get('description'):
                # Just include first paragraph
                desc = primary_setting['description'][:200] + "..." if len(primary_setting.get('description', '')) > 200 else primary_setting.get('description', '')
                user_prompt += f"Description: {desc}\n"
            user_prompt += "\n"

        user_prompt += f"""Create {num_locations} secondary locations that relate to or contrast with the primary setting. For each location, provide:
- name: Location name
- description: 1-2 paragraph description
- atmosphere: The mood and feeling
- key_features: List of 2-3 notable features
- relationship_to_primary: How this location relates to the primary setting

Format as JSON array of location objects."""

        # Assemble full prompt using 5-layer architecture
        system_message, user_message = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='setting_creator',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='plot',
            include_context=True
        )

        # Call OpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        response = llm.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ])

        # Parse JSON response
        content = response.content.strip()

        # Try to extract JSON if wrapped in markdown code blocks
        if '```json' in content:
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1).strip()
        elif '```' in content:
            json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1).strip()

        # Try direct JSON parsing
        try:
            locations = json.loads(content)
            if not isinstance(locations, list):
                logger.warning("Response is not a list, wrapping in list")
                locations = [locations]
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Content was: {content[:500]}...")
            locations = []

        logger.info(f"SettingService.create_secondary_locations - Successfully generated {len(locations)} secondary locations")
        return locations


class OutlineService:
    """Service for outline operations using 5-layer prompt architecture."""

    @staticmethod
    def create_outline(project, plot_data, num_chapters=1, user_language='en', idea_data=None):
        """Create chapter outline using 5-layer prompt architecture."""
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from .prompt_assembly import PromptAssemblyService
        import json
        import re

        logger.info(f"OutlineService.create_outline - project: {project.id}, num_chapters: {num_chapters}, "
                   f"user_language: {user_language}, has_idea_data: {idea_data is not None}")

        # Build user prompt
        user_prompt = f"Create {num_chapters} chapter outline(s) for this story.\n\n"

        # Add act emphasis if generating outline for specific act
        if plot_data and plot_data.get('act_context'):
            act_ctx = plot_data['act_context']
            user_prompt += f"**THIS OUTLINE IS FOR ACT {act_ctx['act_number']} ({act_ctx['subject']}, {act_ctx['percentage']}% of story)**\n\n"
            user_prompt += f"**Act Focus:** {act_ctx['description']}\n\n"
            user_prompt += f"Ensure this chapter outline aligns with the **{act_ctx['subject']}** phase of the story.\n\n"
            user_prompt += "---\n\n"

        # Add plot data
        if plot_data:
            user_prompt += "**Plot Information:**\n"
            # Removed premise - it was causing pollution in generated outlines
            # Acts and themes provide better structured context (added via prompt_assembly)
            if plot_data.get('themes'):
                user_prompt += f"Themes: {plot_data['themes']}\n"
            if plot_data.get('conflict'):
                user_prompt += f"Conflict: {plot_data['conflict']}\n"
            # Removed structure field - it contains premise JSON which pollutes the outline
            # Act context is now emphasized above, and prompt_assembly adds full act details
            user_prompt += "\n"

        # Add original idea if provided
        if idea_data:
            user_prompt += "**Original Idea:**\n"
            if idea_data.get('title'):
                user_prompt += f"Title: {idea_data['title']}\n"
            # Removed premise/description - pollutes generated outlines
            # Theme and conflict are more specific and actionable
            user_prompt += "\n"

        # Determine singular or plural
        plural_suffix = "s" if num_chapters != 1 else ""

        user_prompt += f"""You MUST create exactly {num_chapters} chapter outline{plural_suffix}. No more, no less.

You MUST return a JSON array with the following structure:
[
    {{
        "number": 1,
        "title": "Compelling chapter title",
        "summary": "2-3 sentence summary of what happens in this chapter",
        "events": "Narrative description of the key events that occur in this chapter - what actually happens from beginning to end",
        "pacing": "slow | medium | fast",
        "setting": "Primary location where the chapter takes place",
        "word_count_target": 3000
    }}
]

The array MUST contain exactly {num_chapters} chapter object{plural_suffix}.

Return ONLY the JSON array, no additional text or explanation."""

        # Assemble full prompt using 5-layer architecture
        system_message, user_message = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='outliner',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='outline',
            include_context=True
        )

        # Call OpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        response = llm.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ])

        # Extract token usage
        token_usage = {}
        if hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
            usage = response.response_metadata['token_usage']
            token_usage = {
                'prompt_tokens': usage.get('prompt_tokens', 0),
                'completion_tokens': usage.get('completion_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0)
            }
        elif hasattr(response, 'usage_metadata'):
            token_usage = {
                'prompt_tokens': getattr(response.usage_metadata, 'input_tokens', 0),
                'completion_tokens': getattr(response.usage_metadata, 'output_tokens', 0),
                'total_tokens': getattr(response.usage_metadata, 'total_tokens', 0)
            }

        # Parse JSON response
        content = response.content if hasattr(response, 'content') else str(response)

        chapters = []
        try:
            # Try to parse as JSON directly
            if content.strip().startswith('[') or content.strip().startswith('{'):
                data = json.loads(content)
                if isinstance(data, dict) and 'chapters' in data:
                    chapters = data['chapters']
                elif isinstance(data, list):
                    chapters = data
                else:
                    chapters = [data]
            else:
                # Extract from markdown code block
                json_match = re.search(r'```(?:json)?\s*(\[.*?\]|\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    chapters = json.loads(json_match.group(1))
                else:
                    # Try to find JSON array in content
                    json_match = re.search(r'(\[.*\])', content, re.DOTALL)
                    if json_match:
                        chapters = json.loads(json_match.group(1))
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"Failed to parse outline JSON: {e}, content: {content[:500]}")
            chapters = []

        # Ensure chapters have required fields
        for i, chapter in enumerate(chapters):
            if 'number' not in chapter:
                chapter['number'] = i + 1
            if 'title' not in chapter:
                chapter['title'] = f"Chapter {chapter['number']}"
            if 'summary' not in chapter:
                chapter['summary'] = ""
            if 'pacing' not in chapter:
                chapter['pacing'] = "medium"
            if 'events' not in chapter:
                chapter['events'] = ""
            if 'setting' not in chapter:
                chapter['setting'] = ""
            if 'word_count_target' not in chapter:
                chapter['word_count_target'] = 3000

        outline = {'chapters': chapters}
        logger.info(f"OutlineService generated {len(chapters)} chapters, tokens: {token_usage}")

        return outline, token_usage

    @staticmethod
    def generate_scene_breakdown(project, chapter_outline, user_language='en'):
        """Break down a chapter into scenes."""
        from .prompt_assembly import get_language_name

        service = ProjectService(project)
        outliner = service.get_outliner()

        target_language = get_language_name(user_language)
        logger.info(f"OutlineService.generate_scene_breakdown - user_language: {user_language}, "
                   f"target_language: {target_language}, chapter: {chapter_outline.get('number', 'Unknown')}")

        scenes = outliner.generate_scene_breakdown(chapter_outline, language=target_language)
        logger.info(f"OutlineService.generate_scene_breakdown - Successfully generated {len(scenes)} scenes with language support")
        return scenes


class WritingService:
    """Service for writing operations using 5-layer prompt architecture."""

    @staticmethod
    def write_chapter(project, chapter_outline, writing_style='literary', language='English', target_word_count=3000, example_metadata=None, iteration=1, previous_scores=None):
        """
        Write a complete chapter using 5-layer prompt architecture.

        Args:
            project: NovelProject instance
            chapter_outline: Chapter outline dict or ChapterOutline model instance
            writing_style: Writing style (literary, commercial, etc.)
            language: Target language
            target_word_count: Target word count
            example_metadata: Optional dict with 'category', 'genre', 'total_score', 'scores'
            iteration: Current iteration number (for iterative generation)
            previous_scores: Previous iteration scores (for gap analysis)

        Returns:
            Tuple of (chapter_data, token_usage)
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from .prompt_assembly import PromptAssemblyService

        logger.info(f"WritingService.write_chapter - project: {project.id}, iteration: {iteration}, "
                   f"target_words: {target_word_count}, has_example_metadata: {example_metadata is not None}")

        # Extract outline data (handle both dict and model instance)
        if hasattr(chapter_outline, '__dict__') and hasattr(chapter_outline, 'events'):
            # It's a ChapterOutline model instance
            outline_data = {
                'number': chapter_outline.number,
                'title': chapter_outline.title,
                'pov': getattr(chapter_outline, 'pov', ''),
                'setting': getattr(chapter_outline, 'setting', ''),
                'events': getattr(chapter_outline, 'events', ''),
                'character_development': getattr(chapter_outline, 'character_development', ''),
                'pacing': chapter_outline.pacing,
                'story_beats': getattr(chapter_outline, 'story_beats', ''),
            }
            chapter_outline_model = chapter_outline
        else:
            # It's a dict (legacy support)
            outline_data = chapter_outline
            chapter_outline_model = None

        # Build user prompt
        user_prompt = f"Write Chapter {outline_data.get('number', 1)}: {outline_data.get('title', 'Untitled')}\n\n"

        # Add explicit act emphasis if this chapter belongs to an act
        if chapter_outline_model and hasattr(chapter_outline_model, 'act') and chapter_outline_model.act:
            act = chapter_outline_model.act
            user_prompt += f"**IMPORTANT - Current Story Act:**\n"
            user_prompt += f"This chapter is part of Act {act.act_number}: {act.subject} ({act.percentage}% of story)\n"
            user_prompt += f"Act Focus: {act.description}\n"
            user_prompt += f"Ensure the chapter's content, tone, and pacing align with this act's purpose.\n\n"

        user_prompt += "**Chapter Outline:**\n"

        if outline_data.get('pov'):
            user_prompt += f"POV: {outline_data['pov']}\n"

        if outline_data.get('setting'):
            user_prompt += f"Setting: {outline_data['setting']}\n"

        if outline_data.get('events'):
            user_prompt += f"Events: {outline_data['events']}\n"

        if outline_data.get('character_development'):
            user_prompt += f"Character Development: {outline_data['character_development']}\n"

        user_prompt += f"Pacing: {outline_data.get('pacing', 'medium')}\n"

        if outline_data.get('story_beats'):
            user_prompt += f"Story Beats: {outline_data['story_beats']}\n"

        user_prompt += f"\n**Target Word Count:** {target_word_count} words\n\n"

        # Add example-based quality targeting if provided
        if example_metadata:
            user_prompt += "**Quality Targets (based on example):**\n"
            user_prompt += f"Category: {example_metadata.get('category', 'N/A')}\n"
            user_prompt += f"Target Overall Score: {example_metadata.get('total_score', 'N/A')}\n"

            if example_metadata.get('scores'):
                user_prompt += "\nTarget Scores by Category:\n"
                for score_data in example_metadata['scores']:
                    cat_name = score_data.get('category_name', 'Unknown')
                    target_score = score_data.get('score', 0)
                    user_prompt += f"- {cat_name}: {target_score}/10\n"

        # Add iteration context if this is not the first iteration
        if iteration > 1 and previous_scores:
            user_prompt += f"\n**Iteration {iteration} - Quality Improvement:**\n"
            user_prompt += "This is a revision. Focus on improving scores in these areas:\n"

            for score_data in previous_scores.get('by_category', []):
                cat_name = score_data.get('category_name', 'Unknown')
                current = score_data.get('score', 0)
                target = score_data.get('target_score', 0)
                if current < target:
                    gap = target - current
                    user_prompt += f"- {cat_name}: Current {current}/10, Target {target}/10 (improve by {gap:.1f})\n"

        user_prompt += "\n**Instructions:**\n"
        user_prompt += "Write the complete chapter following the outline and quality targets above.\n"
        user_prompt += "- Use vivid descriptions and engaging prose\n"
        user_prompt += "- Show character emotions through actions and dialogue\n"
        user_prompt += "- Maintain consistent pacing as specified\n"
        user_prompt += "- Include all key events from the outline\n"
        user_prompt += f"- Aim for approximately {target_word_count} words\n"

        if iteration > 1:
            user_prompt += "- This is a revision - focus on addressing the quality gaps noted above\n"

        # Convert language name to code
        language_code = 'zh-hans' if 'Chinese' in language else 'en'

        # Assemble full prompt using 5-layer architecture
        system_message, user_message = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='writer',
            user_prompt=user_prompt,
            project=project,
            language_code=language_code,
            context_type='chapter',
            chapter_outline=chapter_outline_model,
            include_context=True
        )

        # Log act context for debugging
        act_info = "UNASSIGNED"
        if chapter_outline_model and hasattr(chapter_outline_model, 'act') and chapter_outline_model.act:
            act_info = f"Act {chapter_outline_model.act.act_number}: {chapter_outline_model.act.subject}"
        logger.info(f"=== WRITING CHAPTER FOR {act_info} ===")
        # Removed full prompt logging to avoid duplication
        # The ai_client.py monkey-patch already logs all OpenAI API calls with full prompts

        # Call OpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, max_tokens=4096)
        response = llm.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ])

        # Extract token usage
        token_usage = {}
        if hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
            usage = response.response_metadata['token_usage']
            token_usage = {
                'prompt_tokens': usage.get('prompt_tokens', 0),
                'completion_tokens': usage.get('completion_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0)
            }
        elif hasattr(response, 'usage_metadata'):
            token_usage = {
                'prompt_tokens': getattr(response.usage_metadata, 'input_tokens', 0),
                'completion_tokens': getattr(response.usage_metadata, 'output_tokens', 0),
                'total_tokens': getattr(response.usage_metadata, 'total_tokens', 0)
            }

        # Extract content
        content = response.content if hasattr(response, 'content') else str(response)

        # Count words
        word_count = len(content.split())

        chapter_data = {
            'content': content,
            'word_count': word_count,
            'title': outline_data.get('title', f"Chapter {outline_data.get('number', 1)}"),
            'chapter_number': outline_data.get('number', 1)
        }

        logger.info(f"WritingService generated chapter {chapter_data['chapter_number']}, "
                   f"words: {word_count}, tokens: {token_usage}")

        return chapter_data, token_usage

    @staticmethod
    def write_dialogue(project, characters, context, purpose, language='English'):
        """Write a dialogue scene."""
        service = ProjectService(project)
        writer = service.get_writer()

        dialogue = writer.write_dialogue(characters, context, purpose, language)
        return dialogue


class EditingService:
    """Service for editing operations using 5-layer prompt architecture."""

    @staticmethod
    def edit_for_style(project, content, target_style='literary', user_language='en'):
        """Edit content for style using 5-layer prompt architecture.

        Returns:
            str: Edited content
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from .prompt_assembly import PromptAssemblyService

        logger.info(f"EditingService.edit_for_style - project: {project.id}, target_style: {target_style}, content_length: {len(content)}")

        # Build user prompt
        user_prompt = f"Edit the following content to match the '{target_style}' writing style.\n\n"
        user_prompt += "**Instructions:**\n"
        user_prompt += f"- Adjust the writing style to be '{target_style}'\n"
        user_prompt += "- Maintain the original meaning and plot points\n"
        user_prompt += "- Preserve character voices and key details\n"
        user_prompt += "- Return only the edited text, no explanations\n\n"
        user_prompt += "**Original Content:**\n"
        user_prompt += content

        # Assemble full prompt using 5-layer architecture
        system_message, user_message = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='editor',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='chapter',
            include_context=True
        )

        logger.info(f"Built editing prompt: system={len(system_message)} chars, user={len(user_message)} chars")

        # Call OpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        response = llm.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ])

        result = response.content.strip()
        logger.info(f"EditingService.edit_for_style - Successfully edited content, result_length: {len(result)}")
        return result

    @staticmethod
    def edit_for_grammar(project, content, user_language='en'):
        """Check and correct grammar using 5-layer prompt architecture.

        Returns:
            str: Grammar-corrected content
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from .prompt_assembly import PromptAssemblyService

        logger.info(f"EditingService.edit_for_grammar - project: {project.id}, content_length: {len(content)}")

        # Build user prompt
        user_prompt = "Review and correct the grammar, spelling, and punctuation in the following content.\n\n"
        user_prompt += "**Instructions:**\n"
        user_prompt += "- Fix grammar errors\n"
        user_prompt += "- Correct spelling mistakes\n"
        user_prompt += "- Improve punctuation\n"
        user_prompt += "- Maintain the original writing style and voice\n"
        user_prompt += "- Return only the corrected text, no explanations\n\n"
        user_prompt += "**Original Content:**\n"
        user_prompt += content

        # Assemble full prompt using 5-layer architecture
        system_message, user_message = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='editor',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='chapter',
            include_context=False  # Grammar editing doesn't need full context
        )

        # Call OpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)  # Lower temperature for grammar
        response = llm.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ])

        result = response.content.strip()
        logger.info(f"EditingService.edit_for_grammar - Successfully corrected grammar, result_length: {len(result)}")
        return result

    @staticmethod
    def improve_dialogue(project, dialogue, character_names, user_language='en'):
        """Improve dialogue using 5-layer prompt architecture.

        Returns:
            str: Improved dialogue
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from .prompt_assembly import PromptAssemblyService

        logger.info(f"EditingService.improve_dialogue - project: {project.id}, characters: {character_names}, dialogue_length: {len(dialogue)}")

        # Build user prompt
        user_prompt = f"Improve the following dialogue between characters: {', '.join(character_names)}.\n\n"
        user_prompt += "**Instructions:**\n"
        user_prompt += "- Make dialogue more natural and realistic\n"
        user_prompt += "- Ensure each character has a distinct voice\n"
        user_prompt += "- Add subtext where appropriate\n"
        user_prompt += "- Maintain the meaning and plot progression\n"
        user_prompt += "- Return only the improved dialogue, no explanations\n\n"
        user_prompt += "**Original Dialogue:**\n"
        user_prompt += dialogue

        # Assemble full prompt using 5-layer architecture
        system_message, user_message = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='editor',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='chapter',
            include_context=True  # Context helps maintain character voices
        )

        # Call OpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        response = llm.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ])

        result = response.content.strip()
        logger.info(f"EditingService.improve_dialogue - Successfully improved dialogue, result_length: {len(result)}")
        return result


class ConsistencyService:
    """Service for consistency checking using 5-layer prompt architecture."""

    @staticmethod
    def check_chapter_consistency(project, chapter_content, user_language='en'):
        """Check chapter for consistency issues using 5-layer prompt architecture.

        Returns:
            dict: Consistency report with identified issues
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from .prompt_assembly import PromptAssemblyService
        import json
        import re

        logger.info(f"ConsistencyService.check_chapter_consistency - project: {project.id}, content_length: {len(chapter_content)}")

        # Build user prompt
        user_prompt = "Review the following chapter content for consistency issues.\n\n"
        user_prompt += "**Check for:**\n"
        user_prompt += "- Character trait consistency (behavior, personality, speech patterns)\n"
        user_prompt += "- Plot continuity (timeline, cause-effect relationships)\n"
        user_prompt += "- Setting/world-building consistency\n"
        user_prompt += "- Character knowledge and abilities\n\n"
        user_prompt += "**Chapter Content:**\n"
        user_prompt += chapter_content[:3000]  # Limit to avoid token limits
        if len(chapter_content) > 3000:
            user_prompt += "\n... (content truncated)"
        user_prompt += "\n\n**Instructions:**\n"
        user_prompt += "Provide a JSON report with:\n"
        user_prompt += "- issues: List of consistency issues found (each with 'type', 'description', 'severity')\n"
        user_prompt += "- summary: Brief overall assessment\n"
        user_prompt += "- score: Consistency score from 1-10 (10 = perfectly consistent)"

        # Assemble full prompt using 5-layer architecture
        system_message, user_message = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='consistency_checker',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='chapter',
            include_context=True  # Context helps identify inconsistencies
        )

        logger.info(f"Built consistency check prompt: system={len(system_message)} chars, user={len(user_message)} chars")

        # Call OpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)  # Lower temperature for analytical task
        response = llm.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ])

        # Parse JSON response
        content = response.content.strip()

        # Try to extract JSON if wrapped in markdown code blocks
        if '```json' in content:
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1).strip()
        elif '```' in content:
            json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1).strip()

        # Try direct JSON parsing
        try:
            character_check = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Content was: {content[:500]}...")
            character_check = {
                'issues': [],
                'summary': 'Unable to analyze consistency',
                'score': 5
            }

        logger.info(f"ConsistencyService.check_chapter_consistency - Found {len(character_check.get('issues', []))} issues")
        return character_check

    @staticmethod
    def generate_full_report(project, novel_data, user_language='en'):
        """Generate comprehensive consistency report using 5-layer prompt architecture.

        Returns:
            dict: Full consistency report for the entire novel
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from .prompt_assembly import PromptAssemblyService
        import json
        import re

        logger.info(f"ConsistencyService.generate_full_report - project: {project.id}")

        # Build user prompt with novel overview
        user_prompt = "Generate a comprehensive consistency report for this novel.\n\n"

        # Add novel data summary
        if novel_data:
            if novel_data.get('title'):
                user_prompt += f"**Title:** {novel_data['title']}\n"
            if novel_data.get('chapters'):
                user_prompt += f"**Number of Chapters:** {len(novel_data['chapters'])}\n\n"

                # Add chapter summaries (abbreviated)
                user_prompt += "**Chapter Summaries:**\n"
                for i, chapter in enumerate(novel_data['chapters'][:10], 1):  # Limit to first 10
                    content = chapter.get('content', '')[:200]  # First 200 chars
                    user_prompt += f"Chapter {i}: {content}...\n"
                if len(novel_data['chapters']) > 10:
                    user_prompt += f"... and {len(novel_data['chapters']) - 10} more chapters\n"
                user_prompt += "\n"

        user_prompt += """**Instructions:**
Generate a comprehensive consistency report with:
- character_consistency: Issues with character development, traits, behavior
- plot_consistency: Timeline issues, plot holes, unresolved threads
- setting_consistency: World-building inconsistencies, location details
- overall_score: Overall consistency score from 1-10
- recommendations: List of specific recommendations to improve consistency

Format as JSON object."""

        # Assemble full prompt using 5-layer architecture
        system_message, user_message = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='consistency_checker',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='chapter',
            include_context=True
        )

        # Call OpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        response = llm.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ])

        # Parse JSON response
        content = response.content.strip()

        # Try to extract JSON if wrapped in markdown code blocks
        if '```json' in content:
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1).strip()
        elif '```' in content:
            json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1).strip()

        # Try direct JSON parsing
        try:
            report = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Content was: {content[:500]}...")
            report = {
                'character_consistency': [],
                'plot_consistency': [],
                'setting_consistency': [],
                'overall_score': 5,
                'recommendations': []
            }

        logger.info(f"ConsistencyService.generate_full_report - Generated full report with score: {report.get('overall_score', 'N/A')}")
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


class ExampleScoringService:
    """Service for AI-powered example scoring."""

    @staticmethod
    def generate_scores(content, category=None, user_language='en'):
        """
        Generate AI scores for example content across all score categories.

        Args:
            content: The example text to evaluate
            category: Optional category hint (dialogue, action, description, etc.)
            user_language: User's language for response

        Returns:
            dict: {category_id: score_value} for each score category
        """
        from .models import ScoreCategory
        from novel_agent.output import ExampleScorer

        logger.info(f"Generating scores for content (length: {len(content)}, category: {category})")

        # Get all public score categories from Django DB
        categories = ScoreCategory.objects.filter(public=True).order_by('order')

        if not categories.exists():
            logger.warning("No score categories found")
            return {}, {}

        # Build category mapping for novel_agent scorer
        category_descriptions = {
            'Story/Plot': 'Plot structure, pacing, narrative flow, and story development',
            'Character Development': 'Character depth, growth, believability, and complexity',
            'World Building': 'Setting details, atmosphere, immersion, and environmental description',
            'Writing Style': 'Prose quality, voice, readability, and technical execution',
            'Dialogue': 'Natural conversation, character voice, and realistic exchanges',
            'Emotional Impact': 'Emotional resonance, reader engagement, and evocative writing'
        }

        # Create mapping of category names to descriptions for categories that exist in DB
        scorer_categories = {}
        for cat in categories:
            cat_name = str(cat)
            desc = category_descriptions.get(cat_name, 'General quality in this dimension')
            scorer_categories[cat_name] = desc

        # Get the example scorer from novel_agent
        scorer = ExampleScorer()

        try:
            # Call novel_agent scorer (returns tuple of scores and token_usage)
            scores_by_name, token_usage = scorer.score_example(
                content=content,
                categories=scorer_categories,
                category_hint=category
            )

            logger.info(f"AI returned scores: {scores_by_name}, tokens: {token_usage}")

            # Map category names to IDs for Django
            scores_dict = {}
            for cat in categories:
                cat_name = str(cat)
                # Case-insensitive match
                for score_cat_name, score_value in scores_by_name.items():
                    if score_cat_name.lower() == cat_name.lower():
                        scores_dict[cat.id] = score_value
                        break

            logger.info(f"Mapped scores to IDs: {scores_dict}")
            return scores_dict, token_usage

        except Exception as e:
            logger.error(f"Error generating scores: {e}", exc_info=True)
            raise


class AIModificationService:
    """Service for AI-powered text modification with custom prompts using 5-layer prompt architecture."""

    @staticmethod
    def modify_text_selection(user, original_text, user_prompt, content_type='text', project=None):
        """
        Modify selected text based on user's custom prompt using 5-layer prompt architecture.

        Args:
            user: Django User instance (for token tracking)
            original_text: The selected text to modify
            user_prompt: User's modification instructions
            content_type: Type of content (plot, character, outline, chapter, etc.)
            project: Optional NovelProject instance (for styles, techniques, target_language)

        Returns:
            dict: {
                'original_text': str,
                'modified_text': str,
                'user_prompt': str,
                'token_usage': dict
            }
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from .prompt_assembly import PromptAssemblyService

        logger.info(f"Modifying {content_type} text (length: {len(original_text)}) with prompt: {user_prompt[:100]}...")

        # Initialize LLM
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

        # Determine language code
        language_code = project.target_language if project else 'en'

        # Assemble prompts using 5-layer architecture
        system_message, user_context = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='text_modifier',
            user_prompt=user_prompt,
            project=project,
            language_code=language_code,
            context_type=content_type,
            include_context=False  # Don't include full project context for quick edits
        )

        # Add original text to user message
        final_user_message = f"""**Original Text:**
{original_text}

{user_context}

**Instructions:** Provide ONLY the modified text (no explanations, no markers, no comments). Return the complete modified text that should replace the original."""

        # Call OpenAI
        try:
            response = llm.invoke([
                SystemMessage(content=system_message),
                HumanMessage(content=final_user_message)
            ])

            modified_text = response.content.strip()

            # Extract token usage
            token_usage = {
                'prompt_tokens': response.response_metadata.get('token_usage', {}).get('prompt_tokens', 0),
                'completion_tokens': response.response_metadata.get('token_usage', {}).get('completion_tokens', 0),
                'total_tokens': response.response_metadata.get('token_usage', {}).get('total_tokens', 0)
            }

            logger.info(f"Successfully modified text. Original length: {len(original_text)}, "
                       f"Modified length: {len(modified_text)}, Tokens: {token_usage}")

            # Track token usage for user
            if hasattr(user, 'profile'):
                user.profile.add_tokens(
                    prompt_tokens=token_usage['prompt_tokens'],
                    completion_tokens=token_usage['completion_tokens'],
                    total_tokens=token_usage['total_tokens']
                )

            return {
                'original_text': original_text,
                'modified_text': modified_text,
                'user_prompt': user_prompt,
                'token_usage': token_usage
            }

        except Exception as e:
            logger.error(f"Error modifying text: {e}", exc_info=True)
            raise
