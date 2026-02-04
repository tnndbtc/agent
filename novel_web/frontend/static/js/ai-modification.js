// AI Text Modification Module
// Handles text selection and AI-powered modification with custom prompts

// Global state for text selection
let currentSelection = {
    text: '',
    range: null,
    containerElement: null,
    contentType: 'text',
    isTextarea: false,
    textareaStart: null,
    textareaEnd: null
};

// Cache for preset and saved prompts
let presetPrompts = [];
let savedPrompts = [];

// Initialize AI modification functionality
function initAIModification() {
    console.log('Initializing AI modification functionality');

    // Load preset prompts
    loadPresetPrompts();

    // Load user's saved prompts
    loadSavedPrompts();

    // Add global mouseup listener for text selection
    document.addEventListener('mouseup', handleTextSelection);

    // Add click listener to close modal when clicking outside
    document.addEventListener('click', handleOutsideClick);
}

// Enable text selection on a specific element
function enableTextSelection(elementId, contentType) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.warn(`Element ${elementId} not found for text selection`);
        return;
    }

    // Mark the element as selectable
    element.setAttribute('data-ai-selectable', 'true');
    element.setAttribute('data-content-type', contentType);
    element.style.cursor = 'text';
    element.style.userSelect = 'text';

    console.log(`Enabled text selection on ${elementId} (${contentType})`);
}

// Handle text selection
function handleTextSelection(event) {
    // Check if this is a textarea or input element
    const target = event.target;
    const isTextarea = target.tagName === 'TEXTAREA' || target.tagName === 'INPUT';

    if (isTextarea && target.hasAttribute('data-ai-selectable')) {
        // Handle textarea selection
        const start = target.selectionStart;
        const end = target.selectionEnd;
        const selectedText = target.value.substring(start, end).trim();

        if (!selectedText) {
            return;
        }

        // Store selection information for textarea
        currentSelection = {
            text: selectedText,
            range: null,
            containerElement: target,
            contentType: target.getAttribute('data-content-type') || 'text',
            isTextarea: true,
            textareaStart: start,
            textareaEnd: end
        };

        console.log('Textarea text selected:', {
            text: selectedText.substring(0, 50) + '...',
            contentType: currentSelection.contentType,
            element: target.id,
            start: start,
            end: end
        });

        // Show the AI modification modal - DISABLED: Now requires clicking "AI Modify" button
        // showAIModificationModal();
        return;
    }

    // Handle regular text selection (non-textarea)
    const selection = window.getSelection();
    const selectedText = selection.toString().trim();

    if (!selectedText) {
        return;
    }

    // Check if the selection is within a selectable element
    const range = selection.getRangeAt(0);
    let containerElement = range.commonAncestorContainer;

    // If the container is a text node, get its parent element
    if (containerElement.nodeType === Node.TEXT_NODE) {
        containerElement = containerElement.parentElement;
    }

    // Find the closest selectable element
    const selectableElement = containerElement.closest('[data-ai-selectable="true"]');

    if (!selectableElement) {
        return;
    }

    // Store selection information for regular text
    currentSelection = {
        text: selectedText,
        range: range.cloneRange(),
        containerElement: selectableElement,
        contentType: selectableElement.getAttribute('data-content-type') || 'text',
        isTextarea: false,
        textareaStart: null,
        textareaEnd: null
    };

    console.log('Text selected:', {
        text: selectedText.substring(0, 50) + '...',
        contentType: currentSelection.contentType,
        element: selectableElement.id
    });

    // Show the AI modification modal - DISABLED: Now requires clicking "AI Modify" button
    // showAIModificationModal();
}

// Global function to show AI modification dialog (called by "AI Modify" button)
window.showAIModificationDialog = function() {
    if (!currentSelection.text) {
        showToast(gettext('Please select some text first'), 'warning');
        return;
    }
    console.log('Showing AI modification dialog via button click');
    showAIModificationModal();
};

