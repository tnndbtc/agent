"""Serializers for Novel Writing Agent API."""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    NovelProject, Plot, Act, Character, Setting,
    Chapter, Example, GenerationTask,
    ScoreCategory, ScoreCategoryTranslation, ExampleScore,
    UserPrompt,
    SystemPolicy, SystemPolicyTranslation,
    AgentRole, AgentRoleTranslation,
    WritingStyle, WritingStyleTranslation,
    WritingTechnique, WritingTechniqueTranslation,
    ContentPiece
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class ActSerializer(serializers.ModelSerializer):
    """Serializer for Act model."""

    class Meta:
        model = Act
        fields = ['id', 'act_number', 'subject', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PlotSerializer(serializers.ModelSerializer):
    """Serializer for Plot model."""

    acts = ActSerializer(many=True, read_only=True)

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


class ChapterSerializer(serializers.ModelSerializer):
    """Serializer for Chapter model."""

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


class ContentPieceSerializer(serializers.ModelSerializer):
    """Serializer for ContentPiece model (poems, essays, sketches, articles)."""

    structure_template_name = serializers.SerializerMethodField()

    class Meta:
        model = ContentPiece
        fields = ['id', 'project', 'title', 'content', 'word_count',
                  'structure_template', 'structure_template_name', 'sections_data',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_structure_template_name(self, obj):
        """Return structure template name if available."""
        if obj.structure_template:
            return obj.structure_template.name
        return None


class NovelProjectSerializer(serializers.ModelSerializer):
    """Serializer for NovelProject model."""

    user = UserSerializer(read_only=True)
    plot = PlotSerializer(read_only=True)
    characters = CharacterSerializer(many=True, read_only=True)
    settings = SettingSerializer(many=True, read_only=True)
    chapters = ChapterListSerializer(many=True, read_only=True)
    default_style_display = serializers.SerializerMethodField()
    content_piece = serializers.SerializerMethodField()

    class Meta:
        model = NovelProject
        fields = [
            'id', 'user', 'title', 'status', 'content_type',
            'total_word_count', 'created_at', 'updated_at',
            'plot', 'characters', 'settings', 'chapters', 'content_piece',
            'selected_techniques', 'default_style', 'default_style_display'
        ]
        read_only_fields = ['id', 'user', 'chroma_collection_name', 'total_word_count', 'created_at', 'updated_at']

    def get_default_style_display(self, obj):
        """Return minimal default style info (id and display_name)."""
        if obj.default_style:
            request = self.context.get('request')
            language_code = getattr(request, 'LANGUAGE_CODE', 'en') if request else 'en'
            translation = obj.default_style.translations.filter(language_code=language_code).first()
            return {
                'id': obj.default_style.id,
                'name_key': obj.default_style.name_key,
                'display_name': translation.name if translation else obj.default_style.name_key
            }
        return None

    def get_content_piece(self, obj):
        """Return content piece data for poem/essay/sketch/article projects."""
        if hasattr(obj, 'content_piece') and obj.content_piece:
            from .serializers import ContentPieceSerializer
            return ContentPieceSerializer(obj.content_piece).data
        return None

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


class NovelProjectListSerializer(serializers.ModelSerializer):
    """Lighter serializer for project list views."""

    user = UserSerializer(read_only=True)
    chapter_count = serializers.SerializerMethodField()
    default_style_name = serializers.SerializerMethodField()

    class Meta:
        model = NovelProject
        fields = ['id', 'title', 'status', 'content_type', 'total_word_count', 'chapter_count', 'updated_at', 'user', 'default_style_name']
        read_only_fields = fields

    def get_chapter_count(self, obj):
        return obj.chapters.count()

    def get_default_style_name(self, obj):
        """Return localized style name or None."""
        if obj.default_style:
            request = self.context.get('request')
            language_code = getattr(request, 'LANGUAGE_CODE', 'en') if request else 'en'
            translation = obj.default_style.translations.filter(language_code=language_code).first()
            return translation.name if translation else obj.default_style.name_key
        return None


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
        fields = ['id', 'user', 'public', 'is_good', 'category', 'title', 'locale',
                  'content', 'description', 'issues', 'metadata', 'scores', 'total_score', 'created_at']
        read_only_fields = ['id', 'user', 'created_at', 'total_score']
        extra_kwargs = {
            'category': {'allow_null': True, 'required': False},
        }


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
    """Request serializer for chapter writing with optional iterative quality improvement."""
    act_id = serializers.IntegerField(
        required=True,
        help_text="Act ID for chapter creation"
    )
    writing_style = serializers.CharField(default='literary')
    language = serializers.CharField(required=False, allow_blank=True)
    target_word_count = serializers.IntegerField(
        default=10,
        min_value=10,
        max_value=10000,
        help_text="Target word count for the chapter (10-10000)"
    )
    example_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="Optional Example ID for quality targeting"
    )
    iterative_mode = serializers.BooleanField(
        default=True,
        help_text="Whether to use iterative generation (default: True)"
    )
    max_iterations_multiplier = serializers.IntegerField(
        default=3,
        min_value=2,
        max_value=10,
        help_text="Maximum tokens as multiple of first iteration (default: 3)"
    )

    def validate_act_id(self, value):
        """Validate that the act exists."""
        if not value:
            return value

        # Import here to avoid circular imports
        from novels.models import Act

        # If we have project context from the view, validate against it
        if hasattr(self, 'context') and 'project' in self.context:
            project = self.context['project']
            if not Act.objects.filter(id=value, plot__project=project).exists():
                raise serializers.ValidationError(
                    f"Act {value} not found or does not belong to this project."
                )
        else:
            # Basic validation - just check if the act exists
            if not Act.objects.filter(id=value).exists():
                raise serializers.ValidationError(f"Act {value} not found.")

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


class UserPromptSerializer(serializers.ModelSerializer):
    """Serializer for UserPrompt model."""

    class Meta:
        model = UserPrompt
        fields = ['id', 'name', 'prompt_text', 'usage_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


class AIModificationRequestSerializer(serializers.Serializer):
    """Request serializer for AI text modification."""
    original_text = serializers.CharField(
        help_text="The selected text to modify"
    )
    user_prompt = serializers.CharField(
        help_text="User's modification instructions"
    )
    content_type = serializers.ChoiceField(
        choices=['plot', 'act', 'character', 'chapter', 'text'],
        default='text',
        help_text="Type of content being modified"
    )
    save_prompt = serializers.BooleanField(
        default=False,
        help_text="Whether to save this prompt for future use"
    )
    prompt_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Name for the saved prompt (required if save_prompt is True)"
    )
    saved_prompt_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="ID of a saved prompt to use (will override user_prompt)"
    )

    def validate(self, data):
        """Validate that required fields are present based on flags."""
        if data.get('save_prompt') and not data.get('prompt_name'):
            raise serializers.ValidationError({
                'prompt_name': 'Prompt name is required when save_prompt is True.'
            })
        return data


