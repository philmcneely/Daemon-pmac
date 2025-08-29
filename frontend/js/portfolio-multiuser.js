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
        const sections = ['about', 'personal-story', 'skills', 'experience', 'projects', 'achievements', 'goals-values', 'contact'];

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

        // Convert section name to camelCase for container ID
        let containerId = sectionName;
        if (sectionName === 'personal-story') {
            containerId = 'personalStory';
        } else if (sectionName === 'goals-values') {
            containerId = 'goalsValues';
        }

        const container = document.getElementById(`${containerId}Content`);
        if (!container) {
            console.error(`Container not found: ${containerId}Content`);
            return;
        }
        console.log(`Container found for ${sectionName}:`, container);

        try {
            // Special handling for goals-values dual-endpoint section
            if (sectionName === 'goals-values') {
                await this.loadGoalsValuesSection(container, username);
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
     * Format personal story data
     */
    formatPersonalStoryData(items) {
        let html = '<div class="personal-story-container">';
        items.forEach((item, index) => {
            const content = this.extractContent(item);
            const meta = item.meta || {};

            html += '<div class="story-item">';

            // Add story meta information if available
            if (meta.title) {
                html += `<div class="story-meta">
                    <h3 class="story-title">${meta.title}</h3>
                    ${meta.date ? `<span class="story-date">${meta.date}</span>` : ''}
                </div>`;
            }

            // Add the formatted content
            html += `<div class="story-content">${this.formatText(content)}</div>`;

            // Add tags if available
            if (meta.tags && meta.tags.length > 0) {
                html += '<div class="story-tags">';
                meta.tags.forEach(tag => {
                    html += `<span class="story-tag">${tag}</span>`;
                });
                html += '</div>';
            }

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
            html += `<div class="skill-item">${this.formatText(content)}</div>`;
        });
        html += '</div>';
        return html;
    }

    /**
     * Format experience data (resume)
     */
    formatExperienceData(items) {
        if (items.length === 1 && items[0].name) {
            // This is a resume object, format it properly
            return this.formatResumeData(items[0]);
        }

        // Fallback to simple experience list
        let html = '<div class="experience-list">';
        items.forEach(item => {
            const content = this.extractContent(item);
            html += `<div class="experience-item">${this.formatText(content)}</div>`;
        });
        html += '</div>';
        return html;
    }

    /**
     * Format resume data with proper structure
     */
    formatResumeData(resume) {
        let html = '<div class="resume-container">';

        // Header with name and title
        html += '<div class="resume-header">';
        html += `<h2 class="resume-name">${resume.name}</h2>`;
        if (resume.title) {
            html += `<h3 class="resume-title">${resume.title}</h3>`;
        }
        if (resume.summary) {
            html += `<p class="resume-summary">${resume.summary}</p>`;
        }
        html += '</div>';

        // Contact information
        if (resume.contact) {
            html += '<div class="resume-section">';
            html += '<h4>Contact Information</h4>';
            html += '<div class="contact-grid">';
            if (resume.contact.email) html += `<div class="contact-item"><strong>Email:</strong> <a href="mailto:${resume.contact.email}">${resume.contact.email}</a></div>`;
            if (resume.contact.phone) html += `<div class="contact-item"><strong>Phone:</strong> ${resume.contact.phone}</div>`;
            if (resume.contact.location) html += `<div class="contact-item"><strong>Location:</strong> ${resume.contact.location}</div>`;
            if (resume.contact.website) html += `<div class="contact-item"><strong>Website:</strong> <a href="${resume.contact.website}" target="_blank">${resume.contact.website}</a></div>`;
            if (resume.contact.linkedin) html += `<div class="contact-item"><strong>LinkedIn:</strong> <a href="${resume.contact.linkedin}" target="_blank">LinkedIn Profile</a></div>`;
            if (resume.contact.github) html += `<div class="contact-item"><strong>GitHub:</strong> <a href="${resume.contact.github}" target="_blank">GitHub Profile</a></div>`;
            html += '</div>';
            html += '</div>';
        }

        // Experience
        if (resume.experience && resume.experience.length > 0) {
            html += '<div class="resume-section">';
            html += '<h4>Professional Experience</h4>';
            resume.experience.forEach(exp => {
                html += '<div class="experience-entry">';
                html += `<h5 class="position">${exp.position}</h5>`;
                html += `<div class="company-period">`;
                html += `<strong>${exp.company}</strong>`;
                if (exp.start_date || exp.end_date) {
                    html += ` <span class="period">(${exp.start_date || ''} - ${exp.end_date || 'Present'})</span>`;
                }
                html += '</div>';
                if (exp.description) {
                    html += `<p class="description">${exp.description}</p>`;
                }
                if (exp.achievements && exp.achievements.length > 0) {
                    html += '<ul class="achievements">';
                    exp.achievements.forEach(achievement => {
                        html += `<li>${achievement}</li>`;
                    });
                    html += '</ul>';
                }
                if (exp.technologies && exp.technologies.length > 0) {
                    html += '<div class="technologies">';
                    html += '<strong>Technologies:</strong> ';
                    html += exp.technologies.map(tech => `<span class="tech-tag">${tech}</span>`).join(', ');
                    html += '</div>';
                }
                html += '</div>';
            });
            html += '</div>';
        }

        // Education
        if (resume.education && resume.education.length > 0) {
            html += '<div class="resume-section">';
            html += '<h4>Education</h4>';
            resume.education.forEach(edu => {
                html += '<div class="education-entry">';
                html += `<h5>${edu.degree}</h5>`;
                html += `<div class="institution-period">`;
                html += `<strong>${edu.institution}</strong>`;
                if (edu.graduation_date) {
                    html += ` <span class="period">(${edu.graduation_date})</span>`;
                }
                html += '</div>';
                if (edu.details && edu.details.length > 0) {
                    html += '<ul>';
                    edu.details.forEach(detail => {
                        html += `<li>${detail}</li>`;
                    });
                    html += '</ul>';
                }
                html += '</div>';
            });
            html += '</div>';
        }

        // Skills
        if (resume.skills && Object.keys(resume.skills).length > 0) {
            html += '<div class="resume-section">';
            html += '<h4>Technical Skills</h4>';
            html += '<div class="skills-grid">';
            Object.entries(resume.skills).forEach(([category, skills]) => {
                html += '<div class="skill-category">';
                html += `<h6>${category.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}</h6>`;
                if (Array.isArray(skills)) {
                    html += '<div class="skill-tags">';
                    skills.forEach(skill => {
                        html += `<span class="skill-tag">${skill}</span>`;
                    });
                    html += '</div>';
                } else if (typeof skills === 'object') {
                    html += '<div class="skill-details">';
                    Object.entries(skills).forEach(([key, value]) => {
                        html += `<div class="skill-item"><strong>${key}:</strong> ${Array.isArray(value) ? value.join(', ') : value}</div>`;
                    });
                    html += '</div>';
                }
                html += '</div>';
            });
            html += '</div>';
            html += '</div>';
        }

        // Projects
        if (resume.projects && resume.projects.length > 0) {
            html += '<div class="resume-section">';
            html += '<h4>Notable Projects</h4>';
            resume.projects.forEach(project => {
                html += '<div class="project-entry">';
                html += `<h5>${project.name}</h5>`;
                if (project.description) {
                    html += `<p class="description">${project.description}</p>`;
                }
                if (project.technologies && project.technologies.length > 0) {
                    html += '<div class="technologies">';
                    html += '<strong>Technologies:</strong> ';
                    html += project.technologies.map(tech => `<span class="tech-tag">${tech}</span>`).join(', ');
                    html += '</div>';
                }
                if (project.url) {
                    html += `<div class="project-link"><a href="${project.url}" target="_blank">View Project</a></div>`;
                }
                html += '</div>';
            });
            html += '</div>';
        }

        // Certifications
        if (resume.certifications && resume.certifications.length > 0) {
            html += '<div class="resume-section">';
            html += '<h4>Certifications</h4>';
            html += '<ul class="certifications-list">';
            resume.certifications.forEach(cert => {
                html += `<li>`;
                html += `<strong>${cert.name}</strong>`;
                if (cert.issuer) html += ` - ${cert.issuer}`;
                if (cert.date) html += ` (${cert.date})`;
                if (cert.credential_id) html += ` - ID: ${cert.credential_id}`;
                html += `</li>`;
            });
            html += '</ul>';
            html += '</div>';
        }

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
            const meta = item.meta || {};

            html += '<div class="project-item">';

            // Add project meta information if available
            if (meta.title && meta.title !== 'Featured Projects & Portfolio') {
                html += `<div class="project-meta">
                    <h3 class="project-title">${meta.title}</h3>
                    ${meta.date ? `<span class="project-date">${meta.date}</span>` : ''}
                </div>`;
            }

            // Add the formatted content
            html += `<div class="project-content">${this.formatText(content)}</div>`;

            // Add tags if available
            if (meta.tags && meta.tags.length > 0) {
                html += '<div class="project-tags">';
                meta.tags.forEach(tag => {
                    html += `<span class="project-tag">${tag}</span>`;
                });
                html += '</div>';
            }

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
            const meta = item.meta || {};

            html += '<div class="achievement-item">';

            // Add achievement meta information if available
            if (meta.title) {
                html += `<div class="achievement-meta">
                    <h3 class="achievement-title">${meta.title}</h3>
                    ${meta.date ? `<span class="achievement-date">${meta.date}</span>` : ''}
                </div>`;
            }

            // Add the formatted content
            html += `<div class="achievement-content">${this.formatText(content)}</div>`;

            // Add tags if available
            if (meta.tags && meta.tags.length > 0) {
                html += '<div class="achievement-tags">';
                meta.tags.forEach(tag => {
                    html += `<span class="achievement-tag">${tag}</span>`;
                });
                html += '</div>';
            }

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
                const meta = item.meta || {};

                html += '<div class="goals-item">';

                // Add meta information if available
                if (meta.title) {
                    html += `<div class="goals-meta">
                        <h4 class="goals-title">${meta.title}</h4>
                        ${meta.date ? `<span class="goals-date">${meta.date}</span>` : ''}
                    </div>`;
                }

                // Add the formatted content
                html += `<div class="goals-content">${this.formatText(content)}</div>`;

                // Add tags if available
                if (meta.tags && meta.tags.length > 0) {
                    html += '<div class="goals-tags">';
                    meta.tags.forEach(tag => {
                        html += `<span class="goals-tag">${tag}</span>`;
                    });
                    html += '</div>';
                }

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
                const meta = item.meta || {};

                html += '<div class="values-item">';

                // Add meta information if available
                if (meta.title) {
                    html += `<div class="values-meta">
                        <h4 class="values-title">${meta.title}</h4>
                        ${meta.date ? `<span class="values-date">${meta.date}</span>` : ''}
                    </div>`;
                }

                // Add the formatted content
                html += `<div class="values-content">${this.formatText(content)}</div>`;

                // Add tags if available
                if (meta.tags && meta.tags.length > 0) {
                    html += '<div class="values-tags">';
                    meta.tags.forEach(tag => {
                        html += `<span class="values-tag">${tag}</span>`;
                    });
                    html += '</div>';
                }

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
        return `<div class="contact-content">${this.formatText(content)}</div>`;
    }

    /**
     * Load goals and values section with dual-endpoint support
     */
    async loadGoalsValuesSection(container, username = null) {
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
                promises.push(this.api.getEndpointData('goals', username));
            } else {
                promises.push(Promise.resolve([]));
            }

            if (valuesEndpoint) {
                promises.push(this.api.getEndpointData('values', username));
            } else {
                promises.push(Promise.resolve([]));
            }

            const [goalsData, valuesData] = await Promise.all(promises);

            console.log('Goals data:', goalsData);
            console.log('Values data:', valuesData);

            // Format and display the combined data
            const formattedHtml = await this.formatGoalsValuesData(goalsData, valuesData);
            container.innerHTML = formattedHtml;

            console.log('Goals & Values section loaded successfully');

        } catch (error) {
            console.error('Failed to load Goals & Values section:', error);
            container.innerHTML = '<p>Failed to load goals and values information.</p>';
        }
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
     * Format text content (with markdown support)
     */
    formatText(content) {
        if (!content) return 'No content available.';

        // Convert markdown to HTML
        return this.markdownToHTML(content);
    }

    /**
     * Convert markdown to HTML
     */
    markdownToHTML(markdown) {
        if (!markdown) return '';

        let html = markdown;

        // Handle headings (### before ## before #)
        html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

        // Handle bold text
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

        // Handle italic text
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

        // Handle inline code
        html = html.replace(/`(.+?)`/g, '<code>$1</code>');

        // Handle code blocks
        html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            return `<pre><code class="language-${lang || 'text'}">${this.escapeHtml(code.trim())}</code></pre>`;
        });

        // Handle links
        html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank">$1</a>');

        // Handle lists (unordered)
        html = html.replace(/^[\-\*\+] (.+)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/gs, (match) => {
            return '<ul>' + match + '</ul>';
        });

        // Handle ordered lists
        html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
        // Note: This is a simplified approach for ordered lists

        // Handle line breaks and paragraphs
        html = html.split('\n\n').map(paragraph => {
            paragraph = paragraph.trim();
            if (!paragraph) return '';

            // Don't wrap existing HTML elements in paragraphs
            if (paragraph.match(/^<(h[1-6]|ul|ol|li|pre|code|blockquote)/)) {
                return paragraph;
            }

            // Handle single line breaks within paragraphs
            paragraph = paragraph.replace(/\n/g, '<br>');

            return `<p>${paragraph}</p>`;
        }).join('');

        // Clean up any double-wrapped lists
        html = html.replace(/<ul><ul>/g, '<ul>');
        html = html.replace(/<\/ul><\/ul>/g, '</ul>');

        // Handle blockquotes
        html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');

        // Handle horizontal rules
        html = html.replace(/^---$/gm, '<hr>');

        // Handle emoji shortcuts (basic ones)
        html = html.replace(/:rocket:/g, '🚀');
        html = html.replace(/:cloud:/g, '☁️');
        html = html.replace(/:lock:/g, '🔒');
        html = html.replace(/:chart_with_upwards_trend:/g, '📊');

        return html;
    }

    /**
     * Escape HTML characters
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
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
                        <a href="#personal-story" class="nav-link">My Story</a>
                        <a href="#skills" class="nav-link">Skills</a>
                        <a href="#experience" class="nav-link">Experience</a>
                        <a href="#projects" class="nav-link">Projects</a>
                        <a href="#achievements" class="nav-link">Achievements</a>
                        <a href="#goals-values" class="nav-link">Goals & Values</a>
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

            <!-- Personal Story Section -->
            <section id="personal-story" class="section bg-light">
                <div class="container">
                    <h2 class="section-title">My Story</h2>
                    <div id="personalStoryContent" class="content-area">
                        <div class="loading-content">Loading...</div>
                    </div>
                </div>
            </section>

            <!-- Skills Section -->
            <section id="skills" class="section">
                <div class="container">
                    <h2 class="section-title">Skills</h2>
                    <div id="skillsContent" class="content-area">
                        <div class="loading-content">Loading...</div>
                    </div>
                </div>
            </section>

            <!-- Experience Section -->
            <section id="experience" class="section bg-light">
                <div class="container">
                    <h2 class="section-title">Experience</h2>
                    <div id="experienceContent" class="content-area">
                        <div class="loading-content">Loading...</div>
                    </div>
                </div>
            </section>

            <!-- Projects Section -->
            <section id="projects" class="section">
                <div class="container">
                    <h2 class="section-title">Projects</h2>
                    <div id="projectsContent" class="content-area">
                        <div class="loading-content">Loading...</div>
                    </div>
                </div>
            </section>

            <!-- Achievements Section -->
            <section id="achievements" class="section bg-light">
                <div class="container">
                    <h2 class="section-title">Achievements</h2>
                    <div id="achievementsContent" class="content-area">
                        <div class="loading-content">Loading...</div>
                    </div>
                </div>
            </section>

            <!-- Goals & Values Section -->
            <section id="goals-values" class="section">
                <div class="container">
                    <h2 class="section-title">Goals & Values</h2>
                    <div id="goalsValuesContent" class="content-area">
                        <div class="loading-content">Loading...</div>
                    </div>
                </div>
            </section>

            <!-- Contact Section -->
            <section id="contact" class="section bg-light">
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
