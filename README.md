# VideosDGX - Docker Multi-Container para Video LLMs

Infraestrutura containerizada para rodar modelos de geração de vídeo no DGX Spark 2026.

## 📋 Visão Geral

Este projeto fornece uma arquitetura Docker multi-container para executar 4 modelos de geração de vídeo:

- **LTX-2**: Geração completa de vídeo + áudio (FP4, ~25-30GB)
- **Wan 2.1**: Modelo versátil de 14B parâmetros (FP8, ~28-32GB)
- **MAGI-1**: Modelo autoregressive para vídeos longos (FP4, ~20-25GB)
- **Waver 1.0**: Modelo leve para batch generation (FP8, ~15-18GB)

### Características

- ✅ Isolamento por container (controle granular)
- ✅ APIs REST completas para cada modelo
- ✅ Carregamento sob demanda (lazy loading)
- ✅ Quantização otimizada (FP4/FP8)
- ✅ Gerenciamento de fila de jobs
- ✅ Health checks e métricas
- ✅ Volumes persistentes para modelos e outputs

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                    DGX Spark 2026                       │
│              128GB Unified Memory + Blackwell           │
├─────────────┬─────────────┬─────────────┬──────────────┤
│  LTX-2      │  Wan 2.1    │  MAGI-1     │  Waver 1.0   │
│  :8001      │  :8002      │  :8003      │  :8004       │
│  FP4        │  FP8        │  FP4        │  FP8         │
└─────────────┴─────────────┴─────────────┴──────────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                          │
                   ┌──────┴──────┐
                   │   Volumes   │
                   ├─────────────┤
                   │   models/   │
                   │   outputs/  │
                   └─────────────┘
```

## 🚀 Quick Start

### Pré-requisitos

- Docker Engine 24.0+
- Docker Compose 2.20+
- NVIDIA Docker Runtime
- GPU com suporte CUDA 12.3+
- ~100GB de espaço em disco (para modelos)

### 1. Build da Base Image

Primeiro, construa a imagem base compartilhada:

```bash
docker build -t videosdgx-base:latest -f common/base.Dockerfile .
```

### 2. Download dos Modelos

Execute o script de download (interativo):

```bash
./scripts/download_models.sh
```

Ou baixe manualmente usando HuggingFace CLI:

```bash
# Criar volume
docker volume create videosdgx_models

# Exemplo: baixar LTX-2
huggingface-cli download Lightricks/LTX-Video --local-dir /var/lib/docker/volumes/videosdgx_models/_data/ltx2
```

### 3. Build dos Containers

```bash
docker-compose build
```

### 4. Iniciar os Serviços

```bash
docker-compose up -d
```

### 5. Verificar Status

```bash
./scripts/health_check.py
```

Saída esperada:

```
=========================================
VideosDGX - Health Check
=========================================

● LTX-2
   Status:      Online
   Endpoint:    http://localhost:8001
   Modelo:      Não carregado
   GPU Memory:  0.5GB / 128GB
   CPU Memory:  0.8GB / 128GB
   Queue:       0 jobs

...
```

## 📡 Uso das APIs

Todas as APIs seguem o mesmo padrão REST.

### Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Informações gerais da API |
| `/health` | GET | Health check básico |
| `/ready` | GET | Verifica se modelo está carregado |
| `/info` | GET | Informações detalhadas (sistema + modelo) |
| `/generate` | POST | Gera vídeo a partir de prompt |
| `/unload` | POST | Descarrega modelo da memória |
| `/queue/status` | GET | Status da fila de jobs |
| `/jobs/{job_id}` | GET | Status de um job específico |
| `/jobs/{job_id}/download` | GET | Download do vídeo gerado |
| `/metrics` | GET | Métricas de performance |

### Exemplo: Gerar Vídeo

```bash
# LTX-2 (porta 8001)
curl -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A cat walking on a beach at sunset",
    "duration": 5,
    "resolution": "1024x576",
    "fps": 24,
    "seed": 42,
    "guidance_scale": 7.5
  }'
