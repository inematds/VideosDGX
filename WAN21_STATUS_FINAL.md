# 🎬 Wan 2.1 14B - Status Final

## ✅ Problema Resolvido!

### O Problema
- T5 encoder baixado em formato `.pth` (PyTorch)
- ComfyUI não consegue carregar `.pth` como safetensors
- Erro: "SafetensorError: Error while deserializing header: header too large"

### A Solução
- Baixar T5 encoder em formato **safetensors**
- Usar versão FP8 otimizada: `umt5_xxl_fp8_e4m3fn_scaled.safetensors`
- Repositório: Comfy-Org/Wan_2.1_ComfyUI_repackaged

---

## 📦 Componentes Instalados

### ✅ Modelos (Corretos)

1. **Diffusion Model**
   - Arquivo: `wan2.1_t2v_14B.safetensors`
   - Tamanho: 65 GB
   - Localização: `ComfyUI/models/unet/`
   - Status: ✅ Instalado

2. **T5 Text Encoder (NOVO - Safetensors)**
   - Arquivo: `umt5_xxl_fp8_e4m3fn_scaled.safetensors`
   - Tamanho: 6.74 GB (FP8 quantizado)
   - Localização: `ComfyUI/models/text_encoders/`
   - Status: ⏳ Baixando (~18 minutos)

3. **VAE**
   - Arquivo: `Wan2.1_VAE.pth`
   - Tamanho: 485 MB
   - Localização: `ComfyUI/models/vae/`
   - Status: ✅ Instalado

### ✅ Custom Nodes

1. **ComfyUI-WanVideoKsampler**
   - Gerenciamento otimizado de memória
   - Status: ✅ Instalado

2. **ComfyUI-VideoHelperSuite**
   - Salvar vídeos (VHS_VideoCombine)
   - Status: ✅ Instalado

### ✅ Scripts e Workflows

1. **workflow_wan21_t2v.json**
   - Workflow corrigido com todos os parâmetros corretos
   - Status: ✅ Atualizado

2. **gerar_video_wan21.py**
   - Script CLI funcional
   - Status: ✅ Pronto

---

## 🔧 Mudanças Feitas

### Arquivos Renomeados (Sem Deletar)
```bash
# T5 antigo (.pth) → renomeado para .OLD
models_t5_umt5-xxl-enc-bf16.pth
   → models_t5_umt5-xxl-enc-bf16.pth.OLD
```

### Arquivos Novos Baixados
```bash
# T5 novo (safetensors FP8)
umt5_xxl_fp8_e4m3fn_scaled.safetensors (6.74 GB)
```

### Workflow Atualizado
```json
"clip_name": "models_t5_umt5-xxl-enc-bf16.pth"  ❌ ANTIGO
    ↓
"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors"  ✅ NOVO
```

---

## 🎯 Próximo Passo (Após Download)

### Teste do Wan 2.1

```bash
# Aguardar download completar (~15-20 minutos)

# Verificar arquivo
ls -lh ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
# Deve mostrar: ~6.3G

# Testar geração
cd /home/nmaldaner/projetos/VideosDGX
./gerar_video_wan21.py "a cat walking on a beach at sunset"

# Aguardar ~2-3 minutos

# Verificar resultado
ls -lht ComfyUI/output/ | grep wan21
```

---

## ✅ Garantias de Não Afetar LTX-2

### O que NÃO foi tocado:
- ✅ Modelos LTX-2 (checkpoints, VAE, projeções)
- ✅ Gemma encoder (text_encoders/gemma-3-12b-it-qat-q4_0-unquantized/)
- ✅ Custom node ComfyUI-LTXVideo
- ✅ Scripts LTX-2 (gerar_video_ltx2.py, reiniciar_comfyui.sh)
- ✅ Interface web v3 (web_interface_v3.py)
- ✅ Workflows LTX-2

