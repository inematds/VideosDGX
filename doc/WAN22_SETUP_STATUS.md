# Wan 2.2 Setup - Status de Implementação

**Data de início:** 2026-02-16
**Status geral:** 🔄 Em progresso - Fase 2 (Wan 2.2 5B)

---

## Contexto

Após problemas com Wan 2.1 (safetensors headers muito grandes), decidimos implementar Wan 2.2 diretamente.

### Problema Wan 2.1
- ❌ `wan2.1_t2v_14B.safetensors` tem header >48KB
- ❌ `safetensors_rust 0.7.0` não suporta headers tão grandes
- ❌ Erro: "Error while deserializing header: header too large"
- ✅ **Solução:** Migrar para Wan 2.2

---

## Fase 2: Wan 2.2 5B - Status

### Downloads

| Arquivo | Tamanho | Status | Localização |
|---------|---------|--------|-------------|
| `wan2.2_vae.safetensors` | 1.4GB | ✅ Completo | `models/vae/` |
| `wan2.2_ti2v_5B_fp16.safetensors` | 9.3GB | 🔄 Baixando (~1-2h) | `models/unet/` |
| `models_t5_umt5-xxl-enc-bf16.pth` | 11GB | ✅ Compartilhado (2.1) | `models/text_encoders/` |

**Fonte:** `Comfy-Org/Wan_2.2_ComfyUI_Repackaged` (repositório oficial ComfyUI)

### Arquivos Criados

- ✅ `workflow_wan22_5b_t2v.json` - Workflow ComfyUI para Wan 2.2 5B
- ✅ `gerar_video_wan22_5b.py` - Script CLI para geração de vídeos

### Configuração do Workflow

```json
{
  "UNet": "wan2.2_ti2v_5B_fp16.safetensors",
  "VAE": "wan2.2_vae.safetensors",
  "Text Encoder": "models_t5_umt5-xxl-enc-bf16.pth",
  "Resolução padrão": "720x480",
  "Frames padrão": 33 (~2s @ 24fps),
  "CFG padrão": 6.0
}
```

### Próximos Passos (após download completar)

1. ✅ Aguardar download do modelo 5B (9.3GB)
2. 🔲 Reiniciar ComfyUI para carregar novos modelos
3. 🔲 Testar geração com `./gerar_video_wan22_5b.py "test prompt"`
4. 🔲 Verificar qualidade e performance
5. 🔲 Documentar resultados

---

## Fase 3: Wan 2.2 14B MoE - Planejado

### Modelos Necessários (ainda não baixados)

| Arquivo | Tamanho | Localização |
|---------|---------|-------------|
| `wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors` | ~35GB | `models/unet/` |
| `wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors` | ~35GB | `models/unet/` |
| VAE 2.2 | ✅ Já baixado | `models/vae/` |
| T5 Encoder | ✅ Compartilhado | `models/text_encoders/` |

**Total adicional:** ~70GB

### Workflow 14B MoE

Requer **dual-sampler**:
1. High Noise Expert (primeiros steps)
2. Low Noise Expert (steps finais)

Mais complexo que 5B, mas qualidade cinematográfica superior.

---

## Recursos do Wan 2.2 5B

### Capacidades

- ✅ **Text-to-Video**: Gera vídeos a partir de texto
- ✅ **Image-to-Video**: Modelo híbrido T2V+I2V
- ✅ **First-Last Frame**: Suporta condicionamento com frames inicial/final
- ✅ **Resoluções**: Até 720P (1280x720)
- ✅ **FPS**: 24fps output (gera em 16fps internamente)

### Vantagens vs 14B MoE

- ⚡ **Mais rápido**: ~1.5s/frame vs ~2.5s/frame
- 💾 **Menor VRAM**: 8-12GB vs 24GB+
- 📦 **Menor tamanho**: 9.3GB vs ~70GB
- 🔧 **Workflow mais simples**: Single model vs dual-sampler

