/**
 * Personal API Dashboard Application
 * Main application logic and UI management
 */

class Dashboard {
    constructor() {
        this.api = new APIClient();
        this.currentUser = null;
        this.users = [];
        this.endpoints = [];
        this.isMultiUserMode = false;

        this.init();
    }

    /**
     * Initialize the dashboard
     */
    async init() {
        try {
            console.log('Initializing dashboard...');
            this.showLoading('Connecting to API...');

            // Test API connection
            const isConnected = await this.api.testConnection();
            if (!isConnected) {
                this.hideLoading();
                this.showError('Failed to connect to API. Please check if the server is running.');
                return;
            }
            console.log('API connection established');

            // Get system info
            console.log('Fetching system info...');
            const systemInfo = await this.api.getSystemInfo();
            console.log('System info:', systemInfo);
            this.systemInfo = systemInfo;

            // Extract endpoints from system info
            this.endpoints = systemInfo.available_endpoints.map(ep => ep.name) || [];
            console.log('Available endpoints:', this.endpoints);

            // Load appropriate interface
            if (systemInfo.mode === 'single_user') {
                console.log('Loading single user mode for:', systemInfo.user);
                this.currentUser = { username: systemInfo.user };
                await this.loadSingleUserData();
            } else {
                console.log('Loading multi-user mode');
                this.showMultiUserMode();
            }

            // Hide loading when done
            this.hideLoading();
        } catch (error) {
            console.error('Dashboard initialization error:', error);
            this.hideLoading();
            this.showError(`Failed to initialize dashboard: ${error.message}`);
        }
    }

    /**
     * Load system information
     */
    async loadSystemInfo() {
        try {
            const systemInfo = await this.api.getSystemInfo();
            this.endpoints = systemInfo.endpoint_routing || [];
        } catch (error) {
            console.warn('Could not load system info, using fallback endpoints');
            this.endpoints = [
                'resume', 'about', 'skills', 'projects', 'ideas',
                'favorite_books', 'problems', 'hobbies', 'looking_for'
            ];
        }
    }

    /**
     * Load available users
     */
    async loadUsers() {
        try {
            this.users = await this.api.getUsers();
            this.isMultiUserMode = this.users && this.users.length > 1;

            if (!this.isMultiUserMode && this.users && this.users.length === 1) {
                this.currentUser = this.users[0];
            }
        } catch (error) {
            console.warn('Could not load users, assuming single-user mode');
            this.isMultiUserMode = false;
            this.currentUser = { username: 'default', email: 'user@example.com' };
        }
    }

