import os
import requests
import time

# Configuration
DATASET_DIR = "dataset/mini-CelebAMask-HQ-img"
SAMPLE_COUNT = 20
SOURCE_URL = "https://source.unsplash.com/random/512x512/?face,portrait"
# Alternative if Unsplash is rate limited: "https://picsum.photos/512/512"

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def download_samples():
    print(f"Downloading {SAMPLE_COUNT} sample images for demonstration...")
    ensure_dir(DATASET_DIR)
    
    for i in range(SAMPLE_COUNT):
        try:
            # Use Lorem Picsum for stability
            url = f"https://picsum.photos/seed/{i+100}/512/512" 
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                filename = f"sample_suspect_{i+1:03d}.jpg"
                filepath = os.path.join(DATASET_DIR, filename)
                
                with open(filepath, "wb") as f:
                    f.write(response.content)
                
                print(f"[{i+1}/{SAMPLE_COUNT}] Downloaded {filename}")
                time.sleep(0.5) # Be nice to the API
            else:
                print(f"[{i+1}/{SAMPLE_COUNT}] Failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"Error downloading sample {i+1}: {str(e)}")

    print("\n✅ Download complete!")
    print(f"Images saved to: {os.path.abspath(DATASET_DIR)}")
    print("Run the backend now to index these images automatically.")

if __name__ == "__main__":
    download_samples()
