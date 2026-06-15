#!/usr/bin/env python3
"""
LTX-2 Image-to-Video via ComfyUI
Uso: python3 gerar_video_ltx2_i2v.py "prompt" --image imagem.png [opções]
"""
import argparse, json, requests, sys, uuid
from pathlib import Path

COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR  = Path("/home/nmaldaner/projetos/VideosDGX/ComfyUI/output")
GEMMA_PATH  = "gemma-3-12b-it-qat-q4_0-unquantized/model-00001-of-00005.safetensors"
LTX_PATH    = "ltx-2-19b-distilled.safetensors"


def upload_image(image_path: str) -> str:
    """Faz upload da imagem para ComfyUI e retorna o nome do arquivo."""
    p = Path(image_path)
    with open(p, "rb") as f:
        files = {"image": (p.name, f, "image/png")}
        r = requests.post(f"{COMFYUI_URL}/upload/image", files=files, timeout=30)
    r.raise_for_status()
    return r.json()["name"]


def criar_workflow(prompt, image_name, negative="", width=768, height=512,
                   frames=49, fps=24, cfg=3.0, seed=42, prefix="ltx2_i2v"):
    import random
    if seed == -1:
        seed = random.randint(0, 2**32 - 1)

    return {
        "1":  {"inputs": {"ckpt_name": LTX_PATH}, "class_type": "CheckpointLoaderSimple"},
        "2":  {"inputs": {"gemma_path": GEMMA_PATH, "ltxv_path": LTX_PATH, "max_length": 512}, "class_type": "LTXVGemmaCLIPModelLoader"},
        "3":  {"inputs": {"text": prompt, "clip": ["2", 0]}, "class_type": "CLIPTextEncode"},
        "4":  {"inputs": {"text": negative, "clip": ["2", 0]}, "class_type": "CLIPTextEncode"},
        "5":  {"inputs": {"positive": ["3", 0], "negative": ["4", 0], "frame_rate": float(fps)}, "class_type": "LTXVConditioning"},
        "6":  {"inputs": {"width": width, "height": height, "length": frames, "batch_size": 1}, "class_type": "EmptyLTXVLatentVideo"},
        "7":  {"inputs": {"ckpt_name": LTX_PATH}, "class_type": "LTXVAudioVAELoader"},
        "8":  {"inputs": {"audio_vae": ["7", 0], "frames_number": frames, "frame_rate": fps, "batch_size": 1}, "class_type": "LTXVEmptyLatentAudio"},
        "20": {"inputs": {"image": image_name, "upload": "image"}, "class_type": "LoadImage"},
        "21": {"inputs": {"vae": ["1", 2], "image": ["20", 0], "latent": ["6", 0], "strength": 1.0}, "class_type": "LTXVImgToVideoConditionOnly"},
        "9":  {"inputs": {"video_latent": ["21", 0], "audio_latent": ["8", 0]}, "class_type": "LTXVConcatAVLatent"},
        "10": {"inputs": {"noise_seed": seed}, "class_type": "RandomNoise"},
        "11": {"inputs": {"sampler_name": "euler"}, "class_type": "KSamplerSelect"},
        "12": {"inputs": {"sigmas": "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"}, "class_type": "ManualSigmas"},
        "13": {"inputs": {"model": ["1", 0], "positive": ["5", 0], "negative": ["5", 1], "cfg": cfg}, "class_type": "CFGGuider"},
        "14": {"inputs": {"noise": ["10", 0], "guider": ["13", 0], "sampler": ["11", 0], "sigmas": ["12", 0], "latent_image": ["9", 0]}, "class_type": "SamplerCustomAdvanced"},
        "15": {"inputs": {"av_latent": ["14", 1]}, "class_type": "LTXVSeparateAVLatent"},
        "16": {"inputs": {"vae": ["1", 2], "latents": ["15", 0], "spatial_tiles": 4, "temporal_tile_length": 16, "spatial_overlap": 4, "temporal_overlap": 4, "last_frame_fix": False, "working_device": "auto", "working_dtype": "auto"}, "class_type": "LTXVSpatioTemporalTiledVAEDecode"},
        "17": {"inputs": {"samples": ["15", 1], "audio_vae": ["7", 0]}, "class_type": "LTXVAudioVAEDecode"},
        "18": {"inputs": {"images": ["16", 0], "audio": ["17", 0], "fps": float(fps)}, "class_type": "CreateVideo"},
        "19": {"inputs": {"video": ["18", 0], "filename_prefix": prefix, "format": "auto", "codec": "auto"}, "class_type": "SaveVideo"},
    }, seed


def submeter(workflow):
    r = requests.post(f"{COMFYUI_URL}/prompt",
                      json={"prompt": workflow, "client_id": str(uuid.uuid4())},
                      timeout=30)
    r.raise_for_status()
    return r.json()["prompt_id"]


def main():
    p = argparse.ArgumentParser(description="LTX-2 Image-to-Video")
    p.add_argument("prompt")
    p.add_argument("--image",      default="",  help="Caminho local da imagem (faz upload)")
    p.add_argument("--image-name", default="",  dest="image_name", help="Nome do arquivo já no ComfyUI (sem upload)")
    p.add_argument("--negative", default="")
    p.add_argument("--width",    type=int,   default=768)
    p.add_argument("--height",   type=int,   default=512)
    p.add_argument("--frames",   type=int,   default=49)
    p.add_argument("--fps",      type=int,   default=24)
    p.add_argument("--cfg",      type=float, default=3.0)
    p.add_argument("--seed",     type=int,   default=-1)
    p.add_argument("--output",   default="ltx2_i2v")
    args = p.parse_args()

    if args.image_name:
        image_name = args.image_name
        print(f"📎 Imagem já no ComfyUI: {image_name}")
    else:
        print("📤 Fazendo upload da imagem...")
        image_name = upload_image(args.image)
        print(f"   Imagem: {image_name}")

    workflow, seed = criar_workflow(
        args.prompt, image_name, args.negative,
        args.width, args.height, args.frames,
        args.fps, args.cfg, args.seed, args.output
    )

    print(f"🎬 LTX-2 I2V | {args.width}x{args.height} | {args.frames}f | seed={seed}")
    print(f"   Prompt: {args.prompt}")

    prompt_id = submeter(workflow)
    print(f"✅ SUCESSO! Geração iniciada!")
    print(f"   Prompt ID: {prompt_id}")
    print(f"📂 Output: {OUTPUT_DIR}/{args.output}_*.mp4")


if __name__ == "__main__":
    main()
