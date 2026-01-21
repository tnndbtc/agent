"""API URL patterns for novels app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    NovelProjectViewSet, ChapterViewSet,
    GenerationTaskViewSet, ExampleViewSet, ScoreCategoryViewSet,
    ExampleScoreViewSet, ActViewSet,
    UserPromptViewSet, AIModificationViewSet,
    SystemPolicyViewSet, AgentRoleViewSet,
    WritingStyleViewSet, WritingTechniqueViewSet
)

router = DefaultRouter()
router.register(r'projects', NovelProjectViewSet, basename='project')
router.register(r'chapters', ChapterViewSet, basename='chapter')
router.register(r'tasks', GenerationTaskViewSet, basename='task')
router.register(r'examples', ExampleViewSet, basename='example')
router.register(r'example-scores', ExampleScoreViewSet, basename='example-score')
router.register(r'score-categories', ScoreCategoryViewSet, basename='score-category')
router.register(r'acts', ActViewSet, basename='act')
router.register(r'user-prompts', UserPromptViewSet, basename='user-prompt')
router.register(r'ai-modifications', AIModificationViewSet, basename='ai-modification')

# Prompt Architecture (5-Layer) endpoints
router.register(r'system-policies', SystemPolicyViewSet, basename='system-policy')
router.register(r'agent-roles', AgentRoleViewSet, basename='agent-role')
router.register(r'writing-styles', WritingStyleViewSet, basename='writing-style')
router.register(r'writing-techniques', WritingTechniqueViewSet, basename='writing-technique')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
]
