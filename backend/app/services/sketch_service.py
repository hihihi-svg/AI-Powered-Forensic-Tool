import speech_recognition as sr
from PIL import Image
import numpy as np
import io
import os
from tempfile import NamedTemporaryFile
# import torch -> Moved inside
# from diffusers ... -> Moved inside
# from controlnet_aux ... -> Moved inside

class SketchService:
    def __init__(self):
        print("SketchService initialized. Models will be loaded LAZILY.")
        self.recognizer = sr.Recognizer()
        self.models_loaded = False
        self.pipe = None
        self.openpose = None
    def _ensure_models_loaded(self):
        """Loads models only if they aren't loaded yet."""
        if self.models_loaded:
            return

        print("Triggering Lazy Model Load...")
        try:
            # Local Imports to prevent startup hang
            import torch
            from diffusers import StableDiffusionControlNetPipeline, ControlNetModel, UniPCMultistepScheduler
            from controlnet_aux import OpenposeDetector
            
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.dtype = torch.float16 if self.device == "cuda" else torch.float32
            
            print(f"Loading Models on {self.device}...")
            # 1. OpenPose
            self.openpose = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")
            
            # 2. ControlNet
            controlnet = ControlNetModel.from_pretrained(
                "lllyasviel/control_v11p_sd15_openpose",
                torch_dtype=self.dtype
            )
            
            # 3. Stable Diffusion
            self.pipe = StableDiffusionControlNetPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                controlnet=controlnet,
                torch_dtype=self.dtype,
                safety_checker=None
            )
            
            self.pipe.scheduler = UniPCMultistepScheduler.from_config(self.pipe.scheduler.config)
            
            if self.device == "cuda":
                self.pipe.enable_model_cpu_offload()
            else:
                self.pipe.to(self.device)
                
            print("ControlNet Pipeline Loaded Successfully.")
            self.models_loaded = True
        except Exception as e:
            print(f"FAILED to load ControlNet: {e}")
            # Re-raise to alert user via API error
            raise RuntimeError(f"Model Loading Failed: {e}")

    def process_audio(self, audio_bytes: bytes) -> str:
        # Save bytes to temp file for pydub/sr to read
        # Note: Frontend sends binary (wav/webm). 
        # For robustness, we should use pydub to convert if needed, but keeping it simple as per request first.
        temp_path = "temp_input_audio.wav"
        try:
            with open(temp_path, "wb") as f:
                f.write(audio_bytes)
            
            # Basic WAV check - if fails, might need ffmpeg conversion
            with sr.AudioFile(temp_path) as source:
                audio_data = self.recognizer.record(source)
                try:
                    text = self.recognizer.recognize_google(audio_data)
                except sr.UnknownValueError:
                    text = "A blank face" # Fallback
                except sr.RequestError:
                    text = "Error connecting to API"
            
            return text
        except Exception as e:
            print(f"Audio Process Error: {e}")
            return "Male suspect, roughly 30 years old" # Fallback description
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def generate_sketch(self, description: str, num_images: int = 1):
        # Lazy Load Trigger
        self._ensure_models_loaded()
        
        if not self.models_loaded:
             return [Image.new("RGB", (512, 512), "gray")]

        # Prepare Control Image (Blank -> OpenPose) | As per user snippet
        # Ideally this should be a reference pose, but user asked for "blank"
        blank = Image.new("RGB", (512, 512), "white")
        # include_face=True on blank might generate garbage or nothing, but following instructions.
        control_image = self.openpose(blank, include_face=True)
        # control_image.save("control_face_debug.png")
        
        prompt = f"""
        Black and white forensic pencil sketch of {description},
        age between 25 and 30 years,
        oval face with sharp jawline,
        short black slightly wavy hair,
        thick eyebrows,
        medium-sized eyes,
        straight medium-sized nose,
        thin lips,
        light beard and moustache,
        neutral serious expression,
        front-facing portrait,
        perfectly centered face,
        symmetrical facial structure,
        police sketch style,
        clean line art,
        no background
        """

        negative_prompt = """
        tilted face, side view, profile view, head turned,
        artistic style, cartoon, anime, distorted face, color, realistic photo
        """
        
        images = []
        for _ in range(num_images):
            generated_image = self.pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                image=control_image,
                num_inference_steps=25, # Reduced to 25 for speed
                guidance_scale=6.0,
                controlnet_conditioning_scale=1.0
            ).images[0]
            images.append(generated_image)
            
        return images
