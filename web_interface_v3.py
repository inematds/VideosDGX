#!/usr/bin/env python3
"""
Interface Web para Geração de Vídeos LTX-2 (Versão 3 - Auto-Restart)
Reinicia ComfyUI automaticamente entre vídeos para evitar corrupção do Gemma
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
import signal

app = FastAPI(title="LTX-2 Video Generator v3")

# Configurações
OUTPUT_DIR = Path("/home/nmaldaner/projetos/VideosDGX/ComfyUI/output")
SCRIPT_PATH = Path("/home/nmaldaner/projetos/VideosDGX/gerar_video_ltx2.py")
JOBS_FILE = Path("/tmp/ltx2_jobs_v3.json")
RESTART_SCRIPT = Path("/home/nmaldaner/projetos/VideosDGX/reiniciar_comfyui.sh")
JOB_TIMEOUT = 600  # 10 minutos

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

def restart_comfyui():
    """Reinicia ComfyUI para limpar estado do Gemma"""
    try:
        print(f"\n{'='*60}")
        print("🔄 Reiniciando ComfyUI...")
        print(f"{'='*60}\n")

        result = subprocess.run(
            [str(RESTART_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print("✅ ComfyUI reiniciado com sucesso!")
            return True
        else:
            print(f"⚠️ Erro ao reiniciar: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"❌ Erro ao reiniciar ComfyUI: {e}")
        return False

def submit_and_generate_video(job_id: str, request: VideoRequest):
    """Submete vídeo, aguarda geração E reinicia ComfyUI"""
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

        print(f"\n{'='*60}")
        print(f"🎬 Gerando vídeo {job_id}")
        print(f"📝 Prompt: {request.prompt[:50]}...")
        print(f"{'='*60}\n")

        # Submeter (retorna imediatamente após submeter)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0 or "SUCESSO" not in result.stdout:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['error'] = f"Falha ao submeter: {result.stderr[:200]}"
            save_jobs()
            print(f"❌ Job {job_id} falhou ao submeter")
            return

        print(f"✅ Job {job_id} submetido! Aguardando geração...")

        # Aguardar vídeo aparecer (com timeout)
        start_time = time.time()
        video_found = None

        while time.time() - start_time < JOB_TIMEOUT:
            # Procurar vídeo
            all_videos = list(OUTPUT_DIR.glob("*.mp4"))
            videos = [f for f in all_videos if job_id in f.name]

            if videos:
                video_found = sorted(videos, key=lambda x: x.stat().st_mtime, reverse=True)[0]
                break

            time.sleep(5)  # Checar a cada 5 segundos

        elapsed = time.time() - start_time

        if video_found:
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['video_file'] = video_found.name
            jobs[job_id]['completed_at'] = datetime.now().isoformat()
            jobs[job_id]['generation_time'] = f"{elapsed:.1f}s"
            print(f"✅ Vídeo {job_id} gerado em {elapsed:.1f}s!")
        else:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['error'] = f'Timeout após {elapsed:.1f}s - vídeo não encontrado'
            print(f"⏱️ Timeout para job {job_id}")

        save_jobs()

        # 🔄 REINICIAR ComfyUI após cada vídeo (sucesso ou falha)
        print(f"\n{'='*60}")
        print("🔄 Reiniciando ComfyUI para limpar estado do Gemma...")
        print(f"{'='*60}\n")

        restart_comfyui()

        # Aguardar ComfyUI inicializar
        time.sleep(15)

        print(f"{'='*60}")
        print(f"✅ Sistema pronto para próximo vídeo!")
        print(f"{'='*60}\n")

    except Exception as e:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['error'] = str(e)
        save_jobs()
        print(f"❌ Erro no job {job_id}: {e}")

        # Tentar reiniciar mesmo em caso de erro
        restart_comfyui()

def check_timeout_jobs():
    """Verifica jobs que podem ter travado"""
    now = datetime.now()
    for job_id, job in jobs.items():
        if job['status'] == 'processing':
            started = datetime.fromisoformat(job.get('started_at', job['created_at']))
            elapsed = (now - started).total_seconds()

            if elapsed > JOB_TIMEOUT:
                job['status'] = 'error'
                job['error'] = f'Timeout após {elapsed:.0f}s'
                print(f"⏱️ Job {job_id} marcado como timeout")

@app.get("/", response_class=HTMLResponse)
async def home():
    """Página principal"""
    html = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LTX-2 Video Generator v3</title>
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

        .badge {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            margin-top: 10px;
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
            transition: all 0.3s;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
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
            transition: all 0.2s;
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
            flex-wrap: wrap;
            gap: 10px;
        }

        .status-badge {
            padding: 6px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }

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

        .info-text {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }

        .queue-warning {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin-top: 20px;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 LTX-2 Video Generator v3</h1>
            <div class="badge">✨ Auto-Restart • Um vídeo por vez • Sem corrupção</div>
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

                <button type="submit" class="btn" id="submitBtn">🚀 Gerar Vídeo</button>

                <div class="queue-warning" id="queueWarning" style="display: none;">
                    ⚠️ <strong>Um vídeo por vez:</strong> Aguarde o vídeo atual completar antes de gerar outro.
                    ComfyUI será reiniciado automaticamente entre vídeos.
                </div>
            </form>
        </div>

        <div class="jobs-section">
            <h2 style="color: white; margin-bottom: 20px;">Vídeos Recentes (da Fila)</h2>
            <div id="jobsList"></div>
        </div>

        <div class="gallery-section" style="margin-top: 40px;">
            <h2 style="color: white; margin-bottom: 20px;">📂 Todos os Vídeos (Output)</h2>
            <div id="allVideos"></div>
        </div>
    </div>

    <script>
        let isProcessing = false;

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

        function updateButtonState() {
            const btn = document.getElementById('submitBtn');
            const warning = document.getElementById('queueWarning');

            if (isProcessing) {
                btn.disabled = true;
                btn.textContent = '⏳ Gerando vídeo...';
                warning.style.display = 'block';
            } else {
                btn.disabled = false;
                btn.textContent = '🚀 Gerar Vídeo';
                warning.style.display = 'none';
            }
        }

        document.getElementById('videoForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            if (isProcessing) {
                alert('⚠️ Aguarde o vídeo atual terminar!');
                return;
            }

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
                    alert('✅ Vídeo adicionado à fila!\\nAguarde ~2-5 minutos.\\nComfyUI será reiniciado automaticamente após.');
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

                // Verificar se há job processando
                isProcessing = sorted.some(([_, job]) => job.status === 'processing');
                updateButtonState();

                for (const [jobId, job] of sorted) {
                    const card = document.createElement('div');
                    card.className = 'job-card';

                    const statusClass = 'status-' + job.status;
                    const statusText = {
                        processing: 'Processando',
                        completed: 'Concluído',
                        error: 'Erro'
                    }[job.status];

                    let html = `
                        <div class="job-header">
                            <div>
                                <strong>${job.request.prompt.substring(0, 80)}</strong>
                                ${job.generation_time ? `<div class="info-text">⏱️ ${job.generation_time}</div>` : ''}
                            </div>
                            <div class="status-badge ${statusClass}">${statusText}</div>
                        </div>
                    `;

                    if (job.status === 'processing') {
                        html += '<div class="progress-bar"><div class="progress-fill"></div></div>';
                        html += '<div class="info-text">🔄 ComfyUI será reiniciado automaticamente após este vídeo</div>';
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

        async function loadAllVideos() {
            try {
                const response = await fetch('/api/all-videos');
                const videos = await response.json();

                const container = document.getElementById('allVideos');
                container.innerHTML = '';

                if (videos.length === 0) {
                    container.innerHTML = '<div class="job-card"><p style="text-align:center;">Nenhum vídeo encontrado em output/</p></div>';
                    return;
                }

                // Criar cards de galeria
                for (const video of videos) {
                    const card = document.createElement('div');
                    card.className = 'job-card';
                    card.style.cursor = 'pointer';

                    card.innerHTML = `
                        <div class="job-header">
                            <div>
                                <strong>${video.filename}</strong>
                                <div class="info-text">
                                    📅 ${video.modified_str} • 💾 ${video.size_mb} MB
                                </div>
                            </div>
                        </div>
                        <div class="video-player" style="display: none;" id="player-${video.filename}">
                            <video controls>
                                <source src="/api/video/${video.filename}" type="video/mp4">
                            </video>
                        </div>
                    `;

                    // Toggle player ao clicar
                    card.addEventListener('click', (e) => {
                        const player = document.getElementById(`player-${video.filename}`);
                        if (player.style.display === 'none') {
                            player.style.display = 'block';
                        } else {
                            player.style.display = 'none';
                        }
                    });

                    container.appendChild(card);
                }
            } catch (error) {
                console.error('Erro ao carregar vídeos:', error);
            }
        }

        // Auto-atualizar jobs a cada 5 segundos
        setInterval(loadJobs, 5000);

        // Auto-atualizar galeria a cada 10 segundos
        setInterval(loadAllVideos, 10000);

        // Carregar ao iniciar
        loadJobs();
        loadAllVideos();
    </script>
</body>
</html>
    """
    return html

