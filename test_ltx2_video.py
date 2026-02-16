#!/usr/bin/env python3
"""
Script de teste para geração de vídeo com LTX-2 via API do ComfyUI
"""

import json
import requests
import time
import os
from pathlib import Path

COMFYUI_URL = "http://localhost:8188"
WORKFLOW_PATH = "ComfyUI/custom_nodes/ComfyUI-LTXVideo/example_workflows/LTX-2_T2V_Distilled_wLora.json"

def load_workflow():
    """Carrega o workflow JSON"""
    with open(WORKFLOW_PATH, 'r') as f:
        return json.load(f)

def modify_workflow_prompt(workflow, prompt_text):
    """Modifica o prompt no workflow"""
    # Procura por nós de texto/prompt e atualiza
    for node in workflow['nodes']:
        if node['type'] in ['CLIPTextEncode', 'String', 'PrimitiveString']:
            if 'widgets_values' in node and len(node['widgets_values']) > 0:
                if 'prompt' in str(node).lower() or 'text' in str(node).lower():
                    node['widgets_values'][0] = prompt_text
    return workflow

def queue_prompt(workflow):
    """Envia o workflow para a fila do ComfyUI"""
    url = f"{COMFYUI_URL}/prompt"
    payload = {
        "prompt": workflow,
        "client_id": "test-client"
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao enviar prompt: {e}")
        return None

def check_queue():
    """Verifica o status da fila"""
    url = f"{COMFYUI_URL}/queue"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao verificar fila: {e}")
        return None

def wait_for_completion(prompt_id, max_wait=600):
    """Aguarda a conclusão da geração"""
    start_time = time.time()

    while time.time() - start_time < max_wait:
        queue_data = check_queue()
        if not queue_data:
            time.sleep(5)
            continue

        # Verifica se o prompt ainda está na fila
        running = queue_data.get('queue_running', [])
        pending = queue_data.get('queue_pending', [])

        is_running = any(item[1] == prompt_id for item in running)
        is_pending = any(item[1] == prompt_id for item in pending)

        if not is_running and not is_pending:
            print("✓ Geração concluída!")
            return True

        print(f"Aguardando... ({int(time.time() - start_time)}s)")
        time.sleep(5)

    print("⚠ Timeout aguardando conclusão")
    return False

def main():
    print("=== Teste de Geração de Vídeo LTX-2 ===\n")

    # Verifica se o ComfyUI está rodando
    try:
        response = requests.get(f"{COMFYUI_URL}/system_stats", timeout=5)
        print("✓ ComfyUI está online")
    except:
        print("✗ ComfyUI não está acessível. Verifique se está rodando.")
        return

    # Carrega o workflow
    print("Carregando workflow...")
    workflow = load_workflow()

    # Modifica o prompt
    test_prompt = "A cat walking on a beach at sunset, cinematic, high quality"
    print(f"Prompt: {test_prompt}")
    workflow = modify_workflow_prompt(workflow, test_prompt)

    # Envia para a fila
    print("\nEnviando para geração...")
    result = queue_prompt(workflow)

    if not result:
        print("✗ Falha ao enviar workflow")
        return

    prompt_id = result.get('prompt_id')
    print(f"✓ Prompt ID: {prompt_id}")

    # Aguarda conclusão
    print("\nGerando vídeo (isso pode levar alguns minutos)...")
    success = wait_for_completion(prompt_id)

    if success:
        output_dir = Path("ComfyUI/output")
        videos = list(output_dir.glob("*.mp4"))
        if videos:
            latest_video = max(videos, key=lambda p: p.stat().st_mtime)
            print(f"\n✓ Vídeo gerado: {latest_video}")
            print(f"  Tamanho: {latest_video.stat().st_size / (1024**2):.2f} MB")
        else:
            print("\n⚠ Vídeo gerado mas não encontrado no diretório de output")

if __name__ == "__main__":
    main()