    /**
     * Setup UI event listeners and initial state
     */
    setupUI() {
        // User selector for multi-user mode
        const userSelect = document.getElementById('userSelect');
        if (userSelect && this.isMultiUserMode) {
            userSelect.addEventListener('change', (e) => {
                if (e.target.value) {
                    this.selectUser(e.target.value);
                }
            });

            // Populate user selector
            this.populateUserSelector();
        }

        // Modal controls
        const modal = document.getElementById('endpoint-modal');
        const modalClose = document.getElementById('modal-close');

        if (modalClose) {
            modalClose.addEventListener('click', () => this.closeModal());
        }

        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal();
                }
            });
        }

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    /**
     * Show/hide loading overlay
     */
    showLoading(message = 'Loading...') {
        const loading = document.getElementById('loading');
        const loadingText = loading?.querySelector('p');

        if (loading) {
            loading.style.display = 'flex';
            if (loadingText && typeof message === 'string') {
                loadingText.textContent = message;
            }
        }
    }

    /**
     * Hide loading overlay
     */
    hideLoading() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = 'none';
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        const endpointsGrid = document.getElementById('endpoints-grid');
        if (endpointsGrid) {
            endpointsGrid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Connection Error</h3>
                    <p>${message}</p>
                </div>
            `;
        }
    }

    /**
     * Setup multi-user mode UI
     */
    showMultiUserMode() {
        const singleUserPanel = document.getElementById('single-user-panel');
        const multiUserPanel = document.getElementById('multi-user-panel');
        const userSelector = document.getElementById('user-selector');

        if (singleUserPanel) singleUserPanel.style.display = 'none';
        if (multiUserPanel) multiUserPanel.style.display = 'block';
        if (userSelector) userSelector.style.display = 'flex';

        this.renderUserCards();
        this.clearEndpointsContent();
    }

    /**
     * Load and display single user data
     */
    async loadSingleUserData() {
        const singleUserPanel = document.getElementById('single-user-panel');
        const multiUserPanel = document.getElementById('multi-user-panel');
        const userSelector = document.getElementById('user-selector');

        if (singleUserPanel) singleUserPanel.style.display = 'block';
        if (multiUserPanel) multiUserPanel.style.display = 'none';
        if (userSelector) userSelector.style.display = 'none';

        // Update user info
        this.updateUserInfo();

        // Load endpoints data
        await this.loadEndpointsData();
    }

    /**
     * Update user info display
     */
    updateUserInfo() {
        const userName = document.getElementById('user-name');
        const userTitle = document.getElementById('user-title');

        if (userName && this.currentUser) {
            userName.textContent = this.currentUser.username || 'User';
        }

        if (userTitle) {
            userTitle.textContent = this.currentUser?.email || 'Personal API Data';
        }
    }

    /**
     * Populate user selector dropdown
     */
    populateUserSelector() {
        const userSelect = document.getElementById('userSelect');
        if (userSelect && this.users) {
            userSelect.innerHTML = '<option value="">Choose a user...</option>';

            this.users.forEach(user => {
                const option = document.createElement('option');
                option.value = user.username;
                option.textContent = `${user.username} (${user.email})`;
                userSelect.appendChild(option);
            });
        }
    }

    /**
     * Render user cards for multi-user mode
     */
    renderUserCards() {
        const userCards = document.getElementById('user-cards');
        if (!userCards || !this.users) return;

        userCards.innerHTML = this.users.map(user => `
            <div class="user-card" data-username="${user.username}">
                <div class="user-card-avatar">
                    <i class="fas fa-user"></i>
                </div>
                <h3>${user.username}</h3>
                <p>${user.email}</p>
            </div>
        `).join('');

        // Add click handlers
        userCards.querySelectorAll('.user-card').forEach(card => {
            card.addEventListener('click', () => {
                const username = card.dataset.username;
                this.selectUser(username);
            });
        });
    }

    /**
     * Select a user in multi-user mode
     */
    async selectUser(username) {
        try {
            this.showLoading(true);

            // Update current user
            this.currentUser = this.users.find(u => u.username === username);

            // Update UI
            this.updateSelectedUserCard(username);
            this.updateUserSelector(username);

            // Load user's data
            await this.loadEndpointsData(username);

        } catch (error) {
            console.error('Failed to load user data:', error);
            this.showError(`Failed to load data for user: ${username}`);
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Update selected user card visual state
     */
    updateSelectedUserCard(username) {
        const userCards = document.querySelectorAll('.user-card');
        userCards.forEach(card => {
            card.classList.remove('selected');
            if (card.dataset.username === username) {
                card.classList.add('selected');
            }
        });
    }

    /**
     * Update user selector dropdown
     */
    updateUserSelector(username) {
        const userSelect = document.getElementById('userSelect');
        if (userSelect) {
            userSelect.value = username;
        }
    }

    /**
     * Load and display endpoints data
     */
    async loadEndpointsData(username = null) {
        const endpointsGrid = document.getElementById('endpoints-grid');
        if (!endpointsGrid) return;

        try {
            console.log('Loading endpoints data for:', this.endpoints);

            // Check if we have endpoints
            if (!this.endpoints || this.endpoints.length === 0) {
                endpointsGrid.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-info-circle"></i>
                        <h3>No Endpoints Available</h3>
                        <p>No data endpoints found. Add some content to get started!</p>
                    </div>
                `;
                return;
            }

            // Clear existing content
            endpointsGrid.innerHTML = '<div class="loading-endpoints">Loading endpoints...</div>';

            // Load data for each endpoint
            const endpointCards = await Promise.all(
                this.endpoints.map(endpoint => this.loadEndpointCard(endpoint, username))
            );

            // Render endpoint cards
            endpointsGrid.innerHTML = endpointCards.join('');

            // Add click handlers
            endpointsGrid.querySelectorAll('.endpoint-card').forEach(card => {
                card.addEventListener('click', () => {
                    const endpointName = card.dataset.endpoint;
                    this.showEndpointDetails(endpointName, username);
                });
            });

        } catch (error) {
            console.error('Failed to load endpoints:', error);
            endpointsGrid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error Loading Data</h3>
                    <p>Failed to load endpoint data: ${error.message}</p>
                </div>
            `;
        }
    }

    /**
     * Load data for a single endpoint and create card HTML
     */
    async loadEndpointCard(endpointName, username = null) {
        try {
            const data = await this.api.getEndpointData(endpointName, username);
            const dataCount = formatters.countDataItems(data);
            const icon = formatters.getEndpointIcon(endpointName);
            const displayName = formatters.getEndpointDisplayName(endpointName);

            return `
                <div class="endpoint-card" data-endpoint="${endpointName}">
                    <div class="endpoint-card-header">
                        <div class="endpoint-icon">
                            <i class="fas ${icon}"></i>
                        </div>
                        <div class="endpoint-info">
                            <h3>${displayName}</h3>
                            <p>${this.getEndpointDescription(endpointName)}</p>
                        </div>
                    </div>
                    <div class="endpoint-meta">
                        <span class="data-count">
                            <i class="fas fa-database"></i>
                            ${dataCount} ${dataCount === 1 ? 'item' : 'items'}
                        </span>
                        <i class="fas fa-arrow-right view-arrow"></i>
                    </div>
                </div>
            `;
        } catch (error) {
            console.warn(`Failed to load ${endpointName}:`, error);
            const icon = formatters.getEndpointIcon(endpointName);
            const displayName = formatters.getEndpointDisplayName(endpointName);

            return `
                <div class="endpoint-card" data-endpoint="${endpointName}">
                    <div class="endpoint-card-header">
                        <div class="endpoint-icon">
                            <i class="fas ${icon}"></i>
                        </div>
                        <div class="endpoint-info">
                            <h3>${displayName}</h3>
                            <p>No data available</p>
                        </div>
                    </div>
                    <div class="endpoint-meta">
                        <span class="data-count">
                            <i class="fas fa-exclamation-circle"></i>
                            Error loading
                        </span>
                        <i class="fas fa-arrow-right view-arrow"></i>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Get description for endpoint
     */
    getEndpointDescription(endpointName) {
        const descriptions = {
            'resume': 'Professional resume and work history',
            'about': 'Personal information and bio',
            'skills': 'Technical and soft skills',
            'projects': 'Portfolio projects and work',
            'experience': 'Work experience and roles',
            'education': 'Educational background',
            'ideas': 'Thoughts and ideas',
            'favorite_books': 'Book recommendations and reviews',
            'problems': 'Challenges and problem statements',
            'hobbies': 'Personal interests and hobbies',
            'looking_for': 'Current opportunities and interests',
            'skills_matrix': 'Detailed skills assessment'
        };
        return descriptions[endpointName] || 'Data collection';
    }

    /**
     * Show endpoint details in modal
     */
    async showEndpointDetails(endpointName, username = null) {
        const modal = document.getElementById('endpoint-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');

        if (!modal || !modalTitle || !modalBody) return;

        try {
            // Update modal title
            const displayName = formatters.getEndpointDisplayName(endpointName);
            modalTitle.textContent = displayName;

            // Show loading in modal
            modalBody.innerHTML = '<div class="loading-endpoints">Loading data...</div>';
            modal.classList.add('show');

            // Load endpoint data
            const data = await this.api.getEndpointData(endpointName, username);

            // Format and display data
            modalBody.innerHTML = formatters.formatDataForDisplay(data, endpointName);

        } catch (error) {
            console.error(`Failed to load ${endpointName} details:`, error);
            modalBody.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error Loading Data</h3>
                    <p>Failed to load ${endpointName} data: ${error.message}</p>
                </div>
            `;
        }
    }

    /**
     * Close modal
     */
    closeModal() {
        const modal = document.getElementById('endpoint-modal');
        if (modal) {
            modal.classList.remove('show');
        }
    }

    /**
     * Clear endpoints content
     */
    clearEndpointsContent() {
        const endpointsGrid = document.getElementById('endpoints-grid');
        if (endpointsGrid) {
            endpointsGrid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-users"></i>
                    <h3>Select a User</h3>
                    <p>Choose a user above to view their data</p>
                </div>
            `;
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});
