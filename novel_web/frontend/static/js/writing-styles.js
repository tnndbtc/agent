/**
 * Writing Styles Management
 * Handles UI for 5-layer prompt architecture integration
 */

// Global state
let allStyles = [];
let currentProject = null;

/**
 * Initialize writing styles on page load
 */
async function initWritingStylesAndTechniques(projectId = null) {
    currentProject = projectId;

    try {
        // Load styles
        const stylesResponse = await apiRequest('/api/writing-styles/');

        // Handle both paginated and non-paginated responses
        allStyles = stylesResponse.results || stylesResponse;

        console.log(`Loaded ${allStyles.length} styles`);
    } catch (error) {
        console.error('Error loading styles:', error);
        showToast('Failed to load writing styles', 'error');
    }
}

/**
 * Populate a style dropdown select element
 */
function populateStyleSelect(selectId, includeNone = true, noneText = 'Select a style...') {
    const select = document.getElementById(selectId);
    if (!select) return;

    // Clear existing options
    select.innerHTML = '';

    // Add "none" option
    if (includeNone) {
        const noneOption = document.createElement('option');
        noneOption.value = '';
        noneOption.textContent = noneText;
        select.appendChild(noneOption);
    }

    // Group styles by type
    const systemStyles = allStyles.filter(s => s.is_system);
    const publicStyles = allStyles.filter(s => !s.is_system && s.public);
    const privateStyles = allStyles.filter(s => !s.is_system && !s.public);

    // Add system styles
    if (systemStyles.length > 0) {
        const systemGroup = document.createElement('optgroup');
        systemGroup.label = 'System Styles';
        systemStyles.forEach(style => {
            const option = document.createElement('option');
            option.value = style.id;
            option.textContent = style.display_name || style.name_key;
            systemGroup.appendChild(option);
        });
        select.appendChild(systemGroup);
    }

    // Add public styles
    if (publicStyles.length > 0) {
        const publicGroup = document.createElement('optgroup');
        publicGroup.label = 'Public Styles';
        publicStyles.forEach(style => {
            const option = document.createElement('option');
            option.value = style.id;
            option.textContent = style.display_name || style.name_key;
            publicGroup.appendChild(option);
        });
        select.appendChild(publicGroup);
    }

    // Add private styles
    if (privateStyles.length > 0) {
        const privateGroup = document.createElement('optgroup');
        privateGroup.label = 'My Custom Styles';
        privateStyles.forEach(style => {
            const option = document.createElement('option');
            option.value = style.id;
            option.textContent = style.display_name || style.name_key;
            privateGroup.appendChild(option);
        });
        select.appendChild(privateGroup);
    }
}

/**
 * Populate techniques as checkboxes grouped by category
 */
function populateTechniqueCheckboxes(containerId, selectedTechniqueIds = []) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Clear existing content
    container.innerHTML = '';

    // Group techniques by category
    const categories = {};
    allTechniques.forEach(tech => {
        const category = tech.category || 'other';
        if (!categories[category]) {
            categories[category] = [];
        }
        categories[category].push(tech);
    });

    // Create checkbox groups for each category
    Object.keys(categories).sort().forEach(category => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'technique-category';

        const categoryLabel = document.createElement('h5');
        categoryLabel.className = 'technique-category-label';
        categoryLabel.textContent = category.charAt(0).toUpperCase() + category.slice(1);
        categoryDiv.appendChild(categoryLabel);

        const checkboxGroup = document.createElement('div');
        checkboxGroup.className = 'techniques-checkboxes';

        categories[category].forEach(tech => {
            const wrapper = document.createElement('div');
            wrapper.className = 'checkbox-wrapper';

            const label = document.createElement('label');

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.name = 'techniques';
            checkbox.value = tech.id;
            checkbox.checked = selectedTechniqueIds.includes(tech.id);

            const textSpan = document.createElement('span');
            textSpan.className = 'checkbox-text';
            textSpan.textContent = tech.display_name || tech.name_key;

            label.appendChild(checkbox);
            label.appendChild(textSpan);
            wrapper.appendChild(label);
            checkboxGroup.appendChild(wrapper);
        });

        categoryDiv.appendChild(checkboxGroup);
        container.appendChild(categoryDiv);
    });
}

