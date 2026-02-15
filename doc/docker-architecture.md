# Arquitetura Docker para Video LLMs no DGX Spark

## Resumo Executivo

Arquitetura containerizada para rodar 4 modelos de geração de vídeo (LTX-2, Wan 2.1, MAGI-1, Waver 1.0) no DGX Spark 2026.

**Decisões Arquiteturais:**
- ✅ Um container por modelo (isolamento total)
- ✅ API REST completa (FastAPI) para cada modelo
- ✅ Carregamento sob demanda (otimização de memória)
- ✅ Volumes Docker persistentes (portabilidade)

## Especificações do Hardware

**DGX Spark 2026:**
- 128GB memória unificada (CPU+GPU)
- ~1 PFLOP FP4 (Blackwell GB10)
- Suporte nativo a quantização FP4/FP8

## Estrutura do Projeto

```
VideosDGX/
├── docker-compose.yml          # Orquestração dos 4 containers
├── .env                        # Variáveis de ambiente
├── common/                     # Código compartilhado
│   ├── base.Dockerfile        # Base image NVIDIA CUDA
│   ├── api_base.py            # Framework FastAPI
│   ├── model_loader.py        # Lazy loading de modelos
│   └── utils.py               # Logging e métricas
├── ltx2/                      # LTX-2: Video + Audio
│   ├── Dockerfile
│   ├── app.py
│   ├── model_config.py        # FP4/NVFP4
│   └── requirements.txt
├── wan21/                     # Wan 2.1: Versátil 14B
│   ├── Dockerfile
│   ├── app.py
│   ├── model_config.py        # FP8
│   └── requirements.txt
├── magi1/                     # MAGI-1: Vídeo longo
│   ├── Dockerfile
│   ├── app.py
│   ├── model_config.py        # FP4
│   └── requirements.txt
├── waver/                     # Waver: Batch rápido
│   ├── Dockerfile
│   ├── app.py
│   ├── model_config.py        # FP8
│   └── requirements.txt
└── scripts/
    ├── download_models.sh     # Download de modelos
    ├── health_check.py        # Monitoramento
    └── benchmark.py           # Performance tests
```

## Componentes Principais

### 1. Base Image (`common/base.Dockerfile`)

```dockerfile
FROM nvidia/cuda:12.3.0-devel-ubuntu22.04

# Python 3.11 + dependências essenciais
RUN apt-get update && apt-get install -y \
    python3.11 python3-pip git wget \
    && rm -rf /var/lib/apt/lists/*

# PyTorch com CUDA + Blackwell support
RUN pip install --no-cache-dir \
    torch==2.2.0+cu123 torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu123

# Stack de Video LLM
RUN pip install --no-cache-dir \
    transformers>=4.38.0 \
    accelerate diffusers \
    fastapi uvicorn[standard] \
    pydantic python-multipart \
    pillow opencv-python einops safetensors

WORKDIR /app
```

### 2. API Framework (`common/api_base.py`)

**Funcionalidades:**
- Lazy loading: carrega modelo apenas na primeira requisição
- Queue system: gerencia múltiplas requisições
- Health checks: `/health`, `/ready`, `/info`
- Auto-unload: descarrega modelo após timeout (opcional)

**Endpoints Padrão:**
```
POST /generate       → Gera vídeo
GET  /health         → Status do container
GET  /ready          → Modelo carregado?
GET  /info           → Informações do modelo
POST /unload         → Descarrega modelo
GET  /queue/status   → Status da fila
```

### 3. Model Loader (`common/model_loader.py`)

**Responsabilidades:**
- Detecta se modelo já está em memória
- Aplica quantização (FP4/FP8) automaticamente
- Monitora uso de memória GPU
- Implementa cache inteligente

### 4. Docker Compose

