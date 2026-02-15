// Configuração dos modelos
const MODELS = {
    ltx2: { name: 'LTX-2', port: 8001, desc: 'Vídeo + Áudio' },
    wan21: { name: 'Wan 2.1', port: 8002, desc: 'Versátil 14B' },
    magi1: { name: 'MAGI-1', port: 8003, desc: 'Vídeos Longos' },
    waver: { name: 'Waver 1.0', port: 8004, desc: 'Batch Rápido' }
};

// Estado global
let jobs = [];
let completedJobs = [];
let statusInterval = null;
let jobsInterval = null;

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    // Event listeners
    document.getElementById('generateForm').addEventListener('submit', handleGenerate);
    document.getElementById('guidance_scale').addEventListener('input', (e) => {
        document.getElementById('guidanceValue').textContent = e.target.value;
    });

    // Verificar status dos modelos
    checkModelsStatus();
    statusInterval = setInterval(checkModelsStatus, 10000); // A cada 10s

    // Verificar jobs
    jobsInterval = setInterval(updateJobs, 3000); // A cada 3s

    // Carregar jobs salvos do localStorage
    loadSavedJobs();
}

// Verificar status dos modelos
async function checkModelsStatus() {
    const statusGrid = document.getElementById('statusGrid');
    const cards = statusGrid.querySelectorAll('.status-card');

    for (let i = 0; i < Object.keys(MODELS).length; i++) {
        const modelKey = Object.keys(MODELS)[i];
        const model = MODELS[modelKey];
        const card = cards[i];

        try {
            const response = await fetch(`http://localhost:${model.port}/info`, {
                method: 'GET',
                timeout: 5000
            });

            if (response.ok) {
                const data = await response.json();
                updateStatusCard(card, modelKey, data, 'online');
            } else {
                updateStatusCard(card, modelKey, null, 'offline');
            }
        } catch (error) {
            updateStatusCard(card, modelKey, null, 'offline');
        }
    }
}

function updateStatusCard(card, modelKey, data, status) {
    const model = MODELS[modelKey];

    card.className = `status-card ${status}`;

    const statusText = card.querySelector('.model-status');
    const memoryText = card.querySelector('.model-memory');

    if (status === 'online' && data) {
        const modelLoaded = data.model?.loaded || false;
        const gpuMem = data.system?.gpu_memory;

        statusText.textContent = modelLoaded ? '✓ Modelo carregado' : '○ Modelo não carregado';
        statusText.style.color = modelLoaded ? 'var(--success)' : 'var(--warning)';

        if (gpuMem && gpuMem.available) {
            memoryText.textContent = `GPU: ${gpuMem.allocated_gb || 0}GB / ${gpuMem.total_gb || 0}GB`;
        } else {
            memoryText.textContent = 'GPU: N/A';
        }
    } else {
        statusText.textContent = '✗ Offline';
        statusText.style.color = 'var(--danger)';
        memoryText.textContent = '-';
    }
}

// Gerar vídeo
async function handleGenerate(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = {
        prompt: formData.get('prompt'),
        duration: parseInt(formData.get('duration')),
        fps: parseInt(formData.get('fps')),
        resolution: formData.get('resolution'),
        guidance_scale: parseFloat(formData.get('guidance_scale'))
    };

    const seed = formData.get('seed');
    if (seed) {
        data.seed = parseInt(seed);
    }

    const modelKey = formData.get('model');
    if (!modelKey) {
        alert('Selecione um modelo!');
        return;
    }

    const model = MODELS[modelKey];
    const btn = document.getElementById('generateBtn');

    btn.disabled = true;
    btn.textContent = 'Enviando...';

    try {
        const response = await fetch(`http://localhost:${model.port}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();

        // Adicionar job à lista
        const job = {
            ...result,
            model: modelKey,
            modelName: model.name,
            prompt: data.prompt,
            duration: data.duration,
            resolution: data.resolution,
            created_at: new Date().toISOString()
        };

        jobs.push(job);
        saveJobs();
        renderJobs();

        // Limpar formulário
        e.target.reset();
        document.getElementById('guidanceValue').textContent = '7.5';

        alert(`Vídeo adicionado à fila!\nJob ID: ${result.job_id}`);
    } catch (error) {
        console.error('Erro ao gerar vídeo:', error);
        alert(`Erro ao gerar vídeo: ${error.message}\n\nVerifique se o modelo está online.`);
    } finally {
        btn.disabled = false;
        btn.textContent = '🎬 Gerar Vídeo';
    }
}

// Atualizar status dos jobs
async function updateJobs() {
    const updatedJobs = [];

    for (const job of jobs) {
        const model = MODELS[job.model];

        try {
            const response = await fetch(`http://localhost:${model.port}/jobs/${job.job_id}`);

            if (response.ok) {
                const data = await response.json();
                const updatedJob = { ...job, ...data };

                if (data.status === 'completed') {
                    // Mover para concluídos
                    if (!completedJobs.find(j => j.job_id === job.job_id)) {
                        completedJobs.unshift(updatedJob);
                    }
                } else {
                    updatedJobs.push(updatedJob);
                }
            } else {
                updatedJobs.push(job);
            }
        } catch (error) {
            console.error(`Erro ao verificar job ${job.job_id}:`, error);
            updatedJobs.push(job);
        }
    }

    jobs = updatedJobs;
    saveJobs();
    renderJobs();
    renderCompletedJobs();
}

