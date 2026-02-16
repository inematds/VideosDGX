#!/usr/bin/env python3
"""
Monitora o status dos jobs de geração de vídeo
"""
import requests
import time
import json

JOBS = {
    "LTX-2": ("http://localhost:8001", "ltx2-26252c62"),
    "Wan 2.1": ("http://localhost:8002", "wan21-66eb1181"),
    "MAGI-1": ("http://localhost:8003", "magi1-5d8c2647"),
    "Waver": ("http://localhost:8004", "waver-cf98097a")
}

def check_job_status(model_name, api_url, job_id):
    """Verifica status de um job"""
    try:
        response = requests.get(
            f"{api_url}/queue/status",
            params={"job_id": job_id},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def main():
    print("Monitorando geração de vídeos...")
    print("="*80)

    max_iterations = 60  # 10 minutos (60 x 10s)
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"\n[{iteration}/{max_iterations}] Verificando status...")

        all_done = True
        statuses = {}

        for model_name, (api_url, job_id) in JOBS.items():
            status = check_job_status(model_name, api_url, job_id)
            statuses[model_name] = status

            job_status = status.get("status", "unknown")
            print(f"  {model_name:12} - {job_status:12}", end="")

            if "error" in status:
                print(f" ERROR: {status['error']}")
            elif job_status == "completed":
                output = status.get("output_path", "N/A")
                print(f" ✅ Output: {output}")
            elif job_status == "failed":
                error = status.get("error", "Unknown error")
                print(f" ✗ Error: {error}")
            elif job_status in ["processing", "queued"]:
                progress = status.get("progress", 0)
                print(f" ⏳ {progress}%")
                all_done = False
            else:
                print(f" Status: {json.dumps(status)[:100]}")
                all_done = False

        if all_done:
            print("\n" + "="*80)
            print("✅ TODOS OS VÍDEOS FORAM GERADOS!")
            print("="*80)
            for model_name, status in statuses.items():
                if status.get("status") == "completed":
                    print(f"{model_name}: {status.get('output_path')}")
            break

        time.sleep(10)  # Espera 10s antes da próxima verificação

    if iteration >= max_iterations:
        print("\n⏱ Timeout - Alguns jobs ainda estão processando após 10 minutos")

if __name__ == "__main__":
    main()
