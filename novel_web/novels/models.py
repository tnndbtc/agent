"""Database models for Novel Writing Agent."""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import get_language, gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from .utils import calculate_word_count


class UserProfile(models.Model):
    """User profile for tracking token usage and other user-specific data."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    prompt_tokens = models.BigIntegerField(default=0, help_text="Total prompt tokens consumed by this user")
    completion_tokens = models.BigIntegerField(default=0, help_text="Total completion tokens consumed by this user")
    total_tokens = models.BigIntegerField(default=0, help_text="Total tokens consumed by this user")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        return f"{self.user.username}'s profile"

    def add_tokens(self, prompt_tokens=0, completion_tokens=0, total_tokens=0):
        """Add token usage to user's totals."""
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += total_tokens
        self.save()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create UserProfile when a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class UserPrompt(models.Model):
    """User-saved prompts for AI text modification."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_prompts')
    name = models.CharField(max_length=100, help_text="User-friendly name for this prompt")
    prompt_text = models.TextField(help_text="The actual prompt text")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    usage_count = models.IntegerField(default=0, help_text="Number of times this prompt has been used")

    class Meta:
        ordering = ['-usage_count', '-updated_at']
        indexes = [
            models.Index(fields=['user', '-usage_count']),
        ]

    def __str__(self):
        return f"{self.name} by {self.user.username}"

    def increment_usage(self):
        """Increment usage count when prompt is used."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class SystemPolicy(models.Model):
    """System-wide immutable policies for AI behavior."""

    POLICY_TYPE_CHOICES = [
        ('safety', 'Safety'),
        ('copyright', 'Copyright'),
        ('output', 'Output Constraints'),
        ('behavior', 'Behavior Boundaries'),
    ]

    name_key = models.CharField(max_length=50, unique=True, help_text="Unique identifier for this policy")
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPE_CHOICES)
    is_active = models.BooleanField(default=True, help_text="Whether this policy is enforced")
    priority = models.IntegerField(default=0, help_text="Lower number = higher priority")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority', 'name_key']
        verbose_name_plural = "System policies"
        indexes = [
            models.Index(fields=['is_active', 'priority']),
        ]

    def __str__(self):
        return f"{self.name_key} ({self.policy_type})"


class SystemPolicyTranslation(models.Model):
    """Translations for system policies."""

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('zh-hans', 'Simplified Chinese'),
    ]

    policy = models.ForeignKey(SystemPolicy, on_delete=models.CASCADE, related_name='translations')
    language_code = models.CharField(max_length=10, choices=LANGUAGE_CHOICES)
    content = models.TextField(help_text="Policy text in this language")

    class Meta:
        unique_together = [['policy', 'language_code']]
        indexes = [
            models.Index(fields=['language_code']),
        ]

    def __str__(self):
        return f"{self.policy.name_key} - {self.language_code}"


class AgentRole(models.Model):
    """AI agent role definitions for different modules."""

    name_key = models.CharField(max_length=50, unique=True, help_text="Unique identifier for this role")
    module_name = models.CharField(max_length=100, help_text="Associated module name")
    is_system = models.BooleanField(default=False, help_text="Whether this is a system-defined role")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='custom_agent_roles',
        null=True,
        blank=True,
        help_text="User who created this custom role (null for system roles)"
    )
    is_active = models.BooleanField(default=True, help_text="Whether this role is available")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name_key']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['is_system', 'created_by']),
        ]

    def __str__(self):
        return f"{self.name_key} ({self.module_name})"


class AgentRoleTranslation(models.Model):
    """Translations for agent role system prompts."""

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('zh-hans', 'Simplified Chinese'),
    ]

    role = models.ForeignKey(AgentRole, on_delete=models.CASCADE, related_name='translations')
    language_code = models.CharField(max_length=10, choices=LANGUAGE_CHOICES)
    system_prompt = models.TextField(help_text="Role definition/system prompt in this language")

    class Meta:
        unique_together = [['role', 'language_code']]
        indexes = [
            models.Index(fields=['language_code']),
        ]

    def __str__(self):
        return f"{self.role.name_key} - {self.language_code}"


