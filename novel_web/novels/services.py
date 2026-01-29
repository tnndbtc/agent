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
        from openai import OpenAI
        from django.conf import settings
        from .prompt_assembly import PromptAssemblyService
        import json

        logger.info(f"PlotService.create_full_plot - language: {user_language}")

        # Build user prompt requesting JSON format for reliable parsing
        user_prompt = f"""Create a detailed three-act plot structure based on this idea:

**Idea:** {idea_data.get('premise', '')}
**Hook:** {idea_data.get('hook', '')}

You MUST return a JSON object with the following structure for acts and characters:
{{
    "genre": "Story genre",
    "conflict": "Central conflict description",
    "acts": [
        {{
            "act_number": 1,
            "subject": "SETUP",
            "description": "Detailed description of Act 1 - introduce characters, world, and establish the status quo"
        }},
        {{
            "act_number": 2,
            "subject": "CONFRONTATION",
            "description": "Detailed description of Act 2 - rising action, complications, character growth through challenges"
        }},
        {{
            "act_number": 3,
            "subject": "RESOLUTION",
            "description": "Detailed description of Act 3 - climax and resolution of the conflict"
        }}
    ],
    "characters": [
        {{
            "name": "Character name",
            "role": "protagonist/antagonist/mentor/etc",
            "background": "Character background",
            "personality": "Character personality traits",
            "motivation": "What drives this character"
        }}
    ]
}}

Return ONLY the JSON object, no additional text or explanation."""

        # Assemble full prompt - now returns list of message dicts
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='plotter',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='plot',
            include_context=False
        )

        # Call OpenAI directly
        client = OpenAI(api_key=settings.NOVEL_AGENT['OPENAI_API_KEY'])

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7
            )

            # Extract token usage
            token_usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }

            content = response.choices[0].message.content.strip()

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
                logger.error(f"Response content: {content}")
                # Fallback to regex parsing for backward compatibility
                plot = {
                    'premise': '',
                    'genre': '',
                    'conflict': '',
                    'structure': content,
                    'arc': '',
                    'acts': [],
                    'characters': []
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
                'conflict': plot_json.get('conflict', ''),
                'arc': plot_json.get('arc', ''),
                'acts': plot_json.get('acts', []),
                'characters': plot_json.get('characters', []),
                'structure': json.dumps(plot_json, indent=2)  # Keep JSON as structure for legacy compatibility
            }

            # Validate that we have all required fields
            required_fields = ['conflict', 'acts']
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
        from openai import OpenAI
        from django.conf import settings
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

        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='plotter',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='plot',
            include_context=True
        )

        client = OpenAI(api_key=settings.NOVEL_AGENT['OPENAI_API_KEY'])

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7
            )

            subplots = response.choices[0].message.content.strip()
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
            list: List of dicts with keys: act_number, subject, description
        """
        import re

        logger.info(f"Parsing acts from structure text (length: {len(structure_text)})")

        acts = []

        # Pattern to match:
        # ACT 1 - SETUP
        # ... content ...
        # ACT 2 - CONFRONTATION
        act_pattern = r'ACT\s+(\d+)\s*[-–]\s*(\w+)[^\n]*\n(.*?)(?=ACT\s+\d+|$)'

        matches = re.findall(act_pattern, structure_text, re.DOTALL | re.IGNORECASE)

        if not matches:
            logger.warning("No acts found in structure text using regex pattern")
            return acts

        for match in matches:
            act_num_str, subject, description = match
            act_num = int(act_num_str)

            act_data = {
                'act_number': act_num,
                'subject': subject.upper().strip(),
                # percentage field removed in migration 0023
                'description': description.strip()
            }

            acts.append(act_data)
            logger.info(f"Parsed Act {act_num}: {act_data['subject']}")

        return acts


class ContentGenerationService:
    """Generic content generation service for different content types."""

    @staticmethod
    def generate_content(project, idea_data, user_language='en'):
        """
        Generate complete content piece based on project content type.

        Args:
            project: NovelProject instance
            idea_data: Dictionary with idea/theme information
            user_language: Language code for generation (default: 'en')

        Returns:
            Tuple of (content_dict, token_usage)
            content_dict: {'content': str, 'title': str, 'word_count': int, ...}
            token_usage: {'prompt_tokens': int, 'completion_tokens': int, 'total_tokens': int}
        """
        from openai import OpenAI
        from django.conf import settings
        from .content_registry import ContentTypeRegistry

        client = OpenAI(api_key=settings.NOVEL_AGENT['OPENAI_API_KEY'])
        config = ContentTypeRegistry.get_config(project.content_type)

        if not config:
            raise ValueError(f"Unknown content type: {project.content_type}")

        if project.content_type == 'novel':
            # Novels use existing workflow (plot → chapters)
            raise ValueError("Use PlotService and WritingService for novel projects")

        elif project.content_type == 'poem':
            return ContentGenerationService._generate_poem(
                client, project, idea_data, user_language
            )

        elif project.content_type == 'essay':
            return ContentGenerationService._generate_essay(
                client, project, idea_data, user_language
            )

        elif project.content_type == 'sketch':
            return ContentGenerationService._generate_sketch(
                client, project, idea_data, user_language
            )

        elif project.content_type == 'article':
            return ContentGenerationService._generate_article(
                client, project, idea_data, user_language
            )

        else:
            raise ValueError(f"Content generation not implemented for: {project.content_type}")

    @staticmethod
    def _generate_poem(client, project, idea_data, user_language):
        """
        Generate complete poem from idea.

        Args:
            client: OpenAI client instance
            project: NovelProject instance
            idea_data: Dictionary with theme/idea information
            user_language: Language code

        Returns:
            Tuple of (content_dict, token_usage)
        """
        from .prompt_assembly import PromptAssemblyService
        import json

        logger.info(f"Generating poem for project: {project.title}")

        # Extract theme/idea
        theme = idea_data.get('theme', project.title)
        style_notes = idea_data.get('style_notes', '')

        # Build user prompt
        user_prompt = f"""Write a complete poem based on this theme: {theme}

