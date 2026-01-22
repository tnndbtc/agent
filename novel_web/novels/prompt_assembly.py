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

        # Layer 1: System Policies (in priority order)
        policies = SystemPolicy.objects.filter(is_active=True).order_by('priority')
        for policy in policies:
            trans = policy.translations.filter(language_code=language_code).first()

            # Fallback to English if translation not found
            if not trans and language_code != 'en':
                trans = policy.translations.filter(language_code='en').first()

            if trans:
                parts.append(trans.content)
                logger.debug(f"Added policy {policy.name_key} ({language_code})")

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
    def build_style_instructions(project, language_code='en', chapter_outline=None):
        """
        Build Layer 3: Style + Techniques instructions.

        Args:
            project: NovelProject instance
            language_code: Language code (e.g., 'en', 'zh-hans')
            chapter_outline: Optional ChapterOutline for style override

        Returns:
            str: Assembled style and technique instructions
        """
        parts = []

        # Get applicable style (chapter override > project default)
        style = None
        if chapter_outline and chapter_outline.style_override:
            style = chapter_outline.style_override
            logger.debug(f"Using chapter style override: {style.name_key}")
        elif project.default_style:
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
            context_type: Type of context ('plot', 'character', 'outline', 'chapter', 'brainstorm', 'text')
            **kwargs: Additional context parameters

        Returns:
            str: Assembled project context information
        """
        parts = []

        # Include plot context for story-related tasks
        if context_type in ['plot', 'brainstorm', 'outline', 'character', 'chapter']:
            if hasattr(project, 'plot'):
                # Removed premise - it was causing pollution in outline/chapter generation
                # Acts and themes provide better structured context
                parts.append(f"**Themes:** {project.plot.themes}")

                if project.plot.acts.exists():
                    # Check if we have a specific chapter_outline to determine relevant act
                    chapter_outline = kwargs.get('chapter_outline')
                    relevant_act = chapter_outline.act if chapter_outline and hasattr(chapter_outline, 'act') else None

                    if relevant_act and context_type == 'chapter':
                        # Include ONLY the relevant act in full detail
                        act_details = f"- Act {relevant_act.act_number} ({relevant_act.subject}, {relevant_act.percentage}%): {relevant_act.description}"
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
                        # Fallback: Include all acts (for outline generation, plot tasks, or unassigned chapters)
                        acts = "\n".join([
                            f"- Act {act.act_number} ({act.subject}, {act.percentage}%): {act.description}"
                            for act in project.plot.acts.all()
                        ])
                        parts.append(f"**Story Structure:**\n{acts}")

                logger.debug(f"Added plot context for {project.title}")

        # Include character context for character-related and chapter writing tasks
        if context_type in ['character', 'outline', 'chapter']:
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
        if context_type in ['outline', 'chapter']:
            primary_setting = project.settings.filter(is_primary=True).first()
            if primary_setting:
                parts.append(f"**Primary Setting:** {primary_setting.location} - {primary_setting.description[:200] if primary_setting.description else 'No description yet'}")
                logger.debug(f"Added primary setting: {primary_setting.location}")

        context_prompt = "\n\n".join(parts) if parts else ""
        logger.info(f"Built context prompt for {context_type}: {len(context_prompt)} chars")

        return context_prompt

    @staticmethod
    def assemble_full_prompt(agent_role_key, user_prompt, project=None,
                            language_code='en', context_type='text',
                            chapter_outline=None, include_context=True):
        """
        Assemble all 5 layers into final (system_message, user_message).

        Args:
            agent_role_key: Key for agent role (e.g., 'brainstormer', 'writer')
            user_prompt: User's task/request (Layer 5)
            project: Optional NovelProject instance
            language_code: Language code (e.g., 'en', 'zh-hans')
            context_type: Type of context for Layer 4
            chapter_outline: Optional ChapterOutline for style override
            include_context: Whether to include Layer 4 context

        Returns:
            tuple: (system_message, user_message)
        """
        logger.info(f"Assembling prompt for {agent_role_key}, language={language_code}, context_type={context_type}")

        # Layer 1 + 2: System prompt (policies + role)
        system_message = PromptAssemblyService.build_system_prompt(
            agent_role_key, language_code
        )

        user_parts = []

        # Layer 4: Context (if enabled and project provided)
        if include_context and project:
            context = PromptAssemblyService.build_context_prompt(project, context_type)
            if context:
                user_parts.append(f"## Project Context\n{context}")

        # Layer 3: Style and techniques (if project provided)
        if project:
            style = PromptAssemblyService.build_style_instructions(
                project, language_code, chapter_outline
            )
            if style:
                user_parts.append(style)

        # Layer 5: User prompt
        user_parts.append(f"## Task\n{user_prompt}")

        # Language output instruction (if not English)
        if language_code != 'en':
            lang_name = get_language_name(language_code)
            user_parts.append(f"\n**IMPORTANT:** Generate all output in {lang_name}.")

        user_message = "\n\n---\n\n".join(user_parts)

        logger.info(f"Final prompt: system={len(system_message)} chars, user={len(user_message)} chars")
        # Removed DEBUG logging of full prompt content to avoid duplication
        # The ai_client.py monkey-patch already logs all OpenAI API calls

        return system_message, user_message
