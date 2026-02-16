#!/usr/bin/env python3
"""
Script para gerar vídeos com LTX-2 no DGX Spark 2026

Uso:
    python3 gerar_video_ltx2.py "Um gato caminhando na praia ao pôr do sol"
    python3 gerar_video_ltx2.py --prompt "..." --width 1024 --height 576 --frames 121
"""

import argparse
import json
import requests
import time
import sys
from pathlib import Path

# Configuração padrão
COMFYUI_API = "http://localhost:8188/api/prompt"
OUTPUT_DIR = Path("/home/nmaldaner/projetos/VideosDGX/ComfyUI/output")
GEMMA_PATH = "gemma-3-12b-it-qat-q4_0-unquantized/model-00001-of-00005.safetensors"
LTX_PATH = "ltx-2-19b-distilled.safetensors"

def criar_workflow(
    prompt: str,
    negative_prompt: str = "",
    width: int = 512,
    height: int = 512,
    frames: int = 49,
    fps: int = 24,
    cfg: float = 3.0,
    seed: int = 42,
    filename_prefix: str = "ltx2_video"
):
    """Cria workflow LTX-2 com parâmetros customizáveis"""

    workflow = {
        "1": {
            "inputs": {"ckpt_name": LTX_PATH},
            "class_type": "CheckpointLoaderSimple"
        },
        "2": {
            "inputs": {
                "gemma_path": GEMMA_PATH,
                "ltxv_path": LTX_PATH,
                "max_length": 512
            },
            "class_type": "LTXVGemmaCLIPModelLoader"
        },
        "3": {
            "inputs": {
                "text": prompt,
                "clip": ["2", 0]
            },
            "class_type": "CLIPTextEncode"
        },
        "4": {
            "inputs": {
                "text": negative_prompt,
                "clip": ["2", 0]
            },
            "class_type": "CLIPTextEncode"
        },
        "5": {
            "inputs": {
                "positive": ["3", 0],
                "negative": ["4", 0],
                "frame_rate": float(fps)
            },
            "class_type": "LTXVConditioning"
        },
        "6": {
            "inputs": {
                "width": width,
                "height": height,
                "length": frames,
                "batch_size": 1
            },
            "class_type": "EmptyLTXVLatentVideo"
        },
        "7": {
            "inputs": {
                "ckpt_name": LTX_PATH
            },
            "class_type": "LTXVAudioVAELoader"
        },
        "8": {
            "inputs": {
                "audio_vae": ["7", 0],
                "frames_number": frames,
                "frame_rate": fps,
                "batch_size": 1
            },
            "class_type": "LTXVEmptyLatentAudio"
        },
        "9": {
            "inputs": {
                "video_latent": ["6", 0],
                "audio_latent": ["8", 0]
            },
            "class_type": "LTXVConcatAVLatent"
        },
        "10": {
            "inputs": {
                "noise_seed": seed
            },
            "class_type": "RandomNoise"
        },
        "11": {
            "inputs": {
                "sampler_name": "euler"
            },
            "class_type": "KSamplerSelect"
        },
        "12": {
            "inputs": {
                "sigmas": "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"
            },
            "class_type": "ManualSigmas"
        },
        "13": {
            "inputs": {
                "model": ["1", 0],
                "positive": ["5", 0],
                "negative": ["5", 1],
                "cfg": cfg
            },
            "class_type": "CFGGuider"
        },
        "14": {
            "inputs": {
                "noise": ["10", 0],
                "guider": ["13", 0],
                "sampler": ["11", 0],
                "sigmas": ["12", 0],
                "latent_image": ["9", 0]
            },
            "class_type": "SamplerCustomAdvanced"
        },
        "15": {
            "inputs": {
                "av_latent": ["14", 1]
            },
            "class_type": "LTXVSeparateAVLatent"
        },
        "16": {
            "inputs": {
                "vae": ["1", 2],
                "latents": ["15", 0],
                "spatial_tiles": 4,
                "temporal_tile_length": 16,
                "spatial_overlap": 4,
                "temporal_overlap": 4,
                "last_frame_fix": False,
                "working_device": "auto",
                "working_dtype": "auto"
            },
            "class_type": "LTXVSpatioTemporalTiledVAEDecode"
        },
        "17": {
            "inputs": {
                "samples": ["15", 1],
                "audio_vae": ["7", 0]
            },
            "class_type": "LTXVAudioVAEDecode"
        },
        "18": {
            "inputs": {
                "images": ["16", 0],
                "audio": ["17", 0],
                "fps": float(fps)
            },
            "class_type": "CreateVideo"
        },
        "19": {
            "inputs": {
                "video": ["18", 0],
                "filename_prefix": filename_prefix,
                "format": "auto",
                "codec": "auto"
            },
            "class_type": "SaveVideo"
        }
    }

    return workflow


