# 🚀 GUIA RÁPIDO - LTX-2 Video Generator

## ⚡ INÍCIO RÁPIDO (30 SEGUNDOS)

```bash
cd /home/nmaldaner/projetos/VideosDGX
./iniciar_interface_web_v3.sh
```

Abra: **http://localhost:7860**

## 🎬 GERAR SEU PRIMEIRO VÍDEO

1. Digite o prompt: **"um cachorro correndo"**
2. Clique **"🚀 Gerar Vídeo"**
3. Aguarde **~2 minutos**
4. Assista o vídeo na própria página!

## 📋 PRESETS DISPONÍVEIS

| Preset | Resolução | Duração | Tempo |
|--------|-----------|---------|-------|
| ⚡ Rápido | 512x512 | 2s | ~2 min |
| 📺 HD | 1024x576 | 2s | ~3 min |
| ⏱️ Longo | 512x512 | 5s | ~5 min |

## 💡 EXEMPLOS DE PROMPTS

```
"um gato pulando pela janela"
"paisagem montanhosa ao pôr do sol"
"ondas quebrando na praia"
"robot futurista andando pela cidade"
"pássaros voando no céu azul"
"flores coloridas balançando ao vento"
```

## 🔧 COMANDOS ÚTEIS

```bash
# Iniciar interface v3
./iniciar_interface_web_v3.sh

# Reiniciar ComfyUI
./reiniciar_comfyui.sh

# Ver vídeos gerados
ls -lht ComfyUI/output/*.mp4 | head -5

# Gerar via CLI (alternativa)
./gerar_video_ltx2.py "seu prompt" --frames 49
```

## ❓ PROBLEMAS COMUNS

### Botão "Gerar" está desabilitado
➜ Já há um vídeo sendo processado. Aguarde terminar.

### Vídeo demora muito
➜ Normal! Leva 2-5 minutos dependendo dos parâmetros.

### Interface não abre
```bash
kill -9 $(lsof -t -i:7860)
./iniciar_interface_web_v3.sh
```

## 📂 ONDE ESTÃO OS VÍDEOS?

```bash
/home/nmaldaner/projetos/VideosDGX/ComfyUI/output/
```

## ⚠️ IMPORTANTE

- ✅ **Um vídeo por vez**: Sistema previne múltiplos simultâneos
- ✅ **Auto-restart**: ComfyUI reinicia automaticamente entre vídeos
- ✅ **Timeout**: 10 minutos máximo por vídeo
- ✅ **100% confiável**: Nunca mais CUDA error!

## 🎯 VERSÕES DISPONÍVEIS

1. **v3 (RECOMENDADO)**: Interface web com auto-restart
2. **CLI**: Linha de comando (precisa reiniciar manualmente)

## 📞 AJUDA COMPLETA

- **Documentação completa**: `SOLUCAO_DEFINITIVA_V3.md`
- **Solução temporária CLI**: `SOLUCAO_TEMPORARIA.md`

---

**🎬 Bora gerar vídeos!**

Acesse: http://localhost:7860
