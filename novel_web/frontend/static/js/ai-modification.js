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

        // Show the AI modification modal
        showAIModificationModal();
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

    // Show the AI modification modal
    showAIModificationModal();
}

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
                max-height: 80vh;
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

                    <!-- Preset prompts -->
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; font-weight: 600; margin-bottom: 8px;">Quick Presets:</label>
                        <div id="presetButtons" style="display: flex; flex-wrap: wrap; gap: 8px;">
                            ${presetPrompts.map(preset => `
                                <button onclick="selectPresetPrompt('${preset.id}')" style="
                                    background: #3b82f6;
                                    color: white;
                                    border: none;
                                    padding: 6px 12px;
                                    border-radius: 4px;
                                    cursor: pointer;
                                    font-size: 0.875rem;
                                " onmouseover="this.style.background='#2563eb'"
                                   onmouseout="this.style.background='#3b82f6'">${preset.name}</button>
                            `).join('')}
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

                    <!-- Save prompt checkbox -->
                    <div style="margin-bottom: 16px;">
                        <label style="display: flex; align-items: center; cursor: pointer;">
                            <input type="checkbox" id="savePromptCheckbox" onchange="togglePromptName()" style="margin-right: 8px;">
                            <span>Save this prompt for future use</span>
                        </label>
                        <input type="text" id="promptNameInput" placeholder="Enter a name for this prompt..." style="
                            width: 100%;
                            padding: 8px;
                            border: 1px solid #d1d5db;
                            border-radius: 4px;
                            margin-top: 8px;
                            display: none;
                        ">
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
                        <button onclick="applyAIModification()" style="
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

// Toggle prompt name input visibility
function togglePromptName() {
    const checkbox = document.getElementById('savePromptCheckbox');
    const nameInput = document.getElementById('promptNameInput');
    nameInput.style.display = checkbox.checked ? 'block' : 'none';
}

// Apply AI modification
async function applyAIModification() {
    const customPrompt = document.getElementById('customPrompt').value.trim();
    const savePrompt = document.getElementById('savePromptCheckbox').checked;
    const promptName = document.getElementById('promptNameInput').value.trim();
    const statusDiv = document.getElementById('aiModificationStatus');

    // Validation
    if (!customPrompt) {
        statusDiv.innerHTML = '<div style="color: #dc2626; font-size: 0.875rem;">Please enter a modification prompt.</div>';
        statusDiv.style.display = 'block';
        return;
    }

    if (savePrompt && !promptName) {
        statusDiv.innerHTML = '<div style="color: #dc2626; font-size: 0.875rem;">Please enter a name for the saved prompt.</div>';
        statusDiv.style.display = 'block';
        return;
    }

    // Show loading state
    statusDiv.innerHTML = '<div style="color: #3b82f6; font-size: 0.875rem;">⏳ Processing with AI...</div>';
    statusDiv.style.display = 'block';

    try {
        // Prepare request data
        const requestData = {
            original_text: currentSelection.text,
            user_prompt: customPrompt,
            content_type: currentSelection.contentType,
            save_prompt: savePrompt
        };

        if (savePrompt && promptName) {
            requestData.prompt_name = promptName;
        }

        // Call API
        const response = await apiRequest('/api/ai-modifications/modify-text/', {
            method: 'POST',
            body: JSON.stringify(requestData)
        });

        console.log('AI modification response:', response);

        // Replace text in the document
        replaceSelectedText(response.modified_text);

        // Show token usage
        if (response.token_usage) {
            showTokenUsage(response.token_usage);
        }

        // Show success message
        statusDiv.innerHTML = '<div style="color: #10b981; font-size: 0.875rem;">✅ Text modified successfully!</div>';

        // Close modal after a delay
        setTimeout(() => {
            closeAIModificationModal();
            showToast('Text modified successfully!', 'success');
        }, 1500);

        // Reload saved prompts if a new one was created
        if (savePrompt) {
            loadSavedPrompts();
        }

    } catch (error) {
        console.error('AI modification error:', error);
        statusDiv.innerHTML = `<div style="color: #dc2626; font-size: 0.875rem;">❌ Error: ${error.message}</div>`;
    }
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