def submeter_workflow(workflow, client_id=None):
    """Submete workflow para ComfyUI API"""

    if client_id is None:
        client_id = f"ltx2-{int(time.time())}"

    payload = {
        "prompt": workflow,
        "client_id": client_id
    }

    try:
        response = requests.post(COMFYUI_API, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        if 'prompt_id' in result:
            return result['prompt_id']
        else:
            raise Exception(f"Erro na resposta: {result}")

    except requests.exceptions.RequestException as e:
        raise Exception(f"Erro ao conectar com ComfyUI: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Gera vídeos com LTX-2 no DGX Spark 2026",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "prompt",
        nargs='?',
        default=None,
        help="Prompt para geração do vídeo"
    )
    parser.add_argument(
        "--prompt", "-p",
        dest="prompt_arg",
        help="Prompt para geração do vídeo (alternativa)"
    )
    parser.add_argument(
        "--negative",
        default="",
        help="Prompt negativo"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=512,
        help="Largura do vídeo (múltiplo de 32)"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=512,
        help="Altura do vídeo (múltiplo de 32)"
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=49,
        help="Número de frames"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=24,
        help="Frames por segundo"
    )
    parser.add_argument(
        "--cfg",
        type=float,
        default=3.0,
        help="CFG scale (1.0-10.0)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed aleatória"
    )
    parser.add_argument(
        "--output",
        default="ltx2_video",
        help="Prefixo do arquivo de saída"
    )
    parser.add_argument(
        "--save-workflow",
        help="Salvar workflow JSON em arquivo"
    )

    args = parser.parse_args()

    # Determinar prompt
    prompt = args.prompt or args.prompt_arg
    if not prompt:
        print("❌ Erro: Prompt é obrigatório!")
        print("\nUso:")
        print('  python3 gerar_video_ltx2.py "Descrição do vídeo"')
        print('  python3 gerar_video_ltx2.py --prompt "Descrição do vídeo"')
        sys.exit(1)

    # Validações
    if args.width % 32 != 0 or args.height % 32 != 0:
        print("⚠️  Aviso: Largura e altura devem ser múltiplos de 32")
        args.width = (args.width // 32) * 32
        args.height = (args.height // 32) * 32
        print(f"   Ajustado para: {args.width}x{args.height}")

    # Criar workflow
    print("🎬 Gerando workflow LTX-2...")
    print(f"   Prompt: {prompt}")
    print(f"   Resolução: {args.width}x{args.height}")
    print(f"   Frames: {args.frames} @ {args.fps} FPS")
    print(f"   Duração: {args.frames / args.fps:.2f} segundos")
    print(f"   CFG: {args.cfg}")
    print(f"   Seed: {args.seed}")

    workflow = criar_workflow(
        prompt=prompt,
        negative_prompt=args.negative,
        width=args.width,
        height=args.height,
        frames=args.frames,
        fps=args.fps,
        cfg=args.cfg,
        seed=args.seed,
        filename_prefix=args.output
    )

    # Salvar workflow se solicitado
    if args.save_workflow:
        with open(args.save_workflow, 'w') as f:
            json.dump(workflow, f, indent=2)
        print(f"✓ Workflow salvo em: {args.save_workflow}")

    # Submeter
    print("\n🚀 Submetendo para ComfyUI...")
    try:
        prompt_id = submeter_workflow(workflow)

        print(f"\n✅ SUCESSO! Geração iniciada!")
        print(f"\n   Prompt ID: {prompt_id}")
        print(f"\n⏳ Aguardando geração...")

        # Estimar tempo
        estimated_time = (args.frames / 49) * 77  # 77s para 49 frames
        print(f"   Tempo estimado: {int(estimated_time)} segundos")

        print(f"\n📂 Output:")
        print(f"   Diretório: {OUTPUT_DIR}/")
        print(f"   Arquivo: {args.output}_*.mp4")

        print(f"\n📊 Monitorar:")
        print(f"   tail -f /home/nmaldaner/projetos/VideosDGX/comfyui_server.log")
        print(f"   http://localhost:8188")

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
