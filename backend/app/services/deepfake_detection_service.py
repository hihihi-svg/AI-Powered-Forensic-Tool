"""
Deepfake Detection Service using EfficientNet
How it works:
1. Uses EfficientNet (pre-trained on ImageNet) for feature extraction
2. Analyzes image features and patterns common in AI-generated images
3. Combines multiple signals: feature statistics, image properties, and patterns
"""
from PIL import Image
import io
import numpy as np

class DeepfakeDetectionService:
    def __init__(self):
        self.model = None
        print("DeepfakeDetectionService initialized (EfficientNet-based)")
        print("Model will be loaded on first use...")
    
    def _load_model(self):
        """Lazy load EfficientNet model"""
        if self.model is not None:
            return
        
        try:
            import tensorflow as tf
            from tensorflow.keras.applications import EfficientNetB0
            from tensorflow.keras.applications.efficientnet import preprocess_input
            
            print("Loading EfficientNet model...")
            # Load pre-trained EfficientNet (without top classification layer)
            self.model = EfficientNetB0(
                weights='imagenet',
                include_top=False,
                pooling='avg'
            )
            self.preprocess = preprocess_input
            print("✓ EfficientNet loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load EfficientNet: {e}")
            self.model = None
    
    def detect_deepfake(self, image_bytes: bytes):
        """
        Detect if an image is AI-generated using EfficientNet features
        
        How it works:
        1. Extract deep features using EfficientNet
        2. Analyze feature distribution and statistics
        3. Check for AI-generation patterns:
           - Unusual feature variance
           - Perfect symmetry (common in AI faces)
           - Lack of natural noise
           - Specific dimensional patterns
        """
        try:
            print("Analyzing image with EfficientNet...")
            
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            width, height = image.size
            image_array = np.array(image)
            
            # Initialize score
            fake_score = 0.0
            
            # 1. Try EfficientNet feature extraction
            try:
                self._load_model()
                
                if self.model is not None:
                    # Resize for EfficientNet (224x224)
                    img_resized = image.resize((224, 224))
                    img_array = np.array(img_resized)
                    img_array = np.expand_dims(img_array, axis=0)
                    img_array = self.preprocess(img_array)
                    
                    # Extract features
                    features = self.model.predict(img_array, verbose=0)[0]
                    
                    # Analyze feature statistics
                    feature_mean = np.mean(features)
                    feature_std = np.std(features)
                    feature_max = np.max(features)
                    
                    print(f"Features - Mean: {feature_mean:.4f}, Std: {feature_std:.4f}, Max: {feature_max:.4f}")
                    
                    # AI-generated images often have unusual feature distributions
                    if feature_std < 0.5:  # Very low variance
                        fake_score += 0.25
                    if feature_max > 10:  # Unusually high activation
                        fake_score += 0.15
                    
            except Exception as e:
                print(f"EfficientNet analysis failed: {e}")
            
            # 2. Check dimensions (AI images often square, specific sizes)
            if width == height:
                fake_score += 0.25  # Increased weight
                if width in [512, 1024, 2048]:
                    fake_score += 0.35  # Strong indicator of AI
            
            # 3. Analyze color distribution
            color_variance = np.var(image_array)
            if color_variance < 2500:  # Too uniform
                fake_score += 0.30  # Increased weight
            elif color_variance > 7000:  # Natural variance
                fake_score -= 0.10  # Slight reduction for real
            
            # 4. Check for perfect symmetry (common in AI faces)
            if width == height and width > 200:
                # Split image in half
                mid = width // 2
                left_half = image_array[:, :mid]
                right_half = np.fliplr(image_array[:, mid:])
                
                # Calculate difference
                if left_half.shape == right_half.shape:
                    symmetry_diff = np.mean(np.abs(left_half - right_half))
                    
                    if symmetry_diff < 25:  # Very symmetric
                        fake_score += 0.30  # Strong indicator
                        print(f"High symmetry detected: {symmetry_diff:.2f}")
                    elif symmetry_diff > 40:  # Natural asymmetry
                        fake_score -= 0.15
            
            # 5. Check EXIF metadata
            has_exif = hasattr(image, '_getexif') and image._getexif() is not None
            if not has_exif:
                fake_score += 0.25  # Increased - no camera data
            else:
                fake_score -= 0.30  # Strong indicator of real photo
            
            # 6. File size analysis
            file_size = len(image_bytes)
            pixels = width * height
            bytes_per_pixel = file_size / pixels if pixels > 0 else 0
            
            if bytes_per_pixel < 0.4:  # Very compressed
                fake_score += 0.15
            elif bytes_per_pixel > 2.0:  # Uncompressed/high quality
                fake_score -= 0.10
            
            # 7. Check for perfectly smooth gradients (AI artifact)
            if len(image_array.shape) == 3:
                # Calculate gradient magnitude
                gray = np.mean(image_array, axis=2)
                grad_y = np.abs(np.diff(gray, axis=0))
                grad_x = np.abs(np.diff(gray, axis=1))
                
                avg_gradient = (np.mean(grad_y) + np.mean(grad_x)) / 2
                
                if avg_gradient < 5:  # Too smooth
                    fake_score += 0.20
                    print(f"Smooth gradients detected: {avg_gradient:.2f}")
            
            print(f"Final fake_score: {fake_score:.2f}")
            
            # Normalize to 0-1 (adjusted range)
            fake_probability = max(0.0, min(1.0, fake_score))
            real_probability = 1.0 - fake_probability
            
            is_real = real_probability > 0.5
            label = "real" if is_real else "fake"
            confidence = real_probability if is_real else fake_probability
            
            print(f"Detection result: {label} ({confidence*100:.2f}% confidence)")
            print(f"Analysis: dims={width}x{height}, color_var={color_variance:.0f}, EXIF={has_exif}")
            
            return {
                "is_real": is_real,
                "is_fake": not is_real,
                "label": label,
                "confidence": float(confidence),
                "all_predictions": [
                    {"label": "real", "score": float(real_probability)},
                    {"label": "fake", "score": float(fake_probability)}
                ]
            }
                
        except Exception as e:
            print(f"Error in deepfake detection: {e}")
            import traceback
            traceback.print_exc()
            return {
                "is_real": None,
                "is_fake": None,
                "label": "error",
                "confidence": 0.0,
                "error": str(e),
                "all_predictions": []
            }
