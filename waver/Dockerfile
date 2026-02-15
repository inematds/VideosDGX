FROM videosdgx-base:latest AS base

# Dependências específicas do Waver 1.0
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar código comum
COPY common/utils.py /app/
COPY common/model_loader.py /app/
COPY common/api_base.py /app/

# Copiar código específico do modelo
COPY waver/model_config.py /app/
COPY waver/app.py /app/

# Variáveis de ambiente
ENV MODEL_NAME="waver"
ENV QUANTIZATION="fp8"
ENV MAX_MEMORY="20GB"
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
