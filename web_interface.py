#!/usr/bin/env python3
"""
Interface Web para Geração de Vídeos LTX-2
Acesse em: http://localhost:7860
"""

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import json
import subprocess
import os
import time
from pathlib import Path
from datetime import datetime
import uuid

app = FastAPI(title="LTX-2 Video Generator")

# Configurações
OUTPUT_DIR = Path("/home/nmaldaner/projetos/VideosDGX/ComfyUI/output")
SCRIPT_PATH = Path("/home/nmaldaner/projetos/VideosDGX/gerar_video_ltx2.py")
JOBS_FILE = Path("/tmp/ltx2_jobs.json")

# Estado dos jobs
jobs = {}

class VideoRequest(BaseModel):
    prompt: str
    negative: str = ""
    width: int = 512
    height: int = 512
    frames: int = 49
    fps: int = 24
    cfg: float = 3.0
    seed: int = 42

def load_jobs():
    """Carrega jobs salvos"""
    global jobs
    if JOBS_FILE.exists():
        try:
            with open(JOBS_FILE) as f:
                jobs = json.load(f)
        except:
            jobs = {}

def save_jobs():
    """Salva jobs"""
    with open(JOBS_FILE, 'w') as f:
        json.dump(jobs, f, indent=2)

# Carregar jobs ao iniciar
load_jobs()

