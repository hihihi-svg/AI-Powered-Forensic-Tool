from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router
import app.services.sketch_service as ss
print(f"CRITICAL DEBUG: sketch_service loaded from: {ss.__file__}")

app = FastAPI(title="Forensic Sketch Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
import os

# ... (rest of imports)

app.include_router(router, prefix="/api")

# Mount images directory
# Ensure the path is correct relative to execution context (backend/)
image_dir = os.path.join(os.getcwd(), "dataset", "mini-CelebA-HQ-img")
if os.path.exists(image_dir):
    app.mount("/api/images", StaticFiles(directory=image_dir), name="images")
    print(f"DEBUG: Mounted images from {image_dir}")
else:
    print(f"WARNING: Image directory not found: {image_dir}")

@app.get("/")
def read_root():
    return {"message": "Forensic API Active"}
