"""Web URL patterns for novels app."""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import web_views

app_name = 'novels'

urlpatterns = [
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='novels/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='novels:login'), name='logout'),
    path('register/', web_views.register, name='register'),

    # Main views
    path('', web_views.dashboard, name='dashboard'),
    path('project/<uuid:pk>/', web_views.project_detail, name='project_detail'),
    path('project/<uuid:pk>/brainstorm/', web_views.brainstorm_view, name='brainstorm'),
    path('project/<uuid:pk>/chapter/<uuid:chapter_id>/', web_views.chapter_detail, name='chapter_detail'),
]
