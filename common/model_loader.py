"""
Gerenciador de carregamento de modelos sob demanda
"""
import torch
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
import threading
import time
from utils import get_logger, get_gpu_memory_info

logger = get_logger(__name__)

class ModelLoader:
    """
    Gerencia carregamento sob demanda de modelos de vídeo
    """

    def __init__(
        self,
        model_name: str,
        model_path: str,
        load_function: Callable,
        quantization: str = "fp16",
        auto_unload_minutes: Optional[int] = None
    ):
        """
        Args:
            model_name: Nome do modelo (ltx2, wan21, etc)
            model_path: Caminho para os arquivos do modelo
            load_function: Função que carrega o modelo
            quantization: Tipo de quantização (fp4, fp8, fp16)
            auto_unload_minutes: Minutos de inatividade antes de descarregar (None = nunca)
        """
        self.model_name = model_name
        self.model_path = model_path
        self.load_function = load_function
        self.quantization = quantization
        self.auto_unload_minutes = auto_unload_minutes

        self.model = None
        self.pipeline = None
        self.loaded = False
        self.loading = False
        self.last_used = None

        self._lock = threading.Lock()
        self._unload_timer = None

    def is_loaded(self) -> bool:
        """Verifica se modelo está carregado"""
        return self.loaded and self.model is not None

    def load(self) -> Dict[str, Any]:
        """
        Carrega modelo em memória
        Returns:
            Dict com informações do carregamento
        """
        with self._lock:
            if self.loaded:
                logger.info(f"{self.model_name}: Modelo já carregado")
                return {
                    "status": "already_loaded",
                    "model_name": self.model_name,
                    "memory": get_gpu_memory_info()
                }

            if self.loading:
                logger.warning(f"{self.model_name}: Carregamento já em andamento")
                return {
                    "status": "loading_in_progress",
                    "model_name": self.model_name
                }

            self.loading = True

        try:
            logger.info(f"{self.model_name}: Iniciando carregamento...")
            logger.info(f"Memória antes: {get_gpu_memory_info()}")

            start_time = time.time()

            # Chama função de carregamento específica do modelo
            self.model, self.pipeline = self.load_function(
                self.model_path,
                self.quantization
            )

            load_time = time.time() - start_time

            with self._lock:
                self.loaded = True
                self.loading = False
                self.last_used = datetime.now()

            memory_info = get_gpu_memory_info()
            logger.info(f"{self.model_name}: Carregado em {load_time:.2f}s")
            logger.info(f"Memória depois: {memory_info}")

            # Iniciar timer de auto-unload se configurado
            if self.auto_unload_minutes:
                self._start_unload_timer()

            return {
                "status": "loaded",
                "model_name": self.model_name,
                "load_time_seconds": round(load_time, 2),
                "memory": memory_info,
                "quantization": self.quantization
            }

        except Exception as e:
            logger.error(f"{self.model_name}: Erro ao carregar - {str(e)}")
            with self._lock:
                self.loading = False
            raise

    def unload(self) -> Dict[str, Any]:
        """
        Descarrega modelo da memória
        Returns:
            Dict com informações do descarregamento
        """
        with self._lock:
            if not self.loaded:
                logger.info(f"{self.model_name}: Modelo não estava carregado")
                return {
                    "status": "not_loaded",
                    "model_name": self.model_name
                }

        logger.info(f"{self.model_name}: Descarregando modelo...")
        memory_before = get_gpu_memory_info()

        # Cancelar timer de auto-unload
        if self._unload_timer:
            self._unload_timer.cancel()
            self._unload_timer = None

        # Limpar referências
        with self._lock:
            self.model = None
            self.pipeline = None
            self.loaded = False
            self.last_used = None

        # Forçar garbage collection
        import gc
        gc.collect()
        torch.cuda.empty_cache()

        memory_after = get_gpu_memory_info()
        freed_gb = memory_before.get("allocated_gb", 0) - memory_after.get("allocated_gb", 0)

        logger.info(f"{self.model_name}: Descarregado. Memória liberada: {freed_gb:.2f}GB")

        return {
            "status": "unloaded",
            "model_name": self.model_name,
            "memory_freed_gb": round(freed_gb, 2),
            "memory_after": memory_after
        }

    def get_model(self):
        """
        Retorna modelo, carregando se necessário
        """
        if not self.is_loaded():
            self.load()

        with self._lock:
            self.last_used = datetime.now()

        # Reiniciar timer de auto-unload
        if self.auto_unload_minutes:
            self._start_unload_timer()

        return self.model, self.pipeline

    def get_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o modelo"""
        return {
            "model_name": self.model_name,
            "loaded": self.loaded,
            "loading": self.loading,
            "quantization": self.quantization,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "auto_unload_minutes": self.auto_unload_minutes,
            "memory": get_gpu_memory_info() if self.loaded else None
        }

    def _start_unload_timer(self):
        """Inicia timer para auto-unload"""
        if self._unload_timer:
            self._unload_timer.cancel()

        def check_and_unload():
            if self.loaded and self.last_used:
                idle_time = datetime.now() - self.last_used
                if idle_time > timedelta(minutes=self.auto_unload_minutes):
                    logger.info(f"{self.model_name}: Auto-unload por inatividade")
                    self.unload()

        self._unload_timer = threading.Timer(
            self.auto_unload_minutes * 60,
            check_and_unload
        )
        self._unload_timer.daemon = True
        self._unload_timer.start()
