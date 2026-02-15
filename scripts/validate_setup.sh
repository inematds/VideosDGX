#!/bin/bash
# Script de validação - verifica se todos os arquivos necessários existem

set -e

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "VideosDGX - Validação de Setup"
echo "========================================="
echo ""

ERRORS=0
WARNINGS=0

# Função para verificar arquivo
check_file() {
    local file=$1
    local required=$2  # true ou false

    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
        return 0
    else
        if [ "$required" = "true" ]; then
            echo -e "${RED}✗${NC} $file (OBRIGATÓRIO)"
            ((ERRORS++))
        else
            echo -e "${YELLOW}⚠${NC} $file (opcional)"
            ((WARNINGS++))
        fi
        return 1
    fi
}

# Função para verificar diretório
check_dir() {
    local dir=$1

    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $dir/"
        return 0
    else
        echo -e "${RED}✗${NC} $dir/ (FALTANDO)"
        ((ERRORS++))
        return 1
    fi
}

echo "Verificando estrutura de diretórios..."
echo "--------------------------------------"
check_dir "common"
check_dir "ltx2"
check_dir "wan21"
check_dir "magi1"
check_dir "waver"
check_dir "scripts"
echo ""

echo "Verificando arquivos comuns..."
echo "-------------------------------"
check_file "common/base.Dockerfile" "true"
check_file "common/api_base.py" "true"
check_file "common/model_loader.py" "true"
check_file "common/utils.py" "true"
echo ""

echo "Verificando LTX-2..."
echo "--------------------"
check_file "ltx2/Dockerfile" "true"
check_file "ltx2/app.py" "true"
check_file "ltx2/model_config.py" "true"
check_file "ltx2/requirements.txt" "true"
echo ""

echo "Verificando Wan 2.1..."
echo "----------------------"
check_file "wan21/Dockerfile" "true"
check_file "wan21/app.py" "true"
check_file "wan21/model_config.py" "true"
check_file "wan21/requirements.txt" "true"
echo ""

echo "Verificando MAGI-1..."
echo "---------------------"
check_file "magi1/Dockerfile" "true"
check_file "magi1/app.py" "true"
check_file "magi1/model_config.py" "true"
check_file "magi1/requirements.txt" "true"
echo ""

echo "Verificando Waver 1.0..."
echo "------------------------"
check_file "waver/Dockerfile" "true"
check_file "waver/app.py" "true"
check_file "waver/model_config.py" "true"
check_file "waver/requirements.txt" "true"
echo ""

echo "Verificando scripts..."
echo "----------------------"
check_file "scripts/download_models.sh" "true"
check_file "scripts/health_check.py" "true"
check_file "scripts/benchmark.py" "true"
check_file "scripts/validate_setup.sh" "true"
echo ""

echo "Verificando arquivos de configuração..."
echo "----------------------------------------"
check_file "docker-compose.yml" "true"
check_file ".env" "true"
check_file ".dockerignore" "true"
check_file ".gitignore" "true"
check_file "Makefile" "true"
echo ""

echo "Verificando documentação..."
echo "---------------------------"
check_file "README.md" "true"
check_file "QUICKSTART.md" "true"
check_file "ARCHITECTURE.md" "true"
check_file "PROJECT_SUMMARY.md" "true"
check_file "docker-compose.override.yml.example" "false"
echo ""

echo "Verificando permissões de scripts..."
echo "-------------------------------------"
for script in scripts/*.sh scripts/*.py; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            echo -e "${GREEN}✓${NC} $script (executável)"
        else
            echo -e "${YELLOW}⚠${NC} $script (não executável - rode: chmod +x $script)"
            ((WARNINGS++))
        fi
    fi
done
echo ""

echo "Verificando dependências do sistema..."
echo "---------------------------------------"

# Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓${NC} Docker instalado: $DOCKER_VERSION"
else
    echo -e "${RED}✗${NC} Docker não encontrado"
    ((ERRORS++))
fi

# Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo -e "${GREEN}✓${NC} Docker Compose instalado: $COMPOSE_VERSION"
elif docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version)
    echo -e "${GREEN}✓${NC} Docker Compose (plugin) instalado: $COMPOSE_VERSION"
else
    echo -e "${RED}✗${NC} Docker Compose não encontrado"
    ((ERRORS++))
fi

# NVIDIA Docker
if docker run --rm --gpus all nvidia/cuda:12.3.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓${NC} NVIDIA Docker Runtime funcionando"
else
    echo -e "${RED}✗${NC} NVIDIA Docker Runtime não disponível"
    ((ERRORS++))
fi

# Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} Python instalado: $PYTHON_VERSION"
else
    echo -e "${YELLOW}⚠${NC} Python3 não encontrado (necessário para scripts)"
    ((WARNINGS++))
fi

echo ""
echo "========================================="
echo "Resumo da Validação"
echo "========================================="
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Todos os arquivos obrigatórios estão presentes!${NC}"
else
    echo -e "${RED}✗ $ERRORS erros encontrados${NC}"
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS avisos${NC}"
fi

echo ""
echo "Próximos passos:"
echo "----------------"

if [ $ERRORS -eq 0 ]; then
    echo "1. make base        # Build da imagem base"
    echo "2. ./scripts/download_models.sh  # Download dos modelos"
    echo "3. make build       # Build dos containers"
    echo "4. make up          # Iniciar serviços"
    echo "5. make health      # Verificar status"
else
    echo "Corrija os erros acima antes de prosseguir."
fi

echo ""

# Exit code
if [ $ERRORS -eq 0 ]; then
    exit 0
else
    exit 1
fi
