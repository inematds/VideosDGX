# 🌐 Interface Web - LTX-2 Video Generator

**Status**: ✅ Pronta para uso!

---

## 🚀 COMO INICIAR

### Opção 1: Script Automatizado (Mais Fácil)
```bash
cd /home/nmaldaner/projetos/VideosDGX
./iniciar_interface_web.sh
```

### Opção 2: Manual
```bash
cd /home/nmaldaner/projetos/VideosDGX
python3 web_interface.py
```

---

## 🌐 ACESSAR A INTERFACE

Abra seu navegador e acesse:
```
http://localhost:7860
```

**Ou de outro computador na mesma rede:**
```
http://[IP-DO-DGX]:7860
```

Para descobrir o IP do DGX:
```bash
hostname -I | awk '{print $1}'
```

---

## 🎨 FUNCIONALIDADES

### ✨ Interface Bonita e Moderna
- Design gradiente roxo/azul
- Responsiva (funciona em celular)
- Animações suaves
- Fácil de usar

### 🎬 Geração de Vídeos
- **Formulário intuitivo** com todos os parâmetros
- **Presets rápidos**:
  - ⚡ Rápido (512x512, 2s)
  - 📺 HD (1024x576, 2s)
  - ⏱️ Longo (512x512, 5s)
  - ✨ Qualidade (1024x576, 5s)
- **Cálculo automático** de tempo estimado
- **Validação de campos**

### 📊 Gerenciamento de Jobs
- **Lista de todos os vídeos** gerados
- **Status em tempo real**:
  - 🟡 Aguardando
  - 🔵 Processando (com barra de progresso animada)
  - 🟢 Concluído
  - 🔴 Erro
- **Player de vídeo integrado** (assista direto na interface!)
- **Detalhes completos** de cada geração
- **Atualização automática** a cada 5 segundos

### 🎯 Configurações Disponíveis
- **Prompt** (descrição do vídeo)
- **Prompt negativo** (o que evitar)
- **Resolução** (largura x altura)
- **Frames** (duração do vídeo)
- **FPS** (frames por segundo)
- **CFG Scale** (fidelidade ao prompt)
- **Seed** (reproduzibilidade)

---

## 📖 COMO USAR

### 1. Iniciar o Servidor
```bash
./iniciar_interface_web.sh
```

Você verá:
```
============================================================
🎬 Iniciando Interface Web LTX-2
============================================================

🌐 A interface será aberta em:
   http://localhost:7860

⌨️  Pressione Ctrl+C para parar
============================================================
```

### 2. Abrir no Navegador
```
http://localhost:7860
```

### 3. Gerar Vídeo

**Opção A: Usar Preset**
1. Clique em um dos botões de preset (Rápido, HD, Longo, Qualidade)
2. Digite seu prompt
3. Clique em "🚀 Gerar Vídeo"

**Opção B: Customizar**
1. Digite seu prompt
2. Ajuste os parâmetros (resolução, frames, CFG, etc.)
3. Veja o tempo estimado atualizar automaticamente
4. Clique em "🚀 Gerar Vídeo"

### 4. Acompanhar Progresso
- A interface atualiza automaticamente a cada 5 segundos
- Você verá o status mudar:
  - 🟡 **Aguardando** → Job na fila
  - 🔵 **Processando** → Gerando vídeo (veja a barra animada!)
  - 🟢 **Concluído** → Vídeo pronto! (player aparece automaticamente)
  - 🔴 **Erro** → Algo deu errado (mensagem de erro aparece)

### 5. Assistir o Vídeo
- Quando o status ficar **Concluído** (🟢)
- O player de vídeo aparece automaticamente
- Clique em play para assistir!
- Use os controles do player (pause, volume, fullscreen)

---

## 🎯 EXEMPLOS DE USO

### Exemplo 1: Vídeo Rápido
1. Clique em "⚡ Rápido"
2. Digite: "Um gato caminhando na praia ao pôr do sol"
3. Clique em "🚀 Gerar Vídeo"
4. Aguarde ~77 segundos
5. Assista o resultado!

### Exemplo 2: Vídeo HD Cinematográfico
1. Clique em "✨ Qualidade"
2. Prompt: "Epic cinematic shot of a dragon flying over mountains, golden hour lighting, 4k quality"
3. Prompt Negativo: "blur, distorted, low quality"
4. Ajuste CFG para 4.5 (mais fidelidade)
5. Clique em "🚀 Gerar Vídeo"
6. Aguarde ~5 minutos
7. Assista o resultado em HD!

### Exemplo 3: Múltiplos Vídeos
- Você pode submeter **vários vídeos de uma vez**
- Eles serão processados em sequência
- A interface mostra o status de cada um
- Todos ficam salvos na lista para assistir depois

---

## 🔧 CONFIGURAÇÕES AVANÇADAS

### Ajustar Porta
Edite `web_interface.py` na última linha:
```python
uvicorn.run(app, host="0.0.0.0", port=7860)  # Mude 7860 para outra porta
```

