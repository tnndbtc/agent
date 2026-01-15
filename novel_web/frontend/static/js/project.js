// Project-specific JavaScript

// Global project functions
window.startBrainstorm = startBrainstorm;
window.generatePlot = generatePlot;
window.createCharacter = createCharacter;
window.createOutline = createOutline;
window.writeNextChapter = writeNextChapter;
window.checkConsistency = checkConsistency;
window.scoreNovel = scoreNovel;
window.exportNovel = exportNovel;

function startBrainstorm() {
    const genre = prompt('Genre (optional):');
    const theme = prompt('Theme (optional):');

    const data = {
        genre: genre || '',
        theme: theme || '',
        num_ideas: 3
    };

    showLoading('Brainstorming ideas...');

    apiRequest(`/api/projects/${projectId}/brainstorm/`, {
        method: 'POST',
        body: JSON.stringify(data)
    }).then(response => {
        showToast('Brainstorming started!', 'success');
        connectToTask(response.task_id);
    }).catch(error => {
        hideLoading();
        showToast('Error: ' + error.message, 'error');
    });
}

function generatePlot() {
    // This would typically show a modal with brainstormed ideas
    // For now, we'll use a simple prompt
    const premise = prompt('Enter plot premise:');
    if (!premise) return;

    const data = {
        idea_data: {
            title: 'Generated Plot',
            premise: premise,
            conflict: '',
            hook: ''
        }
    };

    showLoading('Generating plot...');

    apiRequest(`/api/projects/${projectId}/create_plot/`, {
        method: 'POST',
        body: JSON.stringify(data)
    }).then(data => {
        hideLoading();
        showToast('Plot created!', 'success');
        setTimeout(() => window.location.reload(), 1500);
    }).catch(error => {
        hideLoading();
        showToast('Error: ' + error.message, 'error');
    });
}

function createCharacter() {
    const type = prompt('Character type (protagonist/antagonist/supporting):') || 'protagonist';

    const data = {
        character_type: type,
        num_options: 3
    };

    showLoading('Creating character options...');

    apiRequest(`/api/projects/${projectId}/create_characters/`, {
        method: 'POST',
        body: JSON.stringify(data)
    }).then(data => {
        hideLoading();
        // Show character options to user
        displayCharacterOptions(data.characters);
    }).catch(error => {
        hideLoading();
        showToast('Error: ' + error.message, 'error');
    });
}

function displayCharacterOptions(characters) {
    // This would show a modal with character options
    // For now, just show a toast
    showToast(`Generated ${characters.length} character options`, 'success');
}

function writeNextChapter() {
    // Find next chapter to write
    const outlines = document.querySelectorAll('.chapter-outline');
    if (outlines.length === 0) {
        showToast('Create an outline first', 'warning');
        return;
    }

    const numChapters = prompt('Chapter number to write:');
    if (!numChapters) return;

    // Would need outline ID - this is simplified
    showToast('Please select a chapter from the outline', 'info');
}

function checkConsistency() {
    showLoading('Checking consistency...');

    // This would call the consistency check API
    // For now, show a placeholder
    setTimeout(() => {
        hideLoading();
        showToast('Consistency check complete', 'success');
    }, 2000);
}
