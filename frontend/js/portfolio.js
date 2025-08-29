/**
 * Professional Portfolio Application
 * Loads and displays all content upfront without requiring user interaction
 */

class Portfolio {
    constructor() {
        this.api = new APIClient();
        this.isLoaded = false;
        this.endpoints = [];
        this.systemInfo = null;

        console.log('Portfolio initialized');
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

            // Load all content
            await this.loadAllContent();

            // Setup navigation
            this.setupNavigation();

            // Hide loading and show portfolio
            this.hideLoadingScreen();
            this.showPortfolio();

            console.log('Portfolio fully loaded');
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
     * Update hero section with name and title
     */
    async updateHeroSection() {
        try {
            console.log('Updating hero section...');

            // Default values
            let name = 'Phil McNeely';  // Extract from your email
            let title = 'Full Stack Developer';

            // Check contact endpoint first for email/name extraction
            const contactEndpoint = this.endpoints.find(ep => ep.name === 'contact' || ep.name === 'contact_info');
            if (contactEndpoint) {
                try {
                    const contactData = await this.api.getEndpointData(contactEndpoint.name);
                    if (contactData.items && contactData.items.length > 0) {
                        const item = contactData.items[0];
                        const content = item.content || '';
                        const meta = item.meta || item.data?.meta || {};

                        // Extract name from email if present
                        const emailMatch = content.match(/hello@(\w+)/i);
                        if (emailMatch) {
                            // Extract from email: hello@philmcneely.com -> Phil McNeely
                            const domain = emailMatch[1]; // philmcneely
                            if (domain === 'philmcneely') {
                                name = 'Phil McNeely';
                            }
                        }

                        // Look for explicit name in meta or content
                        if (meta.name) name = meta.name;
                        if (meta.title && !meta.title.includes('Contact')) {
                            title = meta.title;
                        }
                        if (meta.job_title || meta.position) {
                            title = meta.job_title || meta.position;
                        }
                    }
                } catch (error) {
                    console.warn('Could not load contact data for hero:', error);
                }
            }

            // Try about endpoint for additional info
            const aboutEndpoint = this.endpoints.find(ep => ep.name === 'about');
            if (aboutEndpoint) {
                try {
                    const aboutData = await this.api.getEndpointData(aboutEndpoint.name);
                    if (aboutData.items && aboutData.items.length > 0) {
                        const item = aboutData.items[0];
                        const content = item.content || '';
                        const meta = item.meta || item.data?.meta || {};

                        // Look for developer/professional title in content
                        if (content.includes('developer')) {
                            title = 'Developer';
                        }
                        if (content.includes('Full Stack')) {
                            title = 'Full Stack Developer';
                        }
                        if (content.includes('Software Engineer')) {
                            title = 'Software Engineer';
                        }

                        // Override with explicit meta if available
                        if (meta.name) name = meta.name;
                        if (meta.job_title || meta.position) {
                            title = meta.job_title || meta.position;
                        }
                    }
                } catch (error) {
                    console.warn('Could not load about data for hero:', error);
                }
            }

            // Update the hero elements
            const heroName = document.getElementById('heroName');
            const heroTitle = document.getElementById('heroTitle');

            if (heroName) {
                heroName.textContent = name;
            }

            if (heroTitle) {
                heroTitle.textContent = title;
            }

            console.log(`Hero updated - Name: ${name}, Title: ${title}`);

        } catch (error) {
            console.error('Failed to update hero section:', error);
            // Set fallback values
            const heroName = document.getElementById('heroName');
            const heroTitle = document.getElementById('heroTitle');

            if (heroName) heroName.textContent = 'Phil McNeely';
            if (heroTitle) heroTitle.textContent = 'Full Stack Developer';
        }
    }

    /**
     * Load all content from available endpoints
     */
    async loadAllContent() {
        console.log('Loading all content...');

        // Update hero section first
        await this.updateHeroSection();

        // Load core sections first
        await this.loadCoreContent();

        // Load additional sections
        await this.loadAdditionalContent();
    }

    /**
     * Load core content sections (about, skills, experience, etc.)
     */
    async loadCoreContent() {
        const coreEndpoints = {
            'about': this.loadAboutContent.bind(this),
            'skills': this.loadSkillsContent.bind(this),
            'resume': this.loadExperienceContent.bind(this),
            'experience': this.loadExperienceContent.bind(this),
            'projects': this.loadProjectsContent.bind(this),
            'contact': this.loadContactContent.bind(this),
            'contact_info': this.loadContactContent.bind(this)
        };

        for (const [endpointName, loadFunction] of Object.entries(coreEndpoints)) {
            const endpoint = this.endpoints.find(ep => ep.name === endpointName);
            if (endpoint) {
                try {
                    await loadFunction(endpointName);
                } catch (error) {
                    console.warn(`Failed to load ${endpointName}:`, error);
                }
            }
        }
    }

    /**
     * Load additional content sections for miscellaneous endpoints
     */
    async loadAdditionalContent() {
        const coreEndpointNames = ['about', 'skills', 'resume', 'experience', 'projects', 'contact', 'contact_info'];
        const additionalEndpoints = this.endpoints.filter(ep =>
            !coreEndpointNames.includes(ep.name) &&
            !ep.name.includes('system') &&
            !ep.name.includes('health') &&
            !ep.name.includes('user')
        );

        const additionalContainer = document.getElementById('additionalContent');
        if (!additionalContainer) return;

        additionalContainer.innerHTML = '';

        for (const endpoint of additionalEndpoints) {
            try {
                await this.loadAdditionalSection(endpoint);
            } catch (error) {
                console.warn(`Failed to load ${endpoint.name}:`, error);
            }
        }
    }

    /**
     * Load about content
     */
    async loadAboutContent(endpointName) {
        try {
            const data = await this.api.getEndpointData(endpointName);
            const container = document.getElementById('aboutContent');

            if (data.items && data.items.length > 0) {
                const content = this.extractContent(data.items[0]);
                container.innerHTML = this.formatContent(content);
            } else {
                container.innerHTML = '<p>About information will be added soon.</p>';
            }
        } catch (error) {
            console.warn('Failed to load about content:', error);
            document.getElementById('aboutContent').innerHTML = '<p>About information will be added soon.</p>';
        }
    }

    /**
     * Load skills content
     */
    async loadSkillsContent(endpointName) {
        try {
            const data = await this.api.getEndpointData(endpointName);
            const container = document.getElementById('skillsContent');

            if (data.items && data.items.length > 0) {
                const content = this.extractContent(data.items[0]);
                container.innerHTML = this.formatSkillsContent(content);
            } else {
                container.innerHTML = '<p>Skills information will be added soon.</p>';
            }
        } catch (error) {
            console.warn('Failed to load skills content:', error);
            document.getElementById('skillsContent').innerHTML = '<p>Skills information will be added soon.</p>';
        }
    }

    /**
     * Load experience/resume content
     */
    async loadExperienceContent(endpointName) {
        try {
            const data = await this.api.getEndpointData(endpointName);
            const container = document.getElementById('experienceContent');

            if (data.items && data.items.length > 0) {
                let html = '';
                data.items.forEach(item => {
                    const content = this.extractContent(item);
                    html += this.formatExperienceItem(content, item.meta || item.data?.meta);
                });
                container.innerHTML = html || '<p>Experience information will be added soon.</p>';
            } else {
                container.innerHTML = '<p>Experience information will be added soon.</p>';
            }
        } catch (error) {
            console.warn('Failed to load experience content:', error);
            document.getElementById('experienceContent').innerHTML = '<p>Experience information will be added soon.</p>';
        }
    }

    /**
     * Load projects content
     */
    async loadProjectsContent(endpointName) {
        try {
            const data = await this.api.getEndpointData(endpointName);
            const container = document.getElementById('projectsContent');

            if (data.items && data.items.length > 0) {
                let html = '';
                data.items.forEach(item => {
                    const content = this.extractContent(item);
                    html += this.formatProjectItem(content, item.meta || item.data?.meta);
                });
                container.innerHTML = html || '<p>Projects information will be added soon.</p>';
            } else {
                container.innerHTML = '<p>Projects information will be added soon.</p>';
            }
        } catch (error) {
            console.warn('Failed to load projects content:', error);
            document.getElementById('projectsContent').innerHTML = '<p>Projects information will be added soon.</p>';
        }
    }

    /**
     * Load contact content
     */
    async loadContactContent(endpointName) {
        try {
            const data = await this.api.getEndpointData(endpointName);
            const container = document.getElementById('contactContent');

            if (data.items && data.items.length > 0) {
                const content = this.extractContent(data.items[0]);
                container.innerHTML = this.formatContactContent(content);
            } else {
                container.innerHTML = this.getDefaultContactContent();
            }
        } catch (error) {
            console.warn('Failed to load contact content:', error);
            document.getElementById('contactContent').innerHTML = this.getDefaultContactContent();
        }
    }

    /**
     * Load additional section content
     */
    async loadAdditionalSection(endpoint) {
        try {
            const data = await this.api.getEndpointData(endpoint.name);
            const additionalContainer = document.getElementById('additionalContent');

            if (data.items && data.items.length > 0) {
                const sectionHtml = this.formatAdditionalSection(endpoint, data.items);
                additionalContainer.insertAdjacentHTML('beforeend', sectionHtml);
            }
        } catch (error) {
            console.warn(`Failed to load ${endpoint.name}:`, error);
        }
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
     * Format content with markdown-like styling
     */
    formatContent(content) {
        if (!content) return '<p>No content available.</p>';

        // Convert markdown-like content to HTML
        let html = content
            .replace(/^## (.*$)/gim, '<h3>$1</h3>')
            .replace(/^# (.*$)/gim, '<h2>$1</h2>')
            .replace(/^\* (.*$)/gim, '<li>$1</li>')
            .replace(/^- (.*$)/gim, '<li>$1</li>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');

        // Wrap lists
        html = html.replace(/(<li>.*?<\/li>)/gs, (match) => {
            return match.includes('<ul>') ? match : `<ul>${match}</ul>`;
        });

        // Wrap in paragraphs if not already wrapped
        if (!html.includes('<h') && !html.includes('<ul>') && !html.includes('<p>')) {
            html = `<p>${html}</p>`;
        }

        return `<div class="content-markdown">${html}</div>`;
    }

    /**
     * Format skills content with special styling
     */
    formatSkillsContent(content) {
        const formatted = this.formatContent(content);

        // If content contains lists, create skill categories
        if (formatted.includes('<ul>')) {
            return `<div class="skills-grid">${formatted}</div>`;
        }

        return formatted;
    }

    /**
     * Format experience item
     */
    formatExperienceItem(content, meta) {
        const title = meta?.title || 'Experience';
        const company = meta?.company || '';
        const period = meta?.date || meta?.period || '';

        return `
            <div class="experience-item">
                <div class="experience-header">
                    <div>
                        <h3 class="experience-title">${title}</h3>
                        ${company ? `<p class="experience-company">${company}</p>` : ''}
                    </div>
                    ${period ? `<span class="experience-period">${period}</span>` : ''}
                </div>
                <div class="experience-content">
                    ${this.formatContent(content)}
                </div>
            </div>
        `;
    }

    /**
     * Format project item
     */
    formatProjectItem(content, meta) {
        const title = meta?.title || 'Project';
        const tech = meta?.technology || meta?.tech || '';
        const date = meta?.date || '';

        return `
            <div class="experience-item">
                <div class="experience-header">
                    <div>
                        <h3 class="experience-title">${title}</h3>
                        ${tech ? `<p class="experience-company">${tech}</p>` : ''}
                    </div>
                    ${date ? `<span class="experience-period">${date}</span>` : ''}
                </div>
                <div class="experience-content">
                    ${this.formatContent(content)}
                </div>
            </div>
        `;
    }

    /**
     * Format contact content
     */
    formatContactContent(content) {
        // Check if content contains contact methods
        if (content.includes('@') || content.includes('http') || content.includes('linkedin')) {
            return `
                <div class="contact-methods">
                    ${this.formatContent(content)}
                </div>
            `;
        }

        return this.formatContent(content);
    }

    /**
     * Get default contact content
     */
    getDefaultContactContent() {
        return `
            <div class="contact-methods">
                <div class="contact-method">
                    <i class="fas fa-envelope"></i>
                    <h4>Email</h4>
                    <p>Contact information available upon request</p>
                </div>
                <div class="contact-method">
                    <i class="fab fa-linkedin"></i>
                    <h4>LinkedIn</h4>
                    <p>Professional networking</p>
                </div>
                <div class="contact-method">
                    <i class="fab fa-github"></i>
                    <h4>GitHub</h4>
                    <p>Code repositories and projects</p>
                </div>
            </div>
        `;
    }

    /**
     * Format additional section
     */
    formatAdditionalSection(endpoint, items) {
        const title = this.formatEndpointName(endpoint.name);
        const icon = this.getEndpointIcon(endpoint.name);

        let content = '';
        items.forEach(item => {
            const itemContent = this.extractContent(item);
            content += this.formatContent(itemContent);
        });

        return `
            <div class="additional-card">
                <h3><i class="${icon}"></i> ${title}</h3>
                ${content}
            </div>
        `;
    }

    /**
     * Format endpoint name for display
     */
    formatEndpointName(name) {
        return name
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    /**
     * Get icon for endpoint
     */
    getEndpointIcon(name) {
        const iconMap = {
            'ideas': 'fas fa-lightbulb',
            'favorite_books': 'fas fa-book',
            'books': 'fas fa-book',
            'goals': 'fas fa-target',
            'hobbies': 'fas fa-heart',
            'travel': 'fas fa-plane',
            'photos': 'fas fa-camera',
            'music': 'fas fa-music',
            'movies': 'fas fa-film',
            'quotes': 'fas fa-quote-left',
            'notes': 'fas fa-sticky-note',
            'journal': 'fas fa-journal-whills',
            'tasks': 'fas fa-tasks',
            'calendar': 'fas fa-calendar',
            'reminders': 'fas fa-bell'
        };

        return iconMap[name] || 'fas fa-folder';
    }

    /**
     * Setup smooth scrolling navigation
     */
    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);

                if (targetElement) {
                    const navbar = document.querySelector('.navbar');
                    const navbarHeight = navbar ? navbar.offsetHeight : 0;
                    const targetPosition = targetElement.offsetTop - navbarHeight - 20;

                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        });

        // Update active nav link on scroll
        this.setupScrollSpy();
    }

    /**
     * Setup scroll spy for navigation
     */
    setupScrollSpy() {
        const sections = document.querySelectorAll('.section[id]');
        const navLinks = document.querySelectorAll('.nav-link');

        window.addEventListener('scroll', () => {
            let current = '';
            const navbar = document.querySelector('.navbar');
            const navbarHeight = navbar ? navbar.offsetHeight : 0;

            sections.forEach(section => {
                const sectionTop = section.offsetTop - navbarHeight - 100;
                const sectionHeight = section.offsetHeight;

                if (window.scrollY >= sectionTop && window.scrollY < sectionTop + sectionHeight) {
                    current = section.getAttribute('id');
                }
            });

            navLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === `#${current}`) {
                    link.classList.add('active');
                }
            });
        });
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
            setTimeout(() => {
                loadingScreen.style.opacity = '0';
                setTimeout(() => {
                    loadingScreen.classList.add('hidden');
                    loadingScreen.style.opacity = '1';
                }, 500);
            }, 500);
        }
    }

    /**
     * Show portfolio
     */
    showPortfolio() {
        const portfolio = document.getElementById('portfolio');
        if (portfolio) {
            portfolio.classList.remove('hidden');
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        const loadingScreen = document.getElementById('loadingScreen');
        if (loadingScreen) {
            loadingScreen.innerHTML = `
                <div class="loader">
                    <i class="fas fa-exclamation-triangle" style="font-size: 3rem; color: #ef4444; margin-bottom: 1rem;"></i>
                    <h2>Error Loading Portfolio</h2>
                    <p>${message}</p>
                    <button onclick="location.reload()" class="btn btn-primary" style="margin-top: 1rem;">
                        <i class="fas fa-refresh"></i> Try Again
                    </button>
                </div>
            `;
        }
    }
}

// Initialize portfolio when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing portfolio...');
    window.portfolio = new Portfolio();
});
