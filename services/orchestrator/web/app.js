const API_BASE = 'http://localhost:9000/api/v1';
let token = localStorage.getItem('token');
let currentUser = null;

// Initialize
if (token) {
    validateToken();
} else {
    showAuth();
}

// Auth Functions
function showAuth() {
    document.getElementById('authScreen').classList.remove('hidden');
    document.getElementById('mainApp').classList.add('hidden');
}

function showLogin() {
    document.getElementById('loginForm').classList.remove('hidden');
    document.getElementById('registerForm').classList.add('hidden');
}

function showRegister() {
    document.getElementById('loginForm').classList.add('hidden');
    document.getElementById('registerForm').classList.remove('hidden');
}

async function login() {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    if (!email || !password) {
        showError('Please fill in all fields');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            token = data.access_token;
            localStorage.setItem('token', token);
            currentUser = data.user;
            showSuccess('Login successful!');
            setTimeout(() => {
                document.getElementById('authScreen').classList.add('hidden');
                document.getElementById('mainApp').classList.remove('hidden');
                loadDashboard();
            }, 500);
        } else {
            showError(data.detail || 'Login failed');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

async function register() {
    const name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const role = document.getElementById('registerRole').value;

    if (!name || !email || !password) {
        showError('Please fill in all fields');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password, role })
        });

        const data = await response.json();

        if (response.ok) {
            token = data.access_token;
            localStorage.setItem('token', token);
            currentUser = data.user;
            showSuccess('Registration successful!');
            setTimeout(() => {
                document.getElementById('authScreen').classList.add('hidden');
                document.getElementById('mainApp').classList.remove('hidden');
                loadDashboard();
            }, 500);
        } else {
            showError(data.detail || 'Registration failed');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

function logout() {
    localStorage.removeItem('token');
    token = null;
    currentUser = null;
    location.reload();
}

async function validateToken() {
    try {
        const response = await fetch(`${API_BASE}/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            currentUser = await response.json();
            document.getElementById('authScreen').classList.add('hidden');
            document.getElementById('mainApp').classList.remove('hidden');
            loadDashboard();
        } else {
            showAuth();
        }
    } catch (error) {
        showAuth();
    }
}

function showError(message) {
    const errorDiv = document.getElementById('authError');
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
    setTimeout(() => errorDiv.classList.add('hidden'), 3000);
}

function showSuccess(message) {
    const successDiv = document.getElementById('authSuccess');
    successDiv.textContent = message;
    successDiv.classList.remove('hidden');
    setTimeout(() => successDiv.classList.add('hidden'), 3000);
}

// Navigation
function showPage(page) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
    
    // Remove active class from all nav buttons
    document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
    
    // Show selected page
    document.getElementById('page' + page.charAt(0).toUpperCase() + page.slice(1)).classList.remove('hidden');
    document.getElementById('nav' + page.charAt(0).toUpperCase() + page.slice(1)).classList.add('active');
    
    // Load page data
    switch(page) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'projects':
            loadProjects();
            break;
        case 'activities':
            loadActivities();
            break;
        case 'goals':
            loadGoals();
            break;
        case 'labs':
            loadLabs();
            break;
    }
}

// Dashboard Functions
async function loadDashboard() {
    document.getElementById('userInfo').textContent = `${currentUser.name} (${currentUser.email})`;
    
    // Load health status
    try {
        const health = await apiGet('/health');
        let healthHTML = '<div>';
        healthHTML += `<p>Orchestrator: <span class="status healthy">HEALTHY</span></p>`;
        for (const [service, data] of Object.entries(health.services)) {
            const status = data.status === 'healthy' ? 'healthy' : '';
            healthHTML += `<p>${service.toUpperCase()}: <span class="status ${status}">${data.status.toUpperCase()}</span></p>`;
        }
        healthHTML += '</div>';
        document.getElementById('healthStatus').innerHTML = healthHTML;
    } catch (error) {
        document.getElementById('healthStatus').innerHTML = '<p style="color: #f00;">Failed to load health status</p>';
    }

    // Load stats
    try {
        const dashboard = await apiGet('/dashboard');
        document.getElementById('statProjects').textContent = dashboard.projects?.length || 0;
        document.getElementById('statActivities').textContent = dashboard.activity?.activities_today || 0;
        document.getElementById('statGoals').textContent = dashboard.performance?.active_goals || 0;
        document.getElementById('statLabs').textContent = dashboard.labs?.length || 0;

        // Recent activity
        if (dashboard.activity?.recent_activities?.length > 0) {
            let html = '';
            dashboard.activity.recent_activities.slice(0, 5).forEach(activity => {
                html += `<div class="list-item">
                    <h3>${activity.activity_type}</h3>
                    <p>${activity.description || 'No description'}</p>
                </div>`;
            });
            document.getElementById('recentActivity').innerHTML = html;
        } else {
            document.getElementById('recentActivity').innerHTML = '<p style="color: #aaa;">No recent activities</p>';
        }
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

// Projects Functions
async function loadProjects() {
    const container = document.getElementById('projectsList');
    container.innerHTML = '<div class="loading">Loading projects...</div>';

    try {
        const response = await apiGet('/projects/');
        const projects = response.projects || response || [];
        
        if (!Array.isArray(projects) || projects.length === 0) {
            container.innerHTML = '<p style="color: #aaa;">No projects yet. Create one to get started!</p>';
        } else {
            let html = '';
            projects.forEach(project => {
                html += `<div class="list-item">
                    <h3>${project.name}</h3>
                    <p>${project.description || 'No description'}</p>
                    <p style="font-size: 12px; color: #666; margin-top: 10px;">Created: ${new Date(project.created_at).toLocaleDateString()}</p>
                </div>`;
            });
            container.innerHTML = html;
        }
    } catch (error) {
        container.innerHTML = '<p style="color: #f00;">Failed to load projects: ' + error.message + '</p>';
    }
}

function showCreateProject() {
    document.getElementById('createProjectForm').classList.remove('hidden');
}

function hideCreateProject() {
    document.getElementById('createProjectForm').classList.add('hidden');
    document.getElementById('projectName').value = '';
    document.getElementById('projectDescription').value = '';
}

async function createProject() {
    const name = document.getElementById('projectName').value;
    const description = document.getElementById('projectDescription').value;

    if (!name) {
        alert('Please enter a project name');
        return;
    }

    try {
        await apiPost('/projects/', { name, description });
        hideCreateProject();
        loadProjects();
    } catch (error) {
        alert('Failed to create project: ' + error.message);
    }
}

// Activities Functions
async function loadActivities() {
    const container = document.getElementById('activitiesList');
    container.innerHTML = '<div class="loading">Loading activities...</div>';

    try {
        const response = await apiGet(`/monitoring/activity/${currentUser.id}/today`);
        const activities = response.activities || response || [];
        
        if (!Array.isArray(activities) || activities.length === 0) {
            container.innerHTML = '<p style="color: #aaa;">No activities logged today. Log one to get started!</p>';
        } else {
            let html = '';
            activities.forEach(activity => {
                html += `<div class="list-item">
                    <div class="flex-between">
                        <h3>${activity.activity_type}</h3>
                        <span style="color: #aaa;">${activity.duration || 0} min</span>
                    </div>
                    <p>${activity.description || 'No description'}</p>
                    <p style="font-size: 12px; color: #666; margin-top: 10px;">${new Date(activity.timestamp).toLocaleString()}</p>
                </div>`;
            });
            container.innerHTML = html;
        }
    } catch (error) {
        container.innerHTML = '<p style="color: #f00;">Failed to load activities: ' + error.message + '</p>';
    }
}

function showLogActivity() {
    document.getElementById('logActivityForm').classList.remove('hidden');
}

function hideLogActivity() {
    document.getElementById('logActivityForm').classList.add('hidden');
    document.getElementById('activityDescription').value = '';
}

async function logActivity() {
    const activity_type = document.getElementById('activityType').value;
    const description = document.getElementById('activityDescription').value;
    const duration = parseInt(document.getElementById('activityDuration').value);

    if (!description) {
        alert('Please enter a description');
        return;
    }

    try {
        await apiPost('/monitoring/activity/log', { activity_type, description, duration });
        hideLogActivity();
        loadActivities();
    } catch (error) {
        alert('Failed to log activity: ' + error.message);
    }
}

// Goals Functions
async function loadGoals() {
    const container = document.getElementById('goalsList');
    container.innerHTML = '<div class="loading">Loading goals...</div>';

    try {
        const response = await apiGet(`/performance/user/${currentUser.id}/goals`);
        const goals = response.goals || response || [];
        
        if (!Array.isArray(goals) || goals.length === 0) {
            container.innerHTML = '<p style="color: #aaa;">No goals yet. Create one to track your progress!</p>';
        } else {
            let html = '';
            goals.forEach(goal => {
                html += `<div class="list-item">
                    <div class="flex-between">
                        <h3>${goal.title}</h3>
                        <span style="color: #aaa;">${goal.status}</span>
                    </div>
                    <p>${goal.description || 'No description'}</p>
                    ${goal.target_date ? `<p style="font-size: 12px; color: #666; margin-top: 10px;">Target: ${new Date(goal.target_date).toLocaleDateString()}</p>` : ''}
                </div>`;
            });
            container.innerHTML = html;
        }
    } catch (error) {
        container.innerHTML = '<p style="color: #f00;">Failed to load goals: ' + error.message + '</p>';
    }
}

function showCreateGoal() {
    document.getElementById('createGoalForm').classList.remove('hidden');
}

function hideCreateGoal() {
    document.getElementById('createGoalForm').classList.add('hidden');
    document.getElementById('goalTitle').value = '';
    document.getElementById('goalDescription').value = '';
    document.getElementById('goalTarget').value = '';
}

async function createGoal() {
    const title = document.getElementById('goalTitle').value;
    const description = document.getElementById('goalDescription').value;
    const target_date = document.getElementById('goalTarget').value;

    if (!title) {
        alert('Please enter a goal title');
        return;
    }

    try {
        await apiPost('/performance/goals', { title, description, target_date, status: 'in_progress' });
        hideCreateGoal();
        loadGoals();
    } catch (error) {
        alert('Failed to create goal: ' + error.message);
    }
}

// Labs Functions
async function loadLabs() {
    const container = document.getElementById('labsList');
    container.innerHTML = '<div class="loading">Loading labs...</div>';

    try {
        const response = await apiGet('/research/labs');
        const labs = response.labs || response || [];
        
        if (!Array.isArray(labs) || labs.length === 0) {
            container.innerHTML = '<p style="color: #aaa;">No research labs yet. Create one to start collaborating!</p>';
        } else {
            let html = '';
            labs.forEach(lab => {
                html += `<div class="list-item">
                    <h3>${lab.name}</h3>
                    <p>${lab.description || 'No description'}</p>
                    ${lab.focus_area ? `<p style="font-size: 12px; color: #aaa; margin-top: 5px;">Focus: ${lab.focus_area}</p>` : ''}
                </div>`;
            });
            container.innerHTML = html;
        }
    } catch (error) {
        container.innerHTML = '<p style="color: #f00;">Failed to load labs: ' + error.message + '</p>';
    }
}

function showCreateLab() {
    document.getElementById('createLabForm').classList.remove('hidden');
}

function hideCreateLab() {
    document.getElementById('createLabForm').classList.add('hidden');
    document.getElementById('labName').value = '';
    document.getElementById('labFocus').value = '';
    document.getElementById('labDescription').value = '';
}

async function createLab() {
    const name = document.getElementById('labName').value;
    const focus_area = document.getElementById('labFocus').value;
    const description = document.getElementById('labDescription').value;

    if (!name) {
        alert('Please enter a lab name');
        return;
    }

    try {
        await apiPost('/research/labs', { name, focus_area, description });
        hideCreateLab();
        loadLabs();
    } catch (error) {
        alert('Failed to create lab: ' + error.message);
    }
}

// API Helper Functions
async function apiGet(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
}

async function apiPost(endpoint, data) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
}