class WritingStyle(models.Model):
    """Reusable writing styles (genre-specific or user-created)."""

    PACING_CHOICES = [
        ('slow', 'Slow'),
        ('medium', 'Medium'),
        ('fast', 'Fast'),
    ]

    PARAGRAPH_LENGTH_CHOICES = [
        ('short', 'Short'),
        ('medium', 'Medium'),
        ('long', 'Long'),
    ]

    DIALOGUE_RATIO_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    name_key = models.CharField(max_length=50, help_text="Unique identifier for this style")
    is_system = models.BooleanField(default=False, help_text="True for predefined system styles")
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='writing_styles',
        help_text="User who created this style (NULL for system styles)"
    )
    public = models.BooleanField(default=False, help_text="Whether this style is publicly available")
    content_type = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Content type this style is designed for (blank for generic styles)"
    )

    # Style parameters
    pacing = models.CharField(max_length=20, choices=PACING_CHOICES, default='medium')
    tone = models.CharField(max_length=100, blank=True)
    paragraph_length = models.CharField(max_length=20, choices=PARAGRAPH_LENGTH_CHOICES, default='medium')
    dialogue_ratio = models.CharField(max_length=20, choices=DIALOGUE_RATIO_CHOICES, default='medium')
    cliffhanger_enabled = models.BooleanField(default=False)
    target_locale = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Target language for content generation (e.g., 'en', 'zh-hans', 'ja'). "
                  "When set, overrides user's UI language preference for content generation."
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_system', 'name_key']
        indexes = [
            models.Index(fields=['is_system', 'public']),
            models.Index(fields=['created_by']),
            models.Index(fields=['content_type']),
        ]
        unique_together = [['name_key', 'created_by']]

    def __str__(self):
        if self.is_system:
            return f"{self.name_key} (System)"
        return f"{self.name_key} by {self.created_by.username if self.created_by else 'Unknown'}"

    def is_accessible_by(self, user):
        """Check if style is accessible by given user."""
        if self.is_system or self.public:
            return True
        if self.created_by_id and self.created_by_id == user.id:
            return True
        return False


class WritingStyleTranslation(models.Model):
    """Translations for writing style names and instructions."""

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('zh-hans', 'Simplified Chinese'),
    ]

    style = models.ForeignKey(WritingStyle, on_delete=models.CASCADE, related_name='translations')
    language_code = models.CharField(max_length=10, choices=LANGUAGE_CHOICES)
    name = models.CharField(max_length=100, help_text="Display name in this language")
    description = models.TextField(blank=True, help_text="Style description")
    instructions = models.TextField(help_text="Style-specific prompt instructions")

    class Meta:
        unique_together = [['style', 'language_code']]
        indexes = [
            models.Index(fields=['language_code']),
        ]

    def __str__(self):
        return f"{self.style.name_key} - {self.language_code}: {self.name}"


