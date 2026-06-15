#!/bin/bash
# Interface Web v4.1 - Multi-Model + Image-to-Video
# Modelos T2V: Wan 2.2 14B MoE, Wan 2.2 5B, LTX-2 19B
# Modelos I2V: Wan 2.2 5B (WanImageToVideo), LTX-2 19B (LTXVImgToVideoConditionOnly)
# Acesso: http://localhost:7861

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ativar venv
source comfyui-env/bin/activate

# Verificar dependências
python3 -c "import fastapi, uvicorn, aiofiles" 2>/dev/null || {
    echo "Instalando dependências..."
    pip install fastapi uvicorn aiofiles python-multipart -q
}

python3 -c "import websocket" 2>/dev/null || {
    echo "Instalando websocket-client para progresso real..."
    pip install websocket-client -q
}

# Verificar se ComfyUI está rodando
if ! curl -s http://127.0.0.1:8188/system_stats > /dev/null 2>&1; then
    echo "⚠️  ComfyUI não está rodando. Iniciando..."
    nohup python3 ComfyUI/main.py --listen 0.0.0.0 --highvram > comfyui_server.log 2>&1 &
    sleep 5
    echo "✅ ComfyUI iniciado (porta 8188)"
fi

echo ""
echo "🎬 Interface Web v4.1 - T2V + Image-to-Video"
echo "   T2V:  Wan 2.2 14B MoE | Wan 2.2 5B | LTX-2 19B"
echo "   I2V:  Wan 2.2 5B | LTX-2 19B"
echo "   Acesso: http://localhost:7861"
echo ""
echo "Pressione Ctrl+C para parar"
echo ""

python3 web_interface_v4_1.py
