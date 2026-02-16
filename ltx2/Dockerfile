# Build base image primeiro
FROM videosdgx-base:latest AS base

# Dependências específicas do LTX-2
COPY ltx2/requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Instalar diffusers dev version com suporte LTX-2
RUN pip install --no-cache-dir git+https://github.com/huggingface/diffusers.git

# Copiar e aplicar patch no pipeline LTX para video-only generation
COPY ltx2/patch_pipeline.py /tmp/
RUN python3 /tmp/patch_pipeline.py

# Copiar código comum
COPY common/utils.py /app/
COPY common/model_loader.py /app/
COPY common/api_base.py /app/

# Copiar código específico do modelo
COPY ltx2/model_config.py /app/
COPY ltx2/app.py /app/

# Variáveis de ambiente
ENV MODEL_NAME="ltx2"
ENV QUANTIZATION="fp4"
ENV MAX_MEMORY="32GB"
ENV PORT=8000

# Expor porta
EXPOSE 8000

# Comando de inicialização
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
