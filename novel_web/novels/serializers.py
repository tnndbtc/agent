"""Serializers for Novel Writing Agent API."""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    NovelProject, Plot, Character, Setting,
    ChapterOutline, Chapter, Example, GenerationTask,
    Genre, GenreTranslation,
    ScoreCategory, ScoreCategoryTranslation, ExampleScore
)


class GenreField(serializers.Field):
    """
    Custom field that accepts either Genre ID (int) or genre name (string).
    For backward compatibility with old frontend code.
    """

    def to_representation(self, value):
        """Serialize Genre to ID."""
        if value is None:
            return None
        return value.id

    def to_internal_value(self, data):
        """
        Deserialize data to Genre instance.
        Accepts int (Genre ID) or string (genre name for legacy support).
        """
        if data is None or data == '':
            return None

        # If it's an integer or string that looks like an integer, treat as ID
        if isinstance(data, int) or (isinstance(data, str) and data.isdigit()):
            try:
                return Genre.objects.get(pk=int(data))
            except Genre.DoesNotExist:
                raise serializers.ValidationError(f"Genre with ID {data} does not exist.")

        # If it's a string, try to find matching Genre by translation name
        if isinstance(data, str):
            # Try to find a genre with this translation name in any language
            genre_translation = GenreTranslation.objects.filter(name__iexact=data).first()
            if genre_translation:
                return genre_translation.genre
            # If no match found, return None (will be stored in genre_text)
            return None

        raise serializers.ValidationError("Genre must be an integer ID or string name.")


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class PlotSerializer(serializers.ModelSerializer):
    """Serializer for Plot model."""

    class Meta:
        model = Plot
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class CharacterSerializer(serializers.ModelSerializer):
    """Serializer for Character model."""

    class Meta:
        model = Character
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class SettingSerializer(serializers.ModelSerializer):
    """Serializer for Setting model."""

    class Meta:
        model = Setting
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChapterOutlineSerializer(serializers.ModelSerializer):
    """Serializer for ChapterOutline model."""

    class Meta:
        model = ChapterOutline
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChapterSerializer(serializers.ModelSerializer):
    """Serializer for Chapter model."""

    outline = ChapterOutlineSerializer(read_only=True)

    class Meta:
        model = Chapter
        fields = '__all__'
        read_only_fields = ['id', 'word_count', 'created_at', 'updated_at']


class ChapterListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views."""

    class Meta:
        model = Chapter
        fields = ['id', 'chapter_number', 'title', 'word_count', 'is_draft', 'updated_at']
        read_only_fields = fields


class NovelProjectSerializer(serializers.ModelSerializer):
    """Serializer for NovelProject model."""

    user = UserSerializer(read_only=True)
    plot = PlotSerializer(read_only=True)
    characters = CharacterSerializer(many=True, read_only=True)
    settings = SettingSerializer(many=True, read_only=True)
    chapter_outlines = ChapterOutlineSerializer(many=True, read_only=True)
    chapters = ChapterListSerializer(many=True, read_only=True)

    # Use custom field that accepts both Genre ID and string
    genre = GenreField(required=False, allow_null=True)

    class Meta:
        model = NovelProject
        fields = [
            'id', 'user', 'title', 'genre', 'status',
            'total_word_count', 'created_at', 'updated_at',
            'plot', 'characters', 'settings', 'chapter_outlines', 'chapters'
        ]
        read_only_fields = ['id', 'user', 'chroma_collection_name', 'total_word_count', 'created_at', 'updated_at']

    def validate(self, data):
        """Custom validation for unique title per user."""
        if self.instance is None:  # Creating new project
            user = self.context['request'].user
            title = data.get('title')
            if NovelProject.objects.filter(user=user, title=title).exists():
                raise serializers.ValidationError({
                    'title': f'"{title}" is already taken, choose a different name'
                })
        return data

    def create(self, validated_data):
        """Override create to handle genre_text from legacy string genres."""
        # Check if genre was sent as string in the original data
        genre_value = self.initial_data.get('genre', '')

        if isinstance(genre_value, str) and genre_value and not genre_value.isdigit():
            # Store in genre_text field for legacy compatibility
            validated_data['genre_text'] = genre_value
            # If GenreField successfully matched to a Genre FK, genre will be set
            # If not matched, genre will be None and genre_text will be used

        return super().create(validated_data)


class NovelProjectListSerializer(serializers.ModelSerializer):
    """Lighter serializer for project list views."""

    user = UserSerializer(read_only=True)
    chapter_count = serializers.SerializerMethodField()

    class Meta:
        model = NovelProject
        fields = ['id', 'title', 'genre', 'status', 'total_word_count', 'chapter_count', 'updated_at', 'user']
        read_only_fields = fields

    def get_chapter_count(self, obj):
        return obj.chapters.count()


class ScoreCategoryTranslationSerializer(serializers.ModelSerializer):
    """Serializer for ScoreCategoryTranslation model."""

    class Meta:
        model = ScoreCategoryTranslation
        fields = ['id', 'language_code', 'name']


class ScoreCategorySerializer(serializers.ModelSerializer):
    """Serializer for ScoreCategory model."""

    display_name = serializers.SerializerMethodField()

    class Meta:
        model = ScoreCategory
        fields = ['id', 'name', 'display_name', 'public', 'default_weight', 'is_system', 'created_by', 'order']
        read_only_fields = ['id', 'is_system']

    def get_display_name(self, obj):
        """Return localized name based on current language."""
        return str(obj)

    def create(self, validated_data):
        """Set created_by to current user if not provided."""
        if 'created_by' not in validated_data:
            validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ExampleScoreSerializer(serializers.ModelSerializer):
    """Serializer for ExampleScore model."""

    category_name = serializers.ReadOnlyField()
    weighted_score = serializers.ReadOnlyField()

    class Meta:
        model = ExampleScore
        fields = ['id', 'category', 'category_name', 'weight', 'score', 'weighted_score']
        read_only_fields = ['id']


class ExampleSerializer(serializers.ModelSerializer):
    """Serializer for Example model."""

    scores = ExampleScoreSerializer(many=True, read_only=True)
    total_score = serializers.ReadOnlyField()

    class Meta:
        model = Example
        fields = ['id', 'user', 'genre', 'public', 'is_good', 'category', 'content',
                  'description', 'issues', 'metadata', 'scores', 'total_score', 'created_at']
        read_only_fields = ['id', 'user', 'created_at', 'total_score']


class GenerationTaskSerializer(serializers.ModelSerializer):
    """Serializer for GenerationTask model."""

    class Meta:
        model = GenerationTask
        fields = '__all__'
        read_only_fields = [
            'id', 'user', 'celery_task_id', 'status', 'progress',
            'progress_message', 'result_data', 'error_message',
            'created_at', 'started_at', 'completed_at'
        ]


# Request/Response serializers for AI operations

class BrainstormRequestSerializer(serializers.Serializer):
    """Request serializer for brainstorming."""
    genre = serializers.CharField(required=False, allow_blank=True)
    theme = serializers.CharField(required=False, allow_blank=True)
    num_ideas = serializers.IntegerField(default=3, min_value=1, max_value=10)
    custom_prompt = serializers.CharField(required=False, allow_blank=True)


class PlotIdeaSerializer(serializers.Serializer):
    """Serializer for plot ideas."""
    title = serializers.CharField()
    premise = serializers.CharField()
    conflict = serializers.CharField()
    hook = serializers.CharField()


class CreatePlotRequestSerializer(serializers.Serializer):
    """Request serializer for plot creation."""
    idea_data = serializers.JSONField()


class CreateCharacterRequestSerializer(serializers.Serializer):
    """Request serializer for character creation."""
    character_type = serializers.ChoiceField(
        choices=['protagonist', 'antagonist', 'supporting']
    )
    num_options = serializers.IntegerField(default=3, min_value=1, max_value=5)
    roles = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


class WriteChapterRequestSerializer(serializers.Serializer):
    """Request serializer for chapter writing."""
    chapter_outline_id = serializers.UUIDField()
    writing_style = serializers.CharField(default='literary')
    language = serializers.CharField(required=False, allow_blank=True)
    target_word_count = serializers.IntegerField(
        default=10,
        min_value=10,
        max_value=10000,
        help_text="Target word count for the chapter (10-10000)"
    )

    def validate_chapter_outline_id(self, value):
        """Validate that the chapter outline exists."""
        # Import here to avoid circular imports
        from novels.models import ChapterOutline

        # If we have project context from the view, validate against it
        if hasattr(self, 'context') and 'project' in self.context:
            project = self.context['project']
            if not ChapterOutline.objects.filter(id=value, project=project).exists():
                raise serializers.ValidationError(
                    f"Chapter outline {value} not found or does not belong to this project."
                )
        else:
            # Basic validation - just check if the outline exists
            if not ChapterOutline.objects.filter(id=value).exists():
                raise serializers.ValidationError(f"Chapter outline {value} not found.")

        return value


class EditRequestSerializer(serializers.Serializer):
    """Request serializer for editing."""
    content = serializers.CharField()
    edit_type = serializers.ChoiceField(
        choices=['style', 'grammar', 'pacing', 'dialogue']
    )
    target_style = serializers.CharField(required=False, default='literary')


class ScoreRequestSerializer(serializers.Serializer):
    """Request serializer for scoring."""
    custom_categories = serializers.JSONField(required=False)
