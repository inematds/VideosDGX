#!/usr/bin/env python3
"""
Benchmark para modelos VideosDGX
Testa performance de cada modelo com prompts padronizados
"""
import requests
import json
import time
from typing import Dict, Any, List
from datetime import datetime
import sys
import argparse

# Cores para terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

MODELS = [
    {"name": "LTX-2", "port": 8001, "endpoint": "http://localhost:8001"},
    {"name": "Wan 2.1", "port": 8002, "endpoint": "http://localhost:8002"},
    {"name": "MAGI-1", "port": 8003, "endpoint": "http://localhost:8003"},
    {"name": "Waver 1.0", "port": 8004, "endpoint": "http://localhost:8004"},
]

TEST_PROMPTS = [
    {
        "name": "Simple scene",
        "prompt": "A cat walking on a beach at sunset",
        "duration": 3,
        "resolution": "512x512",
        "fps": 24
    },
    {
        "name": "Complex scene",
        "prompt": "A bustling city street at night with neon lights and people walking",
        "duration": 5,
        "resolution": "1024x576",
        "fps": 24
    },
]

def print_separator(char="=", length=80):
    """Imprime separador"""
    print(char * length)

def run_benchmark(endpoint: str, test_case: Dict) -> Dict[str, Any]:
    """Executa benchmark para um modelo"""
    try:
        # Criar job
        print(f"  Enviando prompt: {test_case['prompt'][:50]}...")

        payload = {
            "prompt": test_case["prompt"],
            "duration": test_case["duration"],
            "resolution": test_case["resolution"],
            "fps": test_case["fps"],
            "seed": 42  # Seed fixo para reprodutibilidade
        }

        start_time = time.time()

        response = requests.post(
            f"{endpoint}/generate",
            json=payload,
            timeout=10
        )

        if response.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "duration": 0
            }

        job_data = response.json()
        job_id = job_data.get("job_id")

        if not job_id:
            return {
                "success": False,
                "error": "No job_id returned",
                "duration": 0
            }

        print(f"  Job criado: {job_id}")
        print(f"  Aguardando conclusão...")

        # Poll job status
        max_wait = 300  # 5 minutos
        poll_interval = 2  # 2 segundos

        elapsed = 0
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval

            status_response = requests.get(
                f"{endpoint}/jobs/{job_id}",
                timeout=5
            )

            if status_response.status_code != 200:
                continue

            job_status = status_response.json()
            status = job_status.get("status")

            if status == "completed":
                total_time = time.time() - start_time
                return {
                    "success": True,
                    "duration": round(total_time, 2),
                    "job_id": job_id,
                    "status": job_status
                }
            elif status == "failed":
                return {
                    "success": False,
                    "error": job_status.get("error", "Unknown error"),
                    "duration": round(time.time() - start_time, 2)
                }

            # Mostrar progresso
            progress = job_status.get("progress", 0)
            print(f"  Progresso: {progress}%", end='\r')

        return {
            "success": False,
            "error": "Timeout",
            "duration": max_wait
        }

    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection refused", "duration": 0}
    except Exception as e:
        return {"success": False, "error": str(e), "duration": 0}

def main():
    parser = argparse.ArgumentParser(description="Benchmark VideosDGX models")
    parser.add_argument(
        "--model",
        choices=["ltx2", "wan21", "magi1", "waver", "all"],
        default="all",
        help="Modelo para testar (default: all)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Executar apenas teste rápido"
    )
    args = parser.parse_args()

    print()
    print_separator()
    print(f"{Colors.BOLD}VideosDGX - Benchmark{Colors.END}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_separator()
    print()

    # Filtrar modelos
    if args.model == "all":
        models_to_test = MODELS
    else:
        port_map = {"ltx2": 8001, "wan21": 8002, "magi1": 8003, "waver": 8004}
        port = port_map[args.model]
        models_to_test = [m for m in MODELS if m["port"] == port]

    # Filtrar testes
    tests = [TEST_PROMPTS[0]] if args.quick else TEST_PROMPTS

    results = []

    for model in models_to_test:
        name = model["name"]
        endpoint = model["endpoint"]

        print(f"{Colors.BOLD}Testando {name}{Colors.END}")
        print(f"Endpoint: {endpoint}")
        print()

        # Verificar se modelo está online
        try:
            health = requests.get(f"{endpoint}/health", timeout=5)
            if health.status_code != 200:
                print(f"{Colors.RED}✗ Modelo offline{Colors.END}\n")
                results.append({
                    "model": name,
                    "online": False,
                    "tests": []
                })
                continue
        except:
            print(f"{Colors.RED}✗ Modelo offline{Colors.END}\n")
            results.append({
                "model": name,
                "online": False,
                "tests": []
            })
            continue

        print(f"{Colors.GREEN}✓ Modelo online{Colors.END}\n")

        model_results = []

        for i, test in enumerate(tests, 1):
            print(f"Teste {i}/{len(tests)}: {test['name']}")

            result = run_benchmark(endpoint, test)

            if result["success"]:
                print(f"{Colors.GREEN}  ✓ Sucesso em {result['duration']}s{Colors.END}\n")
            else:
                print(f"{Colors.RED}  ✗ Falhou: {result['error']}{Colors.END}\n")

            model_results.append({
                "test": test["name"],
                "success": result["success"],
                "duration": result["duration"],
                "error": result.get("error")
            })

        results.append({
            "model": name,
            "online": True,
            "tests": model_results
        })

    # Summary
    print()
    print_separator()
    print(f"{Colors.BOLD}Resumo dos Resultados{Colors.END}")
    print_separator()
    print()

    for result in results:
        model_name = result["model"]

        if not result["online"]:
            print(f"{Colors.RED}●{Colors.END} {model_name}: Offline")
            continue

        tests = result["tests"]
        success_count = sum(1 for t in tests if t["success"])
        total = len(tests)

        if success_count == total:
            icon = f"{Colors.GREEN}●{Colors.END}"
        elif success_count > 0:
            icon = f"{Colors.YELLOW}●{Colors.END}"
        else:
            icon = f"{Colors.RED}●{Colors.END}"

        avg_duration = sum(t["duration"] for t in tests if t["success"]) / max(success_count, 1)

        print(f"{icon} {Colors.BOLD}{model_name}{Colors.END}")
        print(f"   Testes: {success_count}/{total} sucessos")
        print(f"   Tempo médio: {avg_duration:.2f}s")

        for test in tests:
            status = f"{Colors.GREEN}✓{Colors.END}" if test["success"] else f"{Colors.RED}✗{Colors.END}"
            print(f"   {status} {test['test']}: {test['duration']:.2f}s")

        print()

    # Salvar resultados em JSON
    output_file = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results
        }, f, indent=2)

    print(f"Resultados salvos em: {output_file}")
    print()

if __name__ == "__main__":
    main()