### Acesso Remoto
Por padrão, a interface aceita conexões de qualquer IP.

**Para acessar de outro computador:**
1. Descubra o IP do DGX:
   ```bash
   hostname -I | awk '{print $1}'
   ```
   Exemplo: `192.168.1.100`

2. No outro computador, acesse:
   ```
   http://192.168.1.100:7860
   ```

### Persistência de Jobs
Os jobs são salvos em:
```
/tmp/ltx2_jobs.json
```

Se reiniciar o servidor, os jobs anteriores serão carregados automaticamente!

---

## 📊 ESTRUTURA DA API

A interface expõe uma API REST que pode ser usada programaticamente:

### Endpoints Disponíveis

#### `GET /`
- Interface HTML principal

#### `POST /api/generate`
- Gera novo vídeo
- Body (JSON):
```json
{
  "prompt": "Descrição do vídeo",
  "negative": "Prompt negativo",
  "width": 512,
  "height": 512,
  "frames": 49,
  "fps": 24,
  "cfg": 3.0,
  "seed": 42
}
```
- Retorna: `{"job_id": "abc123", "status": "pending"}`

#### `GET /api/jobs`
- Lista todos os jobs
- Retorna: Objeto JSON com todos os jobs

#### `GET /api/video/{filename}`
- Retorna arquivo de vídeo
- Usado pelo player integrado

### Exemplo de Uso via cURL
```bash
# Gerar vídeo
curl -X POST http://localhost:7860/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A cat walking on the beach",
    "width": 512,
    "height": 512,
    "frames": 49
  }'

# Listar jobs
curl http://localhost:7860/api/jobs

# Baixar vídeo
curl http://localhost:7860/api/video/web_abc123_00001_.mp4 -o video.mp4
```

---

## 🎨 DESIGN

### Cores Principais
- **Gradiente Principal**: #667eea → #764ba2 (roxo/azul)
- **Background Cards**: Branco (#ffffff)
- **Texto**: #333333
- **Status**:
  - Aguardando: #ffeaa7 (amarelo)
  - Processando: #74b9ff (azul claro)
  - Concluído: #55efc4 (verde)
  - Erro: #fab1a0 (vermelho)

### Responsividade
- **Desktop**: Layout em grid de 2-4 colunas
- **Tablet**: Layout adaptativo
- **Mobile**: Layout em coluna única

---

## ⚠️ TROUBLESHOOTING

### Porta já em uso
```
ERROR: [Errno 98] Address already in use
```
**Solução**: Mude a porta em `web_interface.py` (linha final)

### Não consigo acessar remotamente
1. Verifique firewall:
   ```bash
   sudo ufw allow 7860
   ```
2. Verifique se está usando IP correto
3. Teste localmente primeiro: `http://localhost:7860`

### Vídeos não aparecem
1. Verifique se ComfyUI está rodando:
   ```bash
   ps aux | grep comfyui
   ```
2. Verifique logs do servidor web (terminal onde rodou)
3. Verifique diretório de output:
   ```bash
   ls -lh /home/nmaldaner/projetos/VideosDGX/ComfyUI/output/
   ```

### Jobs ficam em "Processando" para sempre
1. Veja os logs do terminal
2. Verifique se o script `gerar_video_ltx2.py` está funcionando:
   ```bash
   ./gerar_video_ltx2.py "test"
   ```
3. Verifique o log do ComfyUI:
   ```bash
   tail -f comfyui_server.log
   ```

---

## 🚀 PRÓXIMAS MELHORIAS

Possíveis melhorias futuras:

- [ ] **WebSocket** para updates em tempo real (sem polling)
- [ ] **Cancelar jobs** em andamento
- [ ] **Galeria de templates** de prompts
- [ ] **Download de vídeos** com botão dedicado
- [ ] **Comparação lado-a-lado** de vídeos
- [ ] **Editor de prompts** com sugestões
- [ ] **Dashboard de estatísticas** (total gerado, tempo médio, etc.)
- [ ] **Autenticação** para múltiplos usuários
- [ ] **Temas** (claro/escuro)
- [ ] **Histórico de prompts** recentes

---

## 📞 SUPORTE

- **Documentação**: Este arquivo
- **Logs do servidor**: Terminal onde rodou `iniciar_interface_web.sh`
- **Logs do ComfyUI**: `comfyui_server.log`
- **API docs**: http://localhost:7860/docs (FastAPI auto-docs)

---

## ✅ RESUMO

**TUDO PRONTO!** A interface web está funcionando e pronta para uso!

1. **Iniciar**: `./iniciar_interface_web.sh`
2. **Acessar**: http://localhost:7860
3. **Gerar**: Preencher formulário e clicar em "Gerar Vídeo"
4. **Assistir**: Aguardar processamento e ver o player aparecer!

**Divirta-se gerando vídeos! 🎬🚀**
