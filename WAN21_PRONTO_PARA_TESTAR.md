# ✅ Wan 2.1 - Pronto Para Testar (Quando Downloads Completarem)

## 📦 Status dos Componentes

### ✅ Instalados e Prontos
1. **Modelo Principal**: `wan2.1_t2v_14B.safetensors` (65 GB) ✅
   - Localização: `ComfyUI/models/unet/`

2. **VAE**: `Wan2.1_VAE.pth` (485 MB) ✅
   - Localização: `ComfyUI/models/vae/`

3. **Custom Node**: ComfyUI-WanVideoKsampler ✅
   - Localização: `ComfyUI/custom_nodes/ComfyUI-WanVideoKsampler/`

4. **Workflow JSON**: `workflow_wan21_basic.json` ✅
   - Template pronto para uso

5. **Script CLI**: `gerar_video_wan21.py` ✅
   - Executável e pronto

### ⏳ Aguardando Download
- **T5 Encoder**: `models_t5_umt5-xxl-enc-bf16.pth` (1.3G / 11.4G = 11.4%)
  - Tempo restante: ~8-10 minutos

---

## 🚀 Como Usar (Após T5 Completar)

### Método 1: Script CLI (Recomendado)

```bash
# Vídeo básico (480P, 5s)
./gerar_video_wan21.py "um gato caminhando na praia"

# Vídeo longo (480P, 8s)
./gerar_video_wan21.py "ondas quebrando" --frames 128

# HD 720P
./gerar_video_wan21.py "paisagem montanhosa" --width 1280 --height 720

# Com mais controle criativo
./gerar_video_wan21.py "robot futurista" --cfg 5.0

# Ver todas as opções
./gerar_video_wan21.py --help
```

### Método 2: ComfyUI Interface

1. Abra: `http://localhost:8188`
2. Load workflow: `workflow_wan21_basic.json`
3. Edite o prompt
4. Queue Prompt

---

## 🎯 Parâmetros Recomendados

### Configuração Básica (Melhor para começar)
```bash
./gerar_video_wan21.py "seu prompt" \
  --width 720 \
  --height 480 \
  --frames 80 \
  --cfg 1.0
```
- Duração: ~5 segundos
- VRAM: ~8GB
- Tempo: ~3-4 minutos

### Configuração Longa
```bash
./gerar_video_wan21.py "seu prompt" \
  --width 720 \
  --height 480 \
  --frames 128 \
  --cfg 1.0
```
- Duração: ~8 segundos
- VRAM: ~12GB
- Tempo: ~5-6 minutos

### Configuração HD
```bash
./gerar_video_wan21.py "seu prompt" \
  --width 1280 \
  --height 720 \
  --frames 80 \
  --cfg 1.0
```
- Duração: ~5 segundos (HD)
- VRAM: ~16GB
- Tempo: ~5-7 minutos

---

## 💡 Exemplos de Prompts

### Básicos
```bash
./gerar_video_wan21.py "A cat walking on a beach"
./gerar_video_wan21.py "Robot walking in a futuristic city"
./gerar_video_wan21.py "Flowers blooming in a garden"
./gerar_video_wan21.py "Waves crashing on rocks"
```

### Avançados
```bash
./gerar_video_wan21.py "A golden retriever puppy playing in the snow, slow motion, cinematic lighting"

./gerar_video_wan21.py "Drone shot of a mountain landscape during sunset, 4k quality"

./gerar_video_wan21.py "Person dancing in rain, dramatic lighting, emotional mood"

./gerar_video_wan21.py "Time lapse of clouds moving over a city skyline"
```

### Com Texto (Recurso Único do Wan 2.1!)
```bash
./gerar_video_wan21.py "A neon sign that says 'OPEN' flickering in the night"

./gerar_video_wan21.py "Book opening to reveal text on pages"

./gerar_video_wan21.py "Person holding a sign that says 'HELLO'"
```

### Bilíngue (Chinês + Inglês)
```bash
./gerar_video_wan21.py "中国古代城市街景 (Ancient Chinese city street)"

./gerar_video_wan21.py "熊猫在竹林中玩耍 (Panda playing in bamboo forest)"
```

---

## 📊 Comparação LTX-2 vs Wan 2.1

| Característica | LTX-2 19B | Wan 2.1 14B |
|----------------|-----------|-------------|
| **Áudio** | ✅ Sim | ❌ Não |
| **Geração de texto** | ❌ Não | ✅ Sim |
| **Resolução padrão** | 512x512 | 480P, 720P |
| **Duração máxima** | ~10s | ~8s |
| **Idiomas** | Inglês | Chinês + Inglês |
| **Tamanho total** | ~44GB | ~77GB |
| **VRAM mínima** | 8GB | 8GB (480P, 5s) |

---

## 🔧 Troubleshooting

### T5 Encoder não carrega
```bash
# Verificar se arquivo está completo
ls -lh ComfyUI/models/text_encoders/models_t5_umt5-xxl-enc-bf16.pth
# Deve mostrar: ~10.9G

# Verificar log
tail -50 comfyui_server.log
```

### Out of Memory (OOM)
**Soluções:**
1. Reduzir frames: `--frames 80` → `--frames 60`
2. Reduzir resolução: `720x480` → `640x360`
3. Usar CFG menor: `--cfg 1.0` (ao invés de 5-7)

### Vídeo em slow-motion
**Causa:** Modelo gera em 16fps, mas salvamos em 24fps por padrão

**Solução:** Ajustar FPS de saída:
```bash
./gerar_video_wan21.py "seu prompt" --fps 16  # Velocidade natural
./gerar_video_wan21.py "seu prompt" --fps 24  # Mais suave (padrão)
```

---

## 📂 Onde os Vídeos São Salvos

```bash
/home/nmaldaner/projetos/VideosDGX/ComfyUI/output/

# Listar vídeos Wan 2.1
ls -lht ComfyUI/output/wan21_video_*.mp4

# Ver último gerado
ls -t ComfyUI/output/wan21_video_*.mp4 | head -1
```

---

## 🎬 Primeiro Teste Recomendado

Quando o T5 completar o download, execute:

```bash
# Teste básico (rápido, ~3 minutos)
./gerar_video_wan21.py "a cat walking on a beach at sunset"

# Aguardar ~3-4 minutos

# Verificar resultado
ls -lht ComfyUI/output/ | head -3
```

Se funcionar: ✅ **Wan 2.1 está operacional!**

---

## 📋 Checklist de Verificação

Antes de testar, confirmar:

- [ ] T5 Encoder completou download (11.4 GB)
- [ ] ComfyUI está rodando (`curl http://localhost:8188/system_stats`)
- [ ] Todos os modelos no lugar certo:
  - [ ] `ComfyUI/models/unet/wan2.1_t2v_14B.safetensors`
  - [ ] `ComfyUI/models/text_encoders/models_t5_umt5-xxl-enc-bf16.pth`
  - [ ] `ComfyUI/models/vae/Wan2.1_VAE.pth`
- [ ] Script tem permissão de execução (`ls -l gerar_video_wan21.py`)

---

**Status**: ⏳ Aguardando T5 completar (~8-10 minutos)

Quando concluir, você terá **2 modelos funcionando**:
- ✅ LTX-2 19B (com áudio)
- ✅ Wan 2.1 14B (com geração de texto)

🚀 **Próximo passo**: Testar geração + Adicionar Wan 2.1 à interface web v3!
