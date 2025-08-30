/**
 * API Client for Personal API Dashboard
 * Handles all API communication with the backend
 */

class APIClient {
    constructor() {
        // Determine API base URL - try to use the same host/port as the frontend
        this.baseURL = this.getAPIBaseURL();
        this.isOnline = false;
        console.log('API Client initialized with base URL:', this.baseURL);
        console.log('Current window location:', window.location.href);
    }

    /**
     * Determine the API base URL based on current location
     */
    getAPIBaseURL() {
        // Auto-detect: if frontend is on port 8006, API is on 8000
        // If on same port (like 8004), use same origin
        const protocol = window.location.protocol;
        const hostname = window.location.hostname;
        const currentPort = window.location.port;

        if (currentPort === '8006') {
            // Frontend server mode - API on 8007
            return `${protocol}//${hostname}:8007`;
        } else {
            // Same server mode - use same origin
            return window.location.origin;
        }
    }

    /**
     * Make HTTP request to API
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            console.log(`Making API request to: ${url}`);
            const response = await fetch(url, config);

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`API request failed: ${response.status} ${response.statusText}`, errorText);
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.setOnlineStatus(true);
            return data;
        } catch (error) {
            this.setOnlineStatus(false);
            console.error('API Request failed:', error);

            // Provide more specific error messages
            if (error instanceof TypeError && error.message.includes('fetch')) {
                throw new Error('Network error: Unable to reach the server. Please check if the server is running.');
            } else if (error.name === 'AbortError') {
                throw new Error('Request timeout: The server took too long to respond.');
            } else {
                throw error;
            }
        }
    }

    /**
     * Update online status and UI indicator
     */
    setOnlineStatus(isOnline) {
        this.isOnline = isOnline;
        const indicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');

        if (indicator && statusText) {
            indicator.className = `status-indicator ${isOnline ? 'online' : 'offline'}`;
            statusText.textContent = isOnline ? 'Connected' : 'Offline';
        }
    }

    /**
     * Get system information and available endpoints
     */
    async getSystemInfo() {
        return await this.request('/api/v1/system/info');
    }

    /**
     * Get all available users (for multi-user mode)
     */
    async getUsers() {
        try {
            // Use system info endpoint which includes user list and mode
            const systemInfo = await this.request('/api/v1/system/info');

            if (systemInfo) {
                if (systemInfo.mode === 'multi_user' && systemInfo.users) {
                    // Multi-user mode: return user objects with username and full_name
                    return systemInfo.users.map(user => ({
                        username: user.username,
                        full_name: user.full_name,
                        email: user.email
                    }));
                } else if (systemInfo.mode === 'single_user' && systemInfo.user_info) {
                    // Single-user mode: use the user_info object which has all details
                    return [{
                        username: systemInfo.user_info.username,
                        full_name: systemInfo.user_info.full_name,
                        email: systemInfo.user_info.email
                    }];
                }
            }
            return [];
        } catch (error) {
            // If system info fails, assume single-user mode
            return [];
        }
    }

    /**
     * Get data for a specific endpoint
     */
    async getEndpointData(endpointName, username = null) {
        let url = `/api/v1/${endpointName}`;
        if (username) {
            url = `/api/v1/${endpointName}/users/${username}`;
        }

        // Only add privacy level for endpoints that require it
        const needsPrivacyLevel = ['resume'];
        if (needsPrivacyLevel.includes(endpointName)) {
            const separator = url.includes('?') ? '&' : '?';
            url += `${separator}level=public_full`;
        }

        return await this.request(url);
    }

    /**
     * Get endpoint configuration/schema
     */
    async getEndpointConfig(endpointName) {
        return await this.request(`/api/v1/endpoints/${endpointName}`);
    }

    /**
     * Test API connectivity
     */
    async testConnection() {
        try {
            console.log('Testing API connection to:', this.baseURL);

            // First try a simple fetch to check if server is reachable
            console.log('Step 1: Testing basic connectivity...');
            const response = await fetch(`${this.baseURL}/health`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                }
            });

