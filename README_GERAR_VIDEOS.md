# 🎬 Guia Rápido: Gerar Vídeos com LTX-2

## Script Principal

Use `gerar_video_ltx2.py` para gerar vídeos facilmente:

```bash
./gerar_video_ltx2.py "Descrição do vídeo"
```

## Exemplos de Uso

### Básico (padrões: 512x512, 49 frames, 24fps)
```bash
./gerar_video_ltx2.py "Um gato caminhando na praia ao pôr do sol"
```

### Resolução HD
```bash
./gerar_video_ltx2.py "Paisagem montanhosa com névoa" \
  --width 1024 --height 576
```

### Vídeo Longo (5 segundos)
```bash
./gerar_video_ltx2.py "Ondas quebrando na praia" \
  --frames 121 --fps 24
```

### Com Prompt Negativo
```bash
./gerar_video_ltx2.py "Pessoa dançando" \
  --negative "blur, distorted, low quality"
```

### CFG Scale Alto (mais fidelidade ao prompt)
```bash
./gerar_video_ltx2.py "Robot walking in futuristic city" \
  --cfg 5.0
```

### Seed Específica (reproduzível)
```bash
./gerar_video_ltx2.py "Sunset over ocean" \
  --seed 12345
```

### Completo
```bash
./gerar_video_ltx2.py "Epic cinematic shot of a dragon flying over mountains" \
  --width 1920 \
  --height 1080 \
  --frames 121 \
  --fps 24 \
  --cfg 4.0 \
  --seed 999 \
  --output "dragon_epic" \
  --negative "blur, low quality, distorted"
```

### Salvar Workflow (para debug)
```bash
./gerar_video_ltx2.py "Test video" \
  --save-workflow /tmp/workflow.json
```

## Parâmetros Disponíveis

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `prompt` | - | Descrição do vídeo (obrigatório) |
| `--negative` | "" | Prompt negativo |
| `--width` | 512 | Largura (múltiplo de 32) |
| `--height` | 512 | Altura (múltiplo de 32) |
| `--frames` | 49 | Número de frames |
| `--fps` | 24 | Frames por segundo |
| `--cfg` | 3.0 | CFG scale (1.0-10.0) |
| `--seed` | 42 | Seed aleatória |
| `--output` | ltx2_video | Prefixo do arquivo |
| `--save-workflow` | - | Salvar JSON do workflow |

## Resoluções Recomendadas

### SD (512x512) - Rápido
```bash
--width 512 --height 512
```

### HD (1024x576) - Balanceado
```bash
--width 1024 --height 576
```

### Full HD (1920x1080) - Lento mas qualidade máxima
```bash
--width 1920 --height 1080
```

## Durações Recomendadas

| Duração | Frames (24fps) | Tempo de Geração Estimado |
|---------|----------------|---------------------------|
| 2s | 49 | ~77s |
| 3s | 73 | ~115s |
| 5s | 121 | ~190s |
| 10s | 241 | ~380s |

## Dicas de Prompts

### ✅ Bons Prompts
```
"A red sports car driving through neon-lit city streets at night, cinematic lighting, 4k"
"Close-up of a flower blooming in timelapse, soft focus, natural lighting"
"Aerial view of waves crashing on rocky coastline, golden hour, smooth camera movement"
```

### ❌ Prompts Genéricos
```
"car"  # Muito simples
"something cool"  # Muito vago
"video of stuff"  # Sem detalhes
```

### Estrutura Ideal
```
[SUBJECT] + [ACTION] + [SETTING] + [STYLE] + [QUALITY]

Exemplo:
"Astronaut floating in space, slow rotation, Earth in background, cinematic lighting, 8k quality"
```

## Monitoramento

### Acompanhar Geração em Tempo Real
```bash
tail -f /home/nmaldaner/projetos/VideosDGX/comfyui_server.log
```

### Verificar Vídeos Gerados
```bash
ls -lht /home/nmaldaner/projetos/VideosDGX/ComfyUI/output/ | head -10
```

### Interface Web
```
http://localhost:8188
```

## Troubleshooting

### Erro: "Prompt é obrigatório"
```bash
# ❌ Errado
./gerar_video_ltx2.py

# ✅ Correto
./gerar_video_ltx2.py "Meu prompt"
```

### Erro: "Largura e altura devem ser múltiplos de 32"
O script ajusta automaticamente, mas use múltiplos de 32:
- ✅ 512, 544, 576, 608, 640, 672, 704, 736, 768, 800, 832, 864, 896, 928, 960, 992, 1024
- ❌ 500, 600, 700, 1000

### Vídeo Muito Curto
Aumente `--frames`:
```bash
--frames 121  # 5 segundos @ 24fps
--frames 241  # 10 segundos @ 24fps
```

### Vídeo Não Segue o Prompt
Aumente CFG:
```bash
--cfg 5.0  # Mais fiel ao prompt
--cfg 7.0  # Muito fiel (pode reduzir qualidade)
```

### Geração Muito Lenta
Reduza resolução ou frames:
```bash
--width 512 --height 512 --frames 49  # Mais rápido
```

## Performance

### Tempo de Geração (aproximado)

**512x512, 49 frames**: ~77 segundos
**1024x576, 49 frames**: ~150 segundos
**1920x1080, 49 frames**: ~300 segundos
**512x512, 121 frames**: ~190 segundos

### Uso de Memória

**RAM**: ~32GB (modelos carregados)
**VRAM**: ~28GB durante inferência

## Exemplos Práticos

### Geração em Lote
```bash
#!/bin/bash
prompts=(
    "Ocean waves at sunset"
    "City traffic timelapse"
    "Rain falling on window"
    "Fire burning in fireplace"
)

for i in "${!prompts[@]}"; do
    ./gerar_video_ltx2.py "${prompts[$i]}" \
        --output "video_$(printf "%02d" $i)" \
        --seed $i
    sleep 80  # Aguardar geração completar
done
```

### Variações com Seeds Diferentes
```bash
for seed in {1..5}; do
    ./gerar_video_ltx2.py "Dragon flying over castle" \
        --seed $seed \
        --output "dragon_v${seed}"
    sleep 80
done
```

### Test de Resoluções
```bash
for res in "512x512" "768x768" "1024x576" "1920x1080"; do
    w=${res%x*}
    h=${res#*x}
    ./gerar_video_ltx2.py "Test video $res" \
        --width $w --height $h \
        --output "test_${res}"
    sleep 80
done
```

---

## 📞 Suporte

- **Documentação completa**: `PRIMEIRO_VIDEO_SUCESSO.md`
- **Workflow detalhado**: `submit_workflow_final.py`
- **Logs**: `/home/nmaldaner/projetos/VideosDGX/comfyui_server.log`