def generate_video(job_id: str, request: VideoRequest):
    """Gera vídeo em background"""
    try:
        jobs[job_id]['status'] = 'processing'
        jobs[job_id]['started_at'] = datetime.now().isoformat()
        save_jobs()

        # Comando
        cmd = [
            "python3", str(SCRIPT_PATH),
            request.prompt,
            "--negative", request.negative,
            "--width", str(request.width),
            "--height", str(request.height),
            "--frames", str(request.frames),
            "--fps", str(request.fps),
            "--cfg", str(request.cfg),
            "--seed", str(request.seed),
            "--output", f"web_{job_id}"
        ]

        # Log do comando
        print(f"\n{'='*60}")
        print(f"🎬 Executando job {job_id}")
        print(f"📝 Comando: {' '.join(cmd)}")
        print(f"{'='*60}\n")

        # Executar
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutos max
        )

        # Salvar logs
        jobs[job_id]['stdout'] = result.stdout
        jobs[job_id]['stderr'] = result.stderr
        jobs[job_id]['returncode'] = result.returncode

        print(f"\n📊 Resultado do job {job_id}:")
        print(f"   Return code: {result.returncode}")
        print(f"   Stdout: {result.stdout[:200]}")
        print(f"   Stderr: {result.stderr[:200]}")

        # Verificar resultado
        if result.returncode == 0:
            # Script submeteu com sucesso, agora aguardar o vídeo ser gerado
            print(f"\n⏳ Aguardando vídeo ser gerado (timeout: 15 minutos)...")
            print(f"   Job ID: {job_id}")

            # Padrão principal esperado
            main_pattern = f"web_{job_id}_*.mp4"
            print(f"   Procurando: {main_pattern}")

            max_wait_time = 900  # 15 minutos
            check_interval = 5   # Verificar a cada 5 segundos
            elapsed = 0
            files = []

            while elapsed < max_wait_time and not files:
                # Procurar arquivos - método mais seguro
                try:
                    all_videos = list(OUTPUT_DIR.glob("*.mp4"))
                    # Filtrar por job_id
                    files = [f for f in all_videos if job_id in f.name]
                except Exception as e:
                    print(f"   ⚠️  Erro ao buscar vídeos: {e}")
                    files = []

                if files:
                    break

                # Aguardar e tentar novamente
                time.sleep(check_interval)
                elapsed += check_interval

                # Log de progresso a cada 30 segundos
                if elapsed % 30 == 0:
                    print(f"   ⏱️  Aguardando... {elapsed}s / {max_wait_time}s")
                    jobs[job_id]['progress'] = f"Aguardando vídeo ({elapsed}s)"
                    save_jobs()

            # Remover duplicatas e pegar o mais recente
            if files:
                files = sorted(set(files), key=lambda x: x.stat().st_mtime, reverse=True)

            print(f"\n🔍 Resultado final após {elapsed}s:")
            print(f"   Encontrados: {len(files)} arquivo(s)")

            if files:
                print(f"   ✅ Vídeo: {files[0].name}")
                jobs[job_id]['status'] = 'completed'
                jobs[job_id]['video_file'] = files[0].name
                jobs[job_id]['completed_at'] = datetime.now().isoformat()
                jobs[job_id]['generation_time'] = f"{elapsed}s"
            else:
                # Listar todos os arquivos recentes no output
                recent_files = sorted(OUTPUT_DIR.glob("*.mp4"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
                print(f"   ❌ Vídeo não encontrado após {elapsed}s!")
                print(f"   📁 Últimos 5 arquivos em output:")
                for f in recent_files:
                    print(f"      - {f.name}")

                jobs[job_id]['status'] = 'error'
                jobs[job_id]['error'] = f'Timeout aguardando vídeo ({elapsed}s). ComfyUI pode estar processando ainda. Verifique ComfyUI/output/ manualmente.'
        else:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['error'] = f'Script retornou código {result.returncode}. Stderr: {result.stderr[:500]}'
            print(f"   ❌ Erro: {jobs[job_id]['error']}")

    except subprocess.TimeoutExpired:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['error'] = 'Timeout (>10 minutos)'
        print(f"   ❌ Timeout!")
    except Exception as e:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['error'] = str(e)
        print(f"   ❌ Exception: {e}")
        import traceback
        traceback.print_exc()

    save_jobs()
    print(f"\n{'='*60}\n")

@app.get("/", response_class=HTMLResponse)
async def home():
    """Página principal"""
    html = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LTX-2 Video Generator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .main-card {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            margin-bottom: 30px;
        }

        .form-group {
            margin-bottom: 25px;
        }

        .form-group label {
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
            font-size: 14px;
        }

        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e1e8ed;
            border-radius: 10px;
            font-size: 16px;
            transition: all 0.3s;
        }

        .form-group input:focus, .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .form-group textarea {
            min-height: 100px;
            resize: vertical;
        }

        .form-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }

        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            width: 100%;
            margin-top: 20px;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .jobs-section {
            margin-top: 30px;
        }

        .job-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: all 0.3s;
        }

        .job-card:hover {
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }

        .job-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .job-prompt {
            font-weight: 600;
            color: #333;
            font-size: 16px;
        }

        .status-badge {
            padding: 6px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-pending {
            background: #ffeaa7;
            color: #d63031;
        }

        .status-processing {
            background: #74b9ff;
            color: #0984e3;
        }

        .status-completed {
            background: #55efc4;
            color: #00b894;
        }

        .status-error {
            background: #fab1a0;
            color: #d63031;
        }

        .job-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-bottom: 15px;
            font-size: 13px;
            color: #666;
        }

        .video-player {
            margin-top: 15px;
            border-radius: 10px;
            overflow: hidden;
        }

        .video-player video {
            width: 100%;
            max-height: 400px;
        }

        .progress-bar {
            height: 4px;
            background: #e1e8ed;
            border-radius: 2px;
            overflow: hidden;
            margin-top: 10px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .info-text {
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-top: 10px;
        }

        .preset-buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }

        .preset-btn {
            padding: 10px;
            background: #f8f9fa;
            border: 2px solid #e1e8ed;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 14px;
        }

        .preset-btn:hover {
            border-color: #667eea;
            background: #f0f2ff;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 LTX-2 Video Generator</h1>
            <p>Crie vídeos incríveis com IA no DGX Spark 2026</p>
        </div>

        <div class="main-card">
            <h2 style="margin-bottom: 20px;">Gerar Novo Vídeo</h2>

            <div class="preset-buttons">
                <button class="preset-btn" onclick="setPreset('quick')">⚡ Rápido (512x512, 2s)</button>
                <button class="preset-btn" onclick="setPreset('hd')">📺 HD (1024x576, 2s)</button>
                <button class="preset-btn" onclick="setPreset('long')">⏱️ Longo (512x512, 5s)</button>
                <button class="preset-btn" onclick="setPreset('quality')">✨ Qualidade (1024x576, 5s)</button>
            </div>

            <form id="videoForm">
                <div class="form-group">
                    <label>Prompt (Descrição do Vídeo)</label>
                    <textarea id="prompt" name="prompt" placeholder="Ex: Um gato caminhando na praia ao pôr do sol, 4k quality, cinematic" required></textarea>
                </div>

                <div class="form-group">
                    <label>Prompt Negativo (Opcional)</label>
                    <textarea id="negative" name="negative" placeholder="Ex: blur, distorted, low quality"></textarea>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Largura</label>
                        <input type="number" id="width" name="width" value="512" min="256" max="1920" step="32">
                    </div>
                    <div class="form-group">
                        <label>Altura</label>
                        <input type="number" id="height" name="height" value="512" min="256" max="1920" step="32">
                    </div>
                    <div class="form-group">
                        <label>Frames</label>
                        <input type="number" id="frames" name="frames" value="49" min="25" max="241">
                    </div>
                    <div class="form-group">
                        <label>FPS</label>
                        <input type="number" id="fps" name="fps" value="24" min="12" max="30">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>CFG Scale (Fidelidade)</label>
                        <input type="number" id="cfg" name="cfg" value="3.0" min="1.0" max="10.0" step="0.5">
                    </div>
                    <div class="form-group">
                        <label>Seed (Aleatória)</label>
                        <input type="number" id="seed" name="seed" value="42" min="0" max="999999">
                    </div>
                </div>

                <p class="info-text">Tempo estimado: <span id="estimatedTime">~77 segundos</span></p>

                <button type="submit" class="btn" id="submitBtn">🚀 Gerar Vídeo</button>
            </form>
        </div>

        <div class="jobs-section">
            <h2 style="color: white; margin-bottom: 20px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">Vídeos</h2>
            <div id="jobsList"></div>
        </div>
    </div>

    <script>
        // Presets
        function setPreset(type) {
            const presets = {
                quick: { width: 512, height: 512, frames: 49 },
                hd: { width: 1024, height: 576, frames: 49 },
                long: { width: 512, height: 512, frames: 121 },
                quality: { width: 1024, height: 576, frames: 121 }
            };

            const preset = presets[type];
            document.getElementById('width').value = preset.width;
            document.getElementById('height').value = preset.height;
            document.getElementById('frames').value = preset.frames;
            updateEstimatedTime();
        }

        // Calcular tempo estimado
        function updateEstimatedTime() {
            const width = parseInt(document.getElementById('width').value);
            const height = parseInt(document.getElementById('height').value);
            const frames = parseInt(document.getElementById('frames').value);

            let baseTime = 77; // 512x512, 49 frames
            let multiplier = (width * height) / (512 * 512);
            multiplier *= frames / 49;

            const estimated = Math.round(baseTime * multiplier);
            const minutes = Math.floor(estimated / 60);
            const seconds = estimated % 60;

            document.getElementById('estimatedTime').textContent =
                minutes > 0 ? `~${minutes}min ${seconds}s` : `~${seconds}s`;
        }

        // Atualizar quando mudar inputs
        ['width', 'height', 'frames'].forEach(id => {
            document.getElementById(id).addEventListener('change', updateEstimatedTime);
        });

        // Submeter formulário
        document.getElementById('videoForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const btn = document.getElementById('submitBtn');
            btn.disabled = true;
            btn.textContent = '⏳ Gerando...';

            const formData = {
                prompt: document.getElementById('prompt').value,
                negative: document.getElementById('negative').value,
                width: parseInt(document.getElementById('width').value),
                height: parseInt(document.getElementById('height').value),
                frames: parseInt(document.getElementById('frames').value),
                fps: parseInt(document.getElementById('fps').value),
                cfg: parseFloat(document.getElementById('cfg').value),
                seed: parseInt(document.getElementById('seed').value)
            };

            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                const result = await response.json();

                if (result.job_id) {
                    alert('✅ Vídeo adicionado à fila!\\nID: ' + result.job_id);
                    loadJobs();
                } else {
                    alert('❌ Erro: ' + (result.error || 'Desconhecido'));
                }
            } catch (error) {
                alert('❌ Erro: ' + error.message);
            }

            btn.disabled = false;
            btn.textContent = '🚀 Gerar Vídeo';
        });

        // Carregar lista de jobs
        async function loadJobs() {
            try {
                const response = await fetch('/api/jobs');
                const jobs = await response.json();

                const container = document.getElementById('jobsList');
                container.innerHTML = '';

                // Ordenar por data (mais recentes primeiro)
                const sortedJobs = Object.entries(jobs).sort((a, b) => {
                    return new Date(b[1].created_at) - new Date(a[1].created_at);
                });

                sortedJobs.forEach(([jobId, job]) => {
                    const card = createJobCard(jobId, job);
                    container.appendChild(card);
                });

                if (sortedJobs.length === 0) {
                    container.innerHTML = '<div class="job-card"><p style="text-align:center;color:#666;">Nenhum vídeo gerado ainda. Crie o primeiro!</p></div>';
                }
            } catch (error) {
                console.error('Erro ao carregar jobs:', error);
            }
        }

        // Criar card de job
        function createJobCard(jobId, job) {
            const card = document.createElement('div');
            card.className = 'job-card';

            const statusClass = 'status-' + job.status;
            const statusText = {
                pending: 'Aguardando',
                processing: 'Processando',
                completed: 'Concluído',
                error: 'Erro'
            }[job.status] || job.status;

            let html = `
                <div class="job-header">
                    <div class="job-prompt">${job.request.prompt.substring(0, 80)}${job.request.prompt.length > 80 ? '...' : ''}</div>
                    <div class="status-badge ${statusClass}">${statusText}</div>
                </div>
                <div class="job-details">
                    <div>📐 ${job.request.width}x${job.request.height}</div>
                    <div>🎞️ ${job.request.frames} frames</div>
                    <div>⚡ ${job.request.fps} FPS</div>
                    <div>🎯 CFG ${job.request.cfg}</div>
                    <div>🎲 Seed ${job.request.seed}</div>
                    <div>🕐 ${new Date(job.created_at).toLocaleString('pt-BR')}</div>
                </div>
            `;

            if (job.status === 'processing') {
                html += '<div class="progress-bar"><div class="progress-fill" style="width: 100%"></div></div>';
            }

            if (job.status === 'completed' && job.video_file) {
                html += `
                    <div class="video-player">
                        <video controls>
                            <source src="/api/video/${job.video_file}" type="video/mp4">
                        </video>
                    </div>
                `;
            }

            if (job.status === 'error') {
                html += `<div style="color: #d63031; margin-top: 10px; font-size: 13px;">❌ ${job.error}</div>`;
            }

            card.innerHTML = html;
            return card;
        }

        // Atualizar jobs a cada 5 segundos
        setInterval(loadJobs, 5000);

        // Carregar jobs ao iniciar
        loadJobs();
    </script>