Instructions:
- Create vivid imagery and sensory details
- Pay attention to rhythm and musicality
- Use appropriate poetic form and structure
- Evoke strong emotions
"""
        if style_notes:
            user_prompt += f"\nStyle notes: {style_notes}"

        user_prompt += """

Return the poem in JSON format:
{
    "title": "Poem Title",
    "content": "The complete poem text with line breaks"
}
"""

        # Assemble full prompt with 5-layer architecture
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='poet',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='poem',
            include_context=True
        )

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.8  # Higher temperature for creativity
        )

        content_str = response.choices[0].message.content
        token_usage = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }

        # Parse JSON response
        try:
            result = json.loads(content_str)
            title = result.get('title', 'Untitled')
            content = result.get('content', '')
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON, using raw content")
            title = theme
            content = content_str

        # Calculate word count
        word_count = len(content.split())

        content_dict = {
            'title': title,
            'content': content,
            'word_count': word_count
        }

        logger.info(f"Generated poem: {title} ({word_count} words)")
        return content_dict, token_usage

    @staticmethod
    def _generate_essay(client, project, idea_data, user_language):
        """
        Generate complete essay from idea and structure.

        Args:
            client: OpenAI client instance
            project: NovelProject instance
            idea_data: Dictionary with thesis/topic information
            user_language: Language code

        Returns:
            Tuple of (content_dict, token_usage)
        """
        from .prompt_assembly import PromptAssemblyService
        from .models import ContentStructureTemplate
        import json

        logger.info(f"Generating essay for project: {project.title}")

        # Extract essay parameters
        thesis = idea_data.get('thesis', project.title)
        template_name = idea_data.get('template', 'Five-Paragraph Essay')
        key_points = idea_data.get('key_points', [])

        # Get structure template
        template = ContentStructureTemplate.objects.filter(
            content_type='essay',
            name=template_name
        ).first()

        if not template:
            # Fallback to default
            template = ContentStructureTemplate.objects.filter(
                content_type='essay',
                is_system=True
            ).first()

        # Build user prompt
        user_prompt = f"""Write a complete essay on this thesis: {thesis}

Structure: {template.name if template else 'Five-Paragraph Essay'}
"""
        if template:
            sections = template.structure_data.get('sections', [])
            user_prompt += f"Sections: {', '.join(sections)}\n"

        if key_points:
            user_prompt += f"\nKey points to address:\n"
            for point in key_points:
                user_prompt += f"- {point}\n"

        user_prompt += """
