#!/usr/bin/env python3
"""
Health check para todos os containers VideosDGX
Verifica status, modelos carregados, e uso de memória
"""
import requests
import json
from typing import Dict, Any, List
from datetime import datetime
import sys

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

def check_health(endpoint: str) -> Dict[str, Any]:
    """Verifica endpoint /health"""
    try:
        response = requests.get(f"{endpoint}/health", timeout=5)
        if response.status_code == 200:
            return {"status": "healthy", "data": response.json()}
        else:
            return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"status": "offline", "error": "Connection refused"}
    except requests.exceptions.Timeout:
        return {"status": "timeout", "error": "Request timeout"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def check_ready(endpoint: str) -> Dict[str, Any]:
    """Verifica se modelo está carregado"""
    try:
        response = requests.get(f"{endpoint}/ready", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"ready": False, "error": f"HTTP {response.status_code}"}
    except:
        return {"ready": False, "error": "Request failed"}

def get_info(endpoint: str) -> Dict[str, Any]:
    """Obtém informações detalhadas"""
    try:
        response = requests.get(f"{endpoint}/info", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except:
        return {"error": "Request failed"}

def print_status_icon(status: str) -> str:
    """Retorna ícone colorido baseado no status"""
    if status == "healthy":
        return f"{Colors.GREEN}●{Colors.END}"
    elif status == "offline":
        return f"{Colors.RED}●{Colors.END}"
    else:
        return f"{Colors.YELLOW}●{Colors.END}"

def print_separator(char="=", length=80):
    """Imprime separador"""
    print(char * length)

def format_memory(mem_info: Dict) -> str:
    """Formata informações de memória"""
    if not mem_info or "error" in mem_info:
        return "N/A"

    if not mem_info.get("available", False):
        return "GPU N/A"

    allocated = mem_info.get("allocated_gb", 0)
    total = mem_info.get("total_gb", 0)
    return f"{allocated:.1f}GB / {total:.1f}GB"

def main():
    print()
    print_separator()
    print(f"{Colors.BOLD}VideosDGX - Health Check{Colors.END}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_separator()
    print()

    all_healthy = True
    results = []

    for model in MODELS:
        name = model["name"]
        endpoint = model["endpoint"]

        # Verificar health
        health = check_health(endpoint)
        ready = check_ready(endpoint) if health["status"] == "healthy" else {"ready": False}
        info = get_info(endpoint) if health["status"] == "healthy" else {}

        # Status icon
        icon = print_status_icon(health["status"])

        # Status text
        if health["status"] == "healthy":
            status_text = f"{Colors.GREEN}Online{Colors.END}"
        elif health["status"] == "offline":
            status_text = f"{Colors.RED}Offline{Colors.END}"
            all_healthy = False
        else:
            status_text = f"{Colors.YELLOW}{health['status'].title()}{Colors.END}"
            all_healthy = False

        # Model loaded
        model_loaded = ready.get("ready", False)
        loaded_text = f"{Colors.GREEN}Carregado{Colors.END}" if model_loaded else f"{Colors.YELLOW}Não carregado{Colors.END}"

        # Memory usage
        gpu_mem = "N/A"
        cpu_mem = "N/A"

        if "system" in info:
            gpu_info = info["system"].get("gpu_memory", {})
            cpu_info = info["system"].get("cpu_memory", {})

            gpu_mem = format_memory(gpu_info)
            cpu_mem = f"{cpu_info.get('used_gb', 0):.1f}GB / {cpu_info.get('total_gb', 0):.1f}GB"

        # Queue size
        queue_size = info.get("queue_size", 0)

        # Print model info
        print(f"{icon} {Colors.BOLD}{name}{Colors.END}")
        print(f"   Status:      {status_text}")
        print(f"   Endpoint:    {endpoint}")
        print(f"   Modelo:      {loaded_text}")
        print(f"   GPU Memory:  {gpu_mem}")
        print(f"   CPU Memory:  {cpu_mem}")
        print(f"   Queue:       {queue_size} jobs")

        if health.get("error"):
            print(f"   {Colors.RED}Error: {health['error']}{Colors.END}")

        print()

        results.append({
            "name": name,
            "status": health["status"],
            "loaded": model_loaded,
            "endpoint": endpoint
        })

    # Summary
    print_separator()
    print(f"{Colors.BOLD}Resumo{Colors.END}")
    print_separator()

    online_count = sum(1 for r in results if r["status"] == "healthy")
    loaded_count = sum(1 for r in results if r["loaded"])

    print(f"Containers online: {online_count}/{len(MODELS)}")
    print(f"Modelos carregados: {loaded_count}/{len(MODELS)}")

    if all_healthy:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Todos os serviços estão saudáveis{Colors.END}")
        print()
        return 0
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ Alguns serviços precisam de atenção{Colors.END}")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
