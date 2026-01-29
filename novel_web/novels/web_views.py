"""Web views for the frontend."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Q
from .models import NovelProject, Chapter, GenerationTask, Example, ScoreCategory, UserProfile


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
        'projects': projects,
    })


@login_required
def project_detail(request, pk):
    """Project detail view."""
    project = get_object_or_404(NovelProject, pk=pk, user=request.user)

    context = {
        'project': project,
        'has_plot': hasattr(project, 'plot'),
        'has_idea': hasattr(project, 'idea'),
        'characters': project.characters.all(),
        'settings': project.settings.all(),
        'chapters': project.chapters.select_related('act').all()
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
def manage_examples(request):
    """Manage examples view - shows user's examples and public examples."""
    # Get user's own examples and public examples
    examples = Example.objects.filter(
        Q(public=True) | Q(user=request.user)
    ).select_related('user').prefetch_related('scores__category').order_by('-created_at')

    # Separate into public and private
    public_examples = examples.filter(public=True)
    private_examples = examples.filter(user=request.user, public=False)

    # Get score categories for form
    score_categories = ScoreCategory.objects.filter(
        Q(public=True) | Q(created_by=request.user)
    ).prefetch_related('translations').order_by('order', 'name')

    return render(request, 'novels/manage_examples.html', {
        'public_examples': public_examples,
        'private_examples': private_examples,
        'score_categories': score_categories
    })


@login_required
def user_metadata(request):
    """Display user metadata including token usage."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    return render(request, 'novels/user_metadata.html', {
        'profile': profile,
        'user': request.user
    })
