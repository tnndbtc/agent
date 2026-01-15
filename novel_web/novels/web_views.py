"""Web views for the frontend."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import NovelProject, Chapter


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

    context = {
        'project': project,
        'has_plot': hasattr(project, 'plot'),
        'characters': project.characters.all(),
        'settings': project.settings.all(),
        'outlines': project.chapter_outlines.all(),
        'chapters': project.chapters.all()
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

    return render(request, 'novels/brainstorm.html', {
        'project': project
    })
