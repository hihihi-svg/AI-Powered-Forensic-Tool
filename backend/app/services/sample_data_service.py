import os
import requests
import asyncio
import logging
from app.utils.embedding import generate_embeddings_logic 

# Configuration
DATASET_DIR = "dataset/mini-CelebAMask-HQ-img"
SAMPLE_COUNT = 15

seed_status = {
    "status": "idle",
    "progress": 0,
    "total": SAMPLE_COUNT,
    "message": ""
}

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

async def download_samples_task():
    global seed_status
    seed_status["status"] = "running"
    seed_status["progress"] = 0
    seed_status["message"] = "Starting download..."
    
    try:
        ensure_dir(DATASET_DIR)
        
        # 1. Download Images
        for i in range(SAMPLE_COUNT):
            # Using picsum with different seeds to get faces/people
            # 'seed' ensures determinism, but picsum is random. 
            # We'll stick to a list of reliable IDs if possible, or just random.
            url = f"https://picsum.photos/seed/{i+555}/512/512" 
            
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    filename = f"demo_{i+1:03d}.jpg"
                    filepath = os.path.join(DATASET_DIR, filename)
                    with open(filepath, "wb") as f:
                        f.write(response.content)
            except Exception as e:
                logging.error(f"Error downloading {i}: {e}")
            
            seed_status["progress"] = int((i + 1) / SAMPLE_COUNT * 50) # First 50% is download
            seed_status["message"] = f"Downloaded {i+1}/{SAMPLE_COUNT} images..."
            await asyncio.sleep(0.1)

        # 2. Index Images (The remaining 50%)
        seed_status["message"] = "Processing AI embeddings (this takes a moment)..."
        
        # Run the synchronous embedding logic in a thread pool to avoid blocking asyncio loop
        loop = asyncio.get_event_loop()
        count = await loop.run_in_executor(None, generate_embeddings_logic)
        
        seed_status["progress"] = 100
        seed_status["status"] = "completed"
        seed_status["message"] = f"Successfully loaded {count} demo records!"

    except Exception as e:
        seed_status["status"] = "failed"
        seed_status["message"] = f"Error: {str(e)}"
        logging.error(f"Seed failed: {e}")