// Load preset prompts from API
async function loadPresetPrompts() {
    try {
        const response = await apiRequest('/api/ai-modifications/preset-prompts/');
        presetPrompts = response;
        console.log('Loaded preset prompts:', presetPrompts);
    } catch (error) {
        console.error('Failed to load preset prompts:', error);
        // Use fallback presets
        presetPrompts = [
            { id: 'dramatic', name: 'Make more dramatic', prompt: 'Rewrite this text to be more dramatic and emotionally intense while maintaining the core meaning.' },
            { id: 'simplify', name: 'Simplify language', prompt: 'Simplify the language in this text to make it clearer and easier to understand.' },
            { id: 'detail', name: 'Add more detail', prompt: 'Expand this text with more vivid details and sensory descriptions.' },
        ];
    }
}

// Load user's saved prompts from API
async function loadSavedPrompts() {
    try {
        const response = await apiRequest('/api/user-prompts/');
        savedPrompts = response;
        console.log('Loaded saved prompts:', savedPrompts);
    } catch (error) {
        console.error('Failed to load saved prompts:', error);
        savedPrompts = [];
    }
}

// Show the AI modification modal
function showAIModificationModal() {
    // Remove existing modal if present
    const existingModal = document.getElementById('aiModificationModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Create modal HTML
    const modalHTML = `
        <div id="aiModificationModal" class="modal-overlay" style="
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        ">
            <div class="modal-content" style="
                background: white;
                border-radius: 8px;
                padding: 24px;
                max-width: 600px;
                width: 90%;
                max-height: 90vh;
                overflow-y: auto;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            ">
                <div class="modal-header" style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 16px;
                ">
                    <h3 style="margin: 0; font-size: 1.25rem; font-weight: 600;">AI Text Modification</h3>
                    <button onclick="closeAIModificationModal()" style="
                        background: none;
                        border: none;
                        font-size: 1.5rem;
                        cursor: pointer;
                        color: #666;
                    ">&times;</button>
                </div>

                <div class="modal-body">
                    <!-- Selected text preview -->
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; font-weight: 600; margin-bottom: 4px;">Selected Text:</label>
                        <div style="
                            background: #f3f4f6;
                            border: 1px solid #e5e7eb;
                            border-radius: 4px;
                            padding: 8px;
                            max-height: 100px;
                            overflow-y: auto;
                            font-size: 0.875rem;
                        ">${escapeHtml(currentSelection.text)}</div>
                    </div>

                    <!-- Generation Parameters -->
                    <div style="margin-bottom: 16px; padding: 12px; background: #f9fafb; border-radius: 6px; border: 1px solid #e5e7eb;">
                        <div style="font-weight: 600; margin-bottom: 12px; color: #374151;">Generation Parameters</div>

                        <!-- Temperature Slider -->
                        <div style="margin-bottom: 1.5rem;">
                            <div style="font-weight: 600; color: #374151; margin-bottom: 0.75rem; font-size: 0.95rem;">
                                ${gettext("How Adventurous The Writing Is")}
                            </div>

                            <!-- Contextual labels above slider -->
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem; font-size: 0.7rem; color: #9ca3af;">
                                <span style="text-align: left; flex: 1;">
                                    ${gettext("Rigid/Over-controlled")}
                                </span>
                                <span style="text-align: center; flex: 1;">
                                    ${gettext("Natural/Human-like")}
                                </span>
                                <span style="text-align: right; flex: 1;">
                                    ${gettext("Wild/Chaotic")}
                                </span>
                            </div>

                            <!-- Current value display (centered and highlighted) -->
                            <div style="text-align: center; margin-bottom: 0.5rem;">
                                <span id="aiModTemperatureValue" style="display: inline-block; background-color: #3b82f6; color: white; padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: 600; font-size: 0.9rem; min-width: 3rem;">0.7</span>
                            </div>

                            <input type="range" id="aiModTemperatureSlider" min="0.0" max="1.2" step="0.1" value="0.7" style="width: 100%; cursor: pointer;" />
                        </div>

                        <!-- Top P Slider -->
                        <div style="margin-bottom: 1.5rem;">
                            <div style="font-weight: 600; color: #374151; margin-bottom: 0.75rem; font-size: 0.95rem;">
                                ${gettext("Word Choice")}
                            </div>

                            <!-- Contextual labels above slider -->
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem; font-size: 0.7rem; color: #9ca3af;">
                                <span style="text-align: left; flex: 1;">
                                    ${gettext("Narrow/Repetitive")}
                                </span>
                                <span style="text-align: center; flex: 1;">
                                    ${gettext("Balanced/Coherent")}
                                </span>
                                <span style="text-align: right; flex: 1;">
                                    ${gettext("Loose/Many rare words")}
                                </span>
                            </div>

                            <!-- Current value display (centered and highlighted) -->
                            <div style="text-align: center; margin-bottom: 0.5rem;">
                                <span id="aiModTopPValue" style="display: inline-block; background-color: #10b981; color: white; padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: 600; font-size: 0.9rem; min-width: 3rem;">1.0</span>
                            </div>

                            <input type="range" id="aiModTopPSlider" min="0.3" max="1.0" step="0.1" value="1.0" style="width: 100%; cursor: pointer;" />
                        </div>

                        <!-- Model Selector -->
                        <div>
                            <div style="font-weight: 600; color: #374151; margin-bottom: 0.75rem; font-size: 0.95rem;">
                                ${gettext("AI Model")}
                            </div>
                            <div style="text-align: center; margin-bottom: 0.5rem;">
                                <span id="aiModModelValue" style="display: inline-block; background-color: #8b5cf6; color: white; padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: 600; font-size: 0.9rem; min-width: 8rem;">gpt-5.2</span>
                            </div>
                            <select id="aiModModelSelector" style="width: 100%; padding: 0.5rem; border: 1px solid #d1d5db; border-radius: 0.375rem; cursor: pointer; font-size: 0.9rem;">
                                <option value="gpt-4o-mini">gpt-4o-mini</option>
                                <option value="gpt-5.2" selected>gpt-5.2</option>
                            </select>
                        </div>
                    </div>

                    <!-- Saved prompts dropdown -->
                    ${savedPrompts.length > 0 ? `
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; font-weight: 600; margin-bottom: 4px;">Saved Prompts:</label>
                        <select id="savedPromptSelect" onchange="selectSavedPrompt()" style="
                            width: 100%;
                            padding: 8px;
                            border: 1px solid #d1d5db;
                            border-radius: 4px;
                        ">
                            <option value="">-- Select a saved prompt --</option>
                            ${savedPrompts.map(sp => `
                                <option value="${sp.id}">${sp.name} (used ${sp.usage_count} times)</option>
                            `).join('')}
                        </select>
                    </div>
                    ` : ''}

                    <!-- Custom prompt textarea -->
                    <div style="margin-bottom: 16px;">
                        <label for="customPrompt" style="display: block; font-weight: 600; margin-bottom: 4px;">
                            Custom Prompt:
                        </label>
                        <textarea id="customPrompt" rows="3" style="
                            width: 100%;
                            padding: 8px;
                            border: 1px solid #d1d5db;
                            border-radius: 4px;
                            font-family: inherit;
                            resize: vertical;
                        " placeholder="Enter your modification instructions..."></textarea>
                    </div>

                    <!-- Preview section (hidden by default) -->
                    <div id="aiModificationPreview" style="display: none; margin-bottom: 16px; padding: 16px; background: #f9fafb; border-radius: 6px; border: 1px solid #e5e7eb;">
                        <label for="previewText" style="display: block; font-weight: 600; margin-bottom: 8px; color: #374151;">
                            Preview Modified Text (editable):
                        </label>
                        <textarea id="previewText" rows="8" style="
                            width: 100%;
                            padding: 8px;
                            border: 1px solid #d1d5db;
                            border-radius: 4px;
                            font-family: inherit;
                            resize: vertical;
                            background: white;
                        "></textarea>

                        <!-- Preview action buttons -->
                        <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top: 12px;">
                            <button onclick="cancelPreview()" style="
                                background: #e5e7eb;
                                color: #374151;
                                border: none;
                                padding: 8px 16px;
                                border-radius: 4px;
                                cursor: pointer;
                            " onmouseover="this.style.background='#d1d5db'"
                               onmouseout="this.style.background='#e5e7eb'">Cancel</button>
                            <button id="acceptButton" onclick="acceptModification()" disabled style="
                                background: #9ca3af;
                                color: white;
                                border: none;
                                padding: 8px 16px;
                                border-radius: 4px;
                                cursor: not-allowed;
                                font-weight: 600;
                            ">Accept</button>
                        </div>
                    </div>

                    <!-- Progress bar (hidden by default) -->
                    <div id="aiModProgressContainer" style="display: none; margin-bottom: 16px;">
                        <div style="width: 100%; height: 30px; background: #e5e7eb; border-radius: 15px; overflow: hidden; position: relative;">
                            <div id="aiModProgressBarFill" style="height: 100%; background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%); width: 0%; display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; font-size: 0.875rem; transition: width 0.3s ease; border-radius: 15px;">0%</div>
                        </div>
                        <div id="aiModProgressText" style="margin-top: 0.5rem; text-align: center; font-size: 0.875rem; color: #6b7280;">Processing with AI...</div>
                    </div>

                    <!-- Action buttons -->
                    <div style="display: flex; gap: 8px; justify-content: flex-end;">
                        <button onclick="closeAIModificationModal()" style="
                            background: #e5e7eb;
                            color: #374151;
                            border: none;
                            padding: 8px 16px;
                            border-radius: 4px;
                            cursor: pointer;
                        " onmouseover="this.style.background='#d1d5db'"
                           onmouseout="this.style.background='#e5e7eb'">Cancel</button>
                        <button id="applyModificationButton" onclick="applyAIModification()" style="
                            background: #10b981;
                            color: white;
                            border: none;
                            padding: 8px 16px;
                            border-radius: 4px;
                            cursor: pointer;
                            font-weight: 600;
                        " onmouseover="this.style.background='#059669'"
                           onmouseout="this.style.background='#10b981'">Apply Modification</button>
                    </div>

                    <!-- Status message -->
                    <div id="aiModificationStatus" style="margin-top: 16px; display: none;"></div>
                </div>
            </div>
        </div>
    `;

    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // Add event handlers for generation parameter controls
    const aiModTemperatureSlider = document.getElementById('aiModTemperatureSlider');
    const aiModTemperatureValue = document.getElementById('aiModTemperatureValue');
    const aiModTopPSlider = document.getElementById('aiModTopPSlider');
    const aiModTopPValue = document.getElementById('aiModTopPValue');
    const aiModModelSelector = document.getElementById('aiModModelSelector');
    const aiModModelValue = document.getElementById('aiModModelValue');

    if (aiModTemperatureSlider && aiModTemperatureValue) {
        aiModTemperatureSlider.addEventListener('input', function() {
            aiModTemperatureValue.textContent = parseFloat(this.value).toFixed(1);
        });
    }

    if (aiModTopPSlider && aiModTopPValue) {
        aiModTopPSlider.addEventListener('input', function() {
            aiModTopPValue.textContent = parseFloat(this.value).toFixed(1);
        });
    }

    if (aiModModelSelector && aiModModelValue) {
        aiModModelSelector.addEventListener('change', function() {
            aiModModelValue.textContent = this.value;
        });
    }

    // Add event listener to preview textarea to update Accept button state
    const previewTextarea = document.getElementById('previewText');
    if (previewTextarea) {
        previewTextarea.addEventListener('input', updateAcceptButtonState);
    }

    // Focus on the custom prompt textarea
    document.getElementById('customPrompt').focus();
}

// Close the AI modification modal
function closeAIModificationModal() {
    const modal = document.getElementById('aiModificationModal');
    if (modal) {
        modal.remove();
    }
    // Clear selection
    window.getSelection().removeAllRanges();
}

// Handle clicks outside the modal
function handleOutsideClick(event) {
    const modal = document.getElementById('aiModificationModal');
    if (modal && event.target === modal) {
        closeAIModificationModal();
    }
}

// Select a preset prompt
function selectPresetPrompt(presetId) {
    const preset = presetPrompts.find(p => p.id === presetId);
    if (preset) {
        document.getElementById('customPrompt').value = preset.prompt;
    }
}

// Select a saved prompt
function selectSavedPrompt() {
    const select = document.getElementById('savedPromptSelect');
    const promptId = select.value;

    if (!promptId) {
        document.getElementById('customPrompt').value = '';
        return;
    }

    const savedPrompt = savedPrompts.find(p => p.id === promptId);
    if (savedPrompt) {
        document.getElementById('customPrompt').value = savedPrompt.prompt_text;
    }
}

// Progress bar control variables
let aiModProgressInterval = null;
let aiModCurrentProgress = 0;

// Start progress bar animation
function startAIModProgressBar() {
    const progressContainer = document.getElementById('aiModProgressContainer');
    const progressBarFill = document.getElementById('aiModProgressBarFill');
    const applyButton = document.getElementById('applyModificationButton');

    if (progressContainer) {
        progressContainer.style.display = 'block';
        applyButton.disabled = true;
        applyButton.style.background = '#9ca3af';
        applyButton.style.cursor = 'not-allowed';
        aiModCurrentProgress = 0;

        // Increment 5% every 2 seconds, max 95%
        aiModProgressInterval = setInterval(() => {
            if (aiModCurrentProgress < 95) {
                aiModCurrentProgress += 5;
                if (aiModCurrentProgress > 95) aiModCurrentProgress = 95;
                progressBarFill.style.width = aiModCurrentProgress + '%';
                progressBarFill.textContent = Math.round(aiModCurrentProgress) + '%';
            }
        }, 2000);
    }
}

// Complete progress bar at 100%
function completeAIModProgressBar() {
    const progressBarFill = document.getElementById('aiModProgressBarFill');

    if (aiModProgressInterval) {
        clearInterval(aiModProgressInterval);
    }

    aiModCurrentProgress = 100;
    progressBarFill.style.width = '100%';
    progressBarFill.textContent = '100%';
}

// Reset and hide progress bar
function resetAIModProgressBar() {
    const progressContainer = document.getElementById('aiModProgressContainer');
    const progressBarFill = document.getElementById('aiModProgressBarFill');
    const applyButton = document.getElementById('applyModificationButton');

    if (aiModProgressInterval) {
        clearInterval(aiModProgressInterval);
    }

    if (progressContainer) {
        progressContainer.style.display = 'none';
        aiModCurrentProgress = 0;
        progressBarFill.style.width = '0%';
        progressBarFill.textContent = '0%';
        applyButton.disabled = false;
        applyButton.style.background = '#10b981';
        applyButton.style.cursor = 'pointer';
    }
}

// Apply AI modification
async function applyAIModification() {
    const customPrompt = document.getElementById('customPrompt').value.trim();
    const statusDiv = document.getElementById('aiModificationStatus');

    // Start progress bar
    startAIModProgressBar();
    statusDiv.style.display = 'none';  // Hide status message

    try {
        // Get generation parameters from modal
        const temperature = parseFloat(document.getElementById('aiModTemperatureSlider').value);
        const top_p = parseFloat(document.getElementById('aiModTopPSlider').value);
        const model = document.getElementById('aiModModelSelector').value;

        // Prepare request data
        const requestData = {
            original_text: currentSelection.text,
            user_prompt: customPrompt,
            content_type: currentSelection.contentType,
            temperature: temperature,
            top_p: top_p,
            model: model
        };

        // Log request data for debugging
        console.log('Sending AI modification request:', requestData);

        // Call API
        const response = await apiRequest('/api/ai-modifications/modify-text/', {
            method: 'POST',
            body: JSON.stringify(requestData)
        });

        console.log('AI modification response:', response);

        // Show token usage
        if (response.token_usage) {
            showTokenUsage(response.token_usage);
        }

        // Show preview section with modified text (form remains visible)
        const previewSection = document.getElementById('aiModificationPreview');
        const previewTextarea = document.getElementById('previewText');
        previewTextarea.value = response.modified_text;
        previewSection.style.display = 'block';

        // Auto-scroll to show the preview
        previewSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        // Enable Accept button since we have content
        updateAcceptButtonState();

        // Complete progress bar at 100%
        completeAIModProgressBar();

        // Reset progress bar after a brief delay
        setTimeout(() => {
            resetAIModProgressBar();
        }, 1000);

        // Show success status
        statusDiv.innerHTML = '<div style="color: #10b981; font-size: 0.875rem;">✅ Preview ready! You can edit the text before accepting.</div>';
        statusDiv.style.display = 'block';

    } catch (error) {
        // Reset progress bar on error
        resetAIModProgressBar();

        console.error('AI modification error:', error);

        // Show detailed error information
        let errorMessage = error.message || 'Request failed';

        // If error has field-specific errors, display them
        if (error.user_prompt || error.original_text || error.content_type) {
            const fieldErrors = [];
            if (error.user_prompt) fieldErrors.push(`Prompt: ${error.user_prompt}`);
            if (error.original_text) fieldErrors.push(`Text: ${error.original_text}`);
            if (error.content_type) fieldErrors.push(`Type: ${error.content_type}`);
            errorMessage = fieldErrors.join(', ');
        }

        statusDiv.innerHTML = `<div style="color: #dc2626; font-size: 0.875rem;">❌ Error: ${errorMessage}</div>`;
    }
}

// Update Accept button state based on preview content
function updateAcceptButtonState() {
    const previewTextarea = document.getElementById('previewText');
    const acceptButton = document.getElementById('acceptButton');

    if (!previewTextarea || !acceptButton) return;

    const hasContent = previewTextarea.value.trim().length > 0;

    if (hasContent) {
        // Enable button
        acceptButton.disabled = false;
        acceptButton.style.background = '#10b981';
        acceptButton.style.cursor = 'pointer';
        acceptButton.onmouseover = function() { this.style.background = '#059669'; };
        acceptButton.onmouseout = function() { this.style.background = '#10b981'; };
    } else {
        // Disable button
        acceptButton.disabled = true;
        acceptButton.style.background = '#9ca3af';
        acceptButton.style.cursor = 'not-allowed';
        acceptButton.onmouseover = null;
        acceptButton.onmouseout = null;
    }
}

// Cancel preview and return to form
function cancelPreview() {
    // Hide preview section
    document.getElementById('aiModificationPreview').style.display = 'none';

    // Clear status message
    const statusDiv = document.getElementById('aiModificationStatus');
    statusDiv.style.display = 'none';
    statusDiv.innerHTML = '';

    // Clear preview textarea
    document.getElementById('previewText').value = '';
}

// Accept modified text and replace in document
function acceptModification() {
    // Get the text from preview (user may have edited it)
    const modifiedText = document.getElementById('previewText').value;

    // Replace text in the document
    replaceSelectedText(modifiedText);

    // Close modal
    closeAIModificationModal();

    // Show success toast
    showToast('Text modified successfully!', 'success');
}

// Replace selected text in the document
function replaceSelectedText(newText) {
    // Handle textarea replacement
    if (currentSelection.isTextarea) {
        try {
            const textarea = currentSelection.containerElement;
            const start = currentSelection.textareaStart;
            const end = currentSelection.textareaEnd;

            // Replace the selected text in the textarea value
            const before = textarea.value.substring(0, start);
            const after = textarea.value.substring(end);
            textarea.value = before + newText + after;

            // Set cursor position after the new text
            const newCursorPos = start + newText.length;
            textarea.setSelectionRange(newCursorPos, newCursorPos);

            // Focus the textarea
            textarea.focus();

            // Trigger input event to update word count or other listeners
            textarea.dispatchEvent(new Event('input', { bubbles: true }));

            console.log('Textarea text replaced successfully');
            return;
        } catch (error) {
            console.error('Error replacing textarea text:', error);
            return;
        }
    }

    // Handle regular text replacement
    if (!currentSelection.range) {
        console.error('No selection range available');
        return;
    }

    try {
        // Delete the selected text
        currentSelection.range.deleteContents();

        // Insert the new text
        const textNode = document.createTextNode(newText);
        currentSelection.range.insertNode(textNode);

        // Clear the selection
        window.getSelection().removeAllRanges();

        console.log('Text replaced successfully');
    } catch (error) {
        console.error('Error replacing text:', error);
        // Fallback: try to replace in the container element
        try {
            const container = currentSelection.containerElement;
            const originalHTML = container.innerHTML;
            const updatedHTML = originalHTML.replace(currentSelection.text, newText);
            container.innerHTML = updatedHTML;
            console.log('Text replaced using fallback method');
        } catch (fallbackError) {
            console.error('Fallback replacement also failed:', fallbackError);
        }
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAIModification);
} else {
    initAIModification();
}