class CustomWritingStyle(models.Model):
    """User-created custom writing styles from sample text analysis (simplified)."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='custom_writing_styles',
        help_text="User who created this custom style"
    )
    created_at = models.BigIntegerField(
        help_text="Creation time in UNIX timestamp"
    )
    language_code = models.CharField(
        max_length=10,
        help_text="Detected language code (e.g., 'en', 'zh-hans', 'ja')"
    )
    style_name = models.CharField(
        max_length=200,
        help_text="AI-generated style name"
    )
    style_instruction = models.TextField(
        help_text="AI-generated writing style instructions/prompt"
    )
    sample = models.TextField(
        help_text="First 100 words of user's sample text"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
        verbose_name = "Custom Writing Style"
        verbose_name_plural = "Custom Writing Styles"

    def __str__(self):
        return f"{self.style_name} ({self.language_code}) by {self.user.username}"


class CustomAgentRole(models.Model):
    """User-created custom agent roles linked to custom writing styles."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_custom_agent_roles',
        help_text="User who created this custom agent role"
    )
    created_at = models.BigIntegerField(
        help_text="Creation time in UNIX timestamp"
    )
    language_code = models.CharField(
        max_length=10,
        help_text="Language code (e.g., 'en', 'zh-hans', 'ja')"
    )
    role_name = models.CharField(
        max_length=200,
        help_text="AI-generated agent role name"
    )
    role_instruction = models.TextField(
        help_text="AI-generated agent role instructions/prompt"
    )
    custom_style = models.OneToOneField(
        'CustomWritingStyle',
        on_delete=models.CASCADE,
        related_name='custom_agent_role',
        help_text="Associated custom writing style"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
        verbose_name = "Custom Agent Role"
        verbose_name_plural = "Custom Agent Roles"

    def __str__(self):
        return f"{self.role_name} ({self.language_code}) by {self.user.username}"


class InstructionTemplate(models.Model):
    """Translatable instruction templates for user task prompts (Layer 5)."""

    name_key = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique identifier for this template (e.g., 'poem_instructions')"
    )
    content_type = models.CharField(
        max_length=20,
        help_text="Content type this template is for (poem, essay, sketch, article)"
    )
    is_active = models.BooleanField(default=True, help_text="Whether this template is active")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['content_type', 'name_key']
        indexes = [
            models.Index(fields=['content_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name_key} ({self.content_type})"

    def get_json_format(self, language_code='en'):
        """
        Get JSON format instruction for this template in specified language.

        Args:
            language_code: Language code (e.g., 'en', 'zh-hans')

        Returns:
            String with JSON format instruction, or None if not found
        """
        translation = self.translations.filter(language_code=language_code).first()
        if not translation and language_code != 'en':
            # Fallback to English if requested language not found
            translation = self.translations.filter(language_code='en').first()
        return translation.json_format if translation else None


class InstructionTemplateTranslation(models.Model):
    """Translations for instruction templates."""

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('zh-hans', 'Simplified Chinese'),
    ]

    template = models.ForeignKey(
        InstructionTemplate,
        on_delete=models.CASCADE,
        related_name='translations'
    )
    language_code = models.CharField(max_length=10, choices=LANGUAGE_CHOICES)
    task_description = models.TextField(
        help_text="Main task description (e.g., 'Write a complete poem based on this theme: {theme}')"
    )
    instructions = models.TextField(
        help_text="Bulleted instructions for the task"
    )
    json_format = models.TextField(
        help_text="JSON format specification with example structure"
    )

    class Meta:
        unique_together = [['template', 'language_code']]
        indexes = [
            models.Index(fields=['language_code']),
        ]

    def __str__(self):
        return f"{self.template.name_key} - {self.language_code}"




class ScoreCategory(models.Model):
    """Score category - can be system-defined or user-created."""

    id = models.AutoField(primary_key=True)

    # Core fields
    name = models.CharField(max_length=100, help_text="Category name (can be any language)")
    public = models.BooleanField(default=False, db_index=True, help_text="Whether this category is publicly available")

    # User association (NULL for system categories)
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='score_categories',
        help_text="User who created this category (NULL for system categories)"
    )

    # Optional metadata
    default_weight = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Default weight percentage for this category"
    )
    order = models.IntegerField(default=0, help_text="Display order for system categories")

    # System category marker (for translation support)
    is_system = models.BooleanField(default=False, db_index=True, help_text="True for system-defined categories")
    name_key = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        help_text="Translation key for system categories (e.g., 'story_plot')"
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_system', 'order', 'name']
        indexes = [
            models.Index(fields=['public', 'created_by']),
            models.Index(fields=['is_system']),
        ]
        verbose_name_plural = "Score categories"

    def __str__(self):
        """Return translated name for system categories, raw name for user categories."""
        if self.is_system:
            current_lang = get_language() or 'en'
            # Use prefetched translations if available to avoid N+1 queries
            if hasattr(self, '_prefetched_objects_cache') and 'translations' in self._prefetched_objects_cache:
                translations = self._prefetched_objects_cache['translations']
                translation = next((t for t in translations if t.language_code == current_lang), None)
            else:
                translation = self.translations.filter(language_code=current_lang).first()
            return translation.name if translation else self.name
        return self.name

    def is_accessible_by(self, user):
        """Check if category is accessible by given user."""
        if self.public:
            return True
        if self.created_by_id and self.created_by_id == user.id:
            return True
        return False


