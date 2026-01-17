"""API URL patterns for novels app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    NovelProjectViewSet, ChapterViewSet,
    GenerationTaskViewSet, ExampleViewSet, ScoreCategoryViewSet,
    GenreViewSet
)

router = DefaultRouter()
router.register(r'projects', NovelProjectViewSet, basename='project')
router.register(r'chapters', ChapterViewSet, basename='chapter')
router.register(r'tasks', GenerationTaskViewSet, basename='task')
router.register(r'genres', GenreViewSet, basename='genre')
router.register(r'examples', ExampleViewSet, basename='example')
router.register(r'score-categories', ScoreCategoryViewSet, basename='score-category')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
]
