#!/usr/bin/env python3
"""
Gera vídeos de teste com todos os 4 modelos via API Docker
"""
import requests
import json
import time

MODELS = {
    "LTX-2": "http://localhost:8001",
    "Wan 2.1": "http://localhost:8002",
    "MAGI-1": "http://localhost:8003",
    "Waver": "http://localhost:8004"
}

TEST_PROMPT = "A cat walking on a beach at sunset, cinematic camera movement, golden hour lighting, 4k quality"

def generate_video(model_name, api_url):
    """Gera vídeo usando a API do modelo"""
    print(f"\n{'='*60}")
    print(f"Gerando vídeo com {model_name}...")
    print(f"{'='*60}")

    # Verifica health
    try:
        health = requests.get(f"{api_url}/health", timeout=5).json()
        print(f"✓ {model_name} está saudável: {health}")
    except Exception as e:
        print(f"✗ Erro verificando health: {e}")
        return False

    # Envia requisição de geração
    payload = {
        "prompt": TEST_PROMPT,
        "duration": 5,
        "resolution": "512x512",
        "fps": 24,
        "seed": 42
    }

    print(f"\nPrompt: {TEST_PROMPT}")
    print(f"Configuração: {payload}")
    print("\nEnviando requisição...")

    try:
        response = requests.post(
            f"{api_url}/generate",
            json=payload,
            timeout=600  # 10 minutos timeout
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCESSO! Vídeo gerado com {model_name}!")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"\n✗ Erro HTTP {response.status_code}")
            print(response.text)
            return False

    except requests.Timeout:
        print(f"\n⏱ Timeout - {model_name} está demorando muito (>10min)")
        return False
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        return False

def main():
    print("="*60)
    print("GERAÇÃO DE VÍDEOS - TODOS OS MODELOS")
    print("="*60)

    results = {}

    for model_name, api_url in MODELS.items():
        success = generate_video(model_name, api_url)
        results[model_name] = "✅ SUCESSO" if success else "✗ FALHOU"
        time.sleep(2)  # Pausa entre modelos

    # Resumo final
    print("\n" + "="*60)
    print("RESUMO FINAL")
    print("="*60)
    for model, status in results.items():
        print(f"{model:15} {status}")
    print("="*60)

if __name__ == "__main__":
    main()
