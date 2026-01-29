"""
Content Type Registry for Multi-Content-Type Support.

This module provides a centralized registry for different content types
(novels, poems, essays, sketches, articles) with their specific configurations.
"""


class ContentTypeConfig:
    """Configuration for a specific content type."""

    def __init__(self, content_type, display_name, agent_role,
                 has_structure, workflow_steps, scoring_categories):
        """
        Initialize content type configuration.

        Args:
            content_type: Internal type identifier (e.g., 'novel', 'poem')
            display_name: Human-readable name (e.g., 'Novel', 'Poem')
            agent_role: Key for the agent role to use (e.g., 'novelist', 'poet')
            has_structure: Boolean indicating if this type requires a structure template
            workflow_steps: List of workflow step identifiers
            scoring_categories: List of scoring category name_keys for this type
        """
        self.content_type = content_type
        self.display_name = display_name
        self.agent_role = agent_role
        self.has_structure = has_structure
        self.workflow_steps = workflow_steps
        self.scoring_categories = scoring_categories

    def __repr__(self):
        return f"<ContentTypeConfig: {self.content_type} ({self.display_name})>"


class ContentTypeRegistry:
    """Registry for all content type configurations."""

    _registry = {}

    @classmethod
    def register(cls, config):
        """
        Register a content type configuration.

        Args:
            config: ContentTypeConfig instance to register
        """
        if not isinstance(config, ContentTypeConfig):
            raise TypeError("config must be a ContentTypeConfig instance")
        cls._registry[config.content_type] = config

    @classmethod
    def get_config(cls, content_type):
        """
        Get configuration for a content type.

        Args:
            content_type: Type identifier (e.g., 'novel', 'poem')

        Returns:
            ContentTypeConfig instance or None if not found
        """
        return cls._registry.get(content_type)

    @classmethod
    def get_all_configs(cls):
        """
        Get all registered content type configurations.

        Returns:
            Dictionary of content_type -> ContentTypeConfig
        """
        return cls._registry.copy()

    @classmethod
    def get_all_types(cls):
        """
        Get list of all registered content type identifiers.

        Returns:
            List of content type strings
        """
        return list(cls._registry.keys())

    @classmethod
    def is_registered(cls, content_type):
        """
        Check if a content type is registered.

        Args:
            content_type: Type identifier to check

        Returns:
            Boolean indicating if type is registered
        """
        return content_type in cls._registry


# Register all content types

# Novel - Traditional multi-chapter novel
ContentTypeRegistry.register(ContentTypeConfig(
    content_type='novel',
    display_name='Novel',
    agent_role='novelist',
    has_structure=True,  # Has plot/acts/chapters structure
    workflow_steps=['idea', 'plot', 'characters', 'settings', 'chapters'],
    scoring_categories=[
        'story_plot',
        'character_development',
        'world_building',
        'writing_style',
        'dialogue',
        'emotional_impact'
    ]
))

# Poem - Single poem piece
ContentTypeRegistry.register(ContentTypeConfig(
    content_type='poem',
    display_name='Poem',
    agent_role='poet',
    has_structure=False,  # Free-form, no rigid structure
    workflow_steps=['idea', 'write', 'score'],
    scoring_categories=[
        'imagery_sensory',
        'rhythm_musicality',
        'form_structure',
        'emotional_impact_poem'
    ]
))

# Essay - Structured essay with arguments
ContentTypeRegistry.register(ContentTypeConfig(
    content_type='essay',
    display_name='Essay',
    agent_role='essayist',
    has_structure=True,  # Has template structure (e.g., 5-paragraph)
    workflow_steps=['idea', 'structure', 'write', 'score'],
    scoring_categories=[
        'thesis_clarity',
        'argument_strength',
        'evidence_quality',
        'organization_flow',
        'writing_style_essay'
    ]
))

# Sketch - Observational writing (Moment → Thought → Stop)
ContentTypeRegistry.register(ContentTypeConfig(
    content_type='sketch',
    display_name='Sketch',
    agent_role='sketch_writer',
    has_structure=True,  # Has Moment → Thought → Stop structure
    workflow_steps=['idea', 'structure', 'write', 'score'],
    scoring_categories=[
        'observation_quality',
        'imagery_description',
        'insight_reflection',
        'writing_style_sketch'
    ]
))

# News Article - Journalistic article
ContentTypeRegistry.register(ContentTypeConfig(
    content_type='article',
    display_name='News Article',
    agent_role='journalist',
    has_structure=True,  # Has inverted pyramid or standard news structure
    workflow_steps=['idea', 'structure', 'write', 'score'],
    scoring_categories=[
        # Will be defined in future when article scoring categories are created
        'writing_style'  # Placeholder - reuse existing category for now
    ]
))
