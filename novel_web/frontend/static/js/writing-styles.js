/**
 * Writing Styles Management
 * Handles UI for 5-layer prompt architecture integration
 */

// Global state
let allStyles = [];
let currentProject = null;
let allTechniques = [];  // Initialize techniques array

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

        // Show target locale badge if set
        if (style.target_locale) {
            const localeBadge = document.createElement('span');
            localeBadge.className = 'badge badge-locale';
            localeBadge.textContent = `🌐 ${style.target_locale}`;
            localeBadge.title = `This style generates content in ${style.target_locale}, overriding your UI language`;
            header.appendChild(localeBadge);
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

// ========================================
// Writing Sample Analysis Functions
// ========================================

/**
 * Open analyze writing sample modal
 */
function openAnalyzeSampleModal() {
    const modal = document.getElementById('analyzeSampleModal');
    if (!modal) {
        console.error('Analyze sample modal not found');
        return;
    }

    // Reset form
    document.getElementById('writingSampleText').value = '';
    document.getElementById('sampleCharCount').textContent = '0';
    document.getElementById('sampleWordCount').textContent = '0';
    document.getElementById('analysisResults').style.display = 'none';

    // Add input listener for character/word count
    const textarea = document.getElementById('writingSampleText');
    textarea.addEventListener('input', updateSampleCounts);

    modal.style.display = 'flex';
}

/**
 * Close analyze writing sample modal
 */
function closeAnalyzeSampleModal() {
    const modal = document.getElementById('analyzeSampleModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Update character and word counts for sample text
 */
function updateSampleCounts() {
    const textarea = document.getElementById('writingSampleText');
    const text = textarea.value;

    // Update character count
    document.getElementById('sampleCharCount').textContent = text.length;

    // Update word count (use same logic as backend)
    const cjkPattern = /[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]/g;
    const cjkChars = text.match(cjkPattern);
    let wordCount;
    if (cjkChars) {
        wordCount = cjkChars.length;
    } else {
        wordCount = text.trim().split(/\s+/).filter(word => word.length > 0).length;
    }
    document.getElementById('sampleWordCount').textContent = wordCount;
}

/**
 * Analyze writing sample using AI
 */
async function analyzeSample() {
    const sampleText = document.getElementById('writingSampleText').value.trim();

    if (!sampleText) {
        showToast('Please enter a writing sample', 'error');
        return;
    }

    const btn = document.getElementById('analyzeSampleBtn');
    btn.disabled = true;
    btn.textContent = 'Analyzing...';

    try {
        showLoading('Analyzing writing sample with AI...');
        const response = await apiRequest('/api/analyze-writing-sample/', {
            method: 'POST',
            body: JSON.stringify({ sample_text: sampleText })
        });
        hideLoading();

        // Display results
        displayAnalysisResults(response);

        btn.disabled = false;
        btn.textContent = 'Analyze Sample';
        showToast('Analysis complete!', 'success');

    } catch (error) {
        hideLoading();
        btn.disabled = false;
        btn.textContent = 'Analyze Sample';
        console.error('Analysis error:', error);
        showToast('Failed to analyze sample: ' + (error.message || 'Unknown error'), 'error');
    }
}

/**
 * Display analysis results in the form
 */
function displayAnalysisResults(data) {
    // Show results section
    document.getElementById('analysisResults').style.display = 'block';

    // Display detected language
    document.getElementById('detectedLanguage').textContent = data.detected_language || 'Unknown';
    document.getElementById('detectedLocale').textContent = `🌐 ${data.detected_locale}`;

    // Populate form fields with analyzed data
    document.getElementById('analyzed_pacing').value = data.pacing || 'medium';
    document.getElementById('analyzed_tone').value = data.tone || '';
    document.getElementById('analyzed_paragraph_length').value = data.paragraph_length || 'medium';
    document.getElementById('analyzed_dialogue_ratio').value = data.dialogue_ratio || 'medium';
    document.getElementById('analyzed_instructions').value = data.instructions || '';
    document.getElementById('analyzed_target_locale').value = data.detected_locale || '';

    // Scroll to results
    document.getElementById('analysisResults').scrollIntoView({ behavior: 'smooth' });
}

/**
 * Save writing style from analysis results
 */
async function saveStyleFromAnalysis(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);

    // Build WritingStyle creation data
    const data = {
        name_key: document.getElementById('analyzed_style_name_key').value,
        pacing: document.getElementById('analyzed_pacing').value,
        tone: document.getElementById('analyzed_tone').value,
        paragraph_length: document.getElementById('analyzed_paragraph_length').value,
        dialogue_ratio: document.getElementById('analyzed_dialogue_ratio').value,
        target_locale: document.getElementById('analyzed_target_locale').value,
        cliffhanger_enabled: false,
        public: false,
        translations: [
            {
                language_code: 'en',
                name: document.getElementById('analyzed_style_display_name').value,
                description: `Custom style created from writing sample analysis`,
                instructions: document.getElementById('analyzed_instructions').value
            }
        ]
    };

    try {
        showLoading('Creating custom writing style...');
        const newStyle = await apiRequest('/api/writing-styles/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        hideLoading();

        // Add to local cache
        allStyles.push(newStyle);

        showToast(`Custom style "${data.translations[0].name}" created successfully!`, 'success');
        closeAnalyzeSampleModal();

        // Refresh any style dropdowns on the page
        if (document.getElementById('styleSelect')) {
            populateStyleSelect('styleSelect', true, 'Select a style...');
        }

    } catch (error) {
        hideLoading();
        console.error('Error creating style:', error);
        showToast('Error creating style: ' + (error.message || 'Unknown error'), 'error');
    }
}

// ========================================
// SIMPLIFIED CUSTOM STYLE CREATOR
// ========================================

// Store analysis results temporarily
let tempAnalysisResults = null;

/**
 * Open the simplified custom style creator modal
 */
function openSimpleStyleCreator() {
    const modal = document.getElementById('simpleStyleCreatorModal');
    if (modal) {
        modal.style.display = 'flex';
        resetSimpleStyleCreator();

        // Add word count listener
        const textarea = document.getElementById('customStyleSample');
        const wordCountSpan = document.getElementById('customStyleWordCount');

        if (textarea && wordCountSpan) {
            textarea.addEventListener('input', function() {
                const text = this.value.trim();
                const wordCount = text ? text.split(/\s+/).length : 0;
                wordCountSpan.textContent = wordCount;
            });
        }
    }
}

/**
 * Close the simplified custom style creator modal
 */
function closeSimpleStyleCreator() {
    const modal = document.getElementById('simpleStyleCreatorModal');
    if (modal) {
        modal.style.display = 'none';
        resetSimpleStyleCreator();
    }
}

/**
 * Reset the modal to initial state
 */
function resetSimpleStyleCreator() {
    // Reset input step
    const textarea = document.getElementById('customStyleSample');
    const wordCount = document.getElementById('customStyleWordCount');
    if (textarea) textarea.value = '';
    if (wordCount) wordCount.textContent = '0';

    // Hide results, show input
    document.getElementById('sampleInputStep').style.display = 'block';
    document.getElementById('styleResultsStep').style.display = 'none';

    // Clear temp results
    tempAnalysisResults = null;
}

/**
 * Analyze sample text and create custom style using the simplified API
 */
async function analyzeAndCreateStyle() {
    const textarea = document.getElementById('customStyleSample');
    const sampleText = textarea.value.trim();

    if (!sampleText) {
        showToast('Please paste a writing sample', 'error');
        return;
    }

    const analyzeBtn = document.getElementById('analyzeSimpleBtn');
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyzing...';

    try {
        showLoading('Analyzing your writing sample with AI...');

        // Call the simplified API endpoint
        const response = await apiRequest('/api/analyze-simple-style/', {
            method: 'POST',
            body: JSON.stringify({
                sample_text: sampleText
            })
        });

        hideLoading();

        // Store results
        tempAnalysisResults = response;

        // Display results
        document.getElementById('resultStyleName').textContent = response.style_name || 'N/A';
        document.getElementById('resultLanguageCode').textContent = response.language_code || 'N/A';
        document.getElementById('resultStyleInstruction').textContent = response.style_instruction || 'N/A';
        document.getElementById('resultAgentRoleName').textContent = response.agent_role_name || 'N/A';
        document.getElementById('resultAgentRoleInstruction').textContent = response.agent_role_instruction || 'N/A';
        document.getElementById('resultSample').textContent = response.first_100_words || 'N/A';

        // Switch to results view
        document.getElementById('sampleInputStep').style.display = 'none';
        document.getElementById('styleResultsStep').style.display = 'block';

        showToast('Writing style analyzed successfully!', 'success');

    } catch (error) {
        hideLoading();
        console.error('Error analyzing sample:', error);
        showToast('Error analyzing sample: ' + (error.message || 'Unknown error'), 'error');
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Analyze & Create Style';
    }
}

/**
 * Save the analyzed custom style to the database
 */
async function saveCustomStyle() {
    if (!tempAnalysisResults) {
        showToast('No analysis results to save', 'error');
        return;
    }

    try {
        showLoading('Saving custom style and agent role...');

        // Step 1: Create CustomWritingStyle first
        const styleResponse = await apiRequest('/api/custom-writing-styles/', {
            method: 'POST',
            body: JSON.stringify({
                language_code: tempAnalysisResults.language_code,
                style_name: tempAnalysisResults.style_name,
                style_instruction: tempAnalysisResults.style_instruction,
                sample: tempAnalysisResults.first_100_words
            })
        });

        // Step 2: Create CustomAgentRole linked to the style
        await apiRequest('/api/custom-agent-roles/', {
            method: 'POST',
            body: JSON.stringify({
                language_code: tempAnalysisResults.language_code,
                role_name: tempAnalysisResults.agent_role_name,
                role_instruction: tempAnalysisResults.agent_role_instruction,
                custom_style: styleResponse.id  // Link via FK
            })
        });

        hideLoading();
        closeSimpleStyleCreator();

        // Reload custom styles dropdown with a small delay to ensure DOM is ready
        setTimeout(function() {
            const select = document.getElementById('customStyleSelect');
            if (select) {
                loadCustomStyles();
            }
        }, 100);

        showToast('Custom style and agent role saved successfully!', 'success');

    } catch (error) {
        hideLoading();
        console.error('Error saving custom style and agent role:', error);
        showToast('Error saving: ' + (error.message || 'Unknown error'), 'error');
    }
}

/**
 * Load custom styles and populate the dropdown
 */
async function loadCustomStyles() {
    console.log('[DEBUG] loadCustomStyles() called');
    const select = document.getElementById('customStyleSelect');
    console.log('[DEBUG] customStyleSelect element:', select);

    if (!select) {
        console.log('[DEBUG] customStyleSelect not found, returning');
        return;
    }

    try {
        console.log('[DEBUG] Fetching custom writing styles from API...');
        const response = await apiRequest('/api/custom-writing-styles/');
        console.log('[DEBUG] API response received:', response);

        // Clear existing options
        select.innerHTML = '';

        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Select a custom style...';
        select.appendChild(defaultOption);

        // Add custom style options
        // Handle paginated response (response.results is the actual array)
        const styles = response.results || response;
        if (styles && styles.length > 0) {
            console.log(`[DEBUG] Adding ${styles.length} custom style(s) to dropdown`);
            styles.forEach(style => {
                const option = document.createElement('option');
                option.value = style.id;
                option.textContent = `${style.style_name} (${style.language_code})`;

                // Store style instruction
                option.dataset.styleInstruction = style.style_instruction || '';
                option.dataset.languageCode = style.language_code;

                // Store generation parameters
                option.dataset.temperature = style.temperature !== undefined ? style.temperature : '0.7';
                option.dataset.topP = style.top_p !== undefined ? style.top_p : '1.0';

                // Store agent role data (if exists)
                if (style.custom_agent_role) {
                    option.dataset.agentRoleId = style.custom_agent_role.id;  // Critical: needed for updating
                    option.dataset.agentRoleName = style.custom_agent_role.role_name || '';
                    option.dataset.agentRoleInstruction = style.custom_agent_role.role_instruction || '';
                } else {
                    option.dataset.agentRoleId = '';
                    option.dataset.agentRoleName = '';
                    option.dataset.agentRoleInstruction = '';
                }

                select.appendChild(option);
            });
            console.log('[DEBUG] Custom styles successfully added to dropdown');
        } else {
            console.log('[DEBUG] No custom styles found, showing "create" message');
            const noStylesOption = document.createElement('option');
            noStylesOption.value = '';
            noStylesOption.textContent = 'No custom styles yet - create one below';
            select.appendChild(noStylesOption);
        }

    } catch (error) {
        console.error('[ERROR] Failed to load custom styles:', error);
        select.innerHTML = '<option value="">Error loading styles</option>';
    }
}

/**
 * Handle custom style selection
 * @param {boolean} updateSliders - If true, update temperature/top_p sliders with style defaults.
 *                                   Set to false when programmatically loading to preserve actual values.
 */
function selectCustomStyle(updateSliders = true) {
    const select = document.getElementById('customStyleSelect');
    if (!select) return;

    const selectedOption = select.options[select.selectedIndex];
    const styleId = select.value;

    // Get display elements
    const detailsDiv = document.getElementById('customStyleDetails');
    const agentRoleDisplay = document.getElementById('customAgentRoleDisplay');
    const styleInstructionDisplay = document.getElementById('customStyleInstructionDisplay');

    if (styleId && selectedOption) {
        // Store the selected custom style ID on the project
        // This will be used when generating content
        console.log('Selected custom style:', {
            id: styleId,
            name: selectedOption.textContent,
            instruction: selectedOption.dataset.styleInstruction,
            languageCode: selectedOption.dataset.languageCode,
            agentRoleName: selectedOption.dataset.agentRoleName,
            agentRoleInstruction: selectedOption.dataset.agentRoleInstruction
        });

        // Show the details div
        if (detailsDiv) {
            detailsDiv.style.display = 'block';
        }

        // Populate agent role textarea
        if (agentRoleDisplay) {
            const agentRoleText = selectedOption.dataset.agentRoleInstruction || 'No agent role defined for this style';
            agentRoleDisplay.value = agentRoleText;
        }

        // Populate style instruction textarea
        if (styleInstructionDisplay) {
            const styleInstructionText = selectedOption.dataset.styleInstruction || '';
            styleInstructionDisplay.value = styleInstructionText;
        }

        // Update temperature and top_p sliders with style-specific values
        // Only update if explicitly requested (e.g., user manually changing dropdown)
        // Skip when programmatically loading to preserve actual values from ContentPiece
        if (updateSliders) {
            const temperature = selectedOption.dataset.temperature;
            const topP = selectedOption.dataset.topP;

            if (temperature !== undefined) {
                const temperatureSlider = document.getElementById('temperatureSlider');
                const temperatureValue = document.getElementById('temperatureValue');
                if (temperatureSlider) {
                    temperatureSlider.value = parseFloat(temperature);
                    if (temperatureValue) {
                        temperatureValue.textContent = parseFloat(temperature).toFixed(1);
                    }
                }
            }

            if (topP !== undefined) {
                const topPSlider = document.getElementById('topPSlider');
                const topPValue = document.getElementById('topPValue');
                if (topPSlider) {
                    topPSlider.value = parseFloat(topP);
                    if (topPValue) {
                        topPValue.textContent = parseFloat(topP).toFixed(1);
                    }
                }
            }
        }

        // Save selection to localStorage or make API call to update project
        localStorage.setItem(`project_${PROJECT_ID}_custom_style`, styleId);
        showToast('Custom style selected: ' + selectedOption.textContent, 'success');
    } else {
        // Hide details div when no style is selected
        if (detailsDiv) {
            detailsDiv.style.display = 'none';
        }
    }
}

/**
 * Enable edit mode for custom style instructions
 */
function enableEditMode() {
    const agentRoleTextarea = document.getElementById('customAgentRoleDisplay');
    const styleInstructionTextarea = document.getElementById('customStyleInstructionDisplay');
    const editModeBtn = document.getElementById('editModeBtn');
    const editModeButtons = document.getElementById('editModeButtons');

    if (!agentRoleTextarea || !styleInstructionTextarea) return;

    // Remove readonly attribute
    agentRoleTextarea.removeAttribute('readonly');
    styleInstructionTextarea.removeAttribute('readonly');

    // Change background to white to indicate editable
    agentRoleTextarea.style.backgroundColor = '#FFFFFF';
    styleInstructionTextarea.style.backgroundColor = '#FFFFFF';

    // Store original values for cancel functionality
    agentRoleTextarea.dataset.originalValue = agentRoleTextarea.value;
    styleInstructionTextarea.dataset.originalValue = styleInstructionTextarea.value;

    // Show save/cancel buttons, hide edit button
    if (editModeButtons) editModeButtons.style.display = 'block';
    if (editModeBtn) editModeBtn.style.display = 'none';

    console.log('[DEBUG] Edit mode enabled');
}

/**
 * Disable edit mode and return to readonly state
 */
function disableEditMode() {
    const agentRoleTextarea = document.getElementById('customAgentRoleDisplay');
    const styleInstructionTextarea = document.getElementById('customStyleInstructionDisplay');
    const editModeBtn = document.getElementById('editModeBtn');
    const editModeButtons = document.getElementById('editModeButtons');

    if (!agentRoleTextarea || !styleInstructionTextarea) return;

    // Add readonly attribute back
    agentRoleTextarea.setAttribute('readonly', 'readonly');
    styleInstructionTextarea.setAttribute('readonly', 'readonly');

    // Change background back to gray
    agentRoleTextarea.style.backgroundColor = '#F9FAFB';
    styleInstructionTextarea.style.backgroundColor = '#F9FAFB';

    // Hide save/cancel buttons, show edit button
    if (editModeButtons) editModeButtons.style.display = 'none';
    if (editModeBtn) editModeBtn.style.display = 'block';

    console.log('[DEBUG] Edit mode disabled');
}

/**
 * Cancel edit mode and restore original values
 */
function cancelEditMode() {
    const agentRoleTextarea = document.getElementById('customAgentRoleDisplay');
    const styleInstructionTextarea = document.getElementById('customStyleInstructionDisplay');

    if (!agentRoleTextarea || !styleInstructionTextarea) return;

    // Restore original values
    agentRoleTextarea.value = agentRoleTextarea.dataset.originalValue || '';
    styleInstructionTextarea.value = styleInstructionTextarea.dataset.originalValue || '';

    // Exit edit mode
    disableEditMode();

    console.log('[DEBUG] Edit cancelled, original values restored');
}

/**
 * Save changes to custom style and agent role instructions
 */
async function saveCustomStyleChanges() {
    const select = document.getElementById('customStyleSelect');
    if (!select) return;

    const selectedOption = select.options[select.selectedIndex];
    const styleId = select.value;

    if (!styleId) {
        showToast('No style selected', 'error');
        return;
    }

    const agentRoleTextarea = document.getElementById('customAgentRoleDisplay');
    const styleInstructionTextarea = document.getElementById('customStyleInstructionDisplay');

    const newAgentRoleInstruction = agentRoleTextarea.value.trim();
    const newStyleInstruction = styleInstructionTextarea.value.trim();

    // Validation
    if (newStyleInstruction.length < 10) {
        showToast('Style instruction must be at least 10 characters', 'error');
        return;
    }

    if (newAgentRoleInstruction.length < 10) {
        showToast('Agent role instruction must be at least 10 characters', 'error');
        return;
    }

    try {
        showLoading('Saving changes...');

        // Update CustomWritingStyle
        await apiRequest(`/api/custom-writing-styles/${styleId}/`, {
            method: 'PATCH',
            body: JSON.stringify({
                style_instruction: newStyleInstruction
            })
        });

        console.log('[DEBUG] Style instruction updated successfully');

        // Get agent role ID from dataset
        const agentRoleId = selectedOption.dataset.agentRoleId;

        if (agentRoleId) {
            // Update CustomAgentRole
            await apiRequest(`/api/custom-agent-roles/${agentRoleId}/`, {
                method: 'PATCH',
                body: JSON.stringify({
                    role_instruction: newAgentRoleInstruction
                })
            });
            console.log('[DEBUG] Agent role instruction updated successfully');
        } else {
            console.warn('[WARN] No agent role ID found, only style updated');
        }

        hideLoading();

        // Update dataset with new values so they persist in dropdown
        selectedOption.dataset.styleInstruction = newStyleInstruction;
        selectedOption.dataset.agentRoleInstruction = newAgentRoleInstruction;

        // Update original values for future edits
        agentRoleTextarea.dataset.originalValue = newAgentRoleInstruction;
        styleInstructionTextarea.dataset.originalValue = newStyleInstruction;

        // Exit edit mode
        disableEditMode();

        showToast('Changes saved successfully!', 'success');

    } catch (error) {
        hideLoading();
        console.error('[ERROR] Failed to save changes:', error);
        showToast('Error saving changes: ' + (error.message || 'Unknown error'), 'error');
    }
}

// Load custom styles on page load if the dropdown exists
document.addEventListener('DOMContentLoaded', function() {
    console.log('[DEBUG] DOMContentLoaded fired in writing-styles.js');
    const customStyleSelect = document.getElementById('customStyleSelect');
    console.log('[DEBUG] Checking for customStyleSelect element:', customStyleSelect);

    if (customStyleSelect) {
        console.log('[DEBUG] customStyleSelect found, calling loadCustomStyles()');
        loadCustomStyles();
    } else {
        console.log('[DEBUG] customStyleSelect not found, skipping loadCustomStyles()');
    }
});