            console.log('Response status:', response.status);
            console.log('Response headers:', [...response.headers.entries()]);

            if (!response.ok) {
                throw new Error(`Health check failed: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            console.log('Health check response:', data);
            console.log('API connection successful');
            return true;
        } catch (error) {
            console.error('API connection failed:', error);
            console.error('Error details:', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            return false;
        }
    }

    /**
     * Get user-specific data for all endpoints
     */
    async getUserData(username) {
        try {
            return await this.request(`/api/v1/users/${username}`);
        } catch (error) {
            console.error(`Failed to get user data for ${username}:`, error);
            return null;
        }
    }
}

// Utility functions for data formatting
const formatters = {
    /**
     * Format JSON data for display
     */
    formatJSON(data) {
        return JSON.stringify(data, null, 2);
    },

    /**
     * Format date strings
     */
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        try {
            return new Date(dateString).toLocaleDateString();
        } catch {
            return dateString;
        }
    },

    /**
     * Get appropriate icon for endpoint
     */
    getEndpointIcon(endpointName) {
        const icons = {
            'resume': 'fa-file-alt',
            'about': 'fa-user',
            'skills': 'fa-cogs',
            'projects': 'fa-code',
            'experience': 'fa-briefcase',
            'education': 'fa-graduation-cap',
            'ideas': 'fa-lightbulb',
            'favorite_books': 'fa-book',
            'problems': 'fa-exclamation-triangle',
            'hobbies': 'fa-heart',
            'looking_for': 'fa-search',
            'skills_matrix': 'fa-chart-bar'
        };
        return icons[endpointName] || 'fa-folder';
    },

    /**
     * Get human-readable endpoint name
     */
    getEndpointDisplayName(endpointName) {
        const names = {
            'resume': 'Resume',
            'about': 'About Me',
            'skills': 'Skills',
            'projects': 'Projects',
            'experience': 'Experience',
            'education': 'Education',
            'ideas': 'Ideas',
            'favorite_books': 'Favorite Books',
            'problems': 'Problems',
            'hobbies': 'Hobbies',
            'looking_for': 'Looking For',
            'skills_matrix': 'Skills Matrix'
        };
        return names[endpointName] || endpointName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    },

    /**
     * Truncate text for preview
     */
    truncateText(text, maxLength = 150) {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    },

    /**
     * Count data items in various formats
     */
    countDataItems(data) {
        if (!data) return 0;
        if (Array.isArray(data)) return data.length;
        if (typeof data === 'object') {
            // For objects, count meaningful properties (exclude meta fields)
            const keys = Object.keys(data).filter(key => !key.startsWith('_') && key !== 'id');
            return keys.length;
        }
        return 1;
    },

    /**
     * Format data for display in modal
     */
    formatDataForDisplay(data, endpointName) {
        if (!data) {
            return '<div class="empty-state"><i class="fas fa-inbox"></i><h3>No Data</h3><p>No data available for this endpoint.</p></div>';
        }

        if (Array.isArray(data)) {
            if (data.length === 0) {
                return '<div class="empty-state"><i class="fas fa-inbox"></i><h3>No Items</h3><p>This endpoint has no data items yet.</p></div>';
            }

            return data.map((item, index) => {
                const title = item.title || item.name || item.company || item.institution || `Item ${index + 1}`;
                return `
                    <div class="data-item">
                        <h4>${title}</h4>
                        <div class="data-content">
                            <pre>${this.formatJSON(item)}</pre>
                        </div>
                    </div>
                `;
            }).join('');
        }

        // Single object
        return `
            <div class="data-item">
                <h4>${this.getEndpointDisplayName(endpointName)} Data</h4>
                <div class="data-content">
                    <pre>${this.formatJSON(data)}</pre>
                </div>
            </div>
        `;
    }
};

// Export for use in other modules
window.APIClient = APIClient;
window.formatters = formatters;