class ScoreCategoryTranslation(models.Model):
    """Translations for system-defined score categories."""

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('zh-hans', 'Simplified Chinese'),
    ]

    category = models.ForeignKey(
        ScoreCategory,
        related_name='translations',
        on_delete=models.CASCADE,
        limit_choices_to={'is_system': True}
    )
    language_code = models.CharField(max_length=10, choices=LANGUAGE_CHOICES)
    name = models.CharField(max_length=100, help_text="Translated category name")

    class Meta:
        unique_together = [['category', 'language_code']]
        indexes = [
            models.Index(fields=['language_code']),
        ]

    def __str__(self):
        return f"{self.category.name_key} - {self.language_code}: {self.name}"


class NovelProject(models.Model):
    """Main project model for a novel."""

    CONTENT_TYPE_CHOICES = [
        ('novel', 'Novel'),
        ('poem', 'Poem'),
        ('essay', 'Essay'),
        ('sketch', 'Sketch'),
        ('article', 'News Article'),
        ('other', 'Other - User Specified'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('outlining', 'Outlining'),
        ('writing', 'Writing'),
        ('editing', 'Editing'),
        ('completed', 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='novel_projects')
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='novel',
        help_text="Type of content this project will produce"
    )

    # ChromaDB collection name (unique per project)
    chroma_collection_name = models.CharField(max_length=255, unique=True, editable=False)

    # Prompt architecture settings
    default_style = models.ForeignKey(
        'WritingStyle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects_using',
        help_text="Default writing style for this project"
    )
    target_language = models.CharField(
        max_length=10,
        default='en',
        choices=[('en', 'English'), ('zh-hans', 'Simplified Chinese')],
        help_text="Target output language for AI generation"
    )

    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    total_word_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-updated_at']
        unique_together = [['user', 'title']]
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]

    def __str__(self):
        return f"{self.title} by {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.chroma_collection_name:
            self.chroma_collection_name = f"project_{self.id.hex[:16]}"
        super().save(*args, **kwargs)