/**
 * Get selected technique IDs from checkboxes
 */
function getSelectedTechniques(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return [];

    const checkboxes = container.querySelectorAll('input[name="techniques"]:checked');
    return Array.from(checkboxes).map(cb => parseInt(cb.value));
}

/**
 * Open style browser modal
 */
function openStyleBrowser() {
    const modal = document.getElementById('styleBrowserModal');
    if (!modal) {
        console.error('Style browser modal not found');
        return;
    }

    modal.style.display = 'flex';
    displayStylesInBrowser('all');
}

/**
 * Close style browser modal
 */
function closeStyleBrowser() {
    const modal = document.getElementById('styleBrowserModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Display styles in browser modal with filtering
 */
function displayStylesInBrowser(filter = 'all') {
    const container = document.getElementById('stylesList');
    if (!container) return;

    container.innerHTML = '';

    // Filter styles
    let filteredStyles = allStyles;
    if (filter === 'system') {
        filteredStyles = allStyles.filter(s => s.is_system);
    } else if (filter === 'custom') {
        filteredStyles = allStyles.filter(s => !s.is_system && !s.public);
    } else if (filter === 'public') {
        filteredStyles = allStyles.filter(s => !s.is_system && s.public);
    }

    if (filteredStyles.length === 0) {
        container.innerHTML = '<p class="no-results">No styles found.</p>';
        return;
    }

    // Display each style
    filteredStyles.forEach(style => {
        const card = document.createElement('div');
        card.className = 'style-card';

        const header = document.createElement('div');
        header.className = 'style-card-header';

        const title = document.createElement('h4');
        title.textContent = style.display_name || style.name_key;
        header.appendChild(title);

        if (style.is_system) {
            const systemBadge = document.createElement('span');
            systemBadge.className = 'badge badge-system';
            systemBadge.textContent = 'System';
            header.appendChild(systemBadge);
        }

        card.appendChild(header);

        // Description
        if (style.translations && style.translations.length > 0) {
            const desc = document.createElement('p');
            desc.className = 'style-description';
            desc.textContent = style.translations[0].description || '';
            card.appendChild(desc);
        }

        // Metadata badges
        const metaDiv = document.createElement('div');
        metaDiv.className = 'style-meta';

        if (style.pacing) {
            const badge = document.createElement('span');
            badge.className = 'badge';
            badge.textContent = `Pacing: ${style.pacing}`;
            metaDiv.appendChild(badge);
        }

        if (style.dialogue_ratio) {
            const badge = document.createElement('span');
            badge.className = 'badge';
            badge.textContent = `Dialogue: ${style.dialogue_ratio}`;
            metaDiv.appendChild(badge);
        }

        if (style.paragraph_length) {
            const badge = document.createElement('span');
            badge.className = 'badge';
            badge.textContent = `Paragraphs: ${style.paragraph_length}`;
            metaDiv.appendChild(badge);
        }

        card.appendChild(metaDiv);
        container.appendChild(card);
    });
}

/**
 * Open technique browser modal
 */
function openTechniqueBrowser() {
    const modal = document.getElementById('techniqueBrowserModal');
    if (!modal) {
        console.error('Technique browser modal not found');
        return;
    }

    modal.style.display = 'flex';
    displayTechniquesInBrowser('all');
}

/**
 * Close technique browser modal
 */
function closeTechniqueBrowser() {
    const modal = document.getElementById('techniqueBrowserModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Display techniques in browser modal with filtering
 */
function displayTechniquesInBrowser(filter = 'all') {
    const container = document.getElementById('techniquesList');
    if (!container) return;

    container.innerHTML = '';

    // Filter techniques
    let filteredTechniques = allTechniques;
    if (filter === 'system') {
        filteredTechniques = allTechniques.filter(t => t.is_system);
    } else if (filter === 'custom') {
        filteredTechniques = allTechniques.filter(t => !t.is_system && !t.public);
    } else if (filter === 'public') {
        filteredTechniques = allTechniques.filter(t => !t.is_system && t.public);
    } else if (filter !== 'all') {
        // Filter by category
        filteredTechniques = allTechniques.filter(t => t.category === filter);
    }

    if (filteredTechniques.length === 0) {
        container.innerHTML = '<p class="no-results">No techniques found.</p>';
        return;
    }

    // Display each technique
    filteredTechniques.forEach(tech => {
        const card = document.createElement('div');
        card.className = 'technique-card';

        const header = document.createElement('div');
        header.className = 'technique-card-header';

        const title = document.createElement('h4');
        title.textContent = tech.display_name || tech.name_key;
        header.appendChild(title);

        if (tech.is_system) {
            const systemBadge = document.createElement('span');
            systemBadge.className = 'badge badge-system';
            systemBadge.textContent = 'System';
            header.appendChild(systemBadge);
        }

        card.appendChild(header);

        // Description
        if (tech.translations && tech.translations.length > 0) {
            const desc = document.createElement('p');
            desc.className = 'technique-description';
            desc.textContent = tech.translations[0].description || '';
            card.appendChild(desc);
        }

        // Category badge
        if (tech.category) {
            const badge = document.createElement('span');
            badge.className = 'badge badge-category';
            badge.textContent = tech.category;
            card.appendChild(badge);
        }

        container.appendChild(card);
    });
}

/**
 * Open custom style creator modal
 */
function openCreateStyleModal() {
    const modal = document.getElementById('createStyleModal');
    if (!modal) {
        console.error('Create style modal not found');
        return;
    }

    // Reset form
    const form = document.getElementById('createStyleForm');
    if (form) {
        form.reset();
    }

    modal.style.display = 'flex';
}

/**
 * Close custom style creator modal
 */
function closeCreateStyleModal() {
    const modal = document.getElementById('createStyleModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Submit custom style creation
 */
async function submitCreateStyle(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);

    // Build request data
    const data = {
        name_key: formData.get('name_key'),
        pacing: formData.get('pacing'),
        tone: formData.get('tone') || '',
        paragraph_length: formData.get('paragraph_length'),
        dialogue_ratio: formData.get('dialogue_ratio'),
        cliffhanger_enabled: formData.get('cliffhanger_enabled') === 'on',
        public: formData.get('public') === 'on',
        translations: [
            {
                language_code: 'en', // TODO: Get from user's locale
                name: formData.get('style_name'),
                description: formData.get('description') || '',
                instructions: formData.get('instructions') || ''
            }
        ]
    };

    try {
        showLoading('Creating custom style...');
        const newStyle = await apiRequest('/api/writing-styles/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        hideLoading();

        // Add to local cache
        allStyles.push(newStyle);

        showToast('Custom style created successfully!', 'success');
        closeCreateStyleModal();

        // Refresh any style dropdowns on the page
        if (document.getElementById('styleSelect')) {
            populateStyleSelect('styleSelect', true, 'Select a style...');
        }
        if (document.getElementById('chapterStyleOverride')) {
            populateStyleSelect('chapterStyleOverride', true, 'Use project default');
        }

    } catch (error) {
        hideLoading();
        console.error('Error creating style:', error);
        showToast('Error creating style: ' + (error.message || 'Unknown error'), 'error');
    }
}

/**
 * Open custom technique creator modal
 */
function openCreateTechniqueModal() {
    const modal = document.getElementById('createTechniqueModal');
    if (!modal) {
        console.error('Create technique modal not found');
        return;
    }

    // Reset form
    const form = document.getElementById('createTechniqueForm');
    if (form) {
        form.reset();
    }

    modal.style.display = 'flex';
}

/**
 * Close custom technique creator modal
 */
function closeCreateTechniqueModal() {
    const modal = document.getElementById('createTechniqueModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Setup filter tab functionality
 */
function setupFilterTabs(containerId, displayFunction) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const tabs = container.querySelectorAll('.filter-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active from all tabs
            tabs.forEach(t => t.classList.remove('active'));

            // Add active to clicked tab
            tab.classList.add('active');

            // Get filter value and display
            const filter = tab.getAttribute('data-filter');
            displayFunction(filter);
        });
    });
}
