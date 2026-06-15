# 🎬 Wan 2.1 14B - Informações Técnicas

## 📦 Modelo Instalado

### Arquivos Baixados/Instalando

1. **Diffusion Model**
   - Arquivo: `wan2.1_t2v_14B.safetensors`
   - Tamanho: 65 GB
   - Localização: `ComfyUI/models/unet/`
   - Status: ✅ Instalado

2. **Text Encoder (T5)**
   - Arquivo: `models_t5_umt5-xxl-enc-bf16.pth`
   - Tamanho: 11.4 GB
   - Localização: `ComfyUI/models/text_encoders/`
   - Status: ⏳ Baixando (~20 min restantes)

3. **VAE**
   - Arquivo: `Wan2.1_VAE.pth`
   - Tamanho: 508 MB
   - Localização: `ComfyUI/models/vae/`
   - Status: ⏳ Baixando (~5 min restantes)

4. **Custom Node**
   - Nome: ComfyUI-WanVideoKsampler
   - Função: Gerenciamento otimizado de memória
   - Localização: `ComfyUI/custom_nodes/ComfyUI-WanVideoKsampler/`
   - Status: ✅ Instalado

## ⚙️ Especificações Técnicas

### Arquitetura
- **Parâmetros**: 14 bilhões
- **Tipo**: Diffusion Transformer com Flow Matching
- **Dimensão do modelo**: 5120
- **Layers**: 40 blocos transformer
- **Attention heads**: 40

### Capacidades
- **Text-to-Video** (T2V)
- **Suporte bilíngue**: Chinês e Inglês
- **Resoluções suportadas**: 480P e 720P
- **Frames**: Até 128 frames (8 segundos) com 12GB VRAM
- **Geração de texto**: Primeiro modelo open-source capaz de gerar texto dentro do vídeo

## 🎯 Parâmetros Recomendados

### Configuração Básica (480P, 5s)
```
Resolution: 480P (854x480 ou 720x480)
Frames: 80 frames (~5 segundos)
Steps: 4-8
CFG Scale: 1.0 (oficial) ou 5-7 (mais controle)
Frame Rate: Salvar em 24fps (modelo gera em 16fps)
```

### Configuração Longa (480P, 8s)
```
Resolution: 480P
Frames: 128 frames (~8 segundos)
Steps: 6-8
CFG: 1.0
VRAM mínima: 12GB
```

### Configuração HD (720P, 5s)
```
Resolution: 720P (1280x720)
Frames: 80 frames
Steps: 6-8
CFG: 1.0
VRAM mínima: 16GB+
```

## 💾 Requisitos de Hardware

### VRAM (GPU Memory)

| Configuração | VRAM Mínima | VRAM Recomendada |
|--------------|-------------|------------------|
| 480P, 5s     | 8GB         | 12GB             |
| 480P, 8s     | 12GB        | 16GB             |
| 720P, 5s     | 16GB        | 20GB+            |

**DGX Spark**: ✅ 128GB memória unificada - suporta qualquer configuração!

### RAM (System Memory)
- Mínimo: 32GB
- Recomendado: 64GB+
- **DGX Spark**: ✅ 128GB compartilhados

### Armazenamento
- Modelos: ~77GB (65GB + 11.4GB + 0.5GB)
- Vídeos gerados: ~50-200MB cada

## 🎨 Exemplos de Prompts

### Básicos
```
"A cat walking on a beach"
"Robot walking in a futuristic city"
"Flowers blooming in a garden"
"Waves crashing on rocks"
```

### Avançados
```
"A golden retriever puppy playing in the snow, slow motion, cinematic lighting"
"Drone shot of a mountain landscape during sunset, 4k quality"
"Person dancing in rain, dramatic lighting, emotional mood"
"Time lapse of clouds moving over a city skyline"
```

### Com Texto (Recurso Único!)
```
"A neon sign that says 'OPEN' flickering in the night"
"Book opening to reveal text on pages"
"Person holding a sign that says 'HELLO'"
```

## 🔧 Diferenças vs LTX-2

| Característica | LTX-2 19B | Wan 2.1 14B |
|----------------|-----------|-------------|
| Parâmetros | 19B | 14B |
| Áudio | ✅ Sim | ❌ Não |
| Geração de texto | ❌ Não | ✅ Sim (chinês/inglês) |
| Text Encoder | Gemma 3 12B | T5 uMT5-XXL |
| Resoluções | 512x512 padrão | 480P, 720P otimizados |
| Duração máxima | ~10s (241 frames) | ~8s (128 frames) |
| Tamanho total | ~44GB | ~77GB |
| Idiomas suporte | Inglês | Chinês + Inglês |

## 🚀 Próximos Passos

1. ⏳ Aguardar downloads completarem
2. ✅ Criar workflow JSON para ComfyUI
3. ✅ Criar script CLI `gerar_video_wan21.py`
4. ✅ Testar geração de vídeo
5. ✅ Adicionar à interface web
6. ✅ Documentar uso

## 📚 Referências

- **Repositório oficial**: https://github.com/Wan-Video/Wan2.1
- **HuggingFace**: https://huggingface.co/Wan-AI/Wan2.1-T2V-14B
- **ComfyUI Examples**: https://comfyanonymous.github.io/ComfyUI_examples/wan/
- **Wiki**: https://comfyui-wiki.com/en/tutorial/advanced/video/wan2.1/

---

**Status**: 🔄 Em configuração - Downloads em progresso