Instructions:
- Present a clear, compelling thesis
- Build strong arguments with evidence
- Organize with logical flow
- Address potential counterarguments
- Write with clarity and precision

Return the essay in JSON format:
{
    "title": "Essay Title",
    "content": "The complete essay text with paragraphs separated by double newlines",
    "sections": {
        "introduction": "...",
        "body1": "...",
        "conclusion": "..."
    }
}
"""

        # Assemble full prompt
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='essayist',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='essay',
            include_context=True
        )

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )

        content_str = response.choices[0].message.content
        token_usage = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }

        # Parse JSON response
        try:
            result = json.loads(content_str)
            title = result.get('title', 'Untitled')
            content = result.get('content', '')
            sections_data = result.get('sections', {})
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON, using raw content")
            title = thesis
            content = content_str
            sections_data = {}

        # Calculate word count
        word_count = len(content.split())

        content_dict = {
            'title': title,
            'content': content,
            'word_count': word_count,
            'sections_data': sections_data,
            'structure_template_id': template.id if template else None
        }

        logger.info(f"Generated essay: {title} ({word_count} words)")
        return content_dict, token_usage

    @staticmethod
    def _generate_sketch(client, project, idea_data, user_language):
        """
        Generate sketch using Moment → Thought → Stop structure.

        Args:
            client: OpenAI client instance
            project: NovelProject instance
            idea_data: Dictionary with observation/scene information
            user_language: Language code

        Returns:
            Tuple of (content_dict, token_usage)
        """
        from .prompt_assembly import PromptAssemblyService
        from .models import ContentStructureTemplate
        import json

        logger.info(f"Generating sketch for project: {project.title}")

        # Extract sketch parameters
        observation = idea_data.get('observation', project.title)
        scene_notes = idea_data.get('scene_notes', '')

        # Get sketch template
        template = ContentStructureTemplate.objects.filter(
            content_type='sketch',
            name='Moment-Thought-Stop'
        ).first()

        # Build user prompt
        user_prompt = f"""Write a literary sketch about: {observation}

Structure: Moment → Thought → Stop
- Moment: Capture a specific observation or scene with vivid detail
- Thought: Reflect on its meaning or significance
- Stop: End abruptly, leaving a lasting impression
"""
        if scene_notes:
            user_prompt += f"\nScene notes: {scene_notes}"

        user_prompt += """

Instructions:
- Observe keenly with precise, concrete details
- Use vivid imagery to bring the moment to life
- Reflect thoughtfully on deeper meaning
- Know when to stop - don't over-explain

Return the sketch in JSON format:
{
    "title": "Sketch Title",
    "content": "The complete sketch text",
    "sections": {
        "moment": "The observed moment...",
        "thought": "Reflection on the moment...",
        "stop": "Final thought or image..."
    }
}
"""

        # Assemble full prompt
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='sketch_writer',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='sketch',
            include_context=True
        )

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.75
        )

        content_str = response.choices[0].message.content
        token_usage = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }

        # Parse JSON response
        try:
            result = json.loads(content_str)
            title = result.get('title', 'Untitled')
            content = result.get('content', '')
            sections_data = result.get('sections', {})
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON, using raw content")
            title = observation
            content = content_str
            sections_data = {}

        # Calculate word count
        word_count = len(content.split())

        content_dict = {
            'title': title,
            'content': content,
            'word_count': word_count,
            'sections_data': sections_data,
            'structure_template_id': template.id if template else None
        }

        logger.info(f"Generated sketch: {title} ({word_count} words)")
        return content_dict, token_usage

    @staticmethod
    def _generate_article(client, project, idea_data, user_language):
        """
        Generate news article using journalistic structure.

        Args:
            client: OpenAI client instance
            project: NovelProject instance
            idea_data: Dictionary with story information
            user_language: Language code

        Returns:
            Tuple of (content_dict, token_usage)
        """
        from .prompt_assembly import PromptAssemblyService
        import json

        logger.info(f"Generating article for project: {project.title}")

        # Extract article parameters
        headline = idea_data.get('headline', project.title)
        facts = idea_data.get('facts', [])
        angle = idea_data.get('angle', '')

        # Build user prompt
        user_prompt = f"""Write a news article with this headline: {headline}

