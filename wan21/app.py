"""
API FastAPI para Wan 2.1 Video Generation
"""
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from model_config import load_wan21_model, generate_video_wan21
from model_loader import ModelLoader
from api_base import VideoModelAPI

MODEL_NAME = os.getenv("MODEL_NAME", "wan21")
MODEL_PATH = os.getenv("MODEL_PATH", "/models/wan21")
QUANTIZATION = os.getenv("QUANTIZATION", "fp8")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/outputs")
AUTO_UNLOAD_MINUTES = int(os.getenv("AUTO_UNLOAD_MINUTES", "0"))

model_loader = ModelLoader(
    model_name=MODEL_NAME,
    model_path=MODEL_PATH,
    load_function=load_wan21_model,
    quantization=QUANTIZATION,
    auto_unload_minutes=AUTO_UNLOAD_MINUTES if AUTO_UNLOAD_MINUTES > 0 else None
)

api = VideoModelAPI(
    model_name=MODEL_NAME,
    model_loader=model_loader,
    generate_function=generate_video_wan21,
    output_dir=OUTPUT_DIR
)

app = api.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
