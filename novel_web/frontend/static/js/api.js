// API Client for Novel Writing Agent

// Get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// API Request wrapper
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        credentials: 'same-origin'
    };

    const mergedOptions = { ...defaultOptions, ...options };

    // Merge headers
    if (options.headers) {
        mergedOptions.headers = { ...defaultOptions.headers, ...options.headers };
    }

    try {
        const response = await fetch(url, mergedOptions);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Request failed' }));

            // For validation errors (400), throw the full error object to preserve field-specific errors
            if (response.status === 400 && (errorData.title || errorData.detail || errorData.error)) {
                const error = new Error(errorData.detail || errorData.error || 'Validation failed');
                // Attach the full error data for field-specific error handling
                Object.assign(error, errorData);
                throw error;
            }

            // For other errors, create simple error message
            throw new Error(errorData.error || errorData.detail || 'Request failed');
        }

        // Handle empty responses
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }

        return response;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// WebSocket connection for real-time updates
function connectToTask(taskId, apiType = null) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/generate/${taskId}/`;

    const socket = new WebSocket(wsUrl);
    let estimatedDuration = null;

    // Fetch estimated duration if apiType is provided
    if (apiType) {
        getEstimatedDuration(apiType).then(duration => {
            estimatedDuration = duration;
        });
    }

    socket.onopen = () => {
        console.log('WebSocket connected');
        showLoading('Processing...', 0, estimatedDuration);
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'progress') {
            // Check if task completed even in progress messages
            if (data.status === 'completed' || data.progress >= 100) {
                hideLoading();
                // Extract and display token usage if available
                if (data.result && data.result.token_usage) {
                    console.log('WebSocket progress - calling showTokenUsage with:', data.result.token_usage);
                    showTokenUsage(data.result.token_usage);
                }
                showToast('Task completed!', 'success');
                setTimeout(() => window.location.reload(), 1500);
            } else {
                showLoading(data.message || 'Processing...', data.progress, estimatedDuration);
            }
        } else if (data.type === 'complete') {
            hideLoading();
            // Extract and display token usage if available
            if (data.result && data.result.token_usage) {
                console.log('WebSocket complete - calling showTokenUsage with:', data.result.token_usage);
                showTokenUsage(data.result.token_usage);
            }
            showToast('Task completed!', 'success');
            // Reload page to show new data
            setTimeout(() => window.location.reload(), 1500);
        } else if (data.type === 'error') {
            hideLoading();
            showToast(data.error || 'Task failed', 'error');
        } else if (data.type === 'status') {
            if (data.status === 'completed') {
                hideLoading();
                // Extract and display token usage if available
                if (data.result && data.result.token_usage) {
                    console.log('WebSocket status completed - calling showTokenUsage with:', data.result.token_usage);
                    showTokenUsage(data.result.token_usage);
                }
                showToast('Task completed!', 'success');
                setTimeout(() => window.location.reload(), 1500);
            } else if (data.status === 'failed') {
                hideLoading();
                showToast(data.error || 'Task failed', 'error');
            } else if (data.status === 'running') {
                showLoading(data.message || 'Processing...', data.progress, estimatedDuration);
            }
        }
    };

    socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        hideLoading();
        showToast('Connection error', 'error');
    };

    socket.onclose = () => {
        console.log('WebSocket closed');
    };

    return socket;
}

// Poll task status (fallback if WebSocket not available)
async function pollTaskStatus(taskId, callback) {
    const poll = async () => {
        try {
            const data = await apiRequest(`/api/tasks/${taskId}/`);

            if (callback) {
                callback(data);
            }

            if (data.status === 'completed') {
                return data;
            } else if (data.status === 'failed') {
                throw new Error(data.error_message || 'Task failed');
            } else {
                // Continue polling (reduced to 500ms for faster feedback)
                setTimeout(poll, 500);
            }
        } catch (error) {
            console.error('Polling error:', error);
            throw error;
        }
    };

    return poll();
}

// Performance stats cache
let performanceStatsCache = null;
let lastFetchTime = null;
const CACHE_DURATION = 60000; // 1 minute cache

// Fetch API performance statistics
async function getPerformanceStats(forceRefresh = false) {
    const now = Date.now();

    // Return cached data if available and fresh
    if (!forceRefresh && performanceStatsCache && lastFetchTime && (now - lastFetchTime < CACHE_DURATION)) {
        return performanceStatsCache;
    }

    try {
        const stats = await apiRequest('/api/tasks/performance-stats/');
        performanceStatsCache = stats;
        lastFetchTime = now;
        return stats;
    } catch (error) {
        console.error('Failed to fetch performance stats:', error);
        // Return default estimates if fetch fails
        return {
            'brainstorm': { average_duration_seconds: 30, display_name: 'Idea Generation' },
            'plot': { average_duration_seconds: 20, display_name: 'Plot and Characters' },
            'chapter': { average_duration_seconds: 45, display_name: 'Chapter' }
        };
    }
}

// Get estimated duration for a specific API type
async function getEstimatedDuration(apiType) {
    const stats = await getPerformanceStats();
    return stats[apiType]?.average_duration_seconds || 30;
}

// Format time remaining
function formatTimeRemaining(seconds) {
    if (seconds < 60) {
        return `~${Math.ceil(seconds)} sec`;
    } else {
        const minutes = Math.ceil(seconds / 60);
        return `~${minutes} min`;
    }
}

// Session-wide token usage tracking with sessionStorage persistence
function getSessionTokens() {
    const stored = sessionStorage.getItem('sessionTokens');
    if (stored) {
        try {
            return JSON.parse(stored);
        } catch (e) {
            console.error('Failed to parse sessionTokens from sessionStorage:', e);
        }
    }
    return {
        prompt_tokens: 0,
        completion_tokens: 0,
        total_tokens: 0,
        call_count: 0
    };
}

let sessionTokens = getSessionTokens();

// Initialize token bar on page load
function initTokenBar() {
    const statusBar = document.getElementById('tokenStatusBar');
    const statusText = document.getElementById('tokenStatusText');

    if (!statusBar || !statusText) return;

    // Restore session tokens from storage
    sessionTokens = getSessionTokens();

    // Display current session tokens
    let message = '';
    if (sessionTokens.total_tokens > 0) {
        message = `🪙 Tokens: ${sessionTokens.total_tokens} total (${sessionTokens.prompt_tokens} prompt + ${sessionTokens.completion_tokens} completion) • ${sessionTokens.call_count} API calls`;
    } else {
        message = '🪙 Tokens: 0 total (0 prompt + 0 completion) • 0 API calls';
    }

    statusText.textContent = message;
    statusBar.style.display = 'block';

    // Restore iteration scores if available (from chapter generation)
    const storedIterationHistory = sessionStorage.getItem('iterationHistory');
    if (storedIterationHistory) {
        try {
            const iterationHistory = JSON.parse(storedIterationHistory);
            if (iterationHistory && iterationHistory.length > 0) {
                // Build iteration summary
                let iterationSummary = '';

                // Always show iteration count
                iterationSummary = ` | 🔄 ${iterationHistory.length} iteration${iterationHistory.length > 1 ? 's' : ''}`;

                if (iterationHistory.length === 1) {
                    // Single iteration
                    const iter = iterationHistory[0];
                    if (iter && iter.target_score !== undefined && iter.target_score !== null) {
                        iterationSummary += ` | 📊 Score: ${iter.total_score}/${iter.target_score}`;
                        // Show if target was achieved
                        if (iter.total_score >= iter.target_score) {
                            iterationSummary += ' ✅';
                        }
                    }
                } else {
                    // Multiple iterations - show best score
                    const bestIter = iterationHistory.find(i => i.is_best) || iterationHistory[iterationHistory.length - 1];
                    const finalIter = iterationHistory[iterationHistory.length - 1];
                    if (bestIter && finalIter) {
                        if (bestIter.total_score !== undefined && bestIter.target_score !== undefined) {
                            iterationSummary += ` | 📊 Best: ${bestIter.total_score}/${bestIter.target_score}`;
                        }
                        if (finalIter.total_score !== undefined && finalIter.target_score !== undefined &&
                            finalIter.total_score >= finalIter.target_score) {
                            iterationSummary += ' ✅';
                        }
                    }
                }
                if (iterationSummary) {
                    statusText.textContent = message + iterationSummary;
                }
            }
        } catch (e) {
            console.error('Failed to parse iterationHistory from sessionStorage:', e);
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTokenBar);
} else {
    initTokenBar();
}

// Reset token tracking (clear sessionStorage and UI)
function resetTokens() {
    console.log('resetTokens called - clearing session tokens and iteration history');

    // Clear sessionStorage
    sessionStorage.removeItem('sessionTokens');
    sessionStorage.removeItem('iterationHistory');

    // Reset in-memory object
    sessionTokens = {
        prompt_tokens: 0,
        completion_tokens: 0,
        total_tokens: 0,
        call_count: 0
    };

    // Update UI
    const statusBar = document.getElementById('tokenStatusBar');
    const statusText = document.getElementById('tokenStatusText');

    if (statusBar && statusText) {
        statusText.textContent = '🪙 Tokens: 0 total (0 prompt + 0 completion) • 0 API calls';
        statusBar.style.display = 'block';
    }

    console.log('Session tokens and iteration history reset');
}

// Display token usage in status bar (persistent)
function showTokenUsage(tokenData) {
    console.log('showTokenUsage called with:', tokenData);

    const statusBar = document.getElementById('tokenStatusBar');
    const statusText = document.getElementById('tokenStatusText');

    if (!statusBar || !statusText) {
        console.error('Token status bar elements not found');
        return;
    }

    // Load current session tokens from storage
    sessionTokens = getSessionTokens();

    // Accumulate tokens
    if (tokenData.prompt_tokens) sessionTokens.prompt_tokens += tokenData.prompt_tokens;
    if (tokenData.completion_tokens) sessionTokens.completion_tokens += tokenData.completion_tokens;
    if (tokenData.total_tokens) sessionTokens.total_tokens += tokenData.total_tokens;
    sessionTokens.call_count += 1;

    // Save to sessionStorage for persistence across page reloads
    sessionStorage.setItem('sessionTokens', JSON.stringify(sessionTokens));

    console.log('Session tokens updated and saved:', sessionTokens);

    // Format the message
    let message = '';
    if (sessionTokens.total_tokens > 0) {
        message = `🪙 Tokens: ${sessionTokens.total_tokens} total (${sessionTokens.prompt_tokens} prompt + ${sessionTokens.completion_tokens} completion) • ${sessionTokens.call_count} API calls`;
    } else {
        message = '🪙 Tokens: 0 total (0 prompt + 0 completion) • 0 API calls';
    }

    // Show the status bar (persistent, no auto-hide)
    statusText.textContent = message;
    statusBar.style.display = 'block';
    statusBar.classList.remove('hiding');
}

// Display iteration scores in status bar (in addition to token usage)
function showIterationScores(iterationHistory) {
    try {
        console.log('showIterationScores called with:', iterationHistory);

        const statusBar = document.getElementById('tokenStatusBar');
        const statusText = document.getElementById('tokenStatusText');

        if (!statusBar || !statusText || !iterationHistory || iterationHistory.length === 0) {
            console.log('No iteration history to display');
            return;
        }

        // Save iteration history to sessionStorage for persistence across page reloads
        sessionStorage.setItem('iterationHistory', JSON.stringify(iterationHistory));
        console.log('Iteration history saved to sessionStorage');

        // Build iteration summary
        let iterationSummary = '';

        // Always show iteration count
        iterationSummary = ` | 🔄 ${iterationHistory.length} iteration${iterationHistory.length > 1 ? 's' : ''}`;

        if (iterationHistory.length === 1) {
            // Single iteration
            const iter = iterationHistory[0];
            if (iter && iter.target_score !== undefined && iter.target_score !== null) {
                iterationSummary += ` | 📊 Score: ${iter.total_score}/${iter.target_score}`;
                // Show if target was achieved
                if (iter.total_score >= iter.target_score) {
                    iterationSummary += ' ✅';
                }
            }
        } else {
            // Multiple iterations - show best score
            const bestIter = iterationHistory.find(i => i.is_best) || iterationHistory[iterationHistory.length - 1];
            const finalIter = iterationHistory[iterationHistory.length - 1];

            if (bestIter && finalIter) {
                if (bestIter.total_score !== undefined && bestIter.target_score !== undefined) {
                    iterationSummary += ` | 📊 Best: ${bestIter.total_score}/${bestIter.target_score}`;
                }

                // Show if target was achieved
                if (finalIter.total_score !== undefined && finalIter.target_score !== undefined &&
                    finalIter.total_score >= finalIter.target_score) {
                    iterationSummary += ' ✅';
                }
            }
        }

        // Append to existing token display (don't replace it!)
        if (iterationSummary) {
            const currentText = statusText.textContent;
            statusText.textContent = currentText + iterationSummary;
            console.log('Iteration scores displayed:', iterationSummary);
        }
    } catch (error) {
        console.error('Error in showIterationScores:', error);
        // Don't throw - just log and continue
    }
}