</body>
</html>
    """
    return html

@app.post("/api/generate")
async def generate(request: VideoRequest, background_tasks: BackgroundTasks):
    """Inicia geração de vídeo"""
    job_id = str(uuid.uuid4())[:8]

    jobs[job_id] = {
        'job_id': job_id,
        'status': 'pending',
        'request': request.dict(),
        'created_at': datetime.now().isoformat()
    }
    save_jobs()

    # Adicionar à fila de background
    background_tasks.add_task(generate_video, job_id, request)

    return {"job_id": job_id, "status": "pending"}

@app.get("/api/jobs")
async def get_jobs():
    """Lista todos os jobs"""
    return jobs

@app.get("/api/video/{filename}")
async def get_video(filename: str):
    """Retorna arquivo de vídeo"""
    file_path = OUTPUT_DIR / filename
    if file_path.exists():
        return FileResponse(file_path)
    return {"error": "Vídeo não encontrado"}

if __name__ == "__main__":
    print("=" * 60)
    print("🎬 LTX-2 Video Generator - Interface Web")
    print("=" * 60)
    print()
    print("🌐 Acesse em seu navegador:")
    print("   http://localhost:7860")
    print()
    print("📁 Vídeos salvos em:")
    print(f"   {OUTPUT_DIR}")
    print()
    print("⌨️  Pressione Ctrl+C para parar")
    print("=" * 60)
    print()

    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="info")