### Desvantagens vs 14B MoE

- 📉 **Qualidade inferior**: Boa, mas não cinematográfica
- ⚠️ **Menos aderência ao prompt**: Pode desviar mais do texto
- 🎨 **Menos controle estético**: Menos preciso em iluminação/composição

---

## Comparação de Modelos Video (DGX Spark)

| Modelo | Status | Tamanho | VRAM | Recursos Únicos | Qualidade |
|--------|--------|---------|------|-----------------|-----------|
| **LTX-2 19B** | ✅ 100% | 41GB | ~60GB | **Áudio** | Balanceada |
| **Wan 2.1 14B** | ❌ Problema | 65GB | ~50GB | Velocidade | Boa |
| **Wan 2.2 5B** | 🔄 90% | 9.3GB | ~12GB | Híbrido T2V+I2V | Boa |
| **Wan 2.2 14B MoE** | ⏸️ Planejado | 70GB | ~70GB | Cinematográfico | Excelente |

---

## Comandos Úteis

### Testar Wan 2.2 5B (após download)

```bash
# Teste básico (480P, 2s)
./gerar_video_wan22_5b.py "a cat walking on a beach at sunset"

# HD 720P
./gerar_video_wan22_5b.py "mountain landscape" --width 1280 --height 720 --frames 50

# Vídeo longo (5s)
./gerar_video_wan22_5b.py "ocean waves" --frames 80
```

### Monitorar Downloads

```bash
# Status geral
ls -lh ComfyUI/models/unet/wan2.2*
ls -lh ComfyUI/models/vae/wan2.2*

# Progresso do download 5B
tail -f /tmp/claude-1000/-home-nmaldaner-projetos-VideosDGX/tasks/be8f2f7.output

# Verificar espaço em disco
df -h /home/nmaldaner/projetos/VideosDGX
```

### Reiniciar ComfyUI

```bash
./reiniciar_comfyui.sh
```

---

## Problemas Conhecidos

### Wan 2.1
- ❌ Safetensors header muito grande (>48KB)
- ❌ Incompatível com safetensors_rust 0.7.0
- ✅ Solução: Usar Wan 2.2

### T5 Encoder FP8
- ⚠️ `umt5_xxl_fp8_e4m3fn_scaled.safetensors` também tem header grande
- ✅ Workaround: Usar versão BF16 `.pth` (11GB)
- 📝 Aceitar maior uso de VRAM em troca de compatibilidade

---

## Próxima Atualização

Após download do modelo 5B completar (~1-2h), realizar testes e atualizar este documento com:
- Tempo de geração real
- Qualidade dos vídeos
- Uso de VRAM observado
- Decisão sobre prosseguir para 14B MoE

---

## Interface Web - Histórico de Versões

| Versão | Arquivo | Porta | Novidades |
|--------|---------|-------|-----------|
| v4.0 | `web_interface_v4.py` | 7860 | Multi-modelo inicial |
| v4.1 | `web_interface_v4_1.py` | 7861 | Image-to-Video (I2V) |
| **v4.2** | `web_interface_v4_2.py` | **7862** | **Fila de jobs + Cancelamento** |

### Iniciar Interface v4.2

```bash
cd /home/nmaldaner/projetos/VideosDGX
./iniciar_interface_web_v4_2.sh

# Ou diretamente:
source comfyui-env/bin/activate
python3 web_interface_v4_2.py
# Acesse: http://localhost:7862
```

### v4.2 — Funcionalidades

- **Fila ilimitada**: Submeta vários jobs sem esperar o anterior terminar
- **Status `queued`**: Jobs ficam em fila com posição visível (`#1`, `#2`, ...)
- **Cancelar**: Botão ✕ em cards `queued` (imediato) ou `processing` (≤5s)
- **Botão sempre ativo**: Não bloqueia mais ao ter um job processando

---

**Última atualização:** 2026-02-18 BRT
**Responsável:** Claude Code Agent (Sonnet 4.5)
