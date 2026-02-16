#!/usr/bin/env python3
"""
Interface Web para Geração de Vídeos LTX-2 (Versão 2 - Não Bloqueante)
Acesse em: http://localhost:7860
"""

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel
import uvicorn
import json
import subprocess
import os
import time
from pathlib import Path
from datetime import datetime
import uuid

app = FastAPI(title="LTX-2 Video Generator v2")

# Configurações
OUTPUT_DIR = Path("/home/nmaldaner/projetos/VideosDGX/ComfyUI/output")
SCRIPT_PATH = Path("/home/nmaldaner/projetos/VideosDGX/gerar_video_ltx2.py")
JOBS_FILE = Path("/tmp/ltx2_jobs_v2.json")

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

def submit_video(job_id: str, request: VideoRequest):
    """Submete vídeo para geração (NÃO espera terminar)"""
    try:
        jobs[job_id]['status'] = 'submitting'
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

        print(f"\n{'='*60}")
        print(f"🎬 Submetendo job {job_id}")
        print(f"📝 Prompt: {request.prompt[:50]}...")
        print(f"{'='*60}")

        # Executar (retorna imediatamente após submeter)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # Apenas 30s para submeter
        )

        jobs[job_id]['submitted_at'] = datetime.now().isoformat()
        jobs[job_id]['returncode'] = result.returncode

        if result.returncode == 0 and "SUCESSO" in result.stdout:
            jobs[job_id]['status'] = 'processing'
            print(f"✅ Job {job_id} submetido com sucesso!")
        else:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['error'] = f"Falha ao submeter: {result.stderr[:200]}"
            print(f"❌ Job {job_id} falhou: {result.stderr[:200]}")

        save_jobs()

    except subprocess.TimeoutExpired:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['error'] = 'Timeout ao submeter (>30s)'
        save_jobs()
    except Exception as e:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['error'] = str(e)
        save_jobs()

    print(f"{'='*60}\n")

def check_video_ready(job_id: str):
    """Verifica se o vídeo foi gerado"""
    try:
        # Procurar vídeos com o job_id no nome
        all_videos = list(OUTPUT_DIR.glob("*.mp4"))
        videos = [f for f in all_videos if job_id in f.name]

        if videos:
            # Pegar o mais recente
            video = sorted(videos, key=lambda x: x.stat().st_mtime, reverse=True)[0]
            return video.name
        return None
    except:
        return None