```

Resposta:

```json
{
  "job_id": "ltx2-abc12345",
  "status": "queued",
  "queue_position": 1,
  "estimated_time_seconds": 60,
  "model_loaded": false
}
```

### Verificar Status do Job

```bash
curl http://localhost:8001/jobs/ltx2-abc12345
```

Resposta (em processamento):

```json
{
  "job_id": "ltx2-abc12345",
  "model_name": "ltx2",
  "status": "processing",
  "prompt": "A cat walking on a beach at sunset",
  "duration": 5,
  "created_at": "2026-02-15T10:30:00",
  "started_at": "2026-02-15T10:30:05",
  "completed_at": null,
  "output_path": null,
  "error": null,
  "progress": 45
}
```

### Download do Vídeo

```bash
# Quando status = "completed"
curl -O http://localhost:8001/jobs/ltx2-abc12345/download
```

Ou acesse diretamente no navegador: `http://localhost:8001/jobs/ltx2-abc12345/download`

## 🔧 Configuração

### Variáveis de Ambiente (.env)

```bash
# Auto-unload: minutos de inatividade antes de descarregar modelo
# 0 = nunca descarregar
AUTO_UNLOAD_MINUTES=30

# Logging
LOG_LEVEL=INFO
```

### Portas dos Serviços

| Modelo | Porta | Endpoint |
|--------|-------|----------|
| LTX-2 | 8001 | http://localhost:8001 |
| Wan 2.1 | 8002 | http://localhost:8002 |
| MAGI-1 | 8003 | http://localhost:8003 |
| Waver 1.0 | 8004 | http://localhost:8004 |

## 📊 Monitoramento

### Health Check

```bash
./scripts/health_check.py
```

### Benchmark

Testar performance de todos os modelos:

```bash
./scripts/benchmark.py
```

Testar apenas um modelo:

```bash
./scripts/benchmark.py --model ltx2
```

Teste rápido:

```bash
./scripts/benchmark.py --quick
```

### Logs dos Containers

```bash
# Todos os containers
docker-compose logs -f

# Container específico
docker-compose logs -f ltx2

# Últimas 100 linhas
docker-compose logs --tail=100 wan21
```

### Uso de Recursos

```bash
# GPU
nvidia-smi

# Containers
docker stats

# Volumes
docker volume inspect videosdgx_models
docker volume inspect videosdgx_outputs
```

## 🎯 Gerenciamento de Memória

### Estratégia de Carregamento

1. **Container inicia**: API pronta, modelo NÃO carregado (~500MB RAM)
2. **Primeira requisição**: Modelo carregado automaticamente
3. **Requisições subsequentes**: Modelo já em memória (rápido)
4. **Auto-unload**: Após X minutos de inatividade (configurável)

### Estimativa de Memória

Com 128GB de memória unificada:

| Modelo | Quantização | Memória | Tempo de Carga |
|--------|-------------|---------|----------------|
| LTX-2 | FP4 | ~25-30GB | ~60-90s |
| Wan 2.1 | FP8 | ~28-32GB | ~70-100s |
| MAGI-1 | FP4 | ~20-25GB | ~50-80s |
| Waver 1.0 | FP8 | ~15-18GB | ~40-60s |

**Capacidade**: 3-4 modelos carregados simultaneamente

### Descarregar Modelo Manualmente

```bash
curl -X POST http://localhost:8001/unload
```

Resposta:

```json
{
  "status": "unloaded",
  "model_name": "ltx2",
  "memory_freed_gb": 28.5,
  "memory_after": {
    "allocated_gb": 0.5,
    "free_gb": 127.5
  }
}
```

## 🛠️ Comandos Úteis

### Docker Compose