// Renderizar jobs em processamento
function renderJobs() {
    const jobsList = document.getElementById('jobsList');

    if (jobs.length === 0) {
        jobsList.innerHTML = '<p class="empty-message">Nenhum vídeo em processamento</p>';
        return;
    }

    jobsList.innerHTML = jobs.map(job => `
        <div class="job-card">
            <div class="job-header">
                <span class="job-id">${job.job_id}</span>
                <span class="job-status ${job.status || 'queued'}">${getStatusText(job.status)}</span>
            </div>
            <div class="job-prompt">"${job.prompt}"</div>
            <div class="job-details">
                <span>🎬 ${job.modelName}</span>
                <span>⏱️ ${job.duration}s</span>
                <span>📐 ${job.resolution}</span>
            </div>
            ${job.progress ? `
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${job.progress}%"></div>
                </div>
                <small style="color: var(--text-muted);">Progresso: ${job.progress}%</small>
            ` : ''}
            ${job.error ? `
                <div style="color: var(--danger); margin-top: 0.5rem; font-size: 0.9rem;">
                    ⚠️ Erro: ${job.error}
                </div>
            ` : ''}
            <div class="job-actions">
                <button class="btn-small btn-danger" onclick="removeJob('${job.job_id}')">
                    Remover
                </button>
            </div>
        </div>
    `).join('');
}

// Renderizar jobs concluídos
function renderCompletedJobs() {
    const completedList = document.getElementById('completedList');

    if (completedJobs.length === 0) {
        completedList.innerHTML = '<p class="empty-message">Nenhum vídeo concluído ainda</p>';
        return;
    }

    completedList.innerHTML = completedJobs.map(job => {
        const model = MODELS[job.model];
        const downloadUrl = `http://localhost:${model.port}/jobs/${job.job_id}/download`;

        return `
            <div class="job-card">
                <div class="job-header">
                    <span class="job-id">${job.job_id}</span>
                    <span class="job-status completed">✓ Concluído</span>
                </div>
                <div class="job-prompt">"${job.prompt}"</div>
                <div class="job-details">
                    <span>🎬 ${job.modelName}</span>
                    <span>⏱️ ${job.duration}s</span>
                    <span>📐 ${job.resolution}</span>
                </div>
                <div class="video-container">
                    <video controls>
                        <source src="${downloadUrl}" type="video/mp4">
                        Seu navegador não suporta vídeo.
                    </video>
                </div>
                <div class="job-actions">
                    <a href="${downloadUrl}" download class="btn-small" style="text-decoration: none;">
                        ⬇️ Download
                    </a>
                    <button class="btn-small btn-danger" onclick="removeCompleted('${job.job_id}')">
                        Remover
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Helpers
function getStatusText(status) {
    const statusMap = {
        'queued': '⏳ Na fila',
        'processing': '⚙️ Processando',
        'completed': '✓ Concluído',
        'failed': '✗ Falhou'
    };
    return statusMap[status] || status;
}

function removeJob(jobId) {
    if (confirm('Remover este job da lista?')) {
        jobs = jobs.filter(j => j.job_id !== jobId);
        saveJobs();
        renderJobs();
    }
}

function removeCompleted(jobId) {
    if (confirm('Remover este vídeo da lista?')) {
        completedJobs = completedJobs.filter(j => j.job_id !== jobId);
        saveJobs();
        renderCompletedJobs();
    }
}

// LocalStorage
function saveJobs() {
    localStorage.setItem('videosdgx_jobs', JSON.stringify(jobs));
    localStorage.setItem('videosdgx_completed', JSON.stringify(completedJobs));
}

function loadSavedJobs() {
    try {
        const savedJobs = localStorage.getItem('videosdgx_jobs');
        const savedCompleted = localStorage.getItem('videosdgx_completed');

        if (savedJobs) {
            jobs = JSON.parse(savedJobs);
            renderJobs();
        }

        if (savedCompleted) {
            completedJobs = JSON.parse(savedCompleted);
            renderCompletedJobs();
        }
    } catch (error) {
        console.error('Erro ao carregar jobs salvos:', error);
    }
}

// Cleanup ao sair
window.addEventListener('beforeunload', () => {
    if (statusInterval) clearInterval(statusInterval);
    if (jobsInterval) clearInterval(jobsInterval);
});
