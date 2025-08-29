/**
 * Multi-User Portfolio Application
 * Detects single vs multi-user mode and provides appropriate interface
 */

class MultiUserPortfolio {
    constructor() {
        this.api = new APIClient();
        this.isLoaded = false;
        this.endpoints = [];
        this.systemInfo = null;
        this.users = [];
        this.currentUser = null;
        this.isMultiUser = false;

        console.log('Multi-User Portfolio initialized');
        this.init();
    }

    /**
     * Initialize the portfolio application
     */
    async init() {
        try {
            console.log('Starting portfolio initialization...');

            // Show loading screen
            this.showLoadingScreen();

            // Load system information and endpoints
            await this.loadSystemInfo();

            // Check for multi-user mode
            await this.detectUserMode();

            if (this.isMultiUser) {
                // Multi-user mode: show user selection
                await this.showUserSelection();
            } else {
                // Single-user mode: load the single user's content directly
                await this.loadSingleUserContent();
            }

            console.log('Portfolio initialization complete');
            this.isLoaded = true;

        } catch (error) {
            console.error('Failed to initialize portfolio:', error);
            this.showError('Failed to load portfolio. Please refresh the page.');
        }
    }

    /**
     * Load system information and available endpoints
     */
    async loadSystemInfo() {
        try {
            console.log('Loading system information...');
            this.systemInfo = await this.api.getSystemInfo();
            this.endpoints = this.systemInfo.available_endpoints || [];
            console.log('Loaded system info:', this.systemInfo);
            console.log('Available endpoints:', this.endpoints);
        } catch (error) {
            console.error('Failed to load system info:', error);
            throw error;
        }
    }

    /**
     * Detect if system is in single-user or multi-user mode
     */
    async detectUserMode() {
        try {
            console.log('Detecting user mode...');
            this.users = await this.api.getUsers();
            this.isMultiUser = this.users && this.users.length > 1;

            console.log(`Detected ${this.isMultiUser ? 'multi-user' : 'single-user'} mode`);
            console.log('Available users:', this.users);

            if (!this.isMultiUser && this.users.length === 1) {
                // Single user mode - set the current user
                this.currentUser = this.users[0];
                console.log('Single user mode - current user:', this.currentUser);
            }
        } catch (error) {
            console.warn('Could not detect user mode, defaulting to single-user:', error);
            this.isMultiUser = false;
            this.users = [];
        }
    }

    /**
     * Show user selection interface for multi-user mode
     */
    async showUserSelection() {
        console.log('Creating user selection interface...');

        // Create user selection HTML
        const userSelectionHTML = `
            <div class="user-selection">
                <div class="user-selection-content">
                    <h1>Select User Portfolio</h1>
                    <p>Choose a user to view their personal portfolio:</p>
                    <div class="user-grid">
                        ${this.users.map(user => `
                            <div class="user-card" data-username="${user.username}">
                                <div class="user-avatar">
                                    <i class="fas fa-user"></i>
                                </div>
                                <h3>${user.full_name || user.username}</h3>
                                <p class="user-email">${user.email || ''}</p>
                                <p class="user-role">${user.is_admin ? 'Administrator' : 'User'}</p>
                                <div class="user-card-action">
                                    <span>View Portfolio</span>
                                    <i class="fas fa-arrow-right"></i>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        // Replace the entire portfolio content
        const portfolio = document.getElementById('portfolio');
        portfolio.innerHTML = userSelectionHTML;

        // Add click handlers for user cards
        const userCards = document.querySelectorAll('.user-card');
        userCards.forEach(card => {
            card.addEventListener('click', () => {
                const username = card.dataset.username;
                this.selectUser(username);
            });
        });

        // Hide loading screen
        this.hideLoadingScreen();
    }

