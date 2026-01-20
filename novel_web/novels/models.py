"""Database models for Novel Writing Agent."""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import get_language, gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid


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


class Genre(models.Model):
    """Genre model with multi-language support."""

    id = models.AutoField(primary_key=True)
    name_key = models.CharField(max_length=50, unique=True, help_text="Translation key for genre (e.g., 'fantasy', 'sci_fi')")
    public = models.BooleanField(default=True, help_text="Whether this genre is publicly available")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['name_key']
        indexes = [
            models.Index(fields=['public']),
        ]

    def __str__(self):
        """Return translated genre name based on current language."""
        current_lang = get_language() or 'en'

        # Use prefetched translations if available to avoid N+1 queries
        if hasattr(self, '_prefetched_objects_cache') and 'translations' in self._prefetched_objects_cache:
            # Iterate through prefetched translations
            for translation in self.translations.all():
                if translation.language_code == current_lang:
                    return translation.name
            # Fallback to English
            for translation in self.translations.all():
                if translation.language_code == 'en':
                    return translation.name
        else:
            # No prefetch available, use filter (backwards compatibility)
            translation = self.translations.filter(language_code=current_lang).first()
            if translation:
                return translation.name
            # Fallback to English
            en_translation = self.translations.filter(language_code='en').first()
            if en_translation:
                return en_translation.name

        return self.name_key

    def get_translation(self, language_code):
        """Get translation for specific language."""
        translation = self.translations.filter(language_code=language_code).first()
        return translation.name if translation else self.name_key


class GenreTranslation(models.Model):
    """Translation model for Genre names."""

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('zh-hans', 'Simplified Chinese'),
    ]

    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, related_name='translations')
    language_code = models.CharField(max_length=10, choices=LANGUAGE_CHOICES)
    name = models.CharField(max_length=100, help_text="Translated genre name")

    class Meta:
        unique_together = [['genre', 'language_code']]
        indexes = [
            models.Index(fields=['language_code']),
        ]

    def __str__(self):
        return f"{self.genre.name_key} - {self.language_code}: {self.name}"


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
    genre_text = models.CharField(max_length=100, blank=True, help_text="Legacy genre text - will be migrated to Genre model")
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # ChromaDB collection name (unique per project)
    chroma_collection_name = models.CharField(max_length=255, unique=True, editable=False)

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

    @property
    def genre_display(self):
        """Return the genre display string (localized if using Genre model, or genre_text for legacy)."""
        if self.genre:
            # Use Genre model's __str__ which returns translated name
            return str(self.genre)
        elif self.genre_text:
            # Use legacy genre_text field
            return self.genre_text
        else:
            return None

    def save(self, *args, **kwargs):
        if not self.chroma_collection_name:
            self.chroma_collection_name = f"project_{self.id.hex[:16]}"
        super().save(*args, **kwargs)


class Plot(models.Model):
    """Plot structure for a novel."""

    project = models.OneToOneField(NovelProject, on_delete=models.CASCADE, related_name='plot')

    # Basic plot elements
    premise = models.TextField(help_text="One-paragraph premise")
    genre_text = models.CharField(max_length=100, blank=True, help_text="Legacy genre text - will be migrated to Genre model")
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True, related_name='plots')
    themes = models.TextField(blank=True, help_text="Main themes, comma-separated")
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
    percentage = models.IntegerField(
        help_text="Percentage of story (typically 25%, 50%, 25%)"
    )
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
        return f"Act {self.act_number}: {self.subject} ({self.percentage}%)"


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


class ChapterOutline(models.Model):
    """Outline for a chapter."""

    PACING_CHOICES = [
        ('slow', 'Slow'),
        ('medium', 'Medium'),
        ('fast', 'Fast'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(NovelProject, on_delete=models.CASCADE, related_name='chapter_outlines')
    act = models.ForeignKey(
        'Act',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='outlines',
        help_text="Act this outline belongs to (optional)"
    )

    number = models.IntegerField(help_text="Chapter number (display)")
    order_key = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Ordering key for sorting (allows insertion between items)"
    )
    title = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        """Auto-assign order_key if not provided."""
        if self.order_key is None:
            from decimal import Decimal
            from django.db.models import Max
            max_order_key = ChapterOutline.objects.filter(
                project=self.project
            ).aggregate(max_key=Max('order_key'))['max_key']
            self.order_key = (max_order_key or Decimal('0')) + Decimal('1')
        super().save(*args, **kwargs)

    # Outline details
    pov = models.CharField(max_length=255, blank=True, help_text="Point of view")
    setting = models.CharField(max_length=255, blank=True)
    events = models.TextField(help_text="What happens in this chapter")
    character_development = models.TextField(blank=True)
    pacing = models.CharField(max_length=64, choices=PACING_CHOICES, default='medium')
    story_beats = models.TextField(blank=True, help_text="Major plot points")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order_key']
        unique_together = ['project', 'order_key']
        indexes = [
            models.Index(fields=['project', 'order_key']),
            models.Index(fields=['project', 'number']),
        ]

    def __str__(self):
        return f"Chapter {self.number}: {self.title} - {self.project.title}"


class Chapter(models.Model):
    """Written chapter content."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(NovelProject, on_delete=models.CASCADE, related_name='chapters')
    outline = models.OneToOneField(ChapterOutline, on_delete=models.SET_NULL, null=True, blank=True, related_name='chapter')

    chapter_number = models.IntegerField()
    title = models.CharField(max_length=255)
    content = models.TextField(help_text="Full chapter content")
    summary = models.TextField(blank=True)

    word_count = models.IntegerField(default=0)
    language = models.CharField(max_length=50, default='English')
    writing_style = models.CharField(max_length=50, default='literary')

    # Versioning
    version = models.IntegerField(default=1)
    is_draft = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['chapter_number']
        unique_together = ['project', 'chapter_number', 'version']
        indexes = [
            models.Index(fields=['project', 'chapter_number']),
        ]

    def __str__(self):
        return f"Chapter {self.chapter_number}: {self.title} - {self.project.title}"

    def save(self, *args, **kwargs):
        # Update word count
        if self.content:
            self.word_count = len(self.content.split())
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

    # Genre and visibility
    genre = models.ForeignKey(Genre, null=True, blank=True, on_delete=models.SET_NULL, related_name='examples')
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
        return sum(score.weighted_score for score in self.scores.all())

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
        ('outline', 'Outline Creation'),
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
        ('outline', 'Outlines Generation'),
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
