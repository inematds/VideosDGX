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
        torch_dtype = torch.float16
        device = "cuda" if torch.cuda.is_available() else "cpu"

        if quantization == "fp4":
            # Quantização FP4 (NVFP4 no Blackwell)
            from transformers import BitsAndBytesConfig

            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )

            logger.info("Usando quantização FP4 (NF4)")

        elif quantization == "fp8":
            torch_dtype = torch.float8_e4m3fn
            quantization_config = None
            logger.info("Usando quantização FP8")

        else:
            torch_dtype = torch.float16
            quantization_config = None
            logger.info("Usando FP16 (sem quantização)")

        # Verificar se modelo existe
        model_path_obj = Path(model_path)
        if not model_path_obj.exists():
            logger.warning(f"Modelo não encontrado em {model_path}, tentando baixar...")
            # Por enquanto, usar modelo placeholder
            # Em produção, isso deve baixar do HuggingFace ou outro repositório
            model_id = "Lightricks/LTX-Video"  # ID hipotético
        else:
            model_id = str(model_path_obj)

        # Carregar pipeline de difusão
        # NOTA: Este é um exemplo genérico. O LTX-2 pode ter sua própria classe de pipeline
        pipeline = DiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            quantization_config=quantization_config if quantization == "fp4" else None,
            use_safetensors=True,
            variant="fp16" if quantization == "fp16" else None
        )

        # Mover para GPU
        if quantization != "fp4":  # FP4 já gerencia device automaticamente
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
