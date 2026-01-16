"""Web views for the frontend."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import NovelProject, Chapter, GenerationTask


def register(request):
    """User registration view."""
    if request.method == 'POST':
        form = UserCreationForm(request.data)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('novels:login')
    else:
        form = UserCreationForm()
    return render(request, 'novels/register.html', {'form': form})


@login_required
def dashboard(request):
    """Dashboard showing all user projects."""
    projects = NovelProject.objects.filter(user=request.user)
    return render(request, 'novels/dashboard.html', {
        'projects': projects
    })


@login_required
def project_detail(request, pk):
    """Project detail view."""
    project = get_object_or_404(NovelProject, pk=pk, user=request.user)

    # Get previous brainstorm tasks with results
    previous_tasks = GenerationTask.objects.filter(
        project=project,
        task_type='brainstorm',
        status='completed'
    ).order_by('-created_at')[:10]  # Get last 10 completed brainstorms, ordered by creation date

    # Extract ideas from completed tasks
    previous_ideas = []
    for task in previous_tasks:
        if task.result_data and 'ideas' in task.result_data:
            ideas_list = task.result_data.get('ideas', [])
            if isinstance(ideas_list, list):
                for idea in ideas_list:
                    if isinstance(idea, dict):
                        idea['task_date'] = task.completed_at or task.created_at
                        previous_ideas.append(idea)

    context = {
        'project': project,
        'has_plot': hasattr(project, 'plot'),
        'characters': project.characters.all(),
        'settings': project.settings.all(),
        'outlines': project.chapter_outlines.all(),
        'chapters': project.chapters.all(),
        'previous_ideas': previous_ideas
    }

    return render(request, 'novels/project_detail.html', context)


@login_required
def chapter_detail(request, pk, chapter_id):
    """Chapter detail/editor view."""
    project = get_object_or_404(NovelProject, pk=pk, user=request.user)
    chapter = get_object_or_404(Chapter, pk=chapter_id, project=project)

    return render(request, 'novels/chapter_detail.html', {
        'project': project,
        'chapter': chapter
    })


@login_required
def brainstorm_view(request, pk):
    """Brainstorming ideas view."""
    project = get_object_or_404(NovelProject, pk=pk, user=request.user)

    # Get previous brainstorm tasks with results
    previous_tasks = GenerationTask.objects.filter(
        project=project,
        task_type='brainstorm',
        status='completed'
    ).order_by('-created_at')[:10]  # Get last 10 completed brainstorms, ordered by creation date

    # Extract ideas from completed tasks
    previous_ideas = []
    for task in previous_tasks:
        if task.result_data and 'ideas' in task.result_data:
            ideas_list = task.result_data.get('ideas', [])
            if isinstance(ideas_list, list):
                for idea in ideas_list:
                    if isinstance(idea, dict):
                        idea['task_date'] = task.completed_at or task.created_at
                        previous_ideas.append(idea)

    return render(request, 'novels/brainstorm.html', {
        'project': project,
        'previous_ideas': previous_ideas
    })
