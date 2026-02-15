FROM nvidia/cuda:12.3.0-devel-ubuntu22.04

# Evitar interações durante instalação
ENV DEBIAN_FRONTEND=noninteractive

# Dependências base do sistema
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    git \
    wget \
    curl \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Atualizar pip e setuptools
RUN python3.11 -m pip install --upgrade pip setuptools wheel

# PyTorch com suporte CUDA 12.3 (compatível com Blackwell)
RUN pip install --no-cache-dir \
    torch==2.2.0 \
    torchvision \
    torchaudio \
    --index-url https://download.pytorch.org/whl/cu121

# Dependências comuns para video LLMs
RUN pip install --no-cache-dir \
    transformers>=4.38.0 \
    accelerate>=0.26.0 \
    diffusers>=0.25.0 \
    fastapi>=0.109.0 \
    uvicorn[standard]>=0.27.0 \
    pydantic>=2.5.0 \
    python-multipart>=0.0.6 \
    pillow>=10.2.0 \
    opencv-python>=4.9.0 \
    einops>=0.7.0 \
    safetensors>=0.4.0 \
    huggingface-hub>=0.20.0 \
    sentencepiece>=0.1.99 \
    protobuf>=4.25.0 \
    psutil>=5.9.0 \
    aiofiles>=23.2.1

WORKDIR /app

# Criar diretórios para modelos e outputs
RUN mkdir -p /models /outputs

# Variáveis de ambiente padrão
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/models/.cache
ENV HF_HOME=/models/.cache