@app.post("/api/generate")
async def generate(request: VideoRequest, background_tasks: BackgroundTasks):
    """Inicia geração de vídeo"""
    # Verificar se já há job processando
    for job in jobs.values():
        if job['status'] == 'processing':
            return JSONResponse(
                status_code=429,
                content={"error": "Já há um vídeo sendo processado. Aguarde terminar."}
            )

    job_id = str(uuid.uuid4())[:8]

    jobs[job_id] = {
        'job_id': job_id,
        'status': 'processing',
        'request': request.dict(),
        'created_at': datetime.now().isoformat()
    }
    save_jobs()

    # Processar em background (aguarda terminar + reinicia ComfyUI)
    background_tasks.add_task(submit_and_generate_video, job_id, request)

    return {"job_id": job_id, "status": "processing"}

@app.get("/api/jobs")
async def get_jobs():
    """Lista todos os jobs"""
    check_timeout_jobs()
    save_jobs()
    return jobs

@app.get("/api/video/{filename}")
async def get_video(filename: str):
    """Retorna arquivo de vídeo (confinado a OUTPUT_DIR contra path traversal)"""
    file_path = (OUTPUT_DIR / filename).resolve()
    if OUTPUT_DIR.resolve() in file_path.parents and file_path.is_file():
        return FileResponse(file_path)
    return JSONResponse(status_code=404, content={"error": "Vídeo não encontrado"})

