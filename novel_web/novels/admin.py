"""Admin configuration for novels app."""
from django.contrib import admin
from .models import (
    NovelProject, Idea, Plot, Character, Setting,
    Chapter, Example, GenerationTask,
    ScoreCategory, ScoreCategoryTranslation, ExampleScore,
    SystemPolicy, SystemPolicyTranslation,
    AgentRole, AgentRoleTranslation,
    PromptTemplate,
    InstructionTemplate, InstructionTemplateTranslation,
    WritingStyle, WritingStyleTranslation,
    CustomWritingStyle, CustomAgentRole,
    ContentStructureTemplate, ContentPiece,
    ContentTypeScoringConfig, ContentTypeCategoryWeight
)


@admin.register(NovelProject)
class NovelProjectAdmin(admin.ModelAdmin):
    """Admin for NovelProject."""
    list_display = ['title', 'user', 'content_type', 'status', 'total_word_count', 'updated_at']
    list_filter = ['content_type', 'status', 'created_at']
    search_fields = ['title', 'user__username']
    readonly_fields = ['chroma_collection_name', 'created_at', 'updated_at']


@admin.register(Idea)
class IdeaAdmin(admin.ModelAdmin):
    """Admin for Idea."""
    list_display = ['project', 'content_type', 'updated_at']
    list_filter = ['content_type', 'created_at']
    search_fields = ['project__title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Plot)
class PlotAdmin(admin.ModelAdmin):
    """Admin for Plot."""
    list_display = ['project', 'updated_at']
    search_fields = ['project__title']


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    """Admin for Character."""
    list_display = ['name', 'role', 'project', 'updated_at']
    list_filter = ['role']
    search_fields = ['name', 'project__title']


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    """Admin for Setting."""
    list_display = ['location', 'project', 'is_primary', 'updated_at']
    list_filter = ['is_primary']


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    """Admin for Chapter."""
    list_display = ['chapter_number', 'title', 'project', 'word_count', 'is_draft', 'updated_at']
    list_filter = ['is_draft', 'language', 'writing_style']
    search_fields = ['title', 'project__title']


class ScoreCategoryTranslationInline(admin.TabularInline):
    """Inline admin for ScoreCategoryTranslation."""
    model = ScoreCategoryTranslation
    extra = 0
    fields = ['language_code', 'name']


@admin.register(ScoreCategory)
class ScoreCategoryAdmin(admin.ModelAdmin):
    """Admin for ScoreCategory."""
    list_display = ['id', 'name', 'public', 'is_system', 'created_by', 'default_weight', 'order', 'created_at']
    list_filter = ['public', 'is_system']
    search_fields = ['name', 'name_key']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ScoreCategoryTranslationInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'public', 'created_by')
        }),
        ('System Category Fields', {
            'fields': ('is_system', 'name_key', 'default_weight', 'order'),
            'description': 'These fields are only for system-defined categories'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


class ExampleScoreInline(admin.TabularInline):
    """Inline admin for ExampleScore."""
    model = ExampleScore
    extra = 0
    fields = ['category', 'weight', 'score', 'weighted_score']
    readonly_fields = ['weighted_score']


@admin.register(Example)
class ExampleAdmin(admin.ModelAdmin):
    """Admin for Example."""
    list_display = ['category', 'is_good', 'public', 'user', 'total_score', 'created_at']
    list_filter = ['is_good', 'category', 'public']
    search_fields = ['content', 'description']
    readonly_fields = ['total_score', 'created_at']
    inlines = [ExampleScoreInline]


@admin.register(GenerationTask)
class GenerationTaskAdmin(admin.ModelAdmin):
    """Admin for GenerationTask."""
    list_display = ['task_type', 'status', 'progress', 'project', 'created_at']
    list_filter = ['task_type', 'status']
    readonly_fields = ['created_at', 'started_at', 'completed_at']


# ========================================
# Prompt Architecture Admin (5-Layer)
# ========================================

class SystemPolicyTranslationInline(admin.TabularInline):
    """Inline admin for SystemPolicyTranslation."""
    model = SystemPolicyTranslation
    extra = 0
    fields = ['language_code', 'content']


@admin.register(SystemPolicy)
class SystemPolicyAdmin(admin.ModelAdmin):
    """Admin for SystemPolicy."""
    list_display = ['name_key', 'policy_type', 'model_name', 'is_active', 'priority', 'created_at']
    list_filter = ['policy_type', 'is_active', 'model_name']
    search_fields = ['name_key', 'model_name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [SystemPolicyTranslationInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('name_key', 'policy_type', 'model_name', 'is_active', 'priority'),
            'description': 'Leave model_name blank to create a default policy that applies to all models when no model-specific policy exists.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


class AgentRoleTranslationInline(admin.TabularInline):
    """Inline admin for AgentRoleTranslation."""
    model = AgentRoleTranslation
    extra = 0
    fields = ['language_code', 'system_prompt']


@admin.register(AgentRole)
class AgentRoleAdmin(admin.ModelAdmin):
    """Admin for AgentRole."""
    list_display = ['name_key', 'module_name', 'model_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'model_name']
    search_fields = ['name_key', 'module_name', 'model_name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [AgentRoleTranslationInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('name_key', 'module_name', 'model_name', 'is_active'),
            'description': 'Leave model_name blank to create a default role that applies to all models when no model-specific role exists.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    """Admin for PromptTemplate (English only)."""
    list_display = ['name_key', 'description', 'model_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'model_name']
    search_fields = ['name_key', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('name_key', 'description', 'model_name', 'is_active'),
            'description': 'Leave model_name blank to create a default template that applies to all models when no model-specific template exists.'
        }),
        ('Prompt Messages (English)', {
            'fields': ('system_message', 'developer_message', 'user_message_template'),
            'description': 'System message defines the AI role, developer message adds optional instructions, and user message template contains the main prompt with {placeholders}.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


class InstructionTemplateTranslationInline(admin.TabularInline):
    """Inline admin for InstructionTemplateTranslation."""
    model = InstructionTemplateTranslation
    extra = 0
    fields = ['language_code', 'task_description', 'instructions', 'json_format']


@admin.register(InstructionTemplate)
class InstructionTemplateAdmin(admin.ModelAdmin):
    """Admin for InstructionTemplate."""
    list_display = ['name_key', 'content_type', 'is_active', 'created_at']
    list_filter = ['content_type', 'is_active']
    search_fields = ['name_key']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [InstructionTemplateTranslationInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('name_key', 'content_type', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


class WritingStyleTranslationInline(admin.TabularInline):
    """Inline admin for WritingStyleTranslation."""
    model = WritingStyleTranslation
    extra = 0
    fields = ['language_code', 'name', 'description', 'instructions']


@admin.register(WritingStyle)
class WritingStyleAdmin(admin.ModelAdmin):
    """Admin for WritingStyle."""
    list_display = ['name_key', 'is_system', 'created_by', 'public', 'pacing', 'created_at']
    list_filter = ['is_system', 'public', 'pacing', 'paragraph_length', 'dialogue_ratio']
    search_fields = ['name_key', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [WritingStyleTranslationInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('name_key', 'is_system', 'created_by', 'public')
        }),
        ('Style Parameters', {
            'fields': ('pacing', 'tone', 'paragraph_length', 'dialogue_ratio', 'cliffhanger_enabled')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(CustomWritingStyle)
class CustomWritingStyleAdmin(admin.ModelAdmin):
    """Admin for CustomWritingStyle."""
    list_display = ['style_name', 'user', 'language_code', 'temperature', 'top_p', 'created_at']
    list_filter = ['language_code']
    search_fields = ['style_name', 'user__username', 'style_instruction']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'style_name', 'language_code')
        }),
        ('Instructions', {
            'fields': ('style_instruction', 'sample')
        }),
        ('Generation Parameters', {
            'fields': ('temperature', 'top_p'),
            'description': 'AI-suggested generation parameters for this writing style'
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(CustomAgentRole)
class CustomAgentRoleAdmin(admin.ModelAdmin):
    """Admin for CustomAgentRole."""
    list_display = ['role_name', 'user', 'language_code', 'custom_style', 'created_at']
    list_filter = ['language_code']
    search_fields = ['role_name', 'user__username', 'role_instruction']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'role_name', 'language_code', 'custom_style')
        }),
        ('Instructions', {
            'fields': ('role_instruction',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


# ========================================
# Multi-Content-Type Support Admin
# ========================================

@admin.register(ContentStructureTemplate)
class ContentStructureTemplateAdmin(admin.ModelAdmin):
    """Admin for ContentStructureTemplate."""
    list_display = ['name', 'content_type', 'is_system', 'created_by', 'created_at']
    list_filter = ['content_type', 'is_system']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('content_type', 'name', 'is_system', 'created_by')
        }),
        ('Structure', {
            'fields': ('structure_data', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ContentPiece)
class ContentPieceAdmin(admin.ModelAdmin):
    """Admin for ContentPiece."""
    list_display = ['title', 'project', 'word_count', 'ai_model', 'generation_temperature', 'generation_top_p', 'updated_at']
    search_fields = ['title', 'project__title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    list_filter = ['ai_model', 'writing_style', 'custom_writing_style']
    fieldsets = (
        ('Basic Info', {
            'fields': ('project', 'title', 'word_count')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Structure', {
            'fields': ('structure_template', 'sections_data')
        }),
        ('Generation Metadata', {
            'fields': ('ai_model', 'generation_temperature', 'generation_top_p',
                      'writing_style', 'custom_writing_style'),
            'description': 'Parameters used when this content was generated'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


class ContentTypeCategoryWeightInline(admin.TabularInline):
    """Inline admin for ContentTypeCategoryWeight."""
    model = ContentTypeCategoryWeight
    extra = 0
    fields = ['category', 'weight']


@admin.register(ContentTypeScoringConfig)
class ContentTypeScoringConfigAdmin(admin.ModelAdmin):
    """Admin for ContentTypeScoringConfig."""
    list_display = ['content_type', 'default_temperature', 'default_top_p', 'created_at']
    list_filter = ['content_type']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ContentTypeCategoryWeightInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('content_type',)
        }),
        ('Generation Parameters', {
            'fields': ('default_temperature', 'default_top_p'),
            'description': 'Default parameters for OpenAI API calls for this content type'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
