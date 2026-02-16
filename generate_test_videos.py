#!/usr/bin/env python3
"""
Script para gerar vídeos de teste com LTX-2 e Wan 2.1
"""
import json
import requests
import time
import sys

COMFYUI_URL = "http://localhost:8188"

def test_comfyui_connection():
    """Verifica se ComfyUI está acessível"""
    try:
        response = requests.get(f"{COMFYUI_URL}/system_stats", timeout=5)
        print("✓ ComfyUI está online")
        return True
    except Exception as e:
        print(f"✗ ComfyUI não acessível: {e}")
        return False

def load_workflow(workflow_path):
    """Carrega workflow JSON"""
    try:
        with open(workflow_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"✗ Erro ao carregar workflow: {e}")
        return None

def generate_video_ltx2(prompt="A cat walking on a beach at sunset"):
    """Tenta gerar vídeo com LTX-2"""
    print(f"\n=== Testando LTX-2 ===")
    print(f"Prompt: {prompt}")

    workflow_path = "ComfyUI/custom_nodes/ComfyUI-LTXVideo/example_workflows/LTX-2_T2V_Distilled_wLora.json"
    workflow = load_workflow(workflow_path)

    if not workflow:
        print("✗ Falha ao carregar workflow")
        return False

    # Envia workflow para API
    try:
        payload = {"prompt": workflow}
        response = requests.post(f"{COMFYUI_URL}/prompt", json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        print(f"✓ Workflow enviado: {result.get('prompt_id')}")
        return True
    except Exception as e:
        print(f"✗ Erro ao enviar workflow: {e}")
        return False

def check_models():
    """Verifica modelos disponíveis"""
    print("\n=== Verificando modelos disponíveis ===")

    endpoints = [
        "/checkpoints",
        "/clip",
        "/diffusion_models",
        "/text_encoders",
        "/vae"
    ]

    for endpoint in endpoints:
        try:
            response = requests.get(f"{COMFYUI_URL}{endpoint}", timeout=5)
            if response.status_code == 200:
                models = response.json()
                print(f"  {endpoint}: {len(models)} modelos")
        except:
            pass

def main():
    print("=== Teste de Geração de Vídeos ===\n")

    if not test_comfyui_connection():
        sys.exit(1)

    check_models()

    # Tenta gerar vídeo LTX-2
    success_ltx2 = generate_video_ltx2()

    if success_ltx2:
        print("\n✓ Teste LTX-2 iniciado com sucesso!")
        print("Aguarde alguns minutos para o vídeo ser gerado...")
        print("Vídeos salvos em: ComfyUI/output/")
    else:
        print("\n✗ Falha no teste LTX-2")
        print("Verifique os logs do ComfyUI para mais detalhes")

if __name__ == "__main__":
    main()
