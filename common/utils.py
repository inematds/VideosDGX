"""
Utilidades compartilhadas entre os containers
"""
import logging
import psutil
import torch
from datetime import datetime
from typing import Dict, Any
import json

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_logger(name: str) -> logging.Logger:
    """Retorna logger configurado"""
    return logging.getLogger(name)

def get_gpu_memory_info() -> Dict[str, float]:
    """Retorna informações de memória da GPU"""
    if not torch.cuda.is_available():
        return {"available": False}

    try:
        gpu_mem_allocated = torch.cuda.memory_allocated() / 1024**3  # GB
        gpu_mem_reserved = torch.cuda.memory_reserved() / 1024**3    # GB
        gpu_mem_total = torch.cuda.get_device_properties(0).total_memory / 1024**3

        return {
            "available": True,
            "allocated_gb": round(gpu_mem_allocated, 2),
            "reserved_gb": round(gpu_mem_reserved, 2),
            "total_gb": round(gpu_mem_total, 2),
            "free_gb": round(gpu_mem_total - gpu_mem_reserved, 2)
        }
    except Exception as e:
        return {"available": True, "error": str(e)}

def get_cpu_memory_info() -> Dict[str, float]:
    """Retorna informações de memória da CPU"""
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / 1024**3, 2),
        "available_gb": round(mem.available / 1024**3, 2),
        "used_gb": round(mem.used / 1024**3, 2),
        "percent": mem.percent
    }

def get_system_info() -> Dict[str, Any]:
    """Retorna informações completas do sistema"""
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu_memory": get_cpu_memory_info(),
        "gpu_memory": get_gpu_memory_info(),
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    }

class MetricsCollector:
    """Coleta métricas de inferência"""

    def __init__(self):
        self.metrics = []

    def record_inference(self, duration: float, prompt_length: int,
                        success: bool, error: str = None):
        """Registra métrica de inferência"""
        metric = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(duration, 2),
            "prompt_length": prompt_length,
            "success": success,
            "error": error,
            "gpu_memory": get_gpu_memory_info()
        }
        self.metrics.append(metric)

        # Manter apenas últimas 100 métricas
        if len(self.metrics) > 100:
            self.metrics = self.metrics[-100:]

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas agregadas"""
        if not self.metrics:
            return {"total_inferences": 0}

        successful = [m for m in self.metrics if m["success"]]
        durations = [m["duration_seconds"] for m in successful]

        return {
            "total_inferences": len(self.metrics),
            "successful": len(successful),
            "failed": len(self.metrics) - len(successful),
            "avg_duration_seconds": round(sum(durations) / len(durations), 2) if durations else 0,
            "min_duration_seconds": round(min(durations), 2) if durations else 0,
            "max_duration_seconds": round(max(durations), 2) if durations else 0,
            "last_10": self.metrics[-10:]
        }

def validate_video_params(duration: int, fps: int, resolution: str) -> bool:
    """Valida parâmetros de vídeo"""
    try:
        # Validar duração
        if duration < 1 or duration > 60:
            return False

        # Validar FPS
        if fps not in [24, 30, 60]:
            return False

        # Validar resolução
        width, height = map(int, resolution.split('x'))
        if width < 256 or height < 256 or width > 4096 or height > 4096:
            return False

        return True
    except:
        return False