    /**
     * User selected - load their portfolio
     */
    async selectUser(username) {
        try {
            console.log(`User selected: ${username}`);

            // Find the user object
            this.currentUser = this.users.find(u => u.username === username);

            if (!this.currentUser) {
                throw new Error(`User ${username} not found`);
            }

            // Show loading again
            this.showLoadingScreen();

            // Load user-specific portfolio
            await this.loadUserPortfolio(username);

        } catch (error) {
            console.error(`Failed to load user ${username}:`, error);
            this.showError(`Failed to load user ${username}. Please try again.`);
        }
    }

    /**
     * Load portfolio for a specific user
     */
    async loadUserPortfolio(username) {
        console.log(`Loading portfolio for user: ${username}`);

        // Reset portfolio structure
        this.resetPortfolioStructure();

        // Small delay to ensure DOM is updated
        await new Promise(resolve => setTimeout(resolve, 100));

        // Load content with username
        await this.loadPortfolioContent(username);

        // Add back to users button
        this.addBackButton();

        // Hide loading and show portfolio
        this.hideLoadingScreen();
        this.showPortfolio();
    }

    /**
     * Load content for single-user mode
     */
    async loadSingleUserContent() {
        console.log('Loading single user content...');

        // In single-user mode, load content without username
        await this.loadPortfolioContent();

        // Hide loading and show portfolio
        this.hideLoadingScreen();
        this.showPortfolio();
    }

    /**
     * Load portfolio content (works for both single and multi-user)
     */
    async loadPortfolioContent(username = null) {
        console.log(`Loading portfolio content${username ? ` for user: ${username}` : ''}...`);

        try {
            // Load basic user info for hero section
            await this.loadHeroSection(username);

            // Load all endpoint data
            await this.loadAllEndpoints(username);

        } catch (error) {
            console.error('Failed to load portfolio content:', error);
            this.showError('Failed to load portfolio content.');
        }
    }

    /**
     * Load hero section with user information
     */
    async loadHeroSection(username = null) {
        const heroName = document.getElementById('heroName');
        const heroTitle = document.getElementById('heroTitle');

        if (!heroName || !heroTitle) return;

        try {
            // Get user data or use current user info
            let userInfo = this.currentUser;
            if (username && !userInfo) {
                // Try to get user info from API
                userInfo = this.users.find(u => u.username === username);
            }

            // Set name and title
            heroName.textContent = userInfo?.full_name || userInfo?.username || 'Portfolio';
            heroTitle.textContent = userInfo?.email || 'Personal Portfolio';

        } catch (error) {
            console.warn('Could not load hero section:', error);
            heroName.textContent = 'Portfolio';
            heroTitle.textContent = 'Personal Information';
        }
    }

    /**
     * Load all endpoint data
     */
    async loadAllEndpoints(username = null) {
        console.log(`Loading all endpoints for user: ${username}`);
        const sections = ['about', 'skills', 'experience', 'projects', 'contact'];

        console.log('Available endpoints:', this.endpoints.map(e => e.name));
        console.log('Loading sections:', sections);

        for (const section of sections) {
            try {
                console.log(`Starting to load section: ${section}`);
                await this.loadSectionContent(section, username);
                console.log(`Completed loading section: ${section}`);
            } catch (error) {
                console.error(`Failed to load ${section}:`, error);
            }
        }

        console.log('Finished loading all sections');
    }

