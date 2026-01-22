
import os
import numpy as np
import torch
from PIL import Image

# Global Facenet Models
FACENET_AVAILABLE = False
mtcnn = None
resnet = None

try:
    from facenet_pytorch import MTCNN, InceptionResnetV1
    FACENET_AVAILABLE = True
    # Initialize models (CPU is fine for 1 image)
    # create global instances to reuse
    mtcnn = MTCNN(image_size=160, margin=0, keep_all=False)
    resnet = InceptionResnetV1(pretrained='vggface2').eval()
    print("DEBUG: Facenet-PyTorch loaded successfully (Shared Utils).")
except ImportError:
    FACENET_AVAILABLE = False
    print("WARNING: Facenet-PyTorch not installed. Using Color Histogram fallback.")

def get_image_embedding(file_path):
    """
    Generates an embedding using Facenet-PyTorch.
    Falls back to Color Histogram if no face found or library missing.
    """
    global FACENET_AVAILABLE, mtcnn, resnet

    if FACENET_AVAILABLE and mtcnn is not None and resnet is not None:
        try:
            img = Image.open(file_path)
            # Detect face and crop
            img_cropped = mtcnn(img)
            
            if img_cropped is not None:
                # Calculate embedding
                with torch.no_grad():
                    img_embedding = resnet(img_cropped.unsqueeze(0))
                return img_embedding[0].numpy()
            else:
                 pass # No face found, fallback to histogram
        except Exception as e:
            # print(f"Facenet failed for {file_path}: {e}")
            pass
            
    # Histogram Fallback (when no face detected or lib missing)
    try:
        with Image.open(file_path) as img:
            img = img.resize((64, 64)).convert("RGB")
            hist = img.histogram()
            vec = np.array(hist, dtype=float)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec
    except Exception as e:
        print(f"Embedding failed for {file_path}: {e}")
        return None

def generate_embeddings_logic():
    """
    Scans dataset folder and ensures all images are indexed in Qdrant.
    Returns count of processed images.
    """
    from app.services.qdrant_service import QdrantService
    import glob
    
    qdrant = QdrantService()
    dataset_dir = "dataset/mini-CelebAMask-HQ-img"
    
    if not os.path.exists(dataset_dir):
        return 0
        
    image_paths = glob.glob(os.path.join(dataset_dir, "*.*"))
    count = 0
    
    # Get existing IDs to avoid re-work if possible, or just overwrite
    # For simplicity, we process all and upsert (Qdrant handles dedupe by ID if we used deterministic IDs)
    # But here we stick to the project's likely pattern of just adding.
    
    for img_path in image_paths:
        try:
            filename = os.path.basename(img_path)
            # Check extension
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            embedding = get_image_embedding(img_path)
            if embedding is not None:
                # Create a simple numeric ID or hash
                # Using hash of filename for determinism
                import hashlib
                suspect_id = int(hashlib.md5(filename.encode()).hexdigest(), 16) % (10**8)
                
                metadata = {
                    "filename": filename,
                    "crime_type": "Theft", # Default for demo data
                    "timestamp": "2024-01-01T12:00:00"
                }
                
                qdrant.upsert_suspect(suspect_id, embedding.tolist(), metadata)
                count += 1
        except Exception as e:
            print(f"Error indexing {filename}: {e}")
            
    return count