@app.get("/", response_class=HTMLResponse)
async def home():
    """Página principal"""
    html = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LTX-2 Video Generator v2</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
        }

        .form-group input, .form-group textarea {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e1e8ed;
            border-radius: 10px;
            font-size: 16px;
        }

        .form-group textarea {
            min-height: 100px;
            resize: vertical;
        }

        .form-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
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
            width: 100%;
            margin-top: 20px;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
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
            font-size: 14px;
        }

        .preset-btn:hover {
            border-color: #667eea;
            background: #f0f2ff;
        }

        .job-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .job-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .status-badge {
            padding: 6px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-submitting { background: #ffeaa7; color: #d63031; }
        .status-processing { background: #74b9ff; color: #0984e3; }
        .status-completed { background: #55efc4; color: #00b894; }
        .status-error { background: #fab1a0; color: #d63031; }

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
            margin-top: 10px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            width: 100%;
            animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 LTX-2 Video Generator v2</h1>
            <p>Versão Otimizada - Não Bloqueante</p>
        </div>

        <div class="main-card">
            <h2 style="margin-bottom: 20px;">Gerar Novo Vídeo</h2>

            <div class="preset-buttons">
                <button class="preset-btn" onclick="setPreset('quick')">⚡ Rápido (512x512, 2s)</button>
                <button class="preset-btn" onclick="setPreset('hd')">📺 HD (1024x576, 2s)</button>
                <button class="preset-btn" onclick="setPreset('long')">⏱️ Longo (512x512, 5s)</button>
            </div>

            <form id="videoForm">
                <div class="form-group">
                    <label>Prompt</label>
                    <textarea id="prompt" required placeholder="Ex: um cachorro correndo"></textarea>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Largura</label>
                        <input type="number" id="width" value="512" min="256" max="1920" step="32">
                    </div>
                    <div class="form-group">
                        <label>Altura</label>
                        <input type="number" id="height" value="512" min="256" max="1920" step="32">
                    </div>
                    <div class="form-group">
                        <label>Frames</label>
                        <input type="number" id="frames" value="49" min="25" max="241">
                    </div>
                </div>

                <button type="submit" class="btn">🚀 Gerar Vídeo</button>
            </form>
        </div>

        <div class="jobs-section">
            <h2 style="color: white; margin-bottom: 20px;">Vídeos</h2>
            <div id="jobsList"></div>
        </div>
    </div>

    <script>
        function setPreset(type) {
            const presets = {
                quick: { width: 512, height: 512, frames: 49 },
                hd: { width: 1024, height: 576, frames: 49 },
                long: { width: 512, height: 512, frames: 121 }
            };
            const p = presets[type];
            document.getElementById('width').value = p.width;
            document.getElementById('height').value = p.height;
            document.getElementById('frames').value = p.frames;
        }

        document.getElementById('videoForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const data = {
                prompt: document.getElementById('prompt').value,
                negative: "",
                width: parseInt(document.getElementById('width').value),
                height: parseInt(document.getElementById('height').value),
                frames: parseInt(document.getElementById('frames').value),
                fps: 24,
                cfg: 3.0,
                seed: 42
            };

            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                const result = await response.json();
                if (result.job_id) {
                    alert('✅ Vídeo adicionado à fila!\\nAtualizará automaticamente quando pronto.');
                    loadJobs();
                }
            } catch (error) {
                alert('❌ Erro: ' + error.message);
            }
        });

        async function loadJobs() {
            try {
                const response = await fetch('/api/jobs');
                const jobs = await response.json();

                const container = document.getElementById('jobsList');
                container.innerHTML = '';

                const sorted = Object.entries(jobs).sort((a, b) =>
                    new Date(b[1].created_at) - new Date(a[1].created_at)
                );

                for (const [jobId, job] of sorted) {
                    const card = document.createElement('div');
                    card.className = 'job-card';

                    const statusClass = 'status-' + job.status;
                    const statusText = {
                        submitting: 'Submetendo',
                        processing: 'Processando',
                        completed: 'Concluído',
                        error: 'Erro'
                    }[job.status];

                    let html = `
                        <div class="job-header">
                            <div>${job.request.prompt.substring(0, 80)}</div>
                            <div class="status-badge ${statusClass}">${statusText}</div>
                        </div>
                    `;

                    if (job.status === 'processing') {
                        html += '<div class="progress-bar"><div class="progress-fill"></div></div>';
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
                        html += `<div style="color: #d63031; margin-top: 10px;">❌ ${job.error}</div>`;
                    }

                    card.innerHTML = html;
                    container.appendChild(card);
                }

                if (sorted.length === 0) {
                    container.innerHTML = '<div class="job-card"><p style="text-align:center;">Nenhum vídeo ainda</p></div>';
                }
            } catch (error) {
                console.error('Erro:', error);
            }
        }

        // Auto-atualizar a cada 3 segundos
        setInterval(loadJobs, 3000);
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
        'status': 'submitting',
        'request': request.dict(),
        'created_at': datetime.now().isoformat()
    }
    save_jobs()

    # Submeter em background (retorna rápido)
    background_tasks.add_task(submit_video, job_id, request)

    return {"job_id": job_id, "status": "submitting"}

@app.get("/api/jobs")
async def get_jobs():
    """Lista todos os jobs e atualiza status"""
    # Atualizar jobs que estão processando
    for job_id, job in jobs.items():
        if job['status'] == 'processing':
            video_file = check_video_ready(job_id)
            if video_file:
                job['status'] = 'completed'
                job['video_file'] = video_file
                job['completed_at'] = datetime.now().isoformat()

    save_jobs()
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
    print("🎬 LTX-2 Video Generator v2 - Não Bloqueante")
    print("=" * 60)
    print()
    print("🌐 Acesse: http://localhost:7860")
    print()
    print("✨ Melhorias:")
    print("   - Não bloqueia o servidor")
    print("   - Múltiplos jobs simultâneos")
    print("   - Atualização automática a cada 3s")
    print()
    print("⌨️  Ctrl+C para parar")
    print("=" * 60)
    print()

    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="info")