    /**
     * Load content for a specific section
     */
    async loadSectionContent(sectionName, username = null) {
        console.log(`Loading section: ${sectionName} for user: ${username}`);
        const container = document.getElementById(`${sectionName}Content`);
        if (!container) {
            console.error(`Container not found: ${sectionName}Content`);
            return;
        }
        console.log(`Container found for ${sectionName}:`, container);

        try {
            // Find the endpoint
            const endpoint = this.endpoints.find(ep =>
                ep.name === sectionName ||
                (sectionName === 'experience' && ep.name === 'resume')
            );

            if (!endpoint) {
                console.warn(`Endpoint not found for section: ${sectionName}`);
                console.log('Available endpoints:', this.endpoints.map(e => e.name));
                container.innerHTML = `<p>No ${sectionName} information available.</p>`;
                return;
            }

            console.log(`Found endpoint for ${sectionName}:`, endpoint);

            // Get the data
            console.log(`Calling API for endpoint: ${endpoint.name}, user: ${username}`);
            const data = await this.api.getEndpointData(endpoint.name, username);
            console.log(`Data received for ${sectionName}:`, data);

            if (data && Array.isArray(data) && data.length > 0) {
                console.log(`Formatting ${data.length} items for ${sectionName}`);
                container.innerHTML = this.formatSectionData(sectionName, data);
                console.log(`Successfully loaded ${sectionName} with ${data.length} items`);
            } else {
                console.log(`No data found for ${sectionName}`);
                container.innerHTML = `<p>No ${sectionName} information available.</p>`;
            }

        } catch (error) {
            console.error(`Failed to load ${sectionName}:`, error);
            container.innerHTML = `<p>Unable to load ${sectionName} information.</p>`;
        }
    }

    /**
     * Format section data for display
     */
    formatSectionData(sectionName, items) {
        if (!items || items.length === 0) return '<p>No information available.</p>';

        switch (sectionName) {
            case 'about':
                return this.formatAboutData(items[0]);
            case 'skills':
                return this.formatSkillsData(items);
            case 'experience':
                return this.formatExperienceData(items);
            case 'projects':
                return this.formatProjectsData(items);
            case 'contact':
                return this.formatContactData(items[0]);
            default:
                return this.formatGenericData(items);
        }
    }

    /**
     * Format about data
     */
    formatAboutData(item) {
        const content = this.extractContent(item);
        return `<div class="about-content">${this.formatText(content)}</div>`;
    }

    /**
     * Format skills data
     */
    formatSkillsData(items) {
        let html = '<div class="skills-grid">';
        items.forEach(item => {
            const content = this.extractContent(item);
            html += `<div class="skill-item">${this.formatText(content)}</div>`;
        });
        html += '</div>';
        return html;
    }

    /**
     * Format experience data
     */
    formatExperienceData(items) {
        let html = '<div class="experience-list">';
        items.forEach(item => {
            const content = this.extractContent(item);
            html += `<div class="experience-item">${this.formatText(content)}</div>`;
        });
        html += '</div>';
        return html;
    }

    /**
     * Format projects data
     */
    formatProjectsData(items) {
        let html = '<div class="projects-grid">';
        items.forEach(item => {
            const content = this.extractContent(item);
            html += `<div class="project-item">${this.formatText(content)}</div>`;
        });
        html += '</div>';
        return html;
    }

    /**
     * Format contact data
     */
    formatContactData(item) {
        const content = this.extractContent(item);
        return `<div class="contact-content">${this.formatText(content)}</div>`;
    }

    /**
     * Format generic data
     */
    formatGenericData(items) {
        let html = '<div class="generic-content">';
        items.forEach(item => {
            const content = this.extractContent(item);
            html += `<div class="content-item">${this.formatText(content)}</div>`;
        });
        html += '</div>';
        return html;
    }

    /**
     * Extract content from API response item
     */
    extractContent(item) {
        if (typeof item === 'string') return item;
        if (item.content) return item.content;
        if (item.data && item.data.content) return item.data.content;
        return JSON.stringify(item, null, 2);
    }