Structure: Inverted Pyramid
- Lead: Most important information (who, what, when, where, why, how)
- Body: Supporting details in descending order of importance
- Background: Context and additional information
"""
        if angle:
            user_prompt += f"\nAngle: {angle}"

        if facts:
            user_prompt += f"\n\nKey facts:\n"
            for fact in facts:
                user_prompt += f"- {fact}\n"

        user_prompt += """
Instructions:
- Prioritize accuracy and factual reporting
- Maintain objectivity and balance
- Use clear, concise language
- Present multiple perspectives when relevant
- Follow AP style guidelines

Return the article in JSON format:
{
    "title": "Article Headline",
    "content": "The complete article text"
}
"""

        # Assemble full prompt
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='journalist',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='article',
            include_context=True
        )

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3  # Lower temperature for factual content
        )

        content_str = response.choices[0].message.content
        token_usage = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }

        # Parse JSON response
        try:
            result = json.loads(content_str)
            title = result.get('title', 'Untitled')
            content = result.get('content', '')
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON, using raw content")
            title = headline
            content = content_str

        # Calculate word count
        word_count = len(content.split())

        content_dict = {
            'title': title,
            'content': content,
            'word_count': word_count
        }

        logger.info(f"Generated article: {title} ({word_count} words)")
        return content_dict, token_usage


class CharacterService:
    """Service for character operations using 5-layer prompt architecture."""

    @staticmethod
    def create_protagonists(project, plot_data, num_options=3, user_language='en'):
        """Generate protagonist options using 5-layer prompt architecture.

        Returns:
            tuple: (protagonists, token_usage) where token_usage contains prompt_tokens, completion_tokens, total_tokens
        """
        from openai import OpenAI
        from django.conf import settings
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
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='character_creator',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='character',
            include_context=True
        )

        logger.info(f"Built character creation prompt with {len(messages)} messages")

        # Call OpenAI directly
        client = OpenAI(api_key=settings.NOVEL_AGENT['OPENAI_API_KEY'])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )

        # Extract token usage
        token_usage = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }

        content = response.choices[0].message.content.strip()
        logger.info(f"OpenAI response received: {len(content)} chars, tokens: {token_usage}")

        # Parse JSON response

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
            logger.error(f"Content was: {content}")
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
        from openai import OpenAI
        from django.conf import settings
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
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='character_creator',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='character',
            include_context=True
        )

        # Call OpenAI directly
        client = OpenAI(api_key=settings.NOVEL_AGENT['OPENAI_API_KEY'])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )

        # Extract token usage
        token_usage = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }

        # Parse JSON response
        content = response.choices[0].message.content.strip()

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
            logger.error(f"Content was: {content}")
            antagonist = {}

        logger.info(f"CharacterService.create_antagonist - Successfully generated antagonist with token usage: {token_usage}")
        return antagonist, token_usage

    @staticmethod
    def create_supporting(project, plot_data, protagonist_data, roles, user_language='en'):
        """Create supporting characters using 5-layer prompt architecture.

        Returns:
            list: List of supporting characters (without token usage for backward compatibility)
        """
        from openai import OpenAI
        from django.conf import settings
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
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='character_creator',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='character',
            include_context=True
        )

        # Call OpenAI directly
        client = OpenAI(api_key=settings.NOVEL_AGENT['OPENAI_API_KEY'])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )

        # Parse JSON response
        content = response.choices[0].message.content.strip()

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
            logger.error(f"Content was: {content}")
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
        from openai import OpenAI
        from django.conf import settings
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
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='setting_creator',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='plot',
            include_context=True
        )

        logger.info(f"Built setting creation prompt with {len(messages)} messages")

        # Call OpenAI directly
        client = OpenAI(api_key=settings.NOVEL_AGENT['OPENAI_API_KEY'])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )

        content = response.choices[0].message.content
        logger.info(f"OpenAI response received: {len(content)} chars")

        # Parse JSON response
        content = content.strip()

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
            logger.error(f"Content was: {content}")
            setting = {}

        logger.info(f"SettingService.create_primary_setting - Successfully generated primary setting")
        return setting

    @staticmethod
    def create_secondary_locations(project, primary_setting, num_locations=3, user_language='en'):
        """Create secondary locations using 5-layer prompt architecture.

        Returns:
            list: List of secondary locations
        """
        from openai import OpenAI
        from django.conf import settings
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
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='setting_creator',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='plot',
            include_context=True
        )

        # Call OpenAI directly
        client = OpenAI(api_key=settings.NOVEL_AGENT['OPENAI_API_KEY'])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )

        # Parse JSON response
        content = response.choices[0].message.content.strip()

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
            logger.error(f"Content was: {content}")
            locations = []

        logger.info(f"SettingService.create_secondary_locations - Successfully generated {len(locations)} secondary locations")
        return locations


class WritingService:
    """Service for writing operations using 5-layer prompt architecture."""

    @staticmethod
    def calculate_order_key_for_chapter(project, act=None):
        """
        Calculate appropriate order_key for a new chapter based on its act.

        Args:
            project: NovelProject instance
            act: Act instance (optional)

        Returns:
            Decimal order_key value
        """
        from decimal import Decimal
        from django.db.models import Max, Min, Q
        from .models import Chapter

        chapters = Chapter.objects.filter(project=project).order_by('order_key')

        if not act:
            # No act - append at end
            if chapters.exists():
                max_key = chapters.aggregate(Max('order_key'))['order_key__max']
                return (max_key or Decimal('0')) + Decimal('1')
            return Decimal('1')

        # Find chapters for this act and surrounding acts
        current_act_chapters = chapters.filter(act=act)
        next_act_chapters = chapters.filter(
            act__act_number__gt=act.act_number
        ).order_by('order_key')

        if current_act_chapters.exists():
            # Add after existing chapters in this act
            max_current = current_act_chapters.aggregate(Max('order_key'))['order_key__max']
        else:
            # No chapters for this act yet - find max from previous acts
            prev_act_chapters = chapters.filter(
                act__act_number__lt=act.act_number
            )
            if prev_act_chapters.exists():
                max_current = prev_act_chapters.aggregate(Max('order_key'))['order_key__max']
            else:
                max_current = Decimal('0')

        if next_act_chapters.exists():
            # Insert between current and next act
            min_next = next_act_chapters.first().order_key
            return (max_current + min_next) / Decimal('2')
        else:
            # Append after current act
            return max_current + Decimal('1')

    @staticmethod
    def reorder_chapters_by_act(project):
        """
        Reorder all chapters in a project, renumbering chapter_number based on order_key.

        This ensures chapter numbers reflect the actual display order (by act, then order_key).
        Uses two-pass renumbering to avoid unique constraint violations.

        Args:
            project: NovelProject instance
        """
        from .models import Chapter

        # Get all chapters ordered by order_key (which respects act ordering)
        chapters = Chapter.objects.filter(project=project).order_by('order_key')

        # Pass 1: Set all chapter_numbers to negative temporary values to avoid conflicts
        # This prevents unique constraint violations during renumbering
        for chapter in chapters:
            if chapter.chapter_number > 0:
                chapter.chapter_number = -chapter.chapter_number
                chapter.save(update_fields=['chapter_number'])

        # Pass 2: Set final sequential chapter numbers
        for index, chapter in enumerate(chapters, start=1):
            chapter.chapter_number = index
            chapter.save(update_fields=['chapter_number'])

        logger.info(f"Reordered {chapters.count()} chapters for project {project.id}")

    @staticmethod
    def write_chapter_from_act(project, act, writing_style='literary', language='English', target_word_count=3000, example_metadata=None, iteration=1, previous_scores=None):
        """
        Write a complete chapter directly from an Act.

        Args:
            project: NovelProject instance
            act: Act model instance
            writing_style: Writing style (literary, commercial, etc.)
            language: Target language
            target_word_count: Target word count
            example_metadata: Optional dict with 'category', 'genre', 'total_score', 'scores'
            iteration: Current iteration number (for iterative generation)
            previous_scores: Previous iteration scores (for gap analysis)

        Returns:
            Tuple of (chapter_data, token_usage)
        """
        from openai import OpenAI
        from django.conf import settings
        from .prompt_assembly import PromptAssemblyService
        from .models import Chapter

        logger.info(f"WritingService.write_chapter_from_act - project: {project.id}, act: {act.id}, "
                   f"iteration: {iteration}, target_words: {target_word_count}, has_example_metadata: {example_metadata is not None}")

        # Find the next chapter number for this project
        existing_chapters = Chapter.objects.filter(project=project).order_by('-chapter_number')
        next_chapter_number = 1
        if existing_chapters.exists():
            next_chapter_number = existing_chapters.first().chapter_number + 1

        # Build user prompt for act-based chapter
        user_prompt = f"Write Chapter {next_chapter_number} based on the following Act information:\n\n"
        user_prompt += f"**Act {act.act_number}: {act.subject}**\n"
        user_prompt += f"{act.description}\n\n"
        user_prompt += f"**Writing Requirements:**\n"
        user_prompt += f"- Target word count: {target_word_count} words\n"
        user_prompt += f"- Writing style: {writing_style}\n"
        user_prompt += f"- Language: {language}\n\n"

        # Add iteration-specific instructions if applicable
        if example_metadata and iteration > 1 and previous_scores:
            user_prompt += "**Quality Improvement Instructions:**\n"
            user_prompt += "This is an iterative improvement. Focus on addressing the following gaps:\n"
            for score in previous_scores:
                if score['score'] < score['target_score']:
                    gap = score['target_score'] - score['score']
                    user_prompt += f"- {score['category_name']}: Current score {score['score']:.1f}, "
                    user_prompt += f"target {score['target_score']:.1f} (gap: {gap:.1f})\n"
            user_prompt += "\n"

        user_prompt += "Please write a complete chapter that advances the story according to this act. "
        user_prompt += "Include vivid descriptions, character development, and engaging dialogue where appropriate.\n\n"

        # Request JSON format with title and content
        user_prompt += "**IMPORTANT: Format your response as JSON:**\n"
        user_prompt += "{\n"
        user_prompt += '  "title": "Your creative chapter title here",\n'
        user_prompt += '  "content": "The complete chapter text here..."\n'
        user_prompt += "}"

        # Assemble full prompt using 5-layer architecture
        # Pass act for context instead of chapter_outline
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='novelist',
            user_prompt=user_prompt,
            project=project,
            language_code='en',  # UI language, actual output language is in user_prompt
            context_type='chapter',
            include_context=True,
            act=act  # Pass act for context
        )

        logger.info(f"Built act-based chapter prompt with {len(messages)} messages")

        # Call OpenAI directly
        client = OpenAI(api_key=settings.NOVEL_AGENT['OPENAI_API_KEY'])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )

        # Extract token usage
        token_usage = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }

        # Extract content and title from JSON response
        raw_response = response.choices[0].message.content

        # Log the raw response for debugging
        logger.info(f"=======OpenAI raw RESPONSE (first 500 chars)=======: {raw_response}\n================================================================================")

        # Try to parse as JSON
        try:
            import json
            response_data = json.loads(raw_response)
            # Check if the parsed data is a dictionary (expected format)
            if isinstance(response_data, dict):
                content = response_data.get('content', raw_response)
                ai_title = response_data.get('title', None)
                logger.info(f"Successfully parsed JSON response - Title: '{ai_title}', Content length: {len(content)} chars")
            else:
                # Parsed JSON but not a dict
                logger.warning(f"JSON response is not a dictionary (got {type(response_data).__name__}), using raw content")
                content = raw_response
                ai_title = None
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback to treating entire response as content
            logger.warning(f"Failed to parse JSON response, using raw content: {str(e)}")
            content = raw_response
            ai_title = None

        # Count words
        word_count = len(content.split())

        # Use AI-generated title if available, otherwise use default
        title = ai_title if ai_title else f"Chapter {next_chapter_number}"

        # Calculate order_key based on act position
        order_key = WritingService.calculate_order_key_for_chapter(project, act)

        chapter_data = {
            'content': content,
            'word_count': word_count,
            'title': title,
            'chapter_number': next_chapter_number,
            'order_key': order_key
        }

        logger.info(f"WritingService generated chapter {chapter_data['chapter_number']} from Act {act.act_number}, "
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
        from openai import OpenAI
        from django.conf import settings
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
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='editor',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='chapter',
            include_context=True
        )

        logger.info(f"Built editing prompt with {len(messages)} messages")

        # Call OpenAI directly
        client = OpenAI(api_key=settings.NOVEL_AGENT['OPENAI_API_KEY'])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )

        result = response.choices[0].message.content.strip()
        logger.info(f"EditingService.edit_for_style - Successfully edited content, result_length: {len(result)}")
        return result

    @staticmethod
    def edit_for_grammar(project, content, user_language='en'):
        """Check and correct grammar using 5-layer prompt architecture.

        Returns:
            str: Grammar-corrected content
        """
        from openai import OpenAI
        from django.conf import settings
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
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='editor',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='chapter',
            include_context=False  # Grammar editing doesn't need full context
        )

        # Call OpenAI directly
        client = OpenAI(api_key=settings.NOVEL_AGENT['OPENAI_API_KEY'])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3  # Lower temperature for grammar
        )

        result = response.choices[0].message.content.strip()
        logger.info(f"EditingService.edit_for_grammar - Successfully corrected grammar, result_length: {len(result)}")
        return result

    @staticmethod
    def improve_dialogue(project, dialogue, character_names, user_language='en'):
        """Improve dialogue using 5-layer prompt architecture.

        Returns:
            str: Improved dialogue
        """
        from openai import OpenAI
        from django.conf import settings
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
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='editor',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='chapter',
            include_context=True  # Context helps maintain character voices
        )

        # Call OpenAI directly
        client = OpenAI(api_key=settings.NOVEL_AGENT['OPENAI_API_KEY'])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )

        result = response.choices[0].message.content.strip()
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
        from openai import OpenAI
        from django.conf import settings
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
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='consistency_checker',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='chapter',
            include_context=True  # Context helps identify inconsistencies
        )

        logger.info(f"Built consistency check prompt with {len(messages)} messages")

        # Call OpenAI directly
        client = OpenAI(api_key=settings.NOVEL_AGENT['OPENAI_API_KEY'])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3  # Lower temperature for analytical task
        )

        # Parse JSON response
        content = response.choices[0].message.content.strip()

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
            logger.error(f"Content was: {content}")
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
        from openai import OpenAI
        from django.conf import settings
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
                    user_prompt += f"Chapter {i}: {content}\n"
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
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='consistency_checker',
            user_prompt=user_prompt,
            project=project,
            language_code=user_language,
            context_type='chapter',
            include_context=True
        )

        # Call OpenAI directly
        client = OpenAI(api_key=settings.NOVEL_AGENT['OPENAI_API_KEY'])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3
        )

        # Parse JSON response
        content = response.choices[0].message.content.strip()

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
            logger.error(f"Content was: {content}")
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
            content_type: Type of content (plot, character, chapter, etc.)
            project: Optional NovelProject instance (for styles, techniques, target_language)

        Returns:
            dict: {
                'original_text': str,
                'modified_text': str,
                'user_prompt': str,
                'token_usage': dict
            }
        """
        from openai import OpenAI
        from django.conf import settings
        from .prompt_assembly import PromptAssemblyService

        logger.info(f"Modifying {content_type} text (length: {len(original_text)}) with prompt: {user_prompt[:100]}...")

        # Determine language code
        language_code = project.target_language if project else 'en'

        # Assemble prompts using 5-layer architecture
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='text_modifier',
            user_prompt=user_prompt,
            project=project,
            language_code=language_code,
            context_type=content_type,
            include_context=False  # Don't include full project context for quick edits
        )

        # Add original text to the last user message
        final_user_message = f"""**Original Text:**
{original_text}

{messages[-1]['content']}

**Instructions:** Provide ONLY the modified text (no explanations, no markers, no comments). Return the complete modified text that should replace the original."""

        # Replace the last message content with the final version
        messages[-1]['content'] = final_user_message

        # Call OpenAI directly
        try:
            client = OpenAI(api_key=settings.NOVEL_AGENT['OPENAI_API_KEY'])
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7
            )

            modified_text = response.choices[0].message.content.strip()

            # Extract token usage
            token_usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
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
