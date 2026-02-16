#!/usr/bin/env python3
"""
Teste LTX-2 forçando CPU (muito lento mas prova conceito)
"""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Força CPU

print("=== Teste LTX-2 - CPU Only ===")
print("AVISO: Geração em CPU é MUITO lenta (pode levar horas)\n")

try:
    from ltx_pipelines import DistilledPipeline
    import torch

    print(f"CUDA disponível: {torch.cuda.is_available()}")
    print(f"Device a ser usado: CPU\n")

    model_path = "/home/nmaldaner/projetos/VideosDGX/ComfyUI/models/checkpoints/ltx-2-19b-distilled.safetensors"

    print("Carregando modelo em CPU...")
    print("(Isso pode demorar vários minutos...)\n")

    pipeline = DistilledPipeline.from_pretrained(
        model_path,
        torch_dtype=torch.float32,
        device_map="cpu"
    )

    print("✓ Modelo carregado com sucesso em CPU!")
    print("\nGerando vídeo de 3 segundos...")
    print("(Estimativa: 30-60 minutos em CPU)\n")

    video = pipeline(
        prompt="A simple test: a red ball on white background",
        num_frames=25,  # Apenas 1 segundo para teste rápido
        height=256,     # Resolução mínima para teste
        width=256,
        num_inference_steps=4,  # Mínimo de steps
        guidance_scale=2.0
    )

    print("\n✓ SUCESSO! Vídeo gerado em CPU!")
    print(f"Shape: {video.shape if hasattr(video, 'shape') else type(video)}")

except Exception as e:
    print(f"\n✗ Erro: {e}")
    import traceback
    traceback.print_exc()
