"""Database models for Novel Writing Agent."""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


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
    genre = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # ChromaDB collection name (unique per project)
    chroma_collection_name = models.CharField(max_length=255, unique=True, editable=False)

    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    total_word_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]

    def __str__(self):
        return f"{self.title} by {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.chroma_collection_name:
            self.chroma_collection_name = f"project_{self.id.hex[:16]}"
        super().save(*args, **kwargs)


class Plot(models.Model):
    """Plot structure for a novel."""

    project = models.OneToOneField(NovelProject, on_delete=models.CASCADE, related_name='plot')

    # Basic plot elements
    premise = models.TextField(help_text="One-paragraph premise")
    genre = models.CharField(max_length=100, blank=True)
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

    number = models.IntegerField()
    title = models.CharField(max_length=255)

    # Outline details
    pov = models.CharField(max_length=255, blank=True, help_text="Point of view")
    setting = models.CharField(max_length=255, blank=True)
    events = models.TextField(help_text="What happens in this chapter")
    character_development = models.TextField(blank=True)
    pacing = models.CharField(max_length=10, choices=PACING_CHOICES, default='medium')
    story_beats = models.TextField(blank=True, help_text="Major plot points")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['number']
        unique_together = ['project', 'number']
        indexes = [
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


class Example(models.Model):
    """Good or bad writing examples."""

    CATEGORY_CHOICES = [
        ('writing', 'General Writing'),
        ('dialogue', 'Dialogue'),
        ('description', 'Description'),
        ('exposition', 'Exposition'),
        ('action', 'Action'),
        ('pacing', 'Pacing'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='examples')

    is_good = models.BooleanField(help_text="True for good example, False for bad")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    content = models.TextField()
    description = models.TextField(help_text="Why this is a good/bad example")

    # For bad examples
    issues = models.JSONField(default=list, blank=True, help_text="List of issues")

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_good', 'category']),
        ]

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
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(NovelProject, on_delete=models.CASCADE, related_name='tasks')
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
