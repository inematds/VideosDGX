# Makefile para VideosDGX
# Simplifica comandos comuns do projeto

.PHONY: help build up down restart logs health benchmark clean base

# Variáveis
COMPOSE := docker-compose
PYTHON := python3

# Help
help:
	@echo "VideosDGX - Comandos Disponíveis"
	@echo "================================="
	@echo ""
	@echo "Setup:"
	@echo "  make base         - Build da imagem base"
	@echo "  make build        - Build de todos os containers"
	@echo "  make download     - Download dos modelos"
	@echo ""
	@echo "Operação:"
	@echo "  make up           - Iniciar todos os serviços"
	@echo "  make down         - Parar todos os serviços"
	@echo "  make restart      - Reiniciar todos os serviços"
	@echo "  make logs         - Ver logs (Ctrl+C para sair)"
	@echo ""
	@echo "Monitoramento:"
	@echo "  make health       - Health check de todos os modelos"
	@echo "  make benchmark    - Benchmark de performance"
	@echo "  make stats        - Estatísticas dos containers"
	@echo ""
	@echo "Limpeza:"
	@echo "  make clean        - Parar containers e limpar"
	@echo "  make clean-all    - Limpar tudo (incluindo volumes)"
	@echo ""
	@echo "Desenvolvimento:"
	@echo "  make logs-ltx2    - Logs do LTX-2"
	@echo "  make logs-wan21   - Logs do Wan 2.1"
	@echo "  make logs-magi1   - Logs do MAGI-1"
	@echo "  make logs-waver   - Logs do Waver"
	@echo ""

# Build da imagem base
base:
	@echo "Building base image..."
	docker build -t videosdgx-base:latest -f common/base.Dockerfile .

# Build de todos os containers
build: base
	@echo "Building all containers..."
	$(COMPOSE) build

# Download dos modelos
download:
	@echo "Iniciando download de modelos..."
	./scripts/download_models.sh

# Iniciar serviços
up:
	@echo "Starting all services..."
	$(COMPOSE) up -d
	@echo ""
	@echo "Services started! Run 'make health' to check status"

# Parar serviços
down:
	@echo "Stopping all services..."
	$(COMPOSE) down

# Reiniciar serviços
restart:
	@echo "Restarting all services..."
	$(COMPOSE) restart

# Ver logs
logs:
	$(COMPOSE) logs -f

# Logs específicos por modelo
logs-ltx2:
	$(COMPOSE) logs -f ltx2

logs-wan21:
	$(COMPOSE) logs -f wan21

logs-magi1:
	$(COMPOSE) logs -f magi1

logs-waver:
	$(COMPOSE) logs -f waver

# Health check
health:
	@$(PYTHON) scripts/health_check.py

# Benchmark
benchmark:
	@$(PYTHON) scripts/benchmark.py

# Quick benchmark
benchmark-quick:
	@$(PYTHON) scripts/benchmark.py --quick

# Estatísticas
stats:
	@echo "Container stats:"
	@docker stats --no-stream
	@echo ""
	@echo "GPU stats:"
	@nvidia-smi

# Limpeza básica
clean:
	@echo "Stopping and removing containers..."
	$(COMPOSE) down
	@echo "Cleaning up..."
	docker image prune -f

# Limpeza completa (CUIDADO: remove volumes!)
clean-all:
	@echo "WARNING: This will remove all containers, images, and volumes!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(COMPOSE) down -v; \
		docker image prune -a -f; \
		echo "All cleaned!"; \
	fi

# Setup completo (primeira vez)
setup: base download build
	@echo ""
	@echo "Setup completo! Próximos passos:"
	@echo "1. make up         - Iniciar serviços"
	@echo "2. make health     - Verificar status"
	@echo "3. make benchmark  - Testar performance"

# Test rápido
test: up
	@sleep 5
	@make health
