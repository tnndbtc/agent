"""
Prompt Assembly Service for 5-Layer Prompt Architecture.

This service assembles prompts from five distinct layers:
1. System Policy (Immutable Rules)
2. Role Definition (Agent Identity)
3. Style & Technique Library (Composable)
4. Project Memory (Long-Term Context)
5. User Prompt (Short-Lived)
"""
import logging
from django.db.models import Q

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


class PromptAssemblyService:
    """Service for assembling prompts from 5-layer architecture."""

    @staticmethod
    def build_system_prompt(agent_role_key, language_code='en'):
        """
        Build Layer 1 + Layer 2: System policies + Agent role.

        Args:
            agent_role_key: Key for agent role (e.g., 'brainstormer', 'writer')
            language_code: Language code (e.g., 'en', 'zh-hans')

        Returns:
            str: Assembled system prompt with policies and role definition
        """
        from .models import SystemPolicy, AgentRole

        parts = []

        # Layer 1: System Policy (consolidated)
        system_policy = SystemPolicy.objects.filter(name_key='system_policy', is_active=True).first()
        if system_policy:
            trans = system_policy.translations.filter(language_code=language_code).first()

            # Fallback to English if translation not found
            if not trans and language_code != 'en':
                trans = system_policy.translations.filter(language_code='en').first()

            if trans:
                parts.append(trans.content)
                logger.debug(f"Added consolidated system policy ({language_code})")
        else:
            logger.warning("Consolidated system policy not found")

        # Layer 2: Agent Role
        role = AgentRole.objects.filter(name_key=agent_role_key, is_active=True).first()
        if role:
            trans = role.translations.filter(language_code=language_code).first()

            # Fallback to English if translation not found
            if not trans and language_code != 'en':
                trans = role.translations.filter(language_code='en').first()

            if trans:
                parts.append(trans.system_prompt)
                logger.debug(f"Added role {role.name_key} ({language_code})")
        else:
            logger.warning(f"Agent role '{agent_role_key}' not found")

        system_prompt = "\n\n---\n\n".join(parts) if parts else ""
        logger.info(f"Built system prompt for {agent_role_key} ({language_code}): {len(system_prompt)} chars")

        return system_prompt

    @staticmethod
    def build_style_instructions(project, language_code='en'):
        """
        Build Layer 3: Style + Techniques instructions.

        Args:
            project: NovelProject instance
            language_code: Language code (e.g., 'en', 'zh-hans')

        Returns:
            str: Assembled style and technique instructions
        """
        parts = []

        # Get project default style
        style = None
        if project.default_style:
            style = project.default_style
            logger.debug(f"Using project default style: {style.name_key}")

        if style:
            trans = style.translations.filter(language_code=language_code).first()

            # Fallback to English if translation not found
            if not trans and language_code != 'en':
                trans = style.translations.filter(language_code='en').first()

            if trans:
                parts.append(f"## Writing Style: {trans.name}")
                parts.append(trans.instructions)
                logger.debug(f"Added style {style.name_key} ({language_code})")

        # Get techniques
        for technique in project.selected_techniques.all():
            trans = technique.translations.filter(language_code=language_code).first()

            # Fallback to English if translation not found
            if not trans and language_code != 'en':
                trans = technique.translations.filter(language_code='en').first()

            if trans:
                parts.append(f"## Technique: {trans.name}")
                parts.append(trans.instructions)
                logger.debug(f"Added technique {technique.name_key} ({language_code})")

        style_instructions = "\n\n".join(parts) if parts else ""
        logger.info(f"Built style instructions for project {project.title}: {len(style_instructions)} chars")

        return style_instructions

    @staticmethod
    def build_context_prompt(project, context_type, **kwargs):
        """
        Build Layer 4: Project memory context.

        Args:
            project: NovelProject instance
            context_type: Type of context ('plot', 'character', 'chapter', 'brainstorm', 'text', 'poem', 'essay', 'sketch', 'article')
            **kwargs: Additional context parameters

        Returns:
            str: Assembled project context information
        """
        parts = []

        # Include plot context for story-related tasks
        if context_type in ['plot', 'brainstorm', 'character', 'chapter']:
            if hasattr(project, 'plot'):
                # Removed premise - it was causing pollution in chapter generation
                # Removed themes field in migration 0023
                # Acts provide better structured context

                if project.plot.acts.exists():
                    # Check if we have a specific act to determine relevant act
                    direct_act = kwargs.get('act')  # Direct act for chapter creation
                    relevant_act = direct_act

                    if relevant_act and context_type == 'chapter':
                        # Include ONLY the relevant act in full detail
                        act_details = f"- Act {relevant_act.act_number} ({relevant_act.subject}): {relevant_act.description}"
                        parts.append(f"**Current Act (for this chapter):**\n{act_details}")

                        # Include brief context about other acts (first 100 chars of description)
                        other_acts = project.plot.acts.exclude(id=relevant_act.id).order_by('act_number')
                        if other_acts.exists():
                            other_acts_summary = "\n".join([
                                f"- Act {act.act_number} ({act.subject}): {act.description[:100]}..."
                                for act in other_acts
                            ])
                            parts.append(f"**Overall Story Structure (for context):**\n{other_acts_summary}")
                    else:
                        # Fallback: Include all acts (for plot tasks or unassigned chapters)
                        acts = "\n".join([
                            f"- Act {act.act_number} ({act.subject}): {act.description}"
                            for act in project.plot.acts.all()
                        ])
                        parts.append(f"**Story Structure:**\n{acts}")

                logger.debug(f"Added plot context for {project.title}")

        # Include character context for character-related and chapter writing tasks
        if context_type in ['character', 'chapter']:
            chars = project.characters.filter(
                role__in=['protagonist', 'antagonist', 'mentor']
            )[:3]  # Limit to top 3 key characters

            if chars:
                char_info = "\n".join([
                    f"- {c.name} ({c.role}): {c.background[:200] if c.background else 'No background yet'}"
                    for c in chars
                ])
                parts.append(f"**Key Characters:**\n{char_info}")
                logger.debug(f"Added {len(chars)} characters to context")

        # Include setting context for world-building tasks
        if context_type in ['chapter']:
            primary_setting = project.settings.filter(is_primary=True).first()
            if primary_setting:
                parts.append(f"**Primary Setting:** {primary_setting.location} - {primary_setting.description[:200] if primary_setting.description else 'No description yet'}")
                logger.debug(f"Added primary setting: {primary_setting.location}")

        # Context for new content types
        if project and hasattr(project, 'content_type'):
            if project.content_type == 'poem' and context_type == 'poem':
                # Minimal context for poems - let creativity flow
                parts.append(f"**Theme:** {project.title}")
                logger.debug(f"Added poem context for {project.title}")

            elif project.content_type == 'essay' and context_type == 'essay':
                # Include essay structure template if available
                if hasattr(project, 'content_piece') and project.content_piece and project.content_piece.structure_template:
                    template = project.content_piece.structure_template
                    sections = template.structure_data.get('sections', [])
                    parts.append(f"**Essay Structure:** {template.name}")
                    parts.append(f"**Sections:** {', '.join(sections)}")
                    logger.debug(f"Added essay structure: {template.name}")

            elif project.content_type == 'sketch' and context_type == 'sketch':
                # Sketch format context
                parts.append("**Sketch Format:** Moment → Thought → Stop")
                parts.append("**Structure:**\n- Moment: Capture a specific observation with vivid detail\n- Thought: Reflect on its meaning or significance\n- Stop: End abruptly with a lasting impression")
                logger.debug(f"Added sketch format context")

            elif project.content_type == 'article' and context_type == 'article':
                # Article structure context
                parts.append("**Article Structure:** Inverted Pyramid")
                parts.append("**Format:**\n- Lead: Most important information (5W1H)\n- Body: Supporting details in order of importance\n- Background: Context and additional information")
                logger.debug(f"Added article structure context")

        context_prompt = "\n\n".join(parts) if parts else ""
        logger.info(f"Built context prompt for {context_type}: {len(context_prompt)} chars")

        return context_prompt

    @staticmethod
    def assemble_full_prompt(agent_role_key, user_prompt, project=None,
                            language_code='en', context_type='text',
                            act=None, include_context=True):
        """
        Assemble all 5 layers into OpenAI API message format.

        Args:
            agent_role_key: Key for agent role (e.g., 'brainstormer', 'writer')
            user_prompt: User's task/request (Layer 5)
            project: Optional NovelProject instance
            language_code: Language code (e.g., 'en', 'zh-hans')
            context_type: Type of context for Layer 4
            act: Optional Act for chapter creation
            include_context: Whether to include Layer 4 context

        Returns:
            list: List of message dicts for OpenAI API with 5-layer structure:
                  Layer 1 (System Policy) -> role="system"
                  Layer 2 (Role Definition) -> role="system"
                  Layer 3 (Writing Style) -> role="developer"
                  Layer 4 (Project Context) -> role="developer"
                  Layer 5 (User Task) -> role="user"
        """
        logger.info(f"Assembling prompt for {agent_role_key}, language={language_code}, context_type={context_type}")

        # Extract individual layer contents
        # Layer 1 + 2: System policies + role definition
        system_prompt_combined = PromptAssemblyService.build_system_prompt(
            agent_role_key, language_code
        )

        # Separate Layer 1 (System Policy) and Layer 2 (Role Definition)
        # Split on the separator if present
        if "\n\n---\n\n" in system_prompt_combined:
            parts = system_prompt_combined.split("\n\n---\n\n")
            system_policy = parts[0] if len(parts) > 0 else ""
            role_definition = parts[1] if len(parts) > 1 else ""
        else:
            system_policy = system_prompt_combined
            role_definition = ""

        # Layer 3: Style and techniques
        style_instructions = ""
        if project:
            style_instructions = PromptAssemblyService.build_style_instructions(
                project, language_code
            )

        # Layer 4: Project context (memory)
        project_context = ""
        if include_context and project:
            project_context = PromptAssemblyService.build_context_prompt(
                project, context_type, act=act
            )

        # Layer 5: User task
        user_task = user_prompt

        # Add language instruction to user task if not English
        if language_code != 'en':
            lang_name = get_language_name(language_code)
            user_task = f"{user_task}\n\n**IMPORTANT:** Generate all output in {lang_name}."

        # Build messages with 5-layer structure
        messages = []

        # Layer 1: System Policy (system role)
        if system_policy:
            messages.append({"role": "system", "content": system_policy})

        # Layer 2: Role Definition (developer role)
        if role_definition:
            messages.append({"role": "developer", "content": role_definition})

        # Layer 3: Writing Style (developer role)
        if style_instructions:
            messages.append({"role": "developer", "content": style_instructions})

        # Layer 4: Project Context/Memory (developer role)
        if project_context:
            messages.append({"role": "developer", "content": f"## Project Context\n{project_context}"})

        # Layer 5: User Task (user role)
        messages.append({"role": "user", "content": f"## Task\n{user_task}"})

        logger.info(f"Built prompt with {len(messages)} messages")
        return messages
