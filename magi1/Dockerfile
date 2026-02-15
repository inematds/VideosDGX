FROM videosdgx-base:latest AS base

# Dependências específicas do MAGI-1
COPY magi1/requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar código comum
COPY common/utils.py /app/
COPY common/model_loader.py /app/
COPY common/api_base.py /app/

# Copiar código específico do modelo
COPY magi1/model_config.py /app/
COPY magi1/app.py /app/

# Variáveis de ambiente
ENV MODEL_NAME="magi1"
ENV QUANTIZATION="fp4"
ENV MAX_MEMORY="28GB"
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