    /**
     * Format text content
     */
    formatText(content) {
        if (!content) return 'No content available.';

        // Simple text formatting
        return content
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^(.*)$/g, '<p>$1</p>');
    }

    /**
     * Reset portfolio to original structure
     */
    resetPortfolioStructure() {
        const portfolio = document.getElementById('portfolio');

        portfolio.innerHTML = `
            <!-- Navigation -->
            <nav class="navbar">
                <div class="nav-content">
                    <div class="nav-brand">
                        <h1>Portfolio</h1>
                    </div>
                    <div class="nav-links">
                        <a href="#about" class="nav-link">About</a>
                        <a href="#skills" class="nav-link">Skills</a>
                        <a href="#experience" class="nav-link">Experience</a>
                        <a href="#projects" class="nav-link">Projects</a>
                        <a href="#contact" class="nav-link">Contact</a>
                    </div>
                    <div class="nav-toggle">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </nav>

            <!-- Hero Section -->
            <section id="hero" class="hero">
                <div class="hero-content">
                    <h1 id="heroName">Loading...</h1>
                    <p id="heroTitle">Loading...</p>
                    <div class="hero-cta">
                        <a href="#contact" class="btn-primary">Get In Touch</a>
                        <a href="#projects" class="btn-secondary">View Work</a>
                    </div>
                </div>
            </section>

            <!-- About Section -->
            <section id="about" class="section">
                <div class="container">
                    <h2 class="section-title">About</h2>
                    <div id="aboutContent" class="content-area">
                        <div class="loading-content">Loading...</div>
                    </div>
                </div>
            </section>

            <!-- Skills Section -->
            <section id="skills" class="section bg-light">
                <div class="container">
                    <h2 class="section-title">Skills</h2>
                    <div id="skillsContent" class="content-area">
                        <div class="loading-content">Loading...</div>
                    </div>
                </div>
            </section>

            <!-- Experience Section -->
            <section id="experience" class="section">
                <div class="container">
                    <h2 class="section-title">Experience</h2>
                    <div id="experienceContent" class="content-area">
                        <div class="loading-content">Loading...</div>
                    </div>
                </div>
            </section>

            <!-- Projects Section -->
            <section id="projects" class="section bg-light">
                <div class="container">
                    <h2 class="section-title">Projects</h2>
                    <div id="projectsContent" class="content-area">
                        <div class="loading-content">Loading...</div>
                    </div>
                </div>
            </section>

            <!-- Contact Section -->
            <section id="contact" class="section">
                <div class="container">
                    <h2 class="section-title">Contact</h2>
                    <div id="contactContent" class="content-area">
                        <div class="loading-content">Loading...</div>
                    </div>
                </div>
            </section>

            <!-- Footer -->
            <footer class="footer">
                <div class="container">
                    <p>&copy; 2024 Portfolio. All rights reserved.</p>
                </div>
            </footer>
        `;
    }

    /**
     * Add back to users button in multi-user mode
     */
    addBackButton() {
        if (!this.isMultiUser) return;

        const navBrand = document.querySelector('.nav-brand');
        if (navBrand) {
            navBrand.innerHTML = `
                <button id="backToUsers" class="back-button">
                    <i class="fas fa-arrow-left"></i> Back to Users
                </button>
                <h1>Portfolio - ${this.currentUser?.full_name || this.currentUser?.username || 'User'}</h1>
            `;

            // Add click handler
            document.getElementById('backToUsers').addEventListener('click', () => {
                this.showUserSelection();
            });
        }
    }

    /**
     * Show loading screen
     */
    showLoadingScreen() {
        const loadingScreen = document.getElementById('loadingScreen');
        if (loadingScreen) {
            loadingScreen.classList.remove('hidden');
        }
    }

    /**
     * Hide loading screen
     */
    hideLoadingScreen() {
        const loadingScreen = document.getElementById('loadingScreen');
        if (loadingScreen) {
            loadingScreen.classList.add('hidden');
        }
    }

    /**
     * Show portfolio
     */
    showPortfolio() {
        const portfolio = document.getElementById('portfolio');
        if (portfolio) {
            portfolio.style.display = 'block';
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        const portfolio = document.getElementById('portfolio');
        if (portfolio) {
            portfolio.innerHTML = `
                <div class="error-message">
                    <h2>Oops! Something went wrong</h2>
                    <p>${message}</p>
                    <button onclick="window.location.reload()" class="btn-primary">Refresh Page</button>
                </div>
            `;
        }
        this.hideLoadingScreen();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing multi-user portfolio...');
    new MultiUserPortfolio();
});
