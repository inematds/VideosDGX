FROM videosdgx-base:latest AS base

# Dependências específicas do Wan 2.1
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar código comum
COPY common/utils.py /app/
COPY common/model_loader.py /app/
COPY common/api_base.py /app/

# Copiar código específico do modelo
COPY wan21/model_config.py /app/
COPY wan21/app.py /app/

# Variáveis de ambiente
ENV MODEL_NAME="wan21"
ENV QUANTIZATION="fp8"
ENV MAX_MEMORY="35GB"
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