```yaml
version: '3.8'

services:
  ltx2:
    build:
      context: .
      dockerfile: ltx2/Dockerfile
    ports:
      - "8001:8000"
    volumes:
      - models:/models
      - outputs:/outputs
    environment:
      - MODEL_PATH=/models/ltx2
      - QUANTIZATION=fp4
      - MAX_MEMORY=32GB
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s

  wan21:
    # Similar structure
    ports:
      - "8002:8000"
    environment:
      - QUANTIZATION=fp8
      - MAX_MEMORY=32GB

  magi1:
    ports:
      - "8003:8000"
    environment:
      - QUANTIZATION=fp4
      - MAX_MEMORY=28GB

  waver:
    ports:
      - "8004:8000"
    environment:
      - QUANTIZATION=fp8
      - MAX_MEMORY=20GB

volumes:
  models:     # Modelos baixados (100-200GB)
  outputs:    # Vídeos gerados
```

## Gerenciamento de Memória

### Estratégia de Carregamento Sob Demanda

| Estado | Memória RAM | Latência |
|--------|-------------|----------|
| Container iniciado | ~500MB/container | N/A |
| Modelo carregado | 15-35GB/modelo | 30-60s (primeira requisição) |
| Inferência | Memória constante | <5s (requisições subsequentes) |
| Auto-unload | -15-35GB | Libera após 30min inativo |

### Estimativa de Memória por Modelo

| Modelo | Quantização | RAM Ocupada | Capacidade no Spark |
|--------|-------------|-------------|---------------------|
| LTX-2 | FP4 (NVFP4) | ~25-30GB | ✅ Roda full version |
| Wan 2.1 | FP8 | ~28-32GB | ✅ Contexto máximo |
| MAGI-1 | FP4 (NVFP4) | ~20-25GB | ✅ Vídeos longos |
| Waver | FP8 | ~15-18GB | ✅ Batch paralelo |

**Total:** Com 128GB, pode manter **3-4 modelos carregados simultaneamente**.

## API de Uso

### Gerar Vídeo com LTX-2

```bash
curl -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A cat walking on a beach at sunset",
    "duration": 5,
    "resolution": "1024x576",
    "fps": 24,
    "seed": 42,
    "include_audio": true
  }'
```

**Response:**
```json
{
  "job_id": "ltx2-abc123",
  "status": "processing",
  "estimated_time": 120,
  "model_loaded": true,
  "memory_used_gb": 28.5,
  "queue_position": 0
}
```

### Verificar Status do Job

```bash
curl http://localhost:8001/queue/status?job_id=ltx2-abc123
```

### Verificar Saúde do Sistema

```bash
# Todos os containers
python scripts/health_check.py

# Container específico
curl http://localhost:8001/health
```

## Scripts de Utilidade

### 1. Download de Modelos (`scripts/download_models.sh`)

```bash
#!/bin/bash
# Cria volume e baixa modelos do HuggingFace

docker volume create videosdgx_models

# LTX-2
docker run --rm -v videosdgx_models:/models \
  python:3.11 \
  bash -c "pip install huggingface_hub && \
    huggingface-cli download Lightricks/LTX-Video --cache-dir /models/ltx2"

# Wan 2.1, MAGI-1, Waver...
```

### 2. Health Check (`scripts/health_check.py`)

```python
import requests

CONTAINERS = {
    "LTX-2": "http://localhost:8001",
    "Wan 2.1": "http://localhost:8002",
    "MAGI-1": "http://localhost:8003",
    "Waver": "http://localhost:8004"
}

for name, url in CONTAINERS.items():
    try:
        r = requests.get(f"{url}/health", timeout=5)
        info = requests.get(f"{url}/info").json()

        print(f"✅ {name}: OK")
        print(f"   Modelo carregado: {info['model_loaded']}")
        print(f"   Memória GPU: {info['memory_gb']}GB")
    except:
        print(f"❌ {name}: OFFLINE")
```

### 3. Benchmark (`scripts/benchmark.py`)

Testa performance de cada modelo:
- Tempo de carga inicial
- Tempo de inferência (cold vs warm)
- Qualidade de output
- Uso de memória

## Otimizações para DGX Spark

### 1. Memória Unificada
- Aproveitar 128GB compartilhados CPU+GPU
- Reduz overhead de transferências PCIe
- Permite buffers maiores para vídeo

