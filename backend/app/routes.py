from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Body, Header
from pydantic import BaseModel
from typing import Optional
from .services.qdrant_service import QdrantService
from .services.sketch_service import SketchService
from .services.text_to_image_service import TextToImageService
from .services.deepfake_detection_service import DeepfakeDetectionService
from .services.session_service import SessionService
import random
import base64
import os
from pathlib import Path
from io import BytesIO
import asyncio
import json
import shutil
from datetime import datetime
from PIL import Image, ImageEnhance, ImageOps
import numpy as np

DELETED_LOG_FILE = "deleted_suspects.json"
IMAGE_DIR = os.path.join(os.getcwd(), "dataset", "mini-CelebA-HQ-img")

router = APIRouter()
qdrant_svc = QdrantService()  # Re-enabled for vector search
# Initialize SketchService (loads models)
sketch_svc = SketchService()
# Initialize TextToImageService
text_to_image_svc = TextToImageService()
# Initialize DeepfakeDetectionService  
deepfake_svc = DeepfakeDetectionService()
# Initialize SessionService
session_svc = SessionService()

DATASET_INDEX = None
print("DEBUG: *** SERVER MATCH-DISPLAY-FIX VERSION LOADED ***", flush=True)

class SpeechInput(BaseModel):
    text: str

class IngestRequest(BaseModel):
    image_id: Optional[str]
    context: str

class SearchRequest(BaseModel):
    vector: Optional[list[float]] = None

@router.post("/speech-to-sketch")
async def generate_sketch(file: UploadFile = File(...)):
    """
    Receives audio file -> Transcribes -> Generates Sketch
    """
    print(f"DEBUG: Received speech-to-sketch request. File: {file.filename}")
    try:
        audio_bytes = await file.read()
        print(f"DEBUG: Read {len(audio_bytes)} bytes")
        
        text = sketch_svc.process_audio(audio_bytes)
        print(f"DEBUG: Transcribed text: {text}")
        
        # Determine num images (Optimized to 1 for CPU speed)
        images = sketch_svc.generate_sketch(text, num_images=1)
        
        # Convert images to base64
        encoded_images = []
        search_results = []
        
        # Perform Search using the first generated sketch
        if images:
            primary_sketch = images[0]
            
            # Save temp file for embedding
            temp_sketch_path = f"temp_sketch_{random.randint(0,9999)}.png"
            primary_sketch.save(temp_sketch_path)
            
            try:
                # 1. Get Embedding
                query_embedding = get_image_embedding(temp_sketch_path)
                
                # 2. Search in Dataset (Copy of logic from search_suspect)
                if query_embedding is not None and DATASET_INDEX:
                    scores = []
                    for item in DATASET_INDEX:
                        target_emb = item["embedding"]
                        if len(target_emb) != len(query_embedding): continue
                        
                        norm_q = np.linalg.norm(query_embedding)
                        norm_t = np.linalg.norm(target_emb)
                        
                        if norm_q > 0 and norm_t > 0:
                            sim = np.dot(query_embedding, target_emb) / (norm_q * norm_t)
                            scores.append((sim, item))
                    
                    scores.sort(key=lambda x: x[0], reverse=True)
                    top_matches = scores[:3] # Top 3
                    
                    for score, item in top_matches:
                        # Load Match Image
                        with open(item["path"], "rb") as img_f:
                             b64 = base64.b64encode(img_f.read()).decode()
                        
                        # Generate Metadata
                        import hashlib
                        seed_str = Path(item["filename"]).stem.split("_aug_")[0]
                        seed_int = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
                        random.seed(seed_int)
                        
                        days_offset = random.randint(0, 1000)
                        from datetime import datetime, timedelta
                        random_date = (datetime.now() - timedelta(days=days_offset)).strftime("%Y-%m-%dT%H:%M:%S")
                        crime_list = ["Fraud", "Theft", "Cybercrime", "Assault", "Vandalism", "Burglary"]
                        selected_crime = random.choice(crime_list)
                        random.seed()
                        
                        search_results.append({
                            "id": item["id"],
                            "score": float(score),
                            "payload": {
                                "filename": item["filename"],
                                "crime_type": selected_crime,
                                "timestamp": random_date
                            },
                            "image": f"data:image/jpeg;base64,{b64}"
                        })

            except Exception as e:
                print(f"Sketch Search Error: {e}")
            finally:
                if os.path.exists(temp_sketch_path):
                    os.remove(temp_sketch_path)

        for img in images:
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            encoded_images.append(f"data:image/png;base64,{img_str}")
            
        return {
            "transcription": text,
            "sketches": encoded_images,
            "matches": search_results
        }
    except Exception as e:
        print(f"Error: {e}")
        # raise HTTPException(status_code=500, detail=str(e)) # Don't crash, return partial
        return {"transcription": f"Error processing audio: {str(e)}", "sketches": [], "matches": []}