class Idea(models.Model):
    """Stores the original user idea for any content type."""

    project = models.OneToOneField(
        'NovelProject',
        on_delete=models.CASCADE,
        related_name='idea',
        help_text="The project this idea belongs to"
    )
    idea_data = models.JSONField(
        default=dict,
        help_text="Original idea data (premise, theme, thesis, etc.)"
    )
    content_type = models.CharField(
        max_length=20,
        help_text="Type of content (novel, poem, essay, sketch, article)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Idea for {self.project.title} ({self.content_type})"


class Plot(models.Model):
    """Plot structure for a novel."""

    project = models.OneToOneField(NovelProject, on_delete=models.CASCADE, related_name='plot')

    # Basic plot elements
    # themes field removed in migration 0023
    conflict = models.TextField(blank=True, help_text="Central conflict")

    # Story structure
    structure = models.TextField(blank=True, help_text="Three-act structure details")
    arc = models.TextField(blank=True, help_text="Story arc overview")

    # Additional elements
    tone = models.CharField(max_length=100, blank=True)
    target_audience = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Plot for {self.project.title}"

    @property
    def structure_without_title(self):
        """Return plot structure with the title line removed."""
        if not self.structure:
            return ''

        lines = self.structure.split('\n')
        # Remove first line if it starts with "**Title:"
        if lines and lines[0].strip().startswith('**Title:'):
            # Also remove the following empty line if present
            if len(lines) > 1 and lines[1].strip() == '':
                return '\n'.join(lines[2:])
            return '\n'.join(lines[1:])
        return self.structure


class Act(models.Model):
    """A three-act structure component of a plot."""

    SUBJECT_CHOICES = [
        ('SETUP', 'Setup'),
        ('CONFRONTATION', 'Confrontation'),
        ('RESOLUTION', 'Resolution'),
    ]

    id = models.AutoField(primary_key=True)
    plot = models.ForeignKey('Plot', on_delete=models.CASCADE, related_name='acts')

    act_number = models.IntegerField(
        help_text="Act number (1, 2, or 3)"
    )
    subject = models.CharField(
        max_length=50,
        choices=SUBJECT_CHOICES,
        help_text="Act type (SETUP, CONFRONTATION, RESOLUTION)"
    )
    # percentage field removed in migration 0023
    description = models.TextField(
        help_text="Detailed description of what happens in this act"
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['act_number']
        unique_together = [['plot', 'act_number']]
        indexes = [
            models.Index(fields=['plot', 'act_number']),
        ]

    def __str__(self):
        return f"Act {self.act_number}: {self.subject}"


class Character(models.Model):
    """Character in a novel."""

    ROLE_CHOICES = [
        ('protagonist', 'Protagonist'),
        ('antagonist', 'Antagonist'),
        ('mentor', 'Mentor'),
        ('sidekick', 'Sidekick'),
        ('love_interest', 'Love Interest'),
        ('supporting', 'Supporting'),
        ('minor', 'Minor'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(NovelProject, on_delete=models.CASCADE, related_name='characters')

    name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    age = models.CharField(max_length=50, blank=True)

    # Character details
    background = models.TextField(blank=True)
    personality = models.TextField(blank=True)
    motivation = models.TextField(blank=True)
    flaw = models.TextField(blank=True)
    arc = models.TextField(blank=True, help_text="Character development arc")
    appearance = models.TextField(blank=True)
    relationships = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['role', 'name']
        indexes = [
            models.Index(fields=['project', 'role']),
        ]

    def __str__(self):
        return f"{self.name} ({self.role}) - {self.project.title}"


class Setting(models.Model):
    """World-building and setting information."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(NovelProject, on_delete=models.CASCADE, related_name='settings')

    location = models.CharField(max_length=255)
    is_primary = models.BooleanField(default=False)
    time_period = models.CharField(max_length=255, blank=True)

    # Setting details
    description = models.TextField(blank=True)
    culture = models.TextField(blank=True)
    technology = models.TextField(blank=True)
    politics = models.TextField(blank=True)
    economy = models.TextField(blank=True)
    important_locations = models.TextField(blank=True)
    atmosphere = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_primary', 'location']

    def __str__(self):
        return f"{self.location} - {self.project.title}"


class Chapter(models.Model):
    """Written chapter content."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(NovelProject, on_delete=models.CASCADE, related_name='chapters')
    act = models.ForeignKey(
        'Act',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_chapters',
        help_text="Direct association with act for chapter creation"
    )

    chapter_number = models.IntegerField()
    order_key = models.DecimalField(max_digits=10, decimal_places=6, default=1, help_text="Ordering key for flexible chapter reordering")
    title = models.CharField(max_length=255)
    content = models.TextField(help_text="Full chapter content")
    summary = models.TextField(blank=True)

    word_count = models.IntegerField(default=0)
    language = models.CharField(max_length=50, default='English')
    writing_style = models.CharField(max_length=50, default='literary')

    # Writing style override (new prompt architecture)
    style_override = models.ForeignKey(
        'WritingStyle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chapters_using',
        help_text="Override writing style for this chapter (uses project default if not set)"
    )

    # Versioning
    version = models.IntegerField(default=1)
    is_draft = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order_key']
        unique_together = ['project', 'chapter_number', 'version']
        indexes = [
            models.Index(fields=['project', 'chapter_number']),
            models.Index(fields=['project', 'order_key']),
        ]

    def __str__(self):
        return f"Chapter {self.chapter_number}: {self.title} - {self.project.title}"

    def save(self, *args, **kwargs):
        # Auto-assign order_key if not provided
        if self.order_key is None:
            from decimal import Decimal
            from django.db.models import Max
            max_order_key = Chapter.objects.filter(
                project=self.project
            ).aggregate(max_key=Max('order_key'))['max_key']
            self.order_key = (max_order_key or Decimal('0')) + Decimal('1')

        # Update word count
        if self.content:
            self.word_count = calculate_word_count(self.content)
        super().save(*args, **kwargs)

        # Update project total word count
        self.project.total_word_count = sum(
            ch.word_count for ch in self.project.chapters.all()
        )
        self.project.save(update_fields=['total_word_count'])


class ExampleScore(models.Model):
    """Individual category score for an example."""

    id = models.AutoField(primary_key=True)
    example = models.ForeignKey('Example', related_name='scores', on_delete=models.CASCADE)
    category = models.ForeignKey(ScoreCategory, on_delete=models.CASCADE)

    weight = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Weight percentage for this category (0-100)"
    )
    score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Score for this category (0-10)"
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category__order', 'id']
        unique_together = [['example', 'category']]

    @property
    def weighted_score(self):
        """Calculate weighted score (score * weight/100)."""
        return float(self.score) * (self.weight / 100)

    @property
    def category_name(self):
        """Return category name (localized if system, raw if user-created)."""
        return str(self.category)

    def __str__(self):
        return f"{self.category_name}: {self.score}/10 ({self.weight}%)"


class Example(models.Model):
    """Good or bad writing examples."""

    CATEGORY_CHOICES = [
        ('opening', 'Opening'),
        ('dialogue', 'Dialogue'),
        ('description', 'Description'),
        ('action', 'Action'),
        ('transition', 'Transition'),
        ('ending', 'Ending'),
    ]

    LOCALE_CHOICES = [
        ('English', 'English'),
        ('Chinese', 'Chinese'),
        ('French', 'French'),
        ('Spanish', 'Spanish'),
        ('German', 'German'),
        ('Japanese', 'Japanese'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='examples')

    # Visibility
    public = models.BooleanField(default=False, db_index=True, help_text="Whether this example is publicly available")

    # Basic information
    title = models.CharField(max_length=200, blank=True, help_text="Short one-line summary of the example")
    locale = models.CharField(max_length=50, choices=LOCALE_CHOICES, default='English', help_text="Language of the content")
    is_good = models.BooleanField(help_text="True for good example, False for bad")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True, null=True)
    content = models.TextField()
    description = models.TextField(help_text="Why this is a good/bad example", blank=True)

    # For bad examples
    issues = models.JSONField(default=list, blank=True, help_text="List of issues")

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_good', 'category']),
            models.Index(fields=['public', 'user']),
        ]

    @property
    def total_score(self):
        """Calculate weighted total score from all category scores."""
        # Use prefetched scores if available to avoid N+1 queries
        if hasattr(self, '_prefetched_objects_cache') and 'scores' in self._prefetched_objects_cache:
            scores = self._prefetched_objects_cache['scores']
        else:
            scores = self.scores.all()
        return sum(score.weighted_score for score in scores)

    def __str__(self):
        quality = "Good" if self.is_good else "Bad"
        return f"{quality} {self.category} example"


class GenerationTask(models.Model):
    """Track async AI generation tasks."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    TASK_TYPE_CHOICES = [
        ('brainstorm', 'Brainstorm'),
        ('plot', 'Plot Generation'),
        ('character', 'Character Creation'),
        ('chapter', 'Chapter Writing'),
        ('edit', 'Editing'),
        ('score', 'Scoring'),
        ('example_scoring', 'Example Scoring'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(NovelProject, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Celery task ID
    celery_task_id = models.CharField(max_length=255, blank=True)

    # Progress tracking
    progress = models.IntegerField(default=0, help_text="Progress percentage 0-100")
    progress_message = models.CharField(max_length=255, blank=True)

    # Input/output data
    input_data = models.JSONField(default=dict)
    result_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', '-created_at']),
            models.Index(fields=['celery_task_id']),
        ]

    def __str__(self):
        return f"{self.task_type} task for {self.project.title} - {self.status}"


class APIPerformanceMetric(models.Model):
    """Track API call performance for duration estimation."""

    API_TYPE_CHOICES = [
        ('brainstorm', 'Idea Generation'),
        ('plot', 'Plot and Characters Generation'),
        ('chapter', 'Chapter Generation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    api_type = models.CharField(max_length=20, choices=API_TYPE_CHOICES, db_index=True)
    duration_seconds = models.FloatField(help_text="How long the API call took in seconds")

    # Optional: Store input parameters for better estimates
    input_params = models.JSONField(default=dict, blank=True, help_text="e.g., num_chapters, word_count")

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    # Success tracking
    success = models.BooleanField(default=True, help_text="Whether the API call succeeded")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['api_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.get_api_type_display()} - {self.duration_seconds:.2f}s"

    def save(self, *args, **kwargs):
        """Save and maintain max 50 records per API type."""
        super().save(*args, **kwargs)

        # Keep only last 50 records per API type
        old_records = APIPerformanceMetric.objects.filter(
            api_type=self.api_type
        ).order_by('-created_at')[50:]

        if old_records:
            old_ids = [r.id for r in old_records]
            APIPerformanceMetric.objects.filter(id__in=old_ids).delete()

    @classmethod
    def get_average_duration(cls, api_type):
        """Get average duration for a specific API type."""
        from django.db.models import Avg
        result = cls.objects.filter(
            api_type=api_type,
            success=True
        ).aggregate(avg=Avg('duration_seconds'))
        return result['avg'] or 30.0  # Default to 30 seconds if no data


class ContentStructureTemplate(models.Model):
    """Pre-defined structure templates for different content types."""

    content_type = models.CharField(
        max_length=20,
        choices=NovelProject.CONTENT_TYPE_CHOICES,
        help_text="Type of content this template is for"
    )
    name = models.CharField(
        max_length=100,
        help_text="Template name (e.g., 'Five-Paragraph Essay')"
    )
    is_system = models.BooleanField(
        default=False,
        help_text="System templates cannot be modified by users"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='structure_templates',
        help_text="User who created this template (null for system templates)"
    )
    structure_data = models.JSONField(
        help_text="Template structure as JSON (e.g., {'sections': ['Introduction', 'Body', 'Conclusion']})"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of this template's purpose"
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['content_type', 'name']
        unique_together = [['content_type', 'name']]

    def __str__(self):
        return f"{self.get_content_type_display()}: {self.name}"


class ContentPiece(models.Model):
    """Single content piece (poem, essay, sketch, article).
    For novels, use Plot/Chapter models instead."""

    project = models.OneToOneField(
        'NovelProject',
        on_delete=models.CASCADE,
        related_name='content_piece',
        help_text="The project this content belongs to"
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Title of the content piece"
    )
    content = models.TextField(
        help_text="The actual poem/essay/sketch/article text"
    )
    word_count = models.IntegerField(
        default=0,
        help_text="Word count of the content"
    )

    # For essays/sketches with structure
    structure_template = models.ForeignKey(
        'ContentStructureTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='content_pieces',
        help_text="Structure template used (for essays/sketches)"
    )
    sections_data = models.JSONField(
        default=dict,
        help_text="Content organized by sections (e.g., {'introduction': '...', 'body1': '...'})"
    )

    # Generation parameters (historical record)
    generation_temperature = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.2)],
        help_text="Temperature used when generating this content (0.0-1.2)"
    )
    generation_top_p = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.3), MaxValueValidator(1.0)],
        help_text="Top_p used when generating this content (0.3-1.0)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title or 'Untitled'} ({self.project.get_content_type_display()})"


class ContentTypeScoringConfig(models.Model):
    """Configuration linking content types to their scoring categories."""

    content_type = models.CharField(
        max_length=20,
        choices=NovelProject.CONTENT_TYPE_CHOICES,
        unique=True,
        help_text="Content type this configuration is for"
    )
    score_categories = models.ManyToManyField(
        'ScoreCategory',
        through='ContentTypeCategoryWeight',
        related_name='content_type_configs',
        help_text="Score categories used for this content type"
    )

    default_temperature = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.2)],
        help_text="Default temperature for OpenAI API calls (0.0-1.2). Higher values = more creative/random."
    )

    default_top_p = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=1.0,
        validators=[MinValueValidator(0.3), MaxValueValidator(1.0)],
        help_text="Default top_p for OpenAI API calls (0.3-1.0). Controls diversity via nucleus sampling."
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['content_type']
        verbose_name = "Content Type Scoring Configuration"
        verbose_name_plural = "Content Type Scoring Configurations"

    def __str__(self):
        return f"Scoring Config: {self.get_content_type_display()}"


class ContentTypeCategoryWeight(models.Model):
    """Through model for ContentTypeScoringConfig and ScoreCategory with weight."""

    config = models.ForeignKey(
        'ContentTypeScoringConfig',
        on_delete=models.CASCADE,
        related_name='category_weights'
    )
    category = models.ForeignKey(
        'ScoreCategory',
        on_delete=models.CASCADE,
        related_name='content_type_weights'
    )
    weight = models.IntegerField(
        help_text="Weight/importance percentage for this category (e.g., 25 for 25%)"
    )

    class Meta:
        ordering = ['-weight', 'category__name']
        unique_together = [['config', 'category']]

    def __str__(self):
        return f"{self.config.get_content_type_display()} - {self.category.name} ({self.weight}%)"
