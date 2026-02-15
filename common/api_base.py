"""
Framework base para APIs FastAPI dos modelos de vídeo
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
import time
from enum import Enum

from utils import get_logger, get_system_info, MetricsCollector, validate_video_params
from model_loader import ModelLoader

logger = get_logger(__name__)

class JobStatus(str, Enum):
    """Status de um job de geração"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class GenerateRequest(BaseModel):
    """Request para geração de vídeo"""
    prompt: str = Field(..., min_length=1, max_length=1000, description="Prompt de texto")
    duration: int = Field(5, ge=1, le=60, description="Duração em segundos")
    fps: int = Field(24, description="Frames por segundo")
    resolution: str = Field("1024x576", description="Resolução (WxH)")
    seed: Optional[int] = Field(None, description="Seed para reprodutibilidade")
    negative_prompt: Optional[str] = Field(None, description="Negative prompt")
    guidance_scale: float = Field(7.5, ge=1.0, le=20.0, description="Guidance scale")

class Job:
    """Representa um job de geração de vídeo"""

    def __init__(self, request: GenerateRequest, model_name: str):
        self.id = f"{model_name}-{uuid.uuid4().hex[:8]}"
        self.request = request
        self.model_name = model_name
        self.status = JobStatus.QUEUED
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.output_path = None
        self.error = None
        self.progress = 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dict"""
        return {
            "job_id": self.id,
            "model_name": self.model_name,
            "status": self.status.value,
            "prompt": self.request.prompt,
            "duration": self.request.duration,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "output_path": str(self.output_path) if self.output_path else None,
            "error": self.error,
            "progress": self.progress
        }

class VideoModelAPI:
    """
    Classe base para APIs de modelos de vídeo
    """

    def __init__(
        self,
        model_name: str,
        model_loader: ModelLoader,
        generate_function: callable,
        output_dir: str = "/outputs"
    ):
        """
        Args:
            model_name: Nome do modelo
            model_loader: Instância do ModelLoader
            generate_function: Função que gera vídeo
            output_dir: Diretório para salvar vídeos
        """
        self.model_name = model_name
        self.model_loader = model_loader
        self.generate_function = generate_function
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.app = FastAPI(
            title=f"{model_name} Video Generation API",
            description=f"API para geração de vídeos usando {model_name}",
            version="1.0.0"
        )

        self.jobs: Dict[str, Job] = {}
        self.job_queue: asyncio.Queue = asyncio.Queue()
        self.metrics = MetricsCollector()

        # Registrar rotas
        self._register_routes()

        # Iniciar worker de processamento
        asyncio.create_task(self._process_queue())

    def _register_routes(self):
        """Registra endpoints da API"""

        @self.app.get("/")
        async def root():
            return {
                "model": self.model_name,
                "status": "online",
                "endpoints": [
                    "/generate",
                    "/health",
                    "/ready",
                    "/info",
                    "/unload",
                    "/queue/status",
                    "/jobs/{job_id}",
                    "/jobs/{job_id}/download",
                    "/metrics"
                ]
            }

        @self.app.get("/health")
        async def health():
            """Health check básico"""
            return {
                "status": "healthy",
                "model": self.model_name,
                "timestamp": datetime.now().isoformat()
            }

        @self.app.get("/ready")
        async def ready():
            """Verifica se modelo está carregado"""
            is_ready = self.model_loader.is_loaded()
            return {
                "ready": is_ready,
                "model": self.model_name,
                "loaded": is_ready
            }

        @self.app.get("/info")
        async def info():
            """Informações do modelo e sistema"""
            return {
                "model": self.model_loader.get_info(),
                "system": get_system_info(),
                "queue_size": self.job_queue.qsize(),
                "total_jobs": len(self.jobs)
            }

        @self.app.post("/unload")
        async def unload():
            """Descarrega modelo da memória"""
            try:
                result = self.model_loader.unload()
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/generate")
        async def generate(request: GenerateRequest, background_tasks: BackgroundTasks):
            """Cria job de geração de vídeo"""
            try:
                # Validar parâmetros
                if not validate_video_params(request.duration, request.fps, request.resolution):
                    raise HTTPException(
                        status_code=400,
                        detail="Parâmetros inválidos"
                    )

                # Criar job
                job = Job(request, self.model_name)
                self.jobs[job.id] = job

                # Adicionar à fila
                await self.job_queue.put(job)

                logger.info(f"Job {job.id} criado e adicionado à fila")

                # Estimar tempo
                queue_size = self.job_queue.qsize()
                estimated_time = queue_size * 60  # Estimativa simples: 60s por job

                return {
                    "job_id": job.id,
                    "status": job.status.value,
                    "queue_position": queue_size,
                    "estimated_time_seconds": estimated_time,
                    "model_loaded": self.model_loader.is_loaded()
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Erro ao criar job: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/queue/status")
        async def queue_status(job_id: Optional[str] = None):
            """Status da fila ou de um job específico"""
            if job_id:
                job = self.jobs.get(job_id)
                if not job:
                    raise HTTPException(status_code=404, detail="Job não encontrado")
                return job.to_dict()
            else:
                return {
                    "queue_size": self.job_queue.qsize(),
                    "total_jobs": len(self.jobs),
                    "jobs": [job.to_dict() for job in list(self.jobs.values())[-10:]]
                }

        @self.app.get("/jobs/{job_id}")
        async def get_job(job_id: str):
            """Informações de um job específico"""
            job = self.jobs.get(job_id)
            if not job:
                raise HTTPException(status_code=404, detail="Job não encontrado")
            return job.to_dict()

        @self.app.get("/jobs/{job_id}/download")
        async def download_job(job_id: str):
            """Download do vídeo gerado"""
            job = self.jobs.get(job_id)
            if not job:
                raise HTTPException(status_code=404, detail="Job não encontrado")

            if job.status != JobStatus.COMPLETED:
                raise HTTPException(
                    status_code=400,
                    detail=f"Job não completado (status: {job.status.value})"
                )

            if not job.output_path or not job.output_path.exists():
                raise HTTPException(status_code=404, detail="Arquivo não encontrado")

            return FileResponse(
                path=job.output_path,
                media_type="video/mp4",
                filename=f"{job.id}.mp4"
            )

        @self.app.get("/metrics")
        async def metrics():
            """Métricas de performance"""
            return self.metrics.get_stats()

    async def _process_queue(self):
        """Worker que processa jobs da fila"""
        logger.info(f"{self.model_name}: Worker de processamento iniciado")

        while True:
            try:
                # Pegar próximo job da fila
                job = await self.job_queue.get()

                logger.info(f"Processando job {job.id}")
                job.status = JobStatus.PROCESSING
                job.started_at = datetime.now()

                start_time = time.time()

                try:
                    # Garantir que modelo está carregado
                    model, pipeline = self.model_loader.get_model()

                    # Gerar vídeo
                    output_path = self.output_dir / f"{job.id}.mp4"

                    await asyncio.to_thread(
                        self.generate_function,
                        pipeline,
                        job.request,
                        output_path
                    )

                    # Job completado
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now()
                    job.output_path = output_path
                    job.progress = 100

                    duration = time.time() - start_time
                    self.metrics.record_inference(
                        duration=duration,
                        prompt_length=len(job.request.prompt),
                        success=True
                    )

                    logger.info(f"Job {job.id} completado em {duration:.2f}s")

                except Exception as e:
                    logger.error(f"Erro ao processar job {job.id}: {str(e)}")
                    job.status = JobStatus.FAILED
                    job.error = str(e)
                    job.completed_at = datetime.now()

                    duration = time.time() - start_time
                    self.metrics.record_inference(
                        duration=duration,
                        prompt_length=len(job.request.prompt),
                        success=False,
                        error=str(e)
                    )

                finally:
                    self.job_queue.task_done()

            except Exception as e:
                logger.error(f"Erro no worker de processamento: {str(e)}")
                await asyncio.sleep(1)
