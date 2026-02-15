"""
API FastAPI para LTX-2 Video + Audio Generation
"""
import os
from pathlib import Path
import sys

# Adicionar diretório atual ao path
sys.path.insert(0, str(Path(__file__).parent))

from model_config import load_ltx2_model, generate_video_ltx2
from model_loader import ModelLoader
from api_base import VideoModelAPI

# Configurações
MODEL_NAME = os.getenv("MODEL_NAME", "ltx2")
MODEL_PATH = os.getenv("MODEL_PATH", "/models/ltx2")
QUANTIZATION = os.getenv("QUANTIZATION", "fp4")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/outputs")
AUTO_UNLOAD_MINUTES = int(os.getenv("AUTO_UNLOAD_MINUTES", "0"))

# Criar ModelLoader
model_loader = ModelLoader(
    model_name=MODEL_NAME,
    model_path=MODEL_PATH,
    load_function=load_ltx2_model,
    quantization=QUANTIZATION,
    auto_unload_minutes=AUTO_UNLOAD_MINUTES if AUTO_UNLOAD_MINUTES > 0 else None
)

# Criar API
api = VideoModelAPI(
    model_name=MODEL_NAME,
    model_loader=model_loader,
    generate_function=generate_video_ltx2,
    output_dir=OUTPUT_DIR
)

# Exportar app FastAPI
app = api.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