class AIModificationResponseSerializer(serializers.Serializer):
    """Response serializer for AI text modification."""
    original_text = serializers.CharField()
    modified_text = serializers.CharField()
    user_prompt = serializers.CharField()
    token_usage = serializers.JSONField()
    saved_prompt = UserPromptSerializer(required=False, allow_null=True)


# ========================================
# Prompt Architecture Serializers (5-Layer)
# ========================================

class SystemPolicyTranslationSerializer(serializers.ModelSerializer):
    """Serializer for SystemPolicyTranslation model."""

    class Meta:
        model = SystemPolicyTranslation
        fields = ['id', 'language_code', 'content']
        read_only_fields = ['id']


class SystemPolicySerializer(serializers.ModelSerializer):
    """Serializer for SystemPolicy model with translations."""

    translations = SystemPolicyTranslationSerializer(many=True, read_only=True)

    class Meta:
        model = SystemPolicy
        fields = ['id', 'name_key', 'policy_type', 'is_active', 'priority',
                  'created_at', 'updated_at', 'translations']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AgentRoleTranslationSerializer(serializers.ModelSerializer):
    """Serializer for AgentRoleTranslation model."""

    class Meta:
        model = AgentRoleTranslation
        fields = ['id', 'language_code', 'system_prompt']
        read_only_fields = ['id']


class AgentRoleSerializer(serializers.ModelSerializer):
    """Serializer for AgentRole model with translations."""

    translations = AgentRoleTranslationSerializer(many=True, read_only=True)

    class Meta:
        model = AgentRole
        fields = ['id', 'name_key', 'module_name', 'is_active',
                  'created_at', 'updated_at', 'translations']
        read_only_fields = ['id', 'created_at', 'updated_at']


class WritingStyleTranslationSerializer(serializers.ModelSerializer):
    """Serializer for WritingStyleTranslation model."""

    class Meta:
        model = WritingStyleTranslation
        fields = ['id', 'language_code', 'name', 'description', 'instructions']
        read_only_fields = ['id']


class WritingStyleSerializer(serializers.ModelSerializer):
    """Serializer for WritingStyle model with translations and display name."""

    translations = WritingStyleTranslationSerializer(many=True, read_only=True)
    display_name = serializers.SerializerMethodField()
    created_by_username = serializers.SerializerMethodField()

    class Meta:
        model = WritingStyle
        fields = ['id', 'name_key', 'is_system', 'created_by', 'created_by_username',
                  'public', 'pacing', 'tone', 'paragraph_length', 'dialogue_ratio',
                  'cliffhanger_enabled', 'created_at', 'updated_at', 'translations',
                  'display_name']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_display_name(self, obj):
        """Return localized name based on current language."""
        request = self.context.get('request')
        language_code = getattr(request, 'LANGUAGE_CODE', 'en') if request else 'en'

        translation = obj.translations.filter(language_code=language_code).first()
        if not translation and language_code != 'en':
            translation = obj.translations.filter(language_code='en').first()

        return translation.name if translation else obj.name_key

    def get_created_by_username(self, obj):
        """Return username of creator."""
        return obj.created_by.username if obj.created_by else None


class WritingTechniqueTranslationSerializer(serializers.ModelSerializer):
    """Serializer for WritingTechniqueTranslation model."""

    class Meta:
        model = WritingTechniqueTranslation
        fields = ['id', 'language_code', 'name', 'description', 'instructions']
        read_only_fields = ['id']


class WritingTechniqueSerializer(serializers.ModelSerializer):
    """Serializer for WritingTechnique model with translations and display name."""

    translations = WritingTechniqueTranslationSerializer(many=True, read_only=True)
    display_name = serializers.SerializerMethodField()
    created_by_username = serializers.SerializerMethodField()

    class Meta:
        model = WritingTechnique
        fields = ['id', 'name_key', 'is_system', 'created_by', 'created_by_username',
                  'public', 'category', 'created_at', 'updated_at', 'translations',
                  'display_name']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_display_name(self, obj):
        """Return localized name based on current language."""
        request = self.context.get('request')
        language_code = getattr(request, 'LANGUAGE_CODE', 'en') if request else 'en'

        translation = obj.translations.filter(language_code=language_code).first()
        if not translation and language_code != 'en':
            translation = obj.translations.filter(language_code='en').first()

        return translation.name if translation else obj.name_key

    def get_created_by_username(self, obj):
        """Return username of creator."""
        return obj.created_by.username if obj.created_by else None
