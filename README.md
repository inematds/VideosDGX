# VideosDGX - Docker Multi-Container para Video LLMs

Infraestrutura containerizada para rodar modelos de geração de vídeo no DGX Spark 2026.

## 📋 Visão Geral

Este projeto fornece uma arquitetura Docker multi-container para executar 4 modelos de geração de vídeo:

- **LTX-2**: Geração completa de vídeo + áudio (FP4, ~25-30GB)
- **Wan 2.1**: Modelo versátil de 14B parâmetros (FP8, ~28-32GB)
- **MAGI-1**: Modelo autoregressive para vídeos longos (FP4, ~20-25GB)
- **Waver 1.0**: Modelo leve para batch generation (FP8, ~15-18GB)

## 🎯 Status Atual (2026-02-16)

### ✅ Funcionando

- ✅ **Docker Containers**: Todos os 4 containers (ltx2, wan21, magi1, waver) estão UP e respondendo
- ✅ **APIs REST**: Endpoints /health retornando status saudável em todas as portas (8001-8004)
- ✅ **Job Submission**: Jobs de geração de vídeo aceitos com sucesso por todos os modelos
- ✅ **Modelos Baixados**:
  - LTX-2: 293GB completo (checkpoint 41GB + Gemma FP8 6GB + projections 2.7GB + audio VAE 208MB)
  - Wan 2.1: 65GB completo (modelo montado de 6 shards)
  - MAGI-1: Download em andamento
  - Waver: Disponível no Docker volume

### ⚠️ Issues Conhecidos

1. **LTX-2**: Carregamento iniciou mas travou em 50% (4/8 shards) - possível timeout ou OOM
2. **Wan 2.1 & Waver**: Erro `torch.xpu` AttributeError durante inicialização (relacionado a ARM64 + CUDA)
3. **MAGI-1**: Erro de configuração - falta `model_type` no config.json
4. **CUDA Memory**: Sistema host com 117GB/120GB VRAM já alocados, impedindo testes locais

### 📁 Scripts de Teste Disponíveis

- `generate_all_videos.py`: Submete jobs de geração para todos os 4 modelos simultaneamente
- `check_jobs_status.py`: Monitora status dos jobs em loop (10s de intervalo, 10min timeout)
- `test_ltx2_direct.py`: Testa LTX-2 via API Python direta (ltx_pipelines)
- `test_ltx2_cpu.py`: Teste de fallback em CPU (extremamente lento)

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

## 🔄 Abordagens Alternativas

Além da arquitetura Docker, este projeto inclui duas abordagens alternativas configuradas:

### ComfyUI (Recomendado pela NVIDIA)

ComfyUI está instalado e configurado com custom nodes para LTX-2:

```bash
# Ativar ambiente
source comfyui-env/bin/activate

# Iniciar servidor (requer resolver issue de memória)
cd ComfyUI
python main.py --port 8188

# Acessar: http://localhost:8188
```

**Localização dos modelos ComfyUI**:
- Checkpoint: `ComfyUI/models/checkpoints/ltx-2-19b-distilled.safetensors` (41GB)
- Text Encoder: `ComfyUI/models/clip/gemma_3_12B_it_fp8_e4m3fn.safetensors` (6GB)
- Projections: `ComfyUI/models/clip/ltx-2-19b-dev-fp4_projections_only.safetensors` (2.7GB)
- Audio VAE: `ComfyUI/models/vae/LTX2_audio_vae_bf16.safetensors` (208MB)

**Custom Nodes**:
- ComfyUI-LTXVideo (oficial Lightricks)
- MAGI-1 (SandAI-org)

### Python API Direta (LTX-2)

API oficial da Lightricks instalada via pip:

```bash
# Ativar ambiente
source comfyui-env/bin/activate

# Gerar vídeo via linha de comando
python -m ltx_pipelines.distilled \
  --checkpoint-path ComfyUI/models/checkpoints/ltx-2-19b-distilled.safetensors \
  --gemma-root ComfyUI/models/clip/ \
  --prompt "A cat walking on a beach at sunset" \
  --output-path output.mp4 \
  --num-frames 65 \
  --height 512 \
  --width 768 \
  --num-inference-steps 8 \
  --guidance-scale 3.0
```

**Pacotes instalados**:
- `ltx-core`
- `ltx-pipelines`

## 🧪 Testes Realizados

### Geração de Vídeos (16/02/2026)

Executado `generate_all_videos.py` com prompt: *"A cat walking on a beach at sunset, cinematic camera movement, golden hour lighting, 4k quality"*

**Resultados**:

| Modelo | Status | Job ID | Detalhes |
|--------|--------|--------|----------|
| LTX-2 | ⏸️ Travado | ltx2-26252c62 | Carregamento iniciou (50%), depois timeout |
| Wan 2.1 | ❌ Falhou | wan21-66eb1181 | torch.xpu AttributeError |
| MAGI-1 | ❌ Falhou | magi1-5d8c2647 | Config.json sem model_type |
| Waver | ❌ Falhou | waver-cf98097a | torch.xpu AttributeError |

**Log completo**: `generation_results.log`

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

### ⚠️ Erros Conhecidos e Soluções

#### 1. torch.xpu AttributeError (Wan 2.1, Waver)

**Erro**:
```
AttributeError: module 'torch' has no attribute 'xpu'
```

**Causa**: Bibliotecas tentando detectar Intel XPU em ambiente ARM64 + CUDA

