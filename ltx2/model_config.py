"""
Configuração e carregamento do modelo LTX-2
LTX-2: Modelo de geração de vídeo + áudio da Lightricks
"""
import torch
from pathlib import Path
from typing import Tuple, Any
import os

from utils import get_logger

logger = get_logger(__name__)

def load_ltx2_model(model_path: str, quantization: str = "fp4") -> Tuple[Any, Any]:
    """
    Carrega modelo LTX-2 com configurações otimizadas

    Args:
        model_path: Caminho para os arquivos do modelo
        quantization: Tipo de quantização (fp4, fp8, fp16)

    Returns:
        Tupla (model, pipeline)
    """
    logger.info(f"Carregando LTX-2 de {model_path} com quantização {quantization}")

    try:
        from diffusers import DiffusionPipeline
        from transformers import AutoModel, AutoTokenizer

        # Configurações de quantização e device
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # Por enquanto, usar FP16 até configurar quantização específica do LTX-2
        torch_dtype = torch.float16
        quantization_config = None
        logger.info(f"Usando FP16 (quantização {quantization} não implementada ainda para DiffusionPipeline)")

        # Verificar se modelo existe
        model_path_obj = Path(model_path)

        # Verificar estrutura de cache do HuggingFace
        hf_cache_path = model_path_obj / "models--Lightricks--LTX-2" / "snapshots"
        if hf_cache_path.exists():
            # Pegar o último snapshot
            snapshots = list(hf_cache_path.iterdir())
            if snapshots:
                model_id = str(snapshots[0])
                logger.info(f"Usando modelo do cache HuggingFace: {model_id}")
            else:
                logger.warning(f"Cache vazio em {hf_cache_path}")
                model_id = "Lightricks/LTX-2"
        elif not model_path_obj.exists():
            logger.warning(f"Modelo não encontrado em {model_path}, baixando do HuggingFace...")
            model_id = "Lightricks/LTX-2"  # ID oficial do HuggingFace
        else:
            model_id = str(model_path_obj)

        # Carregar pipeline de difusão
        # NOTA: Este é um exemplo genérico. O LTX-2 pode ter sua própria classe de pipeline
        pipeline = DiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            use_safetensors=True
        )

        # Mover para GPU
        pipeline = pipeline.to(device)

        # Otimizações específicas
        pipeline.enable_attention_slicing()

        if torch.cuda.is_available():
            # Otimizações para Blackwell
            pipeline.enable_model_cpu_offload()  # Aproveitar memória unificada

        logger.info("LTX-2 carregado com sucesso")

        return pipeline, pipeline  # Retorna pipeline duas vezes por compatibilidade

    except Exception as e:
        logger.error(f"Erro ao carregar LTX-2: {str(e)}")
        raise


def generate_video_ltx2(pipeline: Any, request: Any, output_path: Path) -> None:
    """
    Gera vídeo usando LTX-2

    Args:
        pipeline: Pipeline do modelo
        request: Objeto GenerateRequest com parâmetros
        output_path: Caminho para salvar o vídeo
    """
    logger.info(f"Gerando vídeo: {request.prompt[:50]}...")

    try:
        # Parsear resolução
        width, height = map(int, request.resolution.split('x'))

        # Calcular número de frames
        num_frames = request.duration * request.fps

        # Configurar gerador para reprodutibilidade
        generator = None
        if request.seed is not None:
            generator = torch.Generator(device="cuda" if torch.cuda.is_available() else "cpu")
            generator.manual_seed(request.seed)

        # Gerar vídeo
        # NOTA: Interface pode variar dependendo da implementação real do LTX-2
        output = pipeline(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            num_frames=num_frames,
            height=height,
            width=width,
            guidance_scale=request.guidance_scale,
            generator=generator,
            num_inference_steps=50,  # Ajustar conforme necessário
        )

        # Salvar vídeo
        # O output pode ser frames, tensor, ou já um arquivo
        # Este é um exemplo genérico
        if hasattr(output, 'frames'):
            frames = output.frames
        elif isinstance(output, dict) and 'frames' in output:
            frames = output['frames']
        else:
            frames = output

        # Salvar usando imageio ou similar
        import imageio

        # Se frames é tensor, converter para numpy
        if isinstance(frames, torch.Tensor):
            frames = frames.cpu().numpy()
            # Normalizar de [-1, 1] para [0, 255]
            frames = ((frames + 1.0) * 127.5).astype('uint8')

        # Salvar como MP4
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