```bash
# Iniciar todos os serviços
docker-compose up -d

# Parar todos os serviços
docker-compose down

# Rebuild de um serviço específico
docker-compose build ltx2

# Restart de um serviço
docker-compose restart wan21

# Ver logs
docker-compose logs -f

# Escalar serviço (não recomendado para GPUs)
docker-compose up -d --scale waver=2
```

### Volumes

```bash
# Listar volumes
docker volume ls

# Inspecionar volume
docker volume inspect videosdgx_models

# Backup de modelos
docker run --rm -v videosdgx_models:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/models_backup.tar.gz /data

# Restore de modelos
docker run --rm -v videosdgx_models:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/models_backup.tar.gz -C /data
```

### Limpeza

```bash
# Parar e remover containers
docker-compose down

# Remover volumes (CUIDADO: apaga modelos!)
docker-compose down -v

# Limpar imagens não utilizadas
docker image prune -a

# Limpar tudo (CUIDADO!)
docker system prune -a --volumes
```

## 🐛 Troubleshooting

### Container não inicia

```bash
# Verificar logs
docker-compose logs ltx2

# Verificar GPU
nvidia-smi

# Verificar NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.3.0-base-ubuntu22.04 nvidia-smi
```

### Modelo não carrega

```bash
# Verificar se modelo existe
docker volume inspect videosdgx_models

# Verificar permissões
docker exec videosdgx-ltx2 ls -la /models/ltx2

# Verificar logs de carregamento
docker-compose logs ltx2 | grep "Carregando"
```

### Out of Memory

```bash
# Verificar memória GPU
nvidia-smi

# Descarregar modelos não usados
curl -X POST http://localhost:8001/unload
curl -X POST http://localhost:8002/unload

# Reiniciar container
docker-compose restart ltx2
```

### Performance lenta

1. Verificar se modelo está carregado: `curl http://localhost:8001/ready`
2. Verificar fila: `curl http://localhost:8001/queue/status`
3. Verificar métricas: `curl http://localhost:8001/metrics`
4. Ajustar número de inference steps nas configs

## 📚 Estrutura de Arquivos

```
VideosDGX/
├── common/                 # Código compartilhado
│   ├── base.Dockerfile    # Base image com CUDA + PyTorch
│   ├── api_base.py        # Framework FastAPI
│   ├── model_loader.py    # Gerenciador de modelos
│   └── utils.py           # Utilidades (logging, metrics)
├── ltx2/                  # LTX-2 específico
│   ├── Dockerfile
│   ├── app.py
│   ├── model_config.py
│   └── requirements.txt
├── wan21/                 # Wan 2.1 específico
├── magi1/                 # MAGI-1 específico
├── waver/                 # Waver 1.0 específico
├── scripts/               # Scripts de utilidade
│   ├── download_models.sh
│   ├── health_check.py
│   └── benchmark.py
├── docker-compose.yml     # Orquestração
├── .env                   # Configurações
├── .dockerignore
└── README.md
```

## 🔐 Segurança

- **Sem exposição externa**: Por padrão, APIs só acessíveis via localhost
- **Volumes isolados**: Cada container tem acesso controlado
- **Sem root**: Containers rodam com usuário não-privilegiado (TODO)
- **Secrets**: Use Docker secrets para credenciais HuggingFace

## 📈 Próximos Passos

- [ ] Adicionar frontend web
- [ ] Implementar autenticação JWT
- [ ] Sistema de cache de vídeos
- [ ] Auto-scaling baseado em demanda
- [ ] Prometheus + Grafana para monitoramento
- [ ] CI/CD pipeline
- [ ] Fine-tuning de modelos
- [ ] Suporte a múltiplas GPUs

## 📄 Licença

Este projeto é fornecido como está, para uso no DGX Spark 2026.

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, abra uma issue primeiro para discutir mudanças maiores.

## 📞 Suporte

Para problemas, abra uma issue neste repositório.

---

**DGX Spark 2026** | 128GB Unified Memory | ~1 PFLOP FP4 Performance