@router.post("/start-generation")
async def start_generation(request: dict = Body(...)):
    """Start sketch generation and return job_id"""
    try:
        prompt = request.get("prompt", "")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
            
        print(f"Starting job for prompt: {prompt[:50]}...")
        
        # Start background job
        job_id = await text_to_image_svc.start_generation(prompt)
        
        return {"job_id": job_id, "status": "processing"}
        
    except Exception as e:
        print(f"Start generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check-status/{job_id}")
async def check_status(job_id: str):
    """Check status of generation job"""
    try:
        job = text_to_image_svc.get_job_status(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job["status"] == "completed":
            # Image generation done, now process for search
            output_path = job["output_path"]
            
            # Read generated image
            with open(output_path, "rb") as f:
                image_bytes = f.read()
            
            # Convert to base64
            img_b64 = base64.b64encode(image_bytes).decode()
            sketch_data_url = f"data:image/png;base64,{img_b64}"
            
            # Perform search (this is fast)
            search_results = []
            try:
                sketch_embedding = get_image_embedding(output_path)
                
                global DATASET_INDEX
                if DATASET_INDEX is None:
                    print("Loading index from file...", flush=True)
                    import pickle
                    try:
                        # Path relative to where uvicorn is running (backend/)
                        idx_path = "data/face_recognition_system.pkl"
                        if not os.path.exists(idx_path):
                             # Try absolute path fallback
                             idx_path = os.path.join(os.getcwd(), "data", "face_recognition_system.pkl")
                        
                        if os.path.exists(idx_path):
                            with open(idx_path, "rb") as f:
                                data = pickle.load(f)
                                DATASET_INDEX = data.get('index', []) if isinstance(data, dict) else data
                                print(f"Index loaded. Size: {len(DATASET_INDEX)}", flush=True)
                        else:
                            print(f"ERROR: Index file not found at {idx_path}", flush=True)
                    except Exception as e:
                        print(f"Failed to load index: {e}", flush=True)

                if DATASET_INDEX is None:
                    print("ERROR: Index not loaded (Still None)", flush=True)
                else:
                    if sketch_embedding is not None and DATASET_INDEX:
                        scores = []
                        for item in DATASET_INDEX:
                            target_emb = item["embedding"]
                            if len(target_emb) != len(sketch_embedding):
                                continue
                            
                            norm_q = np.linalg.norm(sketch_embedding)
                            norm_t = np.linalg.norm(target_emb)
                            
                            if norm_q > 0 and norm_t > 0:
                                sim = np.dot(sketch_embedding, target_emb) / (norm_q * norm_t)
                                scores.append((sim, item))
                        
                        scores.sort(key=lambda x: x[0], reverse=True)
                        top_matches = scores[:3]
                        
                        for score, item in top_matches:
                            with open(item["path"], "rb") as img_f:
                                b64_match = base64.b64encode(img_f.read()).decode()
                            
                            import hashlib
                            seed_str = Path(item["filename"]).stem.split("_aug_")[0]
                            seed_int = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
                            random.seed(seed_int)
                            
                            from datetime import datetime, timedelta
                            days_offset = random.randint(0, 1000)
                            random_date = (datetime.now() - timedelta(days=days_offset)).strftime("%Y-%m-%dT%H:%M:%S")
                            crime_list = ["Fraud", "Theft", "Cybercrime", "Assault", "Vandalism", "Burglary"]
                            selected_crime = random.choice(crime_list)
                            random.seed()
                            
                            search_results.append({
                                "id": item["id"],
                                "score": float(score),
                                "payload": {
                                    "filename": item["filename"],
                                    "crime_type": selected_crime,
                                    "timestamp": random_date
                                },
                                "image": f"data:image/jpeg;base64,{b64_match}"
                            })
            except Exception as e:
                print(f"Search error: {e}")

            return {
                "status": "completed",
                "progress": 100,
                "sketch": sketch_data_url,
                "matches": search_results
            }
        
        elif job["status"] == "failed":
            return {"status": "failed", "error": job.get("error")}
        
        else:
            return {"status": "processing", "progress": job.get("progress", 0)}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Check status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Legacy endpoint redirect
@router.post("/api/text-to-image")
async def text_to_image(request: dict = Body(...)):
    raise HTTPException(status_code=400, detail="Please update frontend to use /api/start-generation")

@router.post("/detect-deepfake")
async def detect_deepfake(file: UploadFile = File(...)):
    """
    Detect if an uploaded image is AI-generated (deepfake) or real
    Uses Hugging Face model: dima806/human_faces_ai_vs_real_image_detection
    """
    try:
        # Read image bytes
        image_bytes = await file.read()
        
        print(f"Received image for deepfake detection: {file.filename}")
        
        # Detect deepfake
        result = deepfake_svc.detect_deepfake(image_bytes)
        
        # Return result
        return {
            "is_real": result.get("is_real"),
            "is_fake": result.get("is_fake"),
            "label": result.get("label"),
            "confidence": result.get("confidence"),
            "class": result.get("label"),  # For compatibility with frontend
            "all_predictions": result.get("all_predictions", [])
        }
        
    except Exception as e:
        print(f"Deepfake detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-and-search")
async def verify_and_search(file: UploadFile = File(...)):
    """
    Verify uploaded image (real/fake) AND search for matches in database
    """
    try:
        # Read image bytes
        image_bytes = await file.read()
        print(f"Verify & Search for: {file.filename}", flush=True)
        
        # Save temp file
        temp_path = f"temp_verify_{random.randint(0,9999)}.jpg"
        with open(temp_path, "wb") as f:
            f.write(image_bytes)
        
        try:
            # 1. Deepfake Detection
            verification_result = deepfake_svc.detect_deepfake(image_bytes)
            
            # 2. Get Embedding & Search (Using Pickle Index like Module B)
            search_results = []
            
            # Embed Query
            query_embedding = get_image_embedding(temp_path)
            
            # Lazy Load Index if needed
            global DATASET_INDEX
            if DATASET_INDEX is None:
                print("Loading index from file...", flush=True)
                import pickle
                try:
                    idx_path = "dataset_index.pkl"
                    if not os.path.exists(idx_path):
                            idx_path = os.path.join(os.getcwd(), "dataset_index.pkl")
                    
                    if os.path.exists(idx_path):
                        with open(idx_path, "rb") as f:
                            data = pickle.load(f)
                            DATASET_INDEX = data.get('index', []) if isinstance(data, dict) else data
                            print(f"Index loaded. Size: {len(DATASET_INDEX)}", flush=True)
                    else:
                        print(f"ERROR: Index file not found at {idx_path}", flush=True)
                except Exception as e:
                    print(f"Failed to load index: {e}", flush=True)

            if query_embedding is not None and DATASET_INDEX:
                print(f"DEBUG: Searching index of size {len(DATASET_INDEX)}", flush=True)
                scores = []
                for item in DATASET_INDEX:
                    target_emb = item["embedding"]
                    if len(target_emb) != len(query_embedding): continue
                    
                    norm_q = np.linalg.norm(query_embedding)
                    norm_t = np.linalg.norm(target_emb)
                    
                    if norm_q > 0 and norm_t > 0:
                        sim = np.dot(query_embedding, target_emb) / (norm_q * norm_t)
                        scores.append((sim, item))
                
                scores.sort(key=lambda x: x[0], reverse=True)
                top_matches = scores[:10]
                
                for score, item in top_matches:
                    b64 = ""
                    try:
                        with open(item["path"], "rb") as img_f:
                                b64 = base64.b64encode(img_f.read()).decode()
                    except:
                        pass
                    
                    # Metadata generation (Deterministic)
                    import hashlib
                    seed_str = Path(item["filename"]).stem.split("_aug_")[0]
                    seed_int = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
                    random.seed(seed_int)
                    
                    days_offset = random.randint(0, 1000)
                    from datetime import datetime, timedelta
                    random_date = (datetime.now() - timedelta(days=days_offset)).strftime("%Y-%m-%dT%H:%M:%S")
                    crime_list = ["Fraud", "Theft", "Cybercrime", "Assault", "Vandalism", "Burglary"]
                    selected_crime = random.choice(crime_list)
                    random.seed()
                    
                    search_results.append({
                        "id": item["id"],
                        "score": float(score),
                        "payload": {
                            "filename": item["filename"],
                            "crime_type": selected_crime,
                            "timestamp": random_date
                        },
                        "image": f"data:image/jpeg;base64,{b64}" if b64 else None
                    })
            else:
                 print(f"ERROR: Search failed. Query Embedding: {query_embedding is not None}, Index Loaded: {DATASET_INDEX is not None}", flush=True)
        
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        return {
            "verification": {
                "is_real": verification_result.get("is_real"),
                "confidence": verification_result.get("confidence"),
                "label": verification_result.get("label")
            },
            "matches": search_results
        }
        
    except Exception as e:
        print(f"Deepfake detection error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...)):
    """
    Convert speech audio to text using Google Speech Recognition
    """
    try:
        import speech_recognition as sr
        
        # Read audio from uploaded file
        audio_data = await audio.read()
        
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Save temporarily to process
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name
        
        try:
            # Convert audio for speech recognition
            from pydub import AudioSegment
            audio_segment = AudioSegment.from_file(tmp_path)
            wav_path = tmp_path.replace('.webm', '.wav')
            audio_segment.export(wav_path, format="wav")
            
            # Perform speech recognition
            with sr.AudioFile(wav_path) as source:
                audio_recorded = recognizer.record(source)
            
            text = recognizer.recognize_google(audio_recorded)
            
            # Cleanup (Ignoring errors if file is locked)
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                if os.path.exists(wav_path):
                    os.unlink(wav_path)
            except Exception as e:
                print(f"Warning: Could not delete temp files: {e}")
            
            print(f"Transcribed: {text}")
            return {"text": text, "success": True}
            
        finally:
            # Cleanup in case of error (if not already deleted)
            try:
                if 'tmp_path' in locals() and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                if 'wav_path' in locals() and os.path.exists(wav_path):
                    os.unlink(wav_path)
            except Exception:
                pass
        
    except sr.UnknownValueError:
        raise HTTPException(status_code=400, detail="Could not understand audio")
    except sr.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Speech recognition error: {e}")
    except Exception as e:
        print(f"Speech-to-text error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Embedding Strategy: Facenet-PyTorch (Lazy Load)
FACENET_MODELS = None

def get_facenet_models():
    global FACENET_MODELS
    if FACENET_MODELS:
        return FACENET_MODELS
        
    print("DEBUG: Lazy Loading Facenet Models...")
    try:
        from facenet_pytorch import MTCNN, InceptionResnetV1
        import torch
        
        # Initialize models (CPU is fine for 1 image)
        mtcnn = MTCNN(image_size=160, margin=0, keep_all=False)
        resnet = InceptionResnetV1(pretrained='vggface2').eval()
        
        FACENET_MODELS = (mtcnn, resnet, torch)  # Include torch module
        print("DEBUG: Facenet-PyTorch loaded successfully.")
        return FACENET_MODELS
    except ImportError:
        print("WARNING: Facenet-PyTorch not installed. Using Color Histogram fallback.")
        return None
    except Exception as e:
        print(f"WARNING: Facenet Load Failed: {e}")
        return None


import numpy as np
from PIL import Image

# Global storage for embeddings
DATASET_INDEX = None

def get_image_embedding(file_path):
    """
    Generates an embedding using Facenet-PyTorch.
    STRICT MODE: Returns None if no face found. No Histogram fallback.
    """
    models = get_facenet_models()
    
    if models:
        mtcnn, resnet, torch = models  # Unpack torch module
        try:
            img = Image.open(file_path).convert('RGB')
            # Detect face and crop
            img_cropped = mtcnn(img)
            
            if img_cropped is not None:
                # Calculate embedding
                with torch.no_grad():
                    img_embedding = resnet(img_cropped.unsqueeze(0))
                # Normalize!
                emb = img_embedding[0].numpy()
                norm = np.linalg.norm(emb)
                if norm > 0:
                    emb = emb / norm
                return emb
            else:
                 print(f"WARNING: No face detected in {file_path}")
                 return None
        except Exception as e:
            print(f"Facenet failed for {file_path}: {e}")
            return None
            
    return None

def load_or_generate_index(dataset_path: Path):
    global DATASET_INDEX
    
    pickle_path = Path("dataset_index.pkl")
    import pickle
    
    # Load existing index if available
    if pickle_path.exists() and not DATASET_INDEX:
        print(f"DEBUG: Loading existing index from {pickle_path}...")
        try:
            with open(pickle_path, "rb") as f:
                DATASET_INDEX = pickle.load(f)
            print(f"DEBUG: Loaded {len(DATASET_INDEX)} vectors from disk.")
        except Exception as e:
            print(f"Error loading pickle: {e}")
            DATASET_INDEX = []

    print(f"DEBUG: Indexing dataset at {dataset_path}")
    if not dataset_path.exists():
        return

    image_files = list(dataset_path.glob("*.jpg")) + list(dataset_path.glob("*.png"))
    
    # Identify missing files (Incremental Indexing)
    existing_filenames = set(item["filename"] for item in DATASET_INDEX)
    subset = [f for f in image_files if f.name not in existing_filenames]
    
    if not subset:
         # print("DEBUG: Index is up to date.")
         return

    print(f"DEBUG: Found {len(subset)} new images to index (Total: {len(image_files)}).")
    
    # Temporary Limit to unblock server
    if len(subset) > 50:
         print("DEBUG: Limiting indexing to first 50 new images for speed.")
         subset = subset[:50]
    
    for i, file_path in enumerate(subset):
        emb = get_image_embedding(file_path)
        if emb is not None:
             # Find correct new ID
             new_id = len(DATASET_INDEX) + 1
             DATASET_INDEX.append({
                 "id": new_id,
                 "filename": file_path.name,
                 "embedding": emb,
                 "path": str(file_path)
             })
        else:
             print(f"SKIPPING {file_path.name} - Could not generate face embedding.")
        
        # Periodic Save & Log (Every 10 images)
        if (i + 1) % 10 == 0:
            print(f"DEBUG: Indexed {i + 1}/{len(subset)} images...", flush=True)
            try:
                with open(pickle_path, "wb") as f:
                    pickle.dump(DATASET_INDEX, f)
            except Exception as e:
                print(f"Error saving checkpoint: {e}")

    print(f"DEBUG: Indexing complete. {len(DATASET_INDEX)} vectors stored.")
    # Final Save
    try:
        with open(pickle_path, "wb") as f:
            pickle.dump(DATASET_INDEX, f)
        print(f"DEBUG: Saved final index to {pickle_path}")
    except Exception as e:
        print(f"Error saving pickle: {e}")

@router.post("/search")
async def search_suspect(
    file: Optional[UploadFile] = File(None),
    top_k: int = Form(3)
):
    # Initialize index if empty
    path_strategies = [
        Path.cwd() / "dataset" / "mini-CelebA-HQ-img",
        Path(__file__).parent.parent / "dataset" / "mini-CelebA-HQ-img",
        Path("dataset/mini-CelebA-HQ-img").resolve(),
    ]
    dataset_dir = None
    for p in path_strategies:
        if p.exists() and p.is_dir():
            dataset_dir = p
            break
            
    if dataset_dir and not DATASET_INDEX:
        load_or_generate_index(dataset_dir)
        
    results = []
    
    try:
        if file:
            # Save temp query image
            temp_filename = f"temp_query_{random.randint(0,9999)}.png"
            with open(temp_filename, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Embed Query
            query_embedding = get_image_embedding(temp_filename)
        
            if query_embedding is not None and DATASET_INDEX:
                # Cosine Similarity
                scores = []
                for item in DATASET_INDEX:
                    target_emb = item["embedding"]
                    
                    # Ensure same dimension
                    if len(target_emb) != len(query_embedding):
                         continue 
                    
                    norm_q = np.linalg.norm(query_embedding)
                    norm_t = np.linalg.norm(target_emb)
                    
                    if norm_q == 0 or norm_t == 0:
                        sim = 0
                    else:
                        sim = np.dot(query_embedding, target_emb) / (norm_q * norm_t)
                    
                    scores.append((sim, item))
                    
                scores.sort(key=lambda x: x[0], reverse=True)
                top_matches = scores[:top_k]
                
                for score, item in top_matches:


                     with open(item["path"], "rb") as img_f:
                         b64 = base64.b64encode(img_f.read()).decode()
                     
                     # Generate deterministic metadata
                     import hashlib
                     seed_str = Path(item["filename"]).stem.split("_aug_")[0]
                     seed_int = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
                     random.seed(seed_int)
                     
                     days_offset = random.randint(0, 1000)
                     from datetime import datetime, timedelta
                     random_date = (datetime.now() - timedelta(days=days_offset)).strftime("%Y-%m-%dT%H:%M:%S")
                     
                     crime_list = ["Fraud", "Theft", "Cybercrime", "Assault", "Vandalism", "Burglary", "Identity Theft", "Embezzlement"]
                     selected_crime = random.choice(crime_list)
                     
                     random.seed()
                     
                     results.append({
                        "id": item["id"],
                        "score": float(score),
                        "payload": {
                            "filename": item["filename"],
                            "crime_type": selected_crime,
                            "timestamp": random_date
                        },
                        "image": f"data:image/jpeg;base64,{b64}"
                     })
                     
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    except Exception as e:
        print(f"Search Error: {e}")
        
    return {"results": results}

@router.post("/upload-image")
async def check_authenticity(file: UploadFile = File(...)):
    """
    Authenticity Check using Qdrant vector search
    """
    import time
    print(f"[{time.time()}] /upload-image called for {file.filename}", flush=True)
    
    try:
        # Save uploaded file temporarily
        content = await file.read()
        temp_filename = f"temp_auth_{random.randint(0,9999)}.png"
        with open(temp_filename, "wb") as buffer:
            buffer.write(content)
        
        # Generate embedding for uploaded image
        print(f"Generating embedding for {file.filename}...", flush=True)
        embedding = get_image_embedding(temp_filename)
        
        # Cleanup temp file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        
        if embedding is None:
            print("No face detected in uploaded image", flush=True)
            return {
                "filename": file.filename,
                "is_real": True,
                "confidence": 0.0,
                "class": "No Face Detected",
                "match": None
            }
        
        # Search in Qdrant
        print("Searching in Qdrant...", flush=True)
        results = qdrant_svc.search_similar(
            vector=embedding.tolist(),
            limit=5
        )
        
        if not results:
            print("No matches found in Qdrant", flush=True)
            return {
                "filename": file.filename,
                "is_real": True,
                "confidence": 0.0,
                "class": "Not in Dataset",
                "match": None
            }
        
        # Get best match
        best_match = results[0]
        best_score = best_match.score
        
        print(f"Best match: {best_match.payload.get('filename')} with score {best_score:.4f}", flush=True)
        
        # Load matched image
        match_data = None
        if best_match.payload.get('image_path'):
            try:
                with open(best_match.payload['image_path'], "rb") as img_f:
                    b64 = base64.b64encode(img_f.read()).decode()
                match_data = {
                    "filename": best_match.payload.get('filename'),
                    "image": f"data:image/jpeg;base64,{b64}",
                    "id": best_match.id,
                    "crime_type": best_match.payload.get('crime_type'),
                    "arrest_timestamp": best_match.payload.get('arrest_timestamp')
                }
            except Exception as e:
                print(f"Error loading matched image: {e}", flush=True)
        
        return {
            "filename": file.filename,
            "is_real": True,
            "confidence": float(best_score),
            "class": "Verified in Database",
            "match": match_data
        }
        
    except Exception as e:
        print(f"Auth Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return {
            "filename": file.filename,
            "is_real": False,
            "confidence": 0.0,
            "class": "Error",
        }

# ============================================================================
# CRUD OPERATIONS FOR SUSPECT DATABASE
# ============================================================================

@router.post("/suspects")
async def create_suspect(file: UploadFile = File(...), crime_type: str = Form(...), notes: str = Form("")):
    """Create new suspect record"""
    try:
        # Read and save image
        image_bytes = await file.read()
        temp_path = f"temp_upload_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(image_bytes)
        
        # Get embedding
        from app.routes import get_image_embedding
        embedding = get_image_embedding(temp_path)
        
        if embedding is None:
            os.remove(temp_path)
            raise HTTPException(status_code=400, detail="Could not extract face from image")
        
        # Create metadata
        from datetime import datetime
        metadata = {
            "filename": file.filename,
            "image_path": temp_path,
            "crime_type": crime_type,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }
        
        # Insert to Qdrant
        point_id = qdrant_svc.insert_record(embedding.tolist(), metadata)
        
        if point_id:
            return {"success": True, "id": point_id, "message": "Suspect added successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to insert record")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@router.get("/suspects")
async def list_suspects(limit: int = 100, offset: int = 0, crime_type: str = None):
    """List all suspects with optional filtering"""
    try:
        if crime_type:
            records = qdrant_svc.search_by_filters(crime_type=crime_type, limit=limit)
        else:
            records = qdrant_svc.list_records(limit=limit, offset=offset)
        
        return {"success": True, "data": records, "count": len(records)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/suspects/{suspect_id}")
async def update_suspect(suspect_id: str, crime_type: str = Form(None), notes: str = Form(None)):
    """Update suspect metadata"""
    try:
        metadata = {}
        if crime_type:
            metadata["crime_type"] = crime_type
        if notes:
            metadata["notes"] = notes
        
        if not metadata:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        success = qdrant_svc.update_record(suspect_id, metadata)
        
        if success:
            return {"success": True, "message": "Suspect updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Suspect not found or update failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/suspects/{suspect_id}")
async def delete_suspect(suspect_id: str):
    """Delete suspect by ID with archiving"""
    try:
        # Archive before delete
        try:
            record = qdrant_svc.client.retrieve(
                collection_name=qdrant_svc.collection_name,
                ids=[suspect_id],
                with_payload=True,
                with_vectors=False
            )
            
            if record:
                rec = record[0]
                deleted_entry = {
                    "id": rec.id,
                    "payload": rec.payload,
                    "deleted_at": datetime.now().isoformat()
                }
                
                existing = []
                if os.path.exists(DELETED_LOG_FILE):
                    try:
                        with open(DELETED_LOG_FILE, "r") as f:
                            existing = json.load(f)
                    except: pass
                
                existing.insert(0, deleted_entry)
                with open(DELETED_LOG_FILE, "w") as f:
                    json.dump(existing, f, indent=2)
        except Exception as archive_err:
            print(f"Archiving failed: {archive_err}")

        # Proceed to delete
        success = qdrant_svc.delete_record(suspect_id)
        
        if success:
            return {"success": True, "message": "Suspect deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Suspect not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suspects/bulk-delete")
async def bulk_delete_suspects(ids: list[str] = Body(...)):
    """Delete multiple suspects"""
    try:
        success = qdrant_svc.delete_multiple(ids)
        
        if success:
            return {"success": True, "message": f"Deleted {len(ids)} suspects"}
        else:
            raise HTTPException(status_code=500, detail="Bulk delete failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suspects/stats/overview")
async def get_stats():
    """Get database statistics"""
    try:
        stats = qdrant_svc.get_stats()
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suspects/populate-metadata")
async def populate_metadata():
    """Add crime_type and timestamp to records that don't have them"""
    try:
        import random
        from datetime import datetime, timedelta
        import hashlib
        
        crime_types = ["Fraud", "Theft", "Cybercrime", "Assault", "Vandalism", "Burglary", "Identity Theft", "Embezzlement"]
        
        # Get all records
        records = qdrant_svc.list_records(limit=12000)
        updated = 0
        
        for record in records:
            # Check if metadata is missing
            if not record.payload.get('crime_type') or not record.payload.get('timestamp'):
                filename = record.payload.get('filename', f'record_{record.id}')
                
                # Deterministic assignment based on filename
                seed_str = Path(filename).stem.split("_aug_")[0]
                seed_int = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
                random.seed(seed_int)
                
                crime_type = random.choice(crime_types)
                days_offset = random.randint(0, 1095)
                timestamp = (datetime.now() - timedelta(days=days_offset)).isoformat()
                
                random.seed()
                
                # Update
                metadata = {
                    "crime_type": crime_type,
                    "timestamp": timestamp
                }
                
                if qdrant_svc.update_record(record.id, metadata):
                    updated += 1
        
        return {"success": True, "message": f"Updated {updated} records"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suspects/add-original-index")
async def add_original_index():
    """Add original_index field from Pickle to preserve dataset order"""
    try:
        import pickle
        
        # Load Pickle index
        with open("dataset_index.pkl", "rb") as f:
            data = pickle.load(f)
            pickle_index = data.get('index', []) if isinstance(data, dict) else data
        
        # Create filename -> original_index mapping
        filename_to_index = {}
        for i, record in enumerate(pickle_index):
            filename = record.get('filename', '')
            if filename:
                filename_to_index[filename] = i
        
        # Get all Qdrant records
        qdrant_records = qdrant_svc.list_records(limit=15000)
        updated = 0
        
        # Update each record with original_index
        for qrec in qdrant_records:
            filename = qrec.payload.get('filename', '')
            if filename in filename_to_index:
                original_idx = filename_to_index[filename]
                
                metadata = {
                    "original_index": original_idx
                }
                
                if qdrant_svc.update_record(qrec.id, metadata):
                    updated += 1
        
        return {
            "success": True, 
            "message": f"Added original_index to {updated}/{len(qdrant_records)} records",
            "total_in_pickle": len(pickle_index)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suspects")
async def add_suspect(
    file: UploadFile = File(...),
    crime_type: str = Form(...),
    name: str = Form("Unknown"),
):
    """Add a new suspect with auto-generation and augmentation"""
    try:
        if not os.path.exists(IMAGE_DIR):
            os.makedirs(IMAGE_DIR)
            
        # 1. Determine Next ID
        # Scan for max numeric filename to auto-increment from 02000
        max_id = 1999 # Default to start checking from 1999
        for f in os.listdir(IMAGE_DIR):
            if f.endswith(".png") and not "_aug" in f:
                 try:
                     # Check if purely numeric stem
                     stem = Path(f).stem
                     if stem.isdigit():
                         fid = int(stem)
                         if fid > max_id: max_id = fid
                 except: pass
        
        next_id = max_id + 1
        base_filename = f"{next_id:05d}" # e.g. "02000"
        
        # Load Original Image
        content = await file.read()
        original_img = Image.open(BytesIO(content)).convert("RGB")
        
        # Prepare Augmentations
        images_to_save = [] # (image_obj, filename)
        
        # Original
        images_to_save.append((original_img, f"{base_filename}.png"))
        
        # Augmentations (5 variants)
        # 1. Flip
        images_to_save.append((ImageOps.mirror(original_img), f"{base_filename}_aug_0.png"))
        # 2. Brightness
        enhancer = ImageEnhance.Brightness(original_img)
        images_to_save.append((enhancer.enhance(1.5), f"{base_filename}_aug_1.png"))
        # 3. Contrast
        enhancer = ImageEnhance.Contrast(original_img)
        images_to_save.append((enhancer.enhance(1.5), f"{base_filename}_aug_2.png"))
        # 4. Grayscale
        images_to_save.append((ImageOps.grayscale(original_img).convert("RGB"), f"{base_filename}_aug_3.png"))
        # 5. Rotate
        images_to_save.append((original_img.rotate(15), f"{base_filename}_aug_4.png"))
        
        # Process All
        points = []
        import uuid
        from qdrant_client.models import PointStruct
        
        # Use next_id * 10 as base index to keep them grouped at the end
        base_index = next_id * 10 
        
        for i, (img, fname) in enumerate(images_to_save):
            # Save to disk
            fpath = os.path.join(IMAGE_DIR, fname)
            img.save(fpath)
            
            # Metadata
            payload = {
                "filename": fname,
                "crime_type": crime_type,
                "timestamp": datetime.now().isoformat(),
                "original_index": base_index + i,
                "name": name # Store user provided name
            }
            
            # Vector (Dummy for now)
            vector = [0.0] * 512
            
            suspect_id = str(uuid.uuid4())
            points.append(
                PointStruct(
                    id=suspect_id,
                    vector=vector,
                    payload=payload
                )
            )
            
        # Bulk Insert
        qdrant_svc.client.upsert(
            collection_name=qdrant_svc.collection_name,
            points=points
        )
        
        return {
            "success": True, 
            "message": f"Added suspect {name} with {len(points)} variations (ID: {base_filename}).", 
            "data": {"id": points[0].id, "filename": base_filename}
        }
    except Exception as e:
        print(f"Add suspect error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suspects/deleted")
async def get_deleted_suspects():
    # print("DEBUG: Hitting get_deleted_suspects endpoint")
    """Get list of deleted suspects"""
    if not os.path.exists(DELETED_LOG_FILE):
        return {"data": []}
    try:
        with open(DELETED_LOG_FILE, "r") as f:
            data = json.load(f)
        return {"data": data}
    except Exception as e:
        print(f"Error reading deleted log: {e}")
        return {"data": []}

@router.post("/suspects/restore-all-deleted")
async def restore_all_deleted():
    """Restore all suspects from deleted_suspects.json"""
    if not os.path.exists(DELETED_LOG_FILE):
        return {"message": "No log file found"}
    
    try:
        with open(DELETED_LOG_FILE, "r") as f:
            deleted_data = json.load(f)
            
        points = []
        from qdrant_client.models import PointStruct
        
        for item in deleted_data:
            # Dummy vector
            vector = [0.0] * 512
            points.append(PointStruct(
                id=item["id"],
                vector=vector,
                payload=item["payload"]
            ))
            
        if points:
            qdrant_svc.client.upsert(
                collection_name=qdrant_svc.collection_name,
                points=points
            )
            
        return {"message": f"Restored {len(points)} suspects"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suspects/{suspect_id}")
async def get_suspect(suspect_id: str):
    """Get suspect by ID"""
    try:
        record = qdrant_svc.get_record(suspect_id)
        if record:
            return {"success": True, "data": record}
        else:
            raise HTTPException(status_code=404, detail="Suspect not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SESSION MANAGEMENT ENDPOINTS
# ============================================================================

class SessionCreate(BaseModel):
    user_id: Optional[str] = None

class InteractionLog(BaseModel):
    interaction_type: str  # "search", "view", "generate", "detect"
    query: Optional[str] = None
    results: Optional[dict] = None
    metadata: Optional[dict] = None

class ContextUpdate(BaseModel):
    context_data: dict

@router.post("/sessions")
async def create_session(session_data: SessionCreate):
    """
    Create a new user session.
    """
    try:
        session = session_svc.create_session(session_data.user_id)
        return {
            "success": True,
            "session_id": session["session_id"],
            "created_at": session["created_at"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Get session data by ID.
    """
    try:
        session = session_svc.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        return {"success": True, "data": session}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 50):
    """
    Get interaction history for a session.
    """
    try:
        history = session_svc.get_interaction_history(session_id, limit)
        return {
            "success": True,
            "session_id": session_id,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/interactions")
async def log_interaction(session_id: str, interaction: InteractionLog):
    """
    Log a user interaction to session history.
    """
    try:
        interaction_data = {
            "type": interaction.interaction_type,
            "query": interaction.query,
            "results": interaction.results,
            "metadata": interaction.metadata or {}
        }
        
        success = session_svc.log_interaction(session_id, interaction_data)
        if not success:
            # Session might not exist, create it
            session_svc.create_session()
            success = session_svc.log_interaction(session_id, interaction_data)
        
        return {"success": success, "message": "Interaction logged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/context")
async def get_session_context(session_id: str):
    """
    Get current session context.
    """
    try:
        context = session_svc.get_context(session_id)
        return {"success": True, "context": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/sessions/{session_id}/context")
async def update_session_context(session_id: str, context_update: ContextUpdate):
    """
    Update session context.
    """
    try:
        success = session_svc.update_context(session_id, context_update.context_data)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"success": True, "message": "Context updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session.
    """
    try:
        success = session_svc.delete_session(session_id)
        return {"success": success, "message": "Session deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/cleanup")
async def cleanup_expired_sessions():
    """
    Clean up expired sessions (admin endpoint).
    """
    try:
        deleted_count = session_svc.cleanup_expired_sessions()
        return {
            "success": True,
            "message": f"Cleaned up {deleted_count} expired sessions"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/stats/{suspect_id}")
async def get_memory_stats(suspect_id: str):
    """
    Get memory statistics for a suspect record.
    """
    try:
        record = qdrant_svc.get_record(suspect_id, update_access=False)
        if not record:
            raise HTTPException(status_code=404, detail="Suspect not found")
        
        stats = qdrant_svc.memory_service.get_memory_stats(record.payload)
        return {
            "success": True,
            "suspect_id": suspect_id,
            "memory_stats": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