@app.get("/api/all-videos")
async def get_all_videos():
    """Lista todos os vídeos do diretório output"""
    try:
        videos = []
        for video_file in OUTPUT_DIR.glob("*.mp4"):
            stat = video_file.stat()
            videos.append({
                "filename": video_file.name,
                "size": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "modified_str": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })

        # Ordenar por data (mais recentes primeiro)
        videos.sort(key=lambda x: x['modified'], reverse=True)

        return videos
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/restart")
async def restart():
    """Reinicia ComfyUI manualmente"""
    success = restart_comfyui()
    if success:
        return {"status": "success", "message": "ComfyUI reiniciado"}
    else:
        return JSONResponse(
            status_code=500,
            content={"error": "Falha ao reiniciar ComfyUI"}
        )

if __name__ == "__main__":
    print("=" * 60)
    print("🎬 LTX-2 Video Generator v3 - Auto-Restart")
    print("=" * 60)
    print()
    print("🌐 Acesse: http://localhost:7860")
    print()
    print("✨ Melhorias:")
    print("   - Reinicia ComfyUI automaticamente entre vídeos")
    print("   - Previne corrupção do Gemma encoder")
    print("   - Um vídeo por vez (sem fila)")
    print("   - Timeout de 10 minutos por vídeo")
    print("   - Aguarda geração completa")
    print()
    print("⚠️  IMPORTANTE:")
    print("   - Cada vídeo leva ~2-5 minutos")
    print("   - ComfyUI reinicia após cada vídeo (+15s)")
    print("   - Apenas 1 vídeo por vez")
    print()
    print("⌨️  Ctrl+C para parar")
    print("=" * 60)
    print()

    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="info")
