"""
Configuração e carregamento do modelo Waver 1.0
Waver 1.0: Modelo lightweight para batch generation
"""
import torch
from pathlib import Path
from typing import Tuple, Any

from utils import get_logger

logger = get_logger(__name__)

def load_waver_model(model_path: str, quantization: str = "fp8") -> Tuple[Any, Any]:
    """
    Carrega modelo Waver 1.0 com configurações otimizadas

    Args:
        model_path: Caminho para os arquivos do modelo
        quantization: Tipo de quantização (fp8, fp16)

    Returns:
        Tupla (model, pipeline)
    """
    logger.info(f"Carregando Waver 1.0 de {model_path} com quantização {quantization}")

    try:
        from diffusers import DiffusionPipeline

        # Configurações de quantização
        if quantization == "fp8":
            torch_dtype = torch.float8_e4m3fn if hasattr(torch, 'float8_e4m3fn') else torch.float16
            logger.info("Usando quantização FP8")
        else:
            torch_dtype = torch.float16
            logger.info("Usando FP16")

        # Verificar se modelo existe
        model_path_obj = Path(model_path)
        if not model_path_obj.exists():
            logger.warning(f"Modelo não encontrado em {model_path}, baixando do HuggingFace...")
            model_id = "FoundationVision/Waver"  # ID oficial do HuggingFace
        else:
            model_id = str(model_path_obj)

        # Determinar device
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # Carregar pipeline lightweight
        # Explicitly disable device_map to avoid torch.xpu errors
        pipeline = DiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            use_safetensors=True,
            low_cpu_mem_usage=True,  # Otimização para modelo lightweight
            device_map=None  # Prevent auto device detection
        )

        # Mover para GPU
        pipeline = pipeline.to(device)

        # Otimizações para batch processing
        pipeline.enable_attention_slicing()

        if torch.cuda.is_available():
            pipeline.enable_model_cpu_offload()

        logger.info("Waver 1.0 carregado com sucesso")

        return pipeline, pipeline

    except Exception as e:
        import traceback
        logger.error(f"Erro ao carregar Waver 1.0: {str(e)}")
        logger.error(f"Traceback completo:\n{traceback.format_exc()}")
        raise


def generate_video_waver(pipeline: Any, request: Any, output_path: Path) -> None:
    """
    Gera vídeo usando Waver 1.0

    Args:
        pipeline: Pipeline do modelo
        request: Objeto GenerateRequest
        output_path: Caminho para salvar o vídeo
    """
    logger.info(f"Gerando vídeo com Waver 1.0: {request.prompt[:50]}...")

    try:
        width, height = map(int, request.resolution.split('x'))
        num_frames = request.duration * request.fps

        generator = None
        if request.seed is not None:
            generator = torch.Generator(device="cuda" if torch.cuda.is_available() else "cpu")
            generator.manual_seed(request.seed)

        # Gerar vídeo (otimizado para batch)
        output = pipeline(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            num_frames=num_frames,
            height=height,
            width=width,
            guidance_scale=request.guidance_scale,
            generator=generator,
            num_inference_steps=30,  # Menos steps por ser lightweight
        )

        # Salvar vídeo
        import imageio

        frames = output.frames if hasattr(output, 'frames') else output
        if isinstance(frames, torch.Tensor):
            frames = frames.cpu().numpy()
            frames = ((frames + 1.0) * 127.5).astype('uint8')

        imageio.mimwrite(
            str(output_path),
            frames,
            fps=request.fps,
            codec='libx264',
            quality=8
        )

        logger.info(f"Vídeo salvo em {output_path}")

    except Exception as e:
        logger.error(f"Erro ao gerar vídeo: {str(e)}")
        raise
