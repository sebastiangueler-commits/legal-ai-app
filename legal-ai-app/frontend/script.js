// Legal AI Frontend Application
class LegalAIApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000'; // Change this for production
        this.currentUser = null;
        this.token = localStorage.getItem('legal_ai_token');
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupNavigation();
        this.checkAuthStatus();
        this.loadUserCases();
    }

    // Event Listeners Setup
    setupEventListeners() {
        // Navigation toggle for mobile
        const navToggle = document.getElementById('nav-toggle');
        const navMenu = document.getElementById('nav-menu');
        
        if (navToggle && navMenu) {
            navToggle.addEventListener('click', () => {
                navMenu.classList.toggle('active');
            });
        }

        // Form submissions
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');

        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleLogin();
            });
        }

        if (registerForm) {
            registerForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleRegister();
            });
        }

        // Navigation links
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('nav-link')) {
                e.preventDefault();
                const target = e.target.getAttribute('href').substring(1);
                this.handleNavigation(target);
            }
        });

        // Close modals when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target.id);
            }
        });
    }

    // Navigation Setup
    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');
            });
        });
    }

    // Authentication Methods
    async handleLogin() {
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        try {
            this.showLoading();
            const response = await this.apiCall('/auth/token', 'POST', {
                username: email,
                password: password
            });

            if (response.access_token) {
                this.token = response.access_token;
                localStorage.setItem('legal_ai_token', this.token);
                this.currentUser = await this.getCurrentUser();
                this.updateAuthUI();
                this.closeModal('login-modal');
                this.showToast('Inicio de sesión exitoso', 'success');
                this.loadUserCases();
            }
        } catch (error) {
            this.showToast('Error en el inicio de sesión: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async handleRegister() {
        const name = document.getElementById('register-name').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        const confirmPassword = document.getElementById('register-confirm-password').value;

        if (password !== confirmPassword) {
            this.showToast('Las contraseñas no coinciden', 'error');
            return;
        }

        try {
            this.showLoading();
            const response = await this.apiCall('/auth/register', 'POST', {
                full_name: name,
                email: email,
                password: password
            });

            if (response.id) {
                this.showToast('Registro exitoso. Ahora puedes iniciar sesión.', 'success');
                this.closeModal('register-modal');
                this.showModal('login-modal');
            }
        } catch (error) {
            this.showToast('Error en el registro: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async getCurrentUser() {
        try {
            const response = await this.apiCall('/auth/me', 'GET');
            return response;
        } catch (error) {
            console.error('Error getting current user:', error);
            return null;
        }
    }

    logout() {
        this.token = null;
        this.currentUser = null;
        localStorage.removeItem('legal_ai_token');
        this.updateAuthUI();
        this.showToast('Sesión cerrada', 'success');
        this.loadUserCases();
    }

    checkAuthStatus() {
        if (this.token) {
            this.getCurrentUser().then(user => {
                this.currentUser = user;
                this.updateAuthUI();
            });
        }
    }

    updateAuthUI() {
        const loginLink = document.getElementById('login-link');
        const registerLink = document.getElementById('register-link');
        const profileLink = document.getElementById('profile-link');
        const logoutLink = document.getElementById('logout-link');

        if (this.currentUser) {
            if (loginLink) loginLink.classList.add('hidden');
            if (registerLink) registerLink.classList.add('hidden');
            if (profileLink) profileLink.classList.remove('hidden');
            if (logoutLink) logoutLink.classList.remove('hidden');
        } else {
            if (loginLink) loginLink.classList.remove('hidden');
            if (registerLink) registerLink.classList.remove('hidden');
            if (profileLink) profileLink.classList.add('hidden');
            if (logoutLink) logoutLink.classList.add('hidden');
        }
    }

    // Case Analysis Methods
    async analyzeCase() {
        const caseText = document.getElementById('case-text').value;
        const tribunal = document.getElementById('tribunal').value;
        const materia = document.getElementById('materia').value;

        if (!caseText.trim()) {
            this.showToast('Por favor, ingresa el texto del caso', 'warning');
            return;
        }

        try {
            this.showLoading();
            const response = await this.apiCall('/analysis/predict', 'POST', {
                case_text: caseText,
                tribunal: tribunal || null,
                materia: materia || null
            });

            this.displayAnalysisResult(response);
            this.showToast('Análisis completado', 'success');
        } catch (error) {
            this.showToast('Error en el análisis: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    displayAnalysisResult(result) {
        const resultDiv = document.getElementById('analysis-result');
        const predictionValue = document.getElementById('prediction-value');
        const confidence = document.getElementById('confidence');
        const similarCasesList = document.getElementById('similar-cases-list');
        const explanationText = document.getElementById('explanation-text');

        if (result.prediction) {
            predictionValue.textContent = result.prediction;
        }

        if (result.confidence) {
            confidence.textContent = `Confianza: ${(result.confidence * 100).toFixed(1)}%`;
        }

        if (result.similar_cases && result.similar_cases.length > 0) {
            similarCasesList.innerHTML = result.similar_cases.map(case_item => `
                <div class="similar-case-item">
                    <h5>${case_item.tribunal}</h5>
                    <p><strong>Expediente:</strong> ${case_item.expediente}</p>
                    <p><strong>Fecha:</strong> ${new Date(case_item.fecha).toLocaleDateString()}</p>
                    <p><strong>Materia:</strong> ${case_item.materia}</p>
                    <a href="${case_item.url}" target="_blank" class="btn btn-secondary btn-sm">Ver Sentencia</a>
                </div>
            `).join('');
        }

        if (result.explanation) {
            explanationText.innerHTML = `<p>${result.explanation}</p>`;
        }

        resultDiv.classList.remove('hidden');
    }

    // Jurisprudence Search Methods
    async searchJurisprudence() {
        const query = document.getElementById('search-query').value;
        const tribunal = document.getElementById('search-tribunal').value;
        const materia = document.getElementById('search-materia').value;
        const dateFrom = document.getElementById('date-from').value;
        const dateTo = document.getElementById('date-to').value;

        if (!query.trim()) {
            this.showToast('Por favor, ingresa un término de búsqueda', 'warning');
            return;
        }

        try {
            this.showLoading();
            const params = new URLSearchParams({
                query: query,
                ...(tribunal && { tribunal: tribunal }),
                ...(materia && { materia: materia }),
                ...(dateFrom && { date_from: dateFrom }),
                ...(dateTo && { date_to: dateTo })
            });

            const response = await this.apiCall(`/search/query?${params.toString()}`, 'GET');
            this.displaySearchResults(response);
            this.showToast(`Búsqueda completada. ${response.results?.length || 0} resultados encontrados.`, 'success');
        } catch (error) {
            this.showToast('Error en la búsqueda: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    displaySearchResults(response) {
        const resultsDiv = document.getElementById('search-results');
        const resultsCount = document.getElementById('results-count');
        const resultsList = document.getElementById('results-list');

        if (response.results && response.results.length > 0) {
            resultsCount.textContent = `${response.results.length} resultados encontrados`;
            
            resultsList.innerHTML = response.results.map(result => `
                <div class="result-item">
                    <h4>${result.tribunal}</h4>
                    <div class="result-meta">
                        <span><strong>Expediente:</strong> ${result.expediente}</span>
                        <span><strong>Fecha:</strong> ${new Date(result.fecha).toLocaleDateString()}</span>
                        <span><strong>Materia:</strong> ${result.materia}</span>
                    </div>
                    <div class="result-text">
                        ${result.full_text.substring(0, 300)}...
                    </div>
                    <div class="result-actions">
                        <a href="${result.url}" target="_blank" class="btn btn-primary btn-sm">Ver Completo</a>
                        <button class="btn btn-secondary btn-sm" onclick="app.analyzeSimilarCase('${result.id}')">Analizar Similar</button>
                    </div>
                </div>
            `).join('');
        } else {
            resultsCount.textContent = 'No se encontraron resultados';
            resultsList.innerHTML = '<p>No se encontraron sentencias que coincidan con tu búsqueda.</p>';
        }

        resultsDiv.classList.remove('hidden');
    }

    // Document Generation Methods
    async generateDocument() {
        const documentType = document.getElementById('document-type').value;
        const caseDetails = document.getElementById('case-details').value;
        const uploadDocument = document.getElementById('upload-document').files[0];

        if (!documentType || !caseDetails.trim()) {
            this.showToast('Por favor, completa todos los campos requeridos', 'warning');
            return;
        }

        try {
            this.showLoading();
            
            const formData = new FormData();
            formData.append('document_type', documentType);
            formData.append('case_details', caseDetails);
            if (uploadDocument) {
                formData.append('base_document', uploadDocument);
            }

            const response = await this.apiCall('/documents/generate', 'POST', formData, true);
            this.displayGeneratedDocument(response);
            this.showToast('Documento generado exitosamente', 'success');
        } catch (error) {
            this.showToast('Error en la generación del documento: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    displayGeneratedDocument(document) {
        const resultDiv = document.getElementById('document-result');
        const preview = document.getElementById('document-preview');

        if (document.content) {
            preview.textContent = document.content;
        } else if (document.document_url) {
            preview.innerHTML = `<p>Documento generado exitosamente.</p><p><a href="${document.document_url}" target="_blank">Ver documento</a></p>`;
        }

        resultDiv.classList.remove('hidden');
    }

    // Case Management Methods
    showNewCaseForm() {
        const form = document.getElementById('new-case-form');
        if (form) {
            form.classList.remove('hidden');
        }
    }

    cancelNewCase() {
        const form = document.getElementById('new-case-form');
        if (form) {
            form.classList.add('hidden');
            form.reset();
        }
    }

    async createCase() {
        const caseNumber = document.getElementById('case-number').value;
        const caseTitle = document.getElementById('case-title').value;
        const caseDescription = document.getElementById('case-description').value;
        const caseStatus = document.getElementById('case-status').value;
        const casePriority = document.getElementById('case-priority').value;

        if (!caseNumber || !caseTitle || !caseDescription) {
            this.showToast('Por favor, completa todos los campos requeridos', 'warning');
            return;
        }

        try {
            this.showLoading();
            const response = await this.apiCall('/cases/', 'POST', {
                expediente: caseNumber,
                title: caseTitle,
                description: caseDescription,
                status: caseStatus,
                priority: casePriority
            });

            if (response.id) {
                this.showToast('Caso creado exitosamente', 'success');
                this.cancelNewCase();
                this.loadUserCases();
            }
        } catch (error) {
            this.showToast('Error al crear el caso: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async loadUserCases() {
        if (!this.currentUser) {
            const casesGrid = document.getElementById('cases-grid');
            if (casesGrid) {
                casesGrid.innerHTML = '<p>Inicia sesión para ver tus casos</p>';
            }
            return;
        }

        try {
            const response = await this.apiCall('/cases/', 'GET');
            this.displayUserCases(response);
        } catch (error) {
            console.error('Error loading cases:', error);
        }
    }

    displayUserCases(cases) {
        const casesGrid = document.getElementById('cases-grid');
        if (!casesGrid) return;

        if (cases && cases.length > 0) {
            casesGrid.innerHTML = cases.map(case_item => `
                <div class="case-card">
                    <div class="case-header">
                        <span class="case-number">${case_item.expediente}</span>
                        <span class="case-status ${case_item.status}">${this.formatStatus(case_item.status)}</span>
                    </div>
                    <h4 class="case-title">${case_item.title}</h4>
                    <p class="case-description">${case_item.description}</p>
                    <div class="case-meta">
                        <span class="case-priority ${case_item.priority}">${this.formatPriority(case_item.priority)}</span>
                        <span>${new Date(case_item.created_at).toLocaleDateString()}</span>
                    </div>
                    <div class="case-actions">
                        <button class="btn btn-primary btn-sm" onclick="app.editCase('${case_item.id}')">Editar</button>
                        <button class="btn btn-secondary btn-sm" onclick="app.viewCaseDetails('${case_item.id}')">Ver Detalles</button>
                    </div>
                </div>
            `).join('');
        } else {
            casesGrid.innerHTML = '<p>No tienes casos registrados. Crea tu primer caso.</p>';
        }
    }

    formatStatus(status) {
        const statusMap = {
            'iniciado': 'Iniciado',
            'en_proceso': 'En Proceso',
            'resuelto': 'Resuelto',
            'archivado': 'Archivado'
        };
        return statusMap[status] || status;
    }

    formatPriority(priority) {
        const priorityMap = {
            'baja': 'Baja',
            'media': 'Media',
            'alta': 'Alta',
            'urgente': 'Urgente'
        };
        return priorityMap[priority] || priority;
    }

    // Utility Methods
    async apiCall(endpoint, method = 'GET', data = null, isFormData = false) {
        const url = `${this.apiBaseUrl}${endpoint}`;
        const options = {
            method: method,
            headers: {}
        };

        if (this.token) {
            options.headers['Authorization'] = `Bearer ${this.token}`;
        }

        if (data && !isFormData) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(data);
        } else if (data && isFormData) {
            options.body = data;
        }

        const response = await fetch(url, options);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    showLoading() {
        const spinner = document.getElementById('loading-spinner');
        if (spinner) {
            spinner.classList.remove('hidden');
        }
    }

    hideLoading() {
        const spinner = document.getElementById('loading-spinner');
        if (spinner) {
            spinner.classList.add('hidden');
        }
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    handleNavigation(target) {
        switch (target) {
            case 'login':
                this.showModal('login-modal');
                break;
            case 'register':
                this.showModal('register-modal');
                break;
            case 'profile':
                this.showModal('profile-modal');
                this.loadProfileInfo();
                break;
            case 'logout':
                this.logout();
                break;
            default:
                this.scrollToSection(target);
        }
    }

    scrollToSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            section.scrollIntoView({ behavior: 'smooth' });
        }
    }

    async loadProfileInfo() {
        if (this.currentUser) {
            const profileName = document.getElementById('profile-name');
            const profileEmail = document.getElementById('profile-email');
            const profileRole = document.getElementById('profile-role');
            const profileCases = document.getElementById('profile-cases');

            if (profileName) profileName.textContent = this.currentUser.full_name;
            if (profileEmail) profileEmail.textContent = this.currentUser.email;
            if (profileRole) profileRole.textContent = this.currentUser.is_superuser ? 'Administrador' : 'Usuario';
            if (profileCases) profileCases.textContent = 'Cargando...';

            // Load case count
            try {
                const cases = await this.apiCall('/cases/', 'GET');
                if (profileCases) profileCases.textContent = cases?.length || 0;
            } catch (error) {
                if (profileCases) profileCases.textContent = 'Error';
            }
        }
    }

    refreshCases() {
        this.loadUserCases();
        this.showToast('Casos actualizados', 'success');
    }

    editCase(caseId) {
        // Implementation for editing cases
        this.showToast('Función de edición en desarrollo', 'info');
    }

    viewCaseDetails(caseId) {
        // Implementation for viewing case details
        this.showToast('Función de detalles en desarrollo', 'info');
    }

    editProfile() {
        // Implementation for editing profile
        this.showToast('Función de edición de perfil en desarrollo', 'info');
    }

    downloadDocument() {
        // Implementation for downloading documents
        this.showToast('Función de descarga en desarrollo', 'info');
    }

    editDocument() {
        // Implementation for editing documents
        this.showToast('Función de edición de documentos en desarrollo', 'info');
    }

    analyzeSimilarCase(caseId) {
        // Implementation for analyzing similar cases
        this.showToast('Función de análisis similar en desarrollo', 'info');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new LegalAIApp();
});

// Global functions for onclick handlers
function scrollToSection(sectionId) {
    if (window.app) {
        window.app.scrollToSection(sectionId);
    }
}

function analyzeCase() {
    if (window.app) {
        window.app.analyzeCase();
    }
}

function searchJurisprudence() {
    if (window.app) {
        window.app.searchJurisprudence();
    }
}

function generateDocument() {
    if (window.app) {
        window.app.generateDocument();
    }
}

function showNewCaseForm() {
    if (window.app) {
        window.app.showNewCaseForm();
    }
}

function cancelNewCase() {
    if (window.app) {
        window.app.cancelNewCase();
    }
}

function createCase() {
    if (window.app) {
        window.app.createCase();
    }
}

function refreshCases() {
    if (window.app) {
        window.app.refreshCases();
    }
}

function showModal(modalId) {
    if (window.app) {
        window.app.showModal(modalId);
    }
}

function closeModal(modalId) {
    if (window.app) {
        window.app.closeModal(modalId);
    }
}

function editProfile() {
    if (window.app) {
        window.app.editProfile();
    }
}

function downloadDocument() {
    if (window.app) {
        window.app.downloadDocument();
    }
}

function editDocument() {
    if (window.app) {
        window.app.editDocument();
    }
}

// Add smooth scrolling for anchor links
document.addEventListener('DOMContentLoaded', () => {
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
});