# Build base image primeiro
FROM videosdgx-base:latest AS base

# Dependências específicas do LTX-2
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

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