### 2. Quantização Blackwell
```python
# model_config.py exemplo
QUANTIZATION_CONFIG = {
    "load_in_4bit": True,
    "bnb_4bit_compute_dtype": torch.float16,
    "bnb_4bit_use_double_quant": True,
    "bnb_4bit_quant_type": "nf4"  # NVFP4 quando disponível
}
```

### 3. Bandwidth Optimization
- Minimizar transfers entre CPU/GPU
- Usar pinned memory quando possível
- Batch processing inteligente

## Monitoramento (Opcional)

### Prometheus + Grafana

```yaml
# docker-compose.yml adicional
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

**Métricas Coletadas:**
- Tempo de inferência por modelo
- Uso de memória GPU em tempo real
- Taxa de sucesso/erro
- Tamanho da fila de jobs
- Throughput (vídeos/hora)

## Workflow de Desenvolvimento

### 1. Setup Inicial

```bash
# Clone o repositório
cd VideosDGX

# Build das images
docker-compose build

# Download dos modelos (pode demorar horas)
./scripts/download_models.sh

# Iniciar containers
docker-compose up -d

# Verificar saúde
python scripts/health_check.py
```

### 2. Testar Geração

```bash
# LTX-2: Vídeo + Audio
curl -X POST http://localhost:8001/generate \
  -d '{"prompt": "futuristic city", "duration": 5}'

# Wan 2.1: Versatilidade
curl -X POST http://localhost:8002/generate \
  -d '{"prompt": "ocean waves", "duration": 10}'

# MAGI-1: Vídeo longo
curl -X POST http://localhost:8003/generate \
  -d '{"prompt": "time lapse sunrise", "duration": 30}'

# Waver: Batch rápido
curl -X POST http://localhost:8004/generate \
  -d '{"prompt": "product showcase", "duration": 3}'
```

### 3. Verificar Outputs

```bash
# Listar vídeos gerados
docker volume inspect videosdgx_outputs

# Copiar para host
docker cp $(docker ps -qf "name=ltx2"):/outputs/video.mp4 ./output/
```

### 4. Monitorar Recursos

```bash
# GPU usage
nvidia-smi -l 1

# Container stats
docker stats

# Logs
docker-compose logs -f ltx2
```

## Troubleshooting

### Modelo não carrega

```bash
# Verificar espaço em disco
df -h

# Verificar CUDA
nvidia-smi

# Logs detalhados
docker-compose logs ltx2
```

### Out of Memory

```bash
# Descarregar modelos não usados
curl -X POST http://localhost:8001/unload
curl -X POST http://localhost:8002/unload

# Verificar memória disponível
nvidia-smi --query-gpu=memory.used,memory.free --format=csv
```

### Container não inicia

```bash
# Rebuild da image
docker-compose build --no-cache ltx2

# Verificar dependências
docker run --rm videosdgx-ltx2 pip list
```

## Próximos Passos

1. **Fine-tuning**: Adaptar modelos para casos específicos
2. **Web UI**: Interface gráfica para geração de vídeos
3. **Batch Processing**: Sistema de jobs assíncronos
4. **Cache System**: Reutilizar vídeos similares
5. **Auto-scaling**: Carregar/descarregar modelos baseado em demanda
6. **Multi-node**: Distribuir modelos em múltiplos DGX

## Estimativas de Custo Computacional

| Operação | Tempo | Memória GPU |
|----------|-------|-------------|
| Build images | 20-30min | N/A |
| Download modelos | 2-4h | N/A |
| Carga inicial modelo | 30-60s | 15-35GB |
| Gerar vídeo 5s (1024x576) | 1-3min | Constante |
| Gerar vídeo 30s (1024x576) | 5-15min | Constante |

## Referências

- DGX Spark: 128GB memória unificada, ~1 PFLOP FP4
- Blackwell GB10: Suporte nativo FP4/FP8
- Modelos: LTX-2, Wan 2.1, MAGI-1, Waver 1.0
- Documentação original: `doc/videsodgx.txt`
