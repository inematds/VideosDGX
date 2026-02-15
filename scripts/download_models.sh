#!/bin/bash
# Script para baixar modelos de vídeo para volumes Docker

set -e

echo "========================================="
echo "VideosDGX - Download de Modelos"
echo "========================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Criar volume se não existir
echo -e "${YELLOW}Verificando volumes Docker...${NC}"
docker volume create videosdgx_models 2>/dev/null || true
docker volume create videosdgx_outputs 2>/dev/null || true
echo -e "${GREEN}✓ Volumes verificados${NC}"
echo ""

# Função para download de modelo
download_model() {
    local model_name=$1
    local model_id=$2
    local quantization=$3

    echo -e "${YELLOW}Baixando $model_name...${NC}"
    echo "  Model ID: $model_id"
    echo "  Quantization: $quantization"

    # Usar container temporário com Python para download
    docker run --rm \
        -v videosdgx_models:/models \
        python:3.11-slim \
        bash -c "
            pip install -q huggingface-hub && \
            python3 -c '
from huggingface_hub import snapshot_download
import os

model_id = \"$model_id\"
cache_dir = \"/models/$model_name\"

print(f\"Baixando {model_id} para {cache_dir}...\")

try:
    snapshot_download(
        repo_id=model_id,
        cache_dir=cache_dir,
        resume_download=True,
        local_files_only=False
    )
    print(\"✓ Download completo!\")
except Exception as e:
    print(f\"⚠ Aviso: {e}\")
    print(\"Modelo pode não estar disponível. Será necessário configurar manualmente.\")
'
        "

    echo -e "${GREEN}✓ $model_name processado${NC}"
    echo ""
}

# Menu interativo
echo "Selecione quais modelos baixar:"
echo "1) LTX-2 (Full video + audio, ~25-30GB)"
echo "2) Wan 2.1 (14B, versatile, ~28-32GB)"
echo "3) MAGI-1 (Long-form video, ~20-25GB)"
echo "4) Waver 1.0 (Lightweight, ~15-18GB)"
echo "5) Todos os modelos"
echo "0) Sair"
echo ""
read -p "Escolha uma opção [0-5]: " choice

case $choice in
    1)
        echo ""
        echo "=== Baixando LTX-2 ==="
        download_model "ltx2" "Lightricks/LTX-2" "fp4"
        ;;
    2)
        echo ""
        echo "=== Baixando Wan 2.1 ==="
        download_model "wan21" "Wan-AI/Wan2.1-T2V-14B" "fp8"
        ;;
    3)
        echo ""
        echo "=== Baixando MAGI-1 ==="
        download_model "magi1" "sand-ai/MAGI-1" "fp4"
        ;;
    4)
        echo ""
        echo "=== Baixando Waver 1.0 ==="
        download_model "waver" "FoundationVision/Waver" "fp8"
        ;;
    5)
        echo ""
        echo "=== Baixando TODOS os modelos ==="
        download_model "ltx2" "Lightricks/LTX-2" "fp4"
        download_model "wan21" "Wan-AI/Wan2.1-T2V-14B" "fp8"
        download_model "magi1" "sand-ai/MAGI-1" "fp4"
        download_model "waver" "FoundationVision/Waver" "fp8"
        ;;
    0)
        echo "Saindo..."
        exit 0
        ;;
    *)
        echo -e "${RED}Opção inválida${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Download concluído!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Próximos passos:"
echo "1. Build das images: docker-compose build"
echo "2. Iniciar containers: docker-compose up -d"
echo "3. Verificar saúde: python scripts/health_check.py"
echo ""
