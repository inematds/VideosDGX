# Arquitetura VideosDGX

## Visão Geral

VideosDGX implementa uma arquitetura de microserviços containerizada para modelos de geração de vídeo, otimizada para o hardware DGX Spark 2026.

## Componentes Principais

### 1. Common Layer (Camada Compartilhada)

#### base.Dockerfile
- **Propósito**: Imagem base comum para todos os modelos
- **Conteúdo**:
  - Ubuntu 22.04
  - CUDA 12.3
  - PyTorch 2.2.0
  - Dependências comuns (transformers, diffusers, fastapi, etc.)
- **Vantagens**:
  - Build mais rápido (cache compartilhado)
  - Consistência entre containers
  - Redução de espaço em disco

#### model_loader.py
- **Responsabilidades**:
  - Carregamento sob demanda (lazy loading)
  - Gerenciamento de memória
  - Auto-unload baseado em timeout
  - Thread-safe operations
- **Padrão**: Singleton por container
- **Otimizações**:
  - Lock para evitar carregamentos duplicados
  - Timer para auto-unload configurável
  - Monitoramento de memória GPU/CPU

#### api_base.py
- **Framework**: FastAPI com Uvicorn
- **Responsabilidades**:
  - Endpoints REST padronizados
  - Sistema de fila de jobs (asyncio.Queue)
  - Worker assíncrono para processamento
  - Health checks e métricas
- **Padrão**: Template Method para geração de vídeo
- **Features**:
  - Validação automática (Pydantic)
  - Background processing
  - File serving (download de vídeos)

#### utils.py
- **Funções**:
  - Logging configurável
  - Monitoramento de recursos (GPU/CPU)
  - Coleta de métricas
  - Validação de parâmetros
- **Classes**:
  - `MetricsCollector`: Estatísticas de inferência

### 2. Model-Specific Layer

Cada modelo tem sua própria estrutura:

```
model_name/
├── Dockerfile          # Herda de base, adiciona deps específicas
├── app.py             # Entry point, instancia API
├── model_config.py    # Lógica de carregamento e geração
└── requirements.txt   # Dependências específicas
```

#### Dockerfile
- Herda de `videosdgx-base:latest`
- Instala dependências específicas
- Copia código comum + específico
- Define variáveis de ambiente

#### app.py
- Configura `ModelLoader` com função de carregamento
- Instancia `VideoModelAPI` com função de geração
- Exporta app FastAPI

#### model_config.py
- `load_MODEL_model()`: Carrega modelo com quantização
- `generate_video_MODEL()`: Implementa geração de vídeo

## Fluxo de Dados

### Geração de Vídeo

```
1. Cliente HTTP
   ↓
2. POST /generate (FastAPI)
   ↓
3. Validação (Pydantic)
   ↓
4. Criar Job
   ↓
5. Adicionar à Queue (asyncio.Queue)
   ↓
6. Worker assíncrono pega Job
   ↓
7. ModelLoader.get_model()
   ├─ Se não carregado: load()
   └─ Se carregado: retorna
   ↓
8. generate_video_MODEL(pipeline, request, output_path)
   ↓
9. Salvar vídeo em /outputs
   ↓
10. Atualizar Job (status=completed)
   ↓
11. Cliente pode fazer download via /jobs/{id}/download
```

### Carregamento de Modelo (Lazy Loading)

```
1. Container inicia
   ├─ API pronta (~500MB RAM)
   └─ Modelo NÃO carregado

2. Primeira requisição chega
   ↓
3. ModelLoader.get_model()
   ↓
4. Verificar se já carregado
   ├─ Sim: retornar modelo
   └─ Não: chamar load()

5. load()
   ├─ Adquirir lock
   ├─ Chamar load_function (model_config)
   ├─ Carregar com quantização
   ├─ Atualizar estado (loaded=True)
   └─ Iniciar timer de auto-unload

6. Retornar (model, pipeline)

7. Auto-unload (opcional)
   ├─ Timer dispara após X minutos
   ├─ Verificar última utilização
   └─ Se idle > threshold: unload()
```

## Quantização

### Estratégia por Modelo

| Modelo | Quantização | Biblioteca | Razão |
|--------|-------------|------------|-------|
| LTX-2 | FP4 (NF4) | bitsandbytes | Áudio+vídeo = grande, FP4 mantém qualidade |
| Wan 2.1 | FP8 | Native PyTorch | 14B params, FP8 balanceia tamanho/qualidade |
| MAGI-1 | FP4 (NF4) | bitsandbytes | Vídeos longos, economia de memória crítica |
| Waver | FP8 | Native PyTorch | Lightweight, FP8 suficiente |

### Implementação

#### FP4 (bitsandbytes)
```python
from transformers import BitsAndBytesConfig

config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

model = AutoModel.from_pretrained(
    model_id,
    quantization_config=config
)
```

#### FP8 (Native)
```python
model = Model.from_pretrained(
    model_id,
    torch_dtype=torch.float8_e4m3fn
)
```

## Otimizações para DGX Spark

### 1. Memória Unificada (128GB)
- `enable_model_cpu_offload()`: Aproveita memória compartilhada
- Carregamento sob demanda permite até 4 modelos ativos
- Auto-unload libera memória para outros modelos