**Soluções tentadas**:
- ❌ Environment variables (`ACCELERATE_USE_XPU=0`)
- ❌ Monkey-patching `torch.xpu`
- ⏳ **Solução necessária**: Patch no código de inicialização dos containers

**Workaround temporário**:
```python
# Adicionar antes de imports de diffusers/accelerate
import torch
if not hasattr(torch, 'xpu'):
    class DummyXPU:
        @staticmethod
        def is_available(): return False
    torch.xpu = DummyXPU()
```

#### 2. CUDA Out of Memory (Sistema Host)

**Erro**:
```
RuntimeError: CUDA out of memory. Tried to allocate X GB
(GPU 0; 120.00 GiB total capacity; 117.00 GiB already allocated)
```

**Causa**: Processo root (PID 2351379) consumindo 117GB/120GB VRAM

**Solução**:
```bash
# Requer sudo
sudo kill -9 2351379
sudo sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'
nvidia-smi
```

**Verificação**:
```bash
# Mostrar processos usando GPU
fuser -v /dev/nvidia*
ps aux | grep 2351379
```

#### 3. MAGI-1 Config Missing

**Erro**:
```
Unrecognized model in /models/magi1. Should have a `model_type` key in its config.json
```

**Causa**: Download incompleto ou configuração ausente

**Solução**:
```bash
# Verificar integridade do download
docker exec videosdgx-magi1 ls -lah /models/magi1/
docker exec videosdgx-magi1 cat /models/magi1/config.json

# Re-download se necessário
docker exec videosdgx-magi1 huggingface-cli download SandAI-org/MAGI-1 --local-dir /models/magi1
```

#### 4. LTX-2 Loading Timeout

**Sintoma**: Carregamento trava em 50% (4/8 checkpoint shards)

**Diagnóstico**:
```bash
# Verificar logs detalhados
docker logs videosdgx-ltx2 --tail 200

# Verificar uso de memória durante carregamento
docker stats videosdgx-ltx2

# Verificar se processo está travado ou apenas lento
docker exec videosdgx-ltx2 ps aux
```

**Possíveis causas**:
- OOM durante carregamento de shards grandes
- Deadlock em carregamento multi-threaded
- Timeout muito curto nas requisições

**Solução**:
```bash
# Aumentar timeout no check_jobs_status.py
max_iterations = 120  # 20 minutos ao invés de 10

# Ou restart do container
docker-compose restart ltx2
```

#### 5. Gemma Model Gated (resolvido)

**Erro**: `403 Client Error: Forbidden for url: google/gemma-3-12b-it`

**Solução aplicada**: Usar modelo alternativo não-gated
```bash
# Baixado: GitMylo/LTX-2-comfy_gemma_fp8_e4m3fn
# Localização: ComfyUI/models/clip/gemma_3_12B_it_fp8_e4m3fn.safetensors
```

## 📚 Estrutura de Arquivos

```
VideosDGX/
├── common/                    # Código compartilhado (Docker)
│   ├── base.Dockerfile        # Base image com CUDA + PyTorch
│   ├── api_base.py            # Framework FastAPI
│   ├── model_loader.py        # Gerenciador de modelos
│   └── utils.py               # Utilidades (logging, metrics)
├── ltx2/                      # LTX-2 container específico
│   ├── Dockerfile
│   ├── app.py
│   ├── model_config.py
│   └── requirements.txt
├── wan21/                     # Wan 2.1 container
├── magi1/                     # MAGI-1 container
├── waver/                     # Waver container
├── scripts/                   # Scripts de utilidade
│   ├── download_models.sh
│   ├── health_check.py
│   └── benchmark.py
├── ComfyUI/                   # ComfyUI installation
│   ├── models/
│   │   ├── checkpoints/       # LTX-2 checkpoint (41GB)
│   │   ├── clip/              # Gemma FP8 encoder (6GB) + projections (2.7GB)
│   │   └── vae/               # Audio VAE (208MB)
│   └── custom_nodes/
│       ├── ComfyUI-LTXVideo/  # LTX-2 custom node
│       └── MAGI-1/            # MAGI-1 custom node
├── LTX-2/                     # Repositório oficial Lightricks
│   └── src/ltx_pipelines/     # API Python direta
├── comfyui-env/               # Python venv (PyTorch 2.10.0+cu130)
├── docker-compose.yml         # Orquestração dos 4 containers
├── .env                       # Configurações de ambiente
├── generate_all_videos.py    # Script de teste - submete jobs para todos os modelos
├── check_jobs_status.py      # Script de monitoramento de jobs
├── test_ltx2_direct.py        # Teste LTX-2 via Python API
├── test_ltx2_cpu.py           # Teste LTX-2 em CPU (fallback)
├── generation_results.log     # Log dos testes executados
├── CLAUDE.md                  # Instruções para Claude Code
├── ARCHITECTURE.md            # Documentação da arquitetura
├── QUICKSTART.md              # Guia rápido de início
├── PROJECT_SUMMARY.md         # Resumo do projeto
├── CHANGELOG.md               # Histórico de mudanças
└── README.md                  # Este arquivo
```

**Volumes Docker**:
```
videosdgx_models/
├── ltx2/           # 293GB - Repositório completo HuggingFace
├── wan21/          # 65GB  - Modelo Wan 2.1 completo
├── magi1/          # Em download
└── waver/          # Modelo Waver 1.0

videosdgx_outputs/  # Vídeos gerados pelos containers
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
