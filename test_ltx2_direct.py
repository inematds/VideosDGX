#!/usr/bin/env python3
"""
Teste de geração de vídeo LTX-2 usando API Python direta
"""
import torch
from ltx_pipelines import DistilledPipeline

def generate_video():
    print("=== Teste LTX-2 - Geração Direta ===\n")

    # Configurações
    model_path = "/home/nmaldaner/projetos/VideosDGX/ComfyUI/models/checkpoints/ltx-2-19b-distilled.safetensors"
    prompt = "A cat walking on a beach at sunset, cinematic camera movement, golden hour lighting"
    output_path = "test_video_ltx2.mp4"

    print(f"Modelo: {model_path}")
    print(f"Prompt: {prompt}")
    print(f"Output: {output_path}\n")

    try:
        # Limpa cache CUDA antes
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            free, total = torch.cuda.mem_get_info(0)
            print(f"VRAM - Free: {free/(1024**3):.2f}GB / Total: {total/(1024**3):.2f}GB\n")

        print("Carregando modelo...")
        pipeline = DistilledPipeline.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto"
        )

        print("Gerando vídeo...")
        video = pipeline(
            prompt=prompt,
            num_frames=65,  # ~2.7 segundos a 24 fps
            height=512,
            width=768,
            num_inference_steps=8,  # Distilled model usa 8 steps
            guidance_scale=3.0
        )

        print(f"✓ Vídeo gerado com sucesso!")
        print(f"Shape: {video.shape if hasattr(video, 'shape') else 'N/A'}")
        print(f"Salvando em: {output_path}")

        # Salva vídeo
        # (implementação depende do formato retornado)

        return True

    except Exception as e:
        print(f"✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = generate_video()
    exit(0 if success else 1)
