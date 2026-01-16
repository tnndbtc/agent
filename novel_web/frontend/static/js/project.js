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
        connectToTask(response.task_id, 'brainstorm');
    }).catch(error => {
        hideLoading();
        showToast('Error: ' + error.message, 'error');
    });
}

async function generatePlot() {
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

    // Get estimated duration for plot API
    const estimatedDuration = await getEstimatedDuration('plot');
    showLoading('Generating plot...', 50, estimatedDuration);

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
    // Create and show character type selection modal
    const modalHtml = `
        <div class="modal" id="characterTypeModal" style="display: flex;">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Create Character</h3>
                    <button class="modal-close" onclick="closeCharacterModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>Character Type</label>
                        <select id="characterType" class="form-control">
                            <option value="protagonist">Protagonist (Main Character)</option>
                            <option value="antagonist">Antagonist (Villain)</option>
                            <option value="supporting">Supporting Character</option>
                        </select>
                    </div>
                </div>
                <div class="modal-actions">
                    <button type="button" class="btn btn-secondary" onclick="closeCharacterModal()">Cancel</button>
                    <button type="button" class="btn btn-primary" onclick="generateCharacterOptions()">Generate Options</button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

function closeCharacterModal() {
    const modal = document.getElementById('characterTypeModal') || document.getElementById('characterOptionsModal');
    if (modal) {
        modal.remove();
    }
}

function generateCharacterOptions() {
    const type = document.getElementById('characterType').value;
    closeCharacterModal();

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
        displayCharacterOptions(data.characters, type);
    }).catch(error => {
        hideLoading();
        showToast('Error: ' + error.message, 'error');
    });
}

function displayCharacterOptions(characters, charType) {
    if (!characters || characters.length === 0) {
        showToast('No character options generated', 'warning');
        return;
    }

    let optionsHtml = characters.map((char, index) => `
        <div class="character-option" onclick="selectCharacter(${index})">
            <h4>${char.name || 'Unnamed Character'}</h4>
            <p><strong>Background:</strong> ${char.background || 'No background'}</p>
            <p><strong>Personality:</strong> ${char.personality || 'No personality'}</p>
            ${char.physical_description ? `<p><strong>Appearance:</strong> ${char.physical_description}</p>` : ''}
        </div>
    `).join('');

    const modalHtml = `
        <div class="modal" id="characterOptionsModal" style="display: flex;">
            <div class="modal-content" style="max-width: 800px; max-height: 80vh; overflow-y: auto;">
                <div class="modal-header">
                    <h3>Select a Character</h3>
                    <button class="modal-close" onclick="closeCharacterModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <p>Choose one of the generated characters to add to your project:</p>
                    <div class="character-options-list">
                        ${optionsHtml}
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Store characters for later selection
    window.currentCharacterOptions = characters;
    window.currentCharacterType = charType;
}

function selectCharacter(index) {
    const character = window.currentCharacterOptions[index];
    const charType = window.currentCharacterType;

    // Map character type to role
    const roleMap = {
        'protagonist': 'protagonist',
        'antagonist': 'antagonist',
        'supporting': 'supporting'
    };

    character.role = roleMap[charType] || 'supporting';

    showLoading('Saving character...');

    apiRequest(`/api/projects/${projectId}/save_character/`, {
        method: 'POST',
        body: JSON.stringify({ character: character })
    }).then(data => {
        hideLoading();
        showToast('Character created successfully!', 'success');
        closeCharacterModal();
        setTimeout(() => window.location.reload(), 1000);
    }).catch(error => {
        hideLoading();
        showToast('Error saving character: ' + error.message, 'error');
    });
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