### 2. Blackwell GB10
- FP4/FP8 quantização nativa acelerada
- ~1 PFLOP FP4 performance
- Uso de NVFP4 quando disponível

### 3. Bandwidth
- Attention slicing: `enable_attention_slicing()`
- VAE slicing: `enable_vae_slicing()`
- Reduced precision transfers

## Networking

```
┌─────────────────────────────────────────┐
│          Docker Bridge Network          │
│            (videosdgx_network)          │
├─────────────┬─────────────┬─────────────┤
│   ltx2      │   wan21     │   magi1     │
│   :8000     │   :8000     │   :8000     │
└─────────────┴─────────────┴─────────────┘
      │              │              │
      ├──────────────┼──────────────┼────> Host
      :8001          :8002          :8003
```

- Bridge network para comunicação inter-container
- Port mapping para acesso externo
- Containers isolados (network namespace)

## Storage

### Volumes

```
videosdgx_models/
├── ltx2/
│   └── [HuggingFace cache]
├── wan21/
├── magi1/
└── waver/

videosdgx_outputs/
├── ltx2-abc123.mp4
├── wan21-def456.mp4
└── ...
```

- **models**: Persistente, grande (100GB+)
- **outputs**: Persistente, cresce com uso

### Volume Lifecycle

1. **Criação**: `docker volume create videosdgx_models`
2. **Mount**: Todos os containers montam em `/models` e `/outputs`
3. **Compartilhamento**: Modelos compartilhados entre containers
4. **Backup**: `docker run --rm -v videosdgx_models:/data -v $(pwd):/backup ubuntu tar czf /backup/models.tar.gz /data`

## Health Checks

### Container Level
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Application Level
- `/health`: Status básico (sempre responde se API está up)
- `/ready`: Modelo carregado? (false se não carregado)
- `/info`: Detalhes completos (sistema + modelo + fila)

## Métricas

### Coletadas Automaticamente

- **Inference**:
  - Duração por geração
  - Tamanho do prompt
  - Taxa de sucesso/erro

- **Sistema**:
  - Memória GPU (alocada, livre)
  - Memória CPU (usada, disponível)
  - Tamanho da fila

- **Modelo**:
  - Status (carregado/descarregado)
  - Última utilização
  - Auto-unload timer

### Acesso

```bash
curl http://localhost:8001/metrics
```

Resposta:
```json
{
  "total_inferences": 42,
  "successful": 40,
  "failed": 2,
  "avg_duration_seconds": 45.2,
  "min_duration_seconds": 38.1,
  "max_duration_seconds": 62.3,
  "last_10": [...]
}
```

## Segurança

### Considerações Atuais

- Containers rodam como root (TODO: non-root user)
- Bind only localhost (não exposto externamente)
- Volume permissions (755)
- Sem autenticação (TODO: JWT)

### Melhorias Futuras

1. **User namespacing**: Containers com UID/GID não-root
2. **Secrets management**: Docker secrets para HuggingFace tokens
3. **TLS**: HTTPS para APIs
4. **Rate limiting**: Proteção contra abuse
5. **Input validation**: Sanitização de prompts

## Escalabilidade

### Vertical (Single DGX)
- 128GB permite 3-4 modelos simultâneos
- Fila gerencia concorrência
- Auto-unload otimiza uso de memória

### Horizontal (Multi-DGX)
- Replicar containers em múltiplos DGX
- Load balancer (nginx/traefik)
- Shared storage (NFS/Ceph)
- Redis para fila distribuída

### Limitações Atuais
- Single GPU por modelo (CUDA_VISIBLE_DEVICES=0)
- Sem suporte a multi-GPU (model parallelism)
- Fila in-memory (não persiste em restart)

## Testing Strategy

### Unit Tests
```python
# test_model_loader.py
def test_lazy_loading():
    loader = ModelLoader(...)
    assert not loader.is_loaded()
    model, pipeline = loader.get_model()
    assert loader.is_loaded()
```

### Integration Tests
```bash
# test_api_integration.sh
curl -X POST http://localhost:8001/generate -d '{...}'
# Verificar job_id retornado
# Poll até completion
# Download e verificar vídeo
```

### Performance Tests
```bash
./scripts/benchmark.py
# Verifica latência e throughput
```

## Deployment

### Production Checklist

- [ ] Models baixados e verificados
- [ ] Health checks configurados
- [ ] Logging centralizado (Loki/ELK)
- [ ] Monitoramento (Prometheus/Grafana)
- [ ] Backup automático de volumes
- [ ] Rate limiting habilitado
- [ ] Autenticação configurada
- [ ] SSL/TLS certificates
- [ ] Auto-restart policies
- [ ] Resource limits (docker-compose)

## Future Enhancements

1. **WebUI**: Interface web para geração
2. **Streaming**: SSE para progress updates
3. **Priority Queue**: Jobs com prioridade
4. **Model Caching**: Cache de outputs similares
5. **Batch API**: Processar múltiplos prompts
6. **Fine-tuning**: Endpoint para treinar modelos
7. **A/B Testing**: Comparar outputs de modelos
8. **Analytics**: Dashboard de uso

---

**Versão**: 1.0
**Data**: 2026-02-15
**Plataforma**: DGX Spark 2026
