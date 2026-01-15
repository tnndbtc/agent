"""Serializers for Novel Writing Agent API."""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    NovelProject, Plot, Character, Setting,
    ChapterOutline, Chapter, Example, GenerationTask
)


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

    class Meta:
        model = NovelProject
        fields = [
            'id', 'user', 'title', 'genre', 'status',
            'total_word_count', 'created_at', 'updated_at',
            'plot', 'characters', 'settings', 'chapter_outlines', 'chapters'
        ]
        read_only_fields = ['id', 'user', 'chroma_collection_name', 'total_word_count', 'created_at', 'updated_at']


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


class ExampleSerializer(serializers.ModelSerializer):
    """Serializer for Example model."""

    class Meta:
        model = Example
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at']


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
    language = serializers.CharField(default='English')


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