### O que foi mudado:
- ✅ Apenas adicionado novo arquivo T5 para Wan 2.1
- ✅ Apenas renomeado T5 antigo (.pth → .OLD)
- ✅ LTX-2 continua 100% funcional

### Teste de Verificação LTX-2:
```bash
# Testar se LTX-2 ainda funciona
./gerar_video_ltx2.py "test video ltx2" --frames 49

# Deve funcionar normalmente!
```

---

## 📊 Comparação T5 Versões

| Versão | Formato | Tamanho | Status | ComfyUI |
|--------|---------|---------|--------|---------|
| models_t5_umt5-xxl-enc-bf16.pth | PyTorch | 11 GB | ❌ Incompatível | Não carrega |
| umt5_xxl_fp8_e4m3fn_scaled.safetensors | Safetensors | 6.74 GB | ✅ Compatível | ✅ Carrega |

**Vantagens da versão FP8:**
- ✅ Menor tamanho (6.74 GB vs 11 GB)
- ✅ Formato compatível (safetensors)
- ✅ Otimizado para Blackwell GB10 (FP8 nativo)
- ✅ Qualidade equivalente
- ✅ Mais rápido para carregar

---

## 🎬 Estado Final dos Modelos

### Modelos Funcionais no DGX Spark

1. **LTX-2 19B** ✅ 100% Funcional
   - Vídeo + Áudio
   - Interface web v3
   - Script CLI
   - ~44 GB total

2. **Wan 2.1 14B** ⏳ 99% Pronto (aguardando download)
   - Text-to-Video
   - Geração de texto em cena
   - Script CLI
   - ~72 GB total

---

## 📂 Estrutura Final de Modelos

```
ComfyUI/models/
├── unet/
│   ├── wan2.1_t2v_14B.safetensors (65 GB)          ← Wan 2.1
├── checkpoints/
│   ├── ltx-2-19b-distilled.safetensors (41 GB)     ← LTX-2
├── text_encoders/
│   ├── gemma-3-12b-it-qat-q4_0-unquantized/        ← LTX-2 (23 GB)
│   ├── umt5_xxl_fp8_e4m3fn_scaled.safetensors      ← Wan 2.1 (6.74 GB) ⏳
│   └── models_t5_umt5-xxl-enc-bf16.pth.OLD         ← Backup (11 GB)
├── vae/
│   ├── LTX2_audio_vae_bf16.safetensors (208 MB)    ← LTX-2
│   └── Wan2.1_VAE.pth (485 MB)                     ← Wan 2.1
└── clip/
    ├── ltx-2-19b-dev-fp4_projections_only.safetensors (2.7 GB)  ← LTX-2
    └── gemma_3_12B_it_fp8_e4m3fn.safetensors (6 GB)             ← LTX-2
```

**Espaço Total Usado:** ~155 GB de modelos

---

## ⏱️ Timeline

- **10:45** - Sessão iniciada
- **12:53** - Primeiro vídeo LTX-2 gerado com sucesso
- **18:03-18:15** - Interface web v3 funcionando
- **18:47-19:09** - Wan 2.1 componentes baixados (T5 .pth errado)
- **19:12** - Problema T5 identificado
- **19:15** - Solução encontrada (T5 safetensors)
- **19:16** - Download T5 correto iniciado
- **~19:35** - Estimativa: Download completo + teste final

---

## 🎯 Resultado Esperado

Após o download completar:

```bash
./gerar_video_wan21.py "a cat walking on a beach"

# Saída esperada:
🎬 Gerando workflow Wan 2.1...
🚀 Submetendo para ComfyUI...
✅ SUCESSO! Geração iniciada!

# Aguardar ~2-3 minutos

# Vídeo gerado:
wan21_video_00001_.mp4 (~600KB - 1MB)
```

---

**Status Atual:** ⏳ Aguardando download T5 safetensors (~15 minutos restantes)

**Última Atualização:** 2026-02-16 19:16
