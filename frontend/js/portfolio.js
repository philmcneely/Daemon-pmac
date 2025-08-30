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

        // Load all sections in order
        await this.loadAllSections();
    }

    /**
     * Load all portfolio sections
     */
    async loadAllSections() {
        const sections = ['about', 'personal-story', 'skills', 'experience', 'projects', 'achievements', 'goals-values', 'hobbies', 'ideas-philosophy', 'learning-recommendations', 'contact'];

        console.log('Available endpoints:', this.endpoints.map(e => e.name));
        console.log('Loading sections:', sections);

        for (const section of sections) {
            try {
                console.log(`Starting to load section: ${section}`);
                await this.loadSectionContent(section);
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
    async loadSectionContent(sectionName) {
        console.log(`Loading section: ${sectionName}`);

        // Convert section name to camelCase for container ID
        let containerId = sectionName;
        if (sectionName === 'personal-story') {
            containerId = 'personalStory';
        } else if (sectionName === 'goals-values') {
            containerId = 'goalsValues';
        } else if (sectionName === 'ideas-philosophy') {
            containerId = 'ideasPhilosophy';
        } else if (sectionName === 'learning-recommendations') {
            containerId = 'learningRecommendations';
        }

        const container = document.getElementById(`${containerId}Content`);
        if (!container) {
            console.error(`Container not found: ${containerId}Content`);
            return;
        }
        console.log(`Container found for ${sectionName}:`, container);

        try {
            // Special handling for dual/triple-endpoint sections
            if (sectionName === 'goals-values') {
                await this.loadGoalsValuesSection(container);
                return;
            }
            if (sectionName === 'ideas-philosophy') {
                await this.loadIdeasPhilosophySection(container);
                return;
            }
            if (sectionName === 'learning-recommendations') {
                await this.loadLearningRecommendationsSection(container);
                return;
            }

            // Find the endpoint
            const endpoint = this.endpoints.find(ep =>
                ep.name === sectionName ||
                (sectionName === 'experience' && ep.name === 'resume') ||
                (sectionName === 'personal-story' && ep.name === 'personal_story')
            );

            if (!endpoint) {
                console.warn(`Endpoint not found for section: ${sectionName}`);
                console.log('Available endpoints:', this.endpoints.map(e => e.name));
                container.innerHTML = `<p>No ${sectionName} information available.</p>`;
                return;
            }

            console.log(`Found endpoint for ${sectionName}:`, endpoint);

            // Get the data
            console.log(`Calling API for endpoint: ${endpoint.name}`);
            const data = await this.api.getEndpointData(endpoint.name);
            console.log(`Data received for ${sectionName}:`, data);

            if (data && data.items && data.items.length > 0) {
                console.log(`Formatting ${data.items.length} items for ${sectionName}`);
                container.innerHTML = this.formatSectionData(sectionName, data.items);
                console.log(`Successfully loaded ${sectionName} with ${data.items.length} items`);
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
            case 'personal-story':
                return this.formatPersonalStoryData(items);
            case 'skills':
                return this.formatSkillsData(items);
            case 'experience':
                return this.formatExperienceData(items);
            case 'projects':
                return this.formatProjectsData(items);
            case 'achievements':
                return this.formatAchievementsData(items);
            case 'goals-values':
                // This should not be called as goals-values has special handling
                return this.formatGoalsValuesData([], []);
            case 'hobbies':
                return this.formatHobbiesData(items);
            case 'ideas-philosophy':
                // This should not be called as ideas-philosophy has special handling
                return this.formatIdeasPhilosophyData([], []);
            case 'learning-recommendations':
                // This should not be called as learning-recommendations has special handling
                return this.formatLearningRecommendationsData([], [], []);
            case 'contact':
                return this.formatContactData(items[0]);
            default:
                return this.formatGenericData(items);
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
     * Format about data
     */
    formatAboutData(item) {
        const content = this.extractContent(item);
        return `<div class="about-content">${this.formatContent(content)}</div>`;
    }

    /**
     * Format personal story data
     */
    formatPersonalStoryData(items) {
        let html = '<div class="personal-story-container">';
        items.forEach((item, index) => {
            const content = this.extractContent(item);
            html += '<div class="story-item">';
            html += `<div class="story-content">${this.formatContent(content)}</div>`;
            html += '</div>';
        });
        html += '</div>';
        return html;
    }

    /**
     * Format skills data
     */
    formatSkillsData(items) {
        let html = '<div class="skills-grid">';
        items.forEach(item => {
            const content = this.extractContent(item);
            html += `<div class="skill-item">${this.formatContent(content)}</div>`;
        });
        html += '</div>';
        return html;
    }

    /**
     * Format experience data (resume)
     */
    formatExperienceData(items) {
        let html = '<div class="experience-list">';
        items.forEach(item => {
            const content = this.extractContent(item);
            html += `<div class="experience-item">${this.formatContent(content)}</div>`;
        });
        html += '</div>';
        return html;
    }

    /**
     * Format projects data
     */
    formatProjectsData(items) {
        let html = '<div class="projects-container">';
        items.forEach((item, index) => {
            const content = this.extractContent(item);
            html += '<div class="project-item">';
            html += `<div class="project-content">${this.formatContent(content)}</div>`;
            html += '</div>';
        });
        html += '</div>';
        return html;
    }

    /**
     * Format achievements data
     */
    formatAchievementsData(items) {
        let html = '<div class="achievements-container">';
        items.forEach((item, index) => {
            const content = this.extractContent(item);
            html += '<div class="achievement-item">';
            html += `<div class="achievement-content">${this.formatContent(content)}</div>`;
            html += '</div>';
        });
        html += '</div>';
        return html;
    }

    /**
     * Format goals-values data (dual-endpoint section)
     */
    async formatGoalsValuesData(goalsData, valuesData) {
        let html = '<div class="goals-values-container">';

        // Goals Section
        if (goalsData && goalsData.length > 0) {
            html += '<div class="goals-section">';
            html += '<h3 class="subsection-title">🎯 Goals</h3>';
            html += '<div class="goals-items">';

            goalsData.forEach((item, index) => {
                const content = this.extractContent(item);
                html += '<div class="goals-item">';
                html += `<div class="goals-content">${this.formatContent(content)}</div>`;
                html += '</div>';
            });

            html += '</div>';
            html += '</div>';
        }

        // Values Section
        if (valuesData && valuesData.length > 0) {
            html += '<div class="values-section">';
            html += '<h3 class="subsection-title">💎 Values</h3>';
            html += '<div class="values-items">';

            valuesData.forEach((item, index) => {
                const content = this.extractContent(item);
                html += '<div class="values-item">';
                html += `<div class="values-content">${this.formatContent(content)}</div>`;
                html += '</div>';
            });

            html += '</div>';
            html += '</div>';
        }

        html += '</div>';
        return html;
    }

    /**
     * Format hobbies data
     */
    formatHobbiesData(items) {
        let html = '<div class="hobbies-container">';
        items.forEach((item, index) => {
            const content = this.extractContent(item);
            html += '<div class="hobby-item">';
            html += `<div class="hobby-content">${this.formatContent(content)}</div>`;
            html += '</div>';
        });
        html += '</div>';
        return html;
    }

    /**
     * Format ideas-philosophy data (dual-endpoint section)
     */
    async formatIdeasPhilosophyData(ideasData, quotesData) {
        let html = '<div class="ideas-philosophy-container">';

        // Ideas Section
        if (ideasData && ideasData.length > 0) {
            html += '<div class="ideas-section">';
            html += '<h3 class="subsection-title">💡 Ideas</h3>';
            html += '<div class="ideas-items">';

            ideasData.forEach((item, index) => {
                const content = this.extractContent(item);
                html += '<div class="ideas-item">';
                html += `<div class="ideas-content">${this.formatContent(content)}</div>`;
                html += '</div>';
            });

            html += '</div>';
            html += '</div>';
        }

        // Quotes Section
        if (quotesData && quotesData.length > 0) {
            html += '<div class="quotes-section">';
            html += '<h3 class="subsection-title">💬 Philosophy</h3>';
            html += '<div class="quotes-items">';

            quotesData.forEach((item, index) => {
                const content = this.extractContent(item);
                html += '<div class="quotes-item">';
                html += `<div class="quotes-content">${this.formatContent(content)}</div>`;
                html += '</div>';
            });

            html += '</div>';
            html += '</div>';
        }

        html += '</div>';
        return html;
    }

    /**
     * Format learning-recommendations data (triple-endpoint section)
     */
    async formatLearningRecommendationsData(learningData, recommendationsData, booksData) {
        let html = '<div class="learning-recommendations-container">';

        // Learning Section
        if (learningData && learningData.length > 0) {
            html += '<div class="learning-section">';
            html += '<h3 class="subsection-title">🎓 Learning</h3>';
            html += '<div class="learning-items">';

            learningData.forEach((item, index) => {
                const content = this.extractContent(item);
                html += '<div class="learning-item">';
                html += `<div class="learning-content">${this.formatContent(content)}</div>`;
                html += '</div>';
            });

            html += '</div>';
            html += '</div>';
        }

        // Recommendations Section
        if (recommendationsData && recommendationsData.length > 0) {
            html += '<div class="recommendations-section">';
            html += '<h3 class="subsection-title">📋 Recommendations</h3>';
            html += '<div class="recommendations-items">';

            recommendationsData.forEach((item, index) => {
                const content = this.extractContent(item);
                html += '<div class="recommendations-item">';
                html += `<div class="recommendations-content">${this.formatContent(content)}</div>`;
                html += '</div>';
            });

            html += '</div>';
            html += '</div>';
        }

        // Books Section
        if (booksData && booksData.length > 0) {
            html += '<div class="books-section">';
            html += '<h3 class="subsection-title">📚 Favorite Books</h3>';
            html += '<div class="books-items">';

            booksData.forEach((item, index) => {
                const content = this.extractContent(item);
                html += '<div class="books-item">';
                html += `<div class="books-content">${this.formatContent(content)}</div>`;
                html += '</div>';
            });

            html += '</div>';
            html += '</div>';
        }

        html += '</div>';
        return html;
    }

    /**
     * Format contact data
     */
    formatContactData(item) {
        const content = this.extractContent(item);
        return `<div class="contact-content">${this.formatContent(content)}</div>`;
    }

    /**
     * Load goals and values section with dual-endpoint support
     */
    async loadGoalsValuesSection(container) {
        try {
            console.log('Loading Goals & Values section with dual endpoints...');

            // Show loading state
            container.innerHTML = '<div class="loading-content">Loading goals and values...</div>';

            // Find both endpoints
            const goalsEndpoint = this.endpoints.find(ep => ep.name === 'goals');
            const valuesEndpoint = this.endpoints.find(ep => ep.name === 'values');

            if (!goalsEndpoint && !valuesEndpoint) {
                container.innerHTML = '<p>No goals or values information available.</p>';
                return;
            }

            // Load data from both endpoints concurrently
            const promises = [];
            if (goalsEndpoint) {
                promises.push(this.api.getEndpointData('goals'));
            } else {
                promises.push(Promise.resolve({items: []}));
            }

            if (valuesEndpoint) {
                promises.push(this.api.getEndpointData('values'));
            } else {
                promises.push(Promise.resolve({items: []}));
            }

            const [goalsData, valuesData] = await Promise.all(promises);

            console.log('Goals data:', goalsData);
            console.log('Values data:', valuesData);

            // Format and display the combined data
            const formattedHtml = await this.formatGoalsValuesData(
                goalsData.items || [],
                valuesData.items || []
            );
            container.innerHTML = formattedHtml;

            console.log('Goals & Values section loaded successfully');

        } catch (error) {
            console.error('Failed to load Goals & Values section:', error);
            container.innerHTML = '<p>Failed to load goals and values information.</p>';
        }
    }

    /**
     * Load ideas and philosophy section with dual-endpoint support
     */
    async loadIdeasPhilosophySection(container) {
        try {
            console.log('Loading Ideas & Philosophy section with dual endpoints...');

            // Show loading state
            container.innerHTML = '<div class="loading-content">Loading ideas and philosophy...</div>';

            // Find both endpoints
            const ideasEndpoint = this.endpoints.find(ep => ep.name === 'ideas');
            const quotesEndpoint = this.endpoints.find(ep => ep.name === 'quotes');

            if (!ideasEndpoint && !quotesEndpoint) {
                container.innerHTML = '<p>No ideas or philosophy information available.</p>';
                return;
            }

            // Load data from both endpoints concurrently
            const promises = [];
            if (ideasEndpoint) {
                promises.push(this.api.getEndpointData('ideas'));
            } else {
                promises.push(Promise.resolve({items: []}));
            }

            if (quotesEndpoint) {
                promises.push(this.api.getEndpointData('quotes'));
            } else {
                promises.push(Promise.resolve({items: []}));
            }

            const [ideasData, quotesData] = await Promise.all(promises);

            console.log('Ideas data:', ideasData);
            console.log('Quotes data:', quotesData);

            // Format and display the combined data
            const formattedHtml = await this.formatIdeasPhilosophyData(
                ideasData.items || [],
                quotesData.items || []
            );
            container.innerHTML = formattedHtml;

            console.log('Ideas & Philosophy section loaded successfully');

        } catch (error) {
            console.error('Failed to load Ideas & Philosophy section:', error);
            container.innerHTML = '<p>Failed to load ideas and philosophy information.</p>';
        }
    }

    /**
     * Load learning and recommendations section with triple-endpoint support
     */
    async loadLearningRecommendationsSection(container) {
        try {
            console.log('Loading Learning & Recommendations section with triple endpoints...');

            // Show loading state
            container.innerHTML = '<div class="loading-content">Loading learning and recommendations...</div>';

            // Find all three endpoints
            const learningEndpoint = this.endpoints.find(ep => ep.name === 'learning');
            const recommendationsEndpoint = this.endpoints.find(ep => ep.name === 'recommendations');
            const booksEndpoint = this.endpoints.find(ep => ep.name === 'favorite_books');

            if (!learningEndpoint && !recommendationsEndpoint && !booksEndpoint) {
                container.innerHTML = '<p>No learning or recommendations information available.</p>';
                return;
            }

            // Load data from all three endpoints concurrently
            const promises = [];
            if (learningEndpoint) {
                promises.push(this.api.getEndpointData('learning'));
            } else {
                promises.push(Promise.resolve({items: []}));
            }

            if (recommendationsEndpoint) {
                promises.push(this.api.getEndpointData('recommendations'));
            } else {
                promises.push(Promise.resolve({items: []}));
            }

            if (booksEndpoint) {
                promises.push(this.api.getEndpointData('favorite_books'));
            } else {
                promises.push(Promise.resolve({items: []}));
            }

            const [learningData, recommendationsData, booksData] = await Promise.all(promises);

            console.log('Learning data:', learningData);
            console.log('Recommendations data:', recommendationsData);
            console.log('Books data:', booksData);

            // Format and display the combined data
            const formattedHtml = await this.formatLearningRecommendationsData(
                learningData.items || [],
                recommendationsData.items || [],
                booksData.items || []
            );
            container.innerHTML = formattedHtml;

            console.log('Learning & Recommendations section loaded successfully');

        } catch (error) {
            console.error('Failed to load Learning & Recommendations section:', error);
            container.innerHTML = '<p>Failed to load learning and recommendations information.</p>';
        }
    }

    /**
     * Format generic data
     */
    formatGenericData(items) {
        let html = '<div class="generic-content">';
        items.forEach(item => {
            const content = this.extractContent(item);
            html += `<div class="content-item">${this.formatContent(content)}</div>`;
        });
        html += '</div>';
        return html;
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
