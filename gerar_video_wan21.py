#!/usr/bin/env python3
"""
Script CLI para gerar vídeos usando Wan 2.1 14B via ComfyUI
Uso: ./gerar_video_wan21.py "seu prompt aqui" [opções]
"""

import json
import uuid
import sys
import argparse
import requests
import time
from pathlib import Path

# Configurações
COMFYUI_URL = "http://127.0.0.1:8188"
WORKFLOW_TEMPLATE = Path(__file__).parent / "workflow_wan21_t2v_bf16.json"
OUTPUT_DIR = Path(__file__).parent / "ComfyUI" / "output"

def load_workflow_template():
    """Carrega template do workflow"""
    with open(WORKFLOW_TEMPLATE) as f:
        return json.load(f)

def create_workflow(prompt, negative="", width=720, height=480, frames=33, fps=24, cfg=6.0, seed=42, output_prefix="wan21_video"):
    """Cria workflow personalizado"""
    workflow = load_workflow_template()

    # Atualizar prompt
    workflow["1"]["inputs"]["text"] = prompt

    # Atualizar negative prompt
    workflow["6"]["inputs"]["text"] = negative

    # Atualizar dimensões e frames (EmptyHunyuanLatentVideo usa "length")
    workflow["5"]["inputs"]["width"] = width
    workflow["5"]["inputs"]["height"] = height
    workflow["5"]["inputs"]["length"] = frames

    # Atualizar KSampler
    workflow["3"]["inputs"]["cfg"] = cfg
    workflow["3"]["inputs"]["seed"] = seed

    # Atualizar output
    workflow["9"]["inputs"]["filename_prefix"] = output_prefix
    workflow["9"]["inputs"]["fps"] = fps

    return workflow

def submit_workflow(workflow):
    """Submete workflow para ComfyUI"""
    try:
        # Queue prompt
        payload = {
            "prompt": workflow,
            "client_id": str(uuid.uuid4())
        }

        response = requests.post(f"{COMFYUI_URL}/prompt", json=payload)

        if response.status_code == 200:
            data = response.json()
            prompt_id = data.get("prompt_id")
            return prompt_id
        else:
            print(f"❌ Erro ao submeter: {response.status_code}")
            print(response.text)
            return None

    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Gera vídeos usando Wan 2.1 14B",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Vídeo básico (480P, 5s)
  ./gerar_video_wan21.py "um gato caminhando"

  # Vídeo longo (480P, 8s)
  ./gerar_video_wan21.py "ondas na praia" --frames 128

  # HD 720P
  ./gerar_video_wan21.py "paisagem montanhosa" --width 1280 --height 720

  # Com mais controle criativo
  ./gerar_video_wan21.py "robot futurista" --cfg 5.0

  # Seed específica
  ./gerar_video_wan21.py "flores coloridas" --seed 12345

Parâmetros recomendados:
  - 480P, 5s: 720x480, 80 frames (VRAM mínima: 8GB)
  - 480P, 8s: 720x480, 128 frames (VRAM mínima: 12GB)
  - 720P, 5s: 1280x720, 80 frames (VRAM mínima: 16GB)

  CFG: 1.0 (padrão, recomendado) ou 5-7 (mais controle)
  FPS: Salvar em 24fps (modelo gera em 16fps)
        """
    )

    parser.add_argument("prompt", help="Descrição do vídeo a gerar")
    parser.add_argument("--negative", default="", help="Prompt negativo")
    parser.add_argument("--width", type=int, default=720, help="Largura (padrão: 720)")
    parser.add_argument("--height", type=int, default=480, help="Altura (padrão: 480)")
    parser.add_argument("--frames", type=int, default=33, help="Número de frames (padrão: 33 = ~2s)")
    parser.add_argument("--fps", type=int, default=24, help="FPS do vídeo final (padrão: 24)")
    parser.add_argument("--cfg", type=float, default=6.0, help="CFG scale (padrão: 6.0)")
    parser.add_argument("--seed", type=int, default=42, help="Seed (padrão: 42)")
    parser.add_argument("--output", default="wan21_video", help="Prefixo do arquivo de saída")

    args = parser.parse_args()

    # Validações
    if args.frames > 128:
        print("⚠️  Aviso: Frames > 128 podem causar OOM. Recomendado: máx 128 frames")

    if args.width > 1280 or args.height > 720:
        print("⚠️  Aviso: Resoluções > 720P podem causar OOM")

    # Calcular duração
    duration = args.frames / 16  # Modelo gera em 16fps
    duration_output = args.frames / args.fps

    print("🎬 Gerando workflow Wan 2.1...")
    print(f"   Prompt: {args.prompt}")
    print(f"   Resolução: {args.width}x{args.height}")
    print(f"   Frames: {args.frames} @ {args.fps} FPS")
    print(f"   Duração: {duration_output:.2f} segundos")
    print(f"   CFG: {args.cfg}")
    print(f"   Seed: {args.seed}")
    print()

    # Criar workflow
    workflow = create_workflow(
        prompt=args.prompt,
        negative=args.negative,
        width=args.width,
        height=args.height,
        frames=args.frames,
        fps=args.fps,
        cfg=args.cfg,
        seed=args.seed,
        output_prefix=args.output
    )

    # Submeter
    print("🚀 Submetendo para ComfyUI...")
    print()

    prompt_id = submit_workflow(workflow)

    if prompt_id:
        print("✅ SUCESSO! Geração iniciada!")
        print()
        print(f"   Prompt ID: {prompt_id}")
        print()

        # Estimar tempo
        # Wan 2.1: ~2-3s por frame em média no DGX
        estimated_time = int(args.frames * 2.5)
        print(f"⏳ Aguardando geração...")
        print(f"   Tempo estimado: {estimated_time} segundos")
        print()

        print("📂 Output:")
        print(f"   Diretório: {OUTPUT_DIR}/")
        print(f"   Arquivo: {args.output}_*.mp4")
        print()

        print("📊 Monitorar:")
        print(f"   tail -f {Path(__file__).parent}/comfyui_server.log")
        print(f"   {COMFYUI_URL}")
        print()

    else:
        print("❌ ERRO: Falha ao submeter workflow")
        print()
        print("Verificar:")
        print(f"  1. ComfyUI está rodando? curl {COMFYUI_URL}/system_stats")
        print(f"  2. Modelos estão no lugar certo?")
        print(f"     - UNet: ComfyUI/models/unet/wan2.1_t2v_14B.safetensors")
        print(f"     - T5: ComfyUI/models/text_encoders/models_t5_umt5-xxl-enc-bf16.pth")
        print(f"     - VAE: ComfyUI/models/vae/Wan2.1_VAE.pth")
        print(f"  3. Log: tail -50 {Path(__file__).parent}/comfyui_server.log")
        sys.exit(1)

if __name__ == "__main__":
    main()
