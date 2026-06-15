# LTX-2.3 — Análise de upgrade (spark-922b / GB10)

> Análise feita em **08/Jun/2026**. Fonte: <https://huggingface.co/Lightricks/LTX-2.3> (model card, lastModified 13/Abr/2026).
> **Nada foi instalado/baixado** — documento de avaliação apenas.

## 1. O que já está instalado (LTX-2 19B)

Em `/home/nmaldaner/projetos/VideosDGX/`:

- Checkpoint `ComfyUI/models/checkpoints/ltx-2-19b-distilled.safetensors` — **41 GB**
- Projeções `ltx-2-19b-dev-fp4_projections_only.safetensors` — 2,7 GB
- Audio VAE `LTX2_audio_vae_bf16.safetensors` — 208 MB
- Text encoder: Gemma 3 12B
- Repo `LTX-2/` — commit `28c3c73` de **09/Fev/2026** (branch main), `ltx-core` v1.0.0
- Nó `ComfyUI/custom_nodes/ComfyUI-LTXVideo` — commit `82bd963` de **11/Fev/2026**

## 2. O que é a LTX-2.3 (nova)

Atualização da LTX-2 — modelo **22B** (vs 19B), lançada **13/Abr/2026**. Melhor qualidade
de áudio/vídeo e aderência a prompt. Gera **vídeo + áudio sincronizados** num único modelo
(DiT audio-video foundation model). Paper: arXiv:2601.03233.

### Checkpoints disponíveis no HF

| Arquivo | Tamanho | Pra quê |
|---|---|---|
| `ltx-2.3-22b-dev` | 46,15 GB | modelo cheio, treinável (bf16) |
| `ltx-2.3-22b-distilled` | 46,15 GB | distilled, 8 passos, CFG=1 (rápido) |
| `ltx-2.3-22b-distilled-1.1` | 46,15 GB | v1.1, **áudio melhorado** (recomendado) |
| `ltx-2.3-22b-distilled-lora-384` | 7,61 GB | LoRA aplicável ao modelo cheio |
| `ltx-2.3-22b-distilled-lora-384-1.1` | 7,61 GB | LoRA da v1.1 |
| `ltx-2.3-spatial-upscaler-x2-1.1` | 1,00 GB | upscale resolução x2 |
| `ltx-2.3-spatial-upscaler-x1.5-1.0` | 1,09 GB | upscale resolução x1.5 |
| `ltx-2.3-spatial-upscaler-x2-1.0` | 1,00 GB | upscale resolução x2 (1.0) |
| `ltx-2.3-temporal-upscaler-x2-1.0` | 0,26 GB | upscale FPS x2 |

Kit completo (todos) ≈ **250 GB**.

## 3. Requisitos

- **Disco:** ~46 GB por checkpoint principal. ⚠️ disco `/` em **94%** (239 GB livres) →
  cabe 1–2 checkpoints, **não** o kit inteiro. Limpar antes se for baixar vários.
- **Memória:** 22B bf16 ≈ 46 GB de pesos + encoder + VAE + ativações → estimativa
  **~55–75 GB** em uso. Cabe folgado nos **119 GB unificados** do GB10. Memória **não é gargalo**
  (o 19B de 41 GB já roda).
- **Software (model card):** Python ≥3.12, **CUDA >12.7**, PyTorch ~2.7.
  ComfyUI (nós built-in via Manager) **ou** repo PyTorch LTX-2 (`uv sync`).
  Diffusers: suporte "coming soon" (ainda não).

## 4. Compatibilidade com spark-922b — ✅ COMPATÍVEL

| Requisito | Máquina | OK |
|---|---|---|
| Python ≥3.12 | 3.12.3 | ✅ |
| CUDA >12.7 | toolkit **13.0** (V13.0.88), driver 580.95.05 | ✅ |
| GPU/memória | GB10 Blackwell, 119 GB unificada | ✅ (já roda LTX-2 19B) |
| `uv` (repo) | `/home/nmaldaner/.local/bin/uv` | ✅ |

> Obs: o doc `SETUP_COMPLETO_LTX2_DGX_SPARK.md` cita "CUDA 12.3" — **desatualizado**;
> o toolkit real é 13.0.

### Ressalvas (não bloqueiam, exigem ação antes de rodar)

1. **Nó ComfyUI desatualizado** — `ComfyUI-LTXVideo` é de 11/Fev (anterior à 2.3 de 13/Abr).
   Atualizar via **ComfyUI Manager** pra reconhecer o checkpoint 22B.
2. **Diffusers não suporta** a 2.3 ainda → hoje só **ComfyUI** ou **repo PyTorch LTX-2**.
3. **Verificar PyTorch do ComfyUI** — `torch` não está no Python do sistema (está num venv);
   o model card pede ~2.7. Conferir antes de gerar.

## 4.1. Lipsync

Sim — LTX-2/2.3 faz **lipsync nativo**, como parte da geração conjunta áudio+vídeo
(não é ferramenta separada tipo Wav2Lip).

- Arquitetura (`ltx-core/README.md`): *Bidirectional Cross-Modal Attention* com 1D temporal
  RoPE → alinhamento sub-frame mapeando pistas visuais a eventos sonoros (**lip-sync**, foley).
  Stream de vídeo 14B + stream de áudio 5B com atenção cruzada.
- Controle: parâmetro `modality_scale` (em `ltx-pipelines/.../args.py`) ajusta a
  **qualidade do lipsync** (1.0 = sem efeito).
- Negative prompt padrão penaliza "mismatched lip sync, off-sync audio, distorted voice".

Gera vídeo **e** fala já sincronizados (texto→áudio+vídeo, imagem→áudio+vídeo; modos
`audio-to-video`/`image-to-audio-video`). **Não** é lipsync pós-hoc de pegar um vídeo/foto
pronto e só trocar a boca com áudio externo arbitrário (Wav2Lip/SadTalker).

## 5. Caminho de upgrade (quando decidir — NÃO executado)

1. Liberar disco (`/` está em 94%).
2. Atualizar o nó `ComfyUI-LTXVideo` (ComfyUI Manager → Update).
3. Baixar 1 checkpoint — recomendado `ltx-2.3-22b-distilled-1.1.safetensors` (46 GB) pra
   `ComfyUI/models/checkpoints/`.
4. (Opcional) upscalers spatial/temporal pra pipeline multiscale.
5. Usar workflow LTX-2.3 do nó atualizado.
