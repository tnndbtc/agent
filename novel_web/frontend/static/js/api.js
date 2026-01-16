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
            const error = await response.json().catch(() => ({ error: 'Request failed' }));
            throw new Error(error.error || error.detail || 'Request failed');
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
                showToast('Task completed!', 'success');
                setTimeout(() => window.location.reload(), 1500);
            } else {
                showLoading(data.message || 'Processing...', data.progress, estimatedDuration);
            }
        } else if (data.type === 'complete') {
            hideLoading();
            showToast('Task completed!', 'success');
            // Reload page to show new data
            setTimeout(() => window.location.reload(), 1500);
        } else if (data.type === 'error') {
            hideLoading();
            showToast(data.error || 'Task failed', 'error');
        } else if (data.type === 'status') {
            if (data.status === 'completed') {
                hideLoading();
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
            'outline': { average_duration_seconds: 60, display_name: 'Outlines' },
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
