"""
Text-to-Sketch using Stable Diffusion + ControlNet (In-Process)
"""
import torch
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
from PIL import Image
import os
import uuid
import asyncio
from datetime import datetime
import functools

class TextToImageService:
    def __init__(self):
        print("TextToImageService initialized (Stable Diffusion + ControlNet)")
        self.pipe = None
        self.jobs = {}  # {job_id: {status, output_path, error, progress}}
        self.model_lock = asyncio.Lock() # Not strictly needed for thread executor but good practice

    def _load_models(self):
        """Load models if not already loaded. Run this in the worker thread."""
        if self.pipe is not None:
            return

        print("[Service] Loading models (first run only)...")
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = torch.float16 if device == "cuda" else torch.float32

            controlnet = ControlNetModel.from_pretrained(
                "lllyasviel/control_v11p_sd15_openpose",
                torch_dtype=dtype
            )

            self.pipe = StableDiffusionControlNetPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                controlnet=controlnet,
                torch_dtype=dtype,
                safety_checker=None
            )

            if device == "cuda":
                self.pipe = self.pipe.to("cuda")
            else:
                self.pipe = self.pipe.to("cpu")
                
            # Optimize for speed
            self.pipe.enable_attention_slicing()
            
            print("[Service] Models loaded successfully!")
        except Exception as e:
            print(f"[Service] Failed to load models: {e}")
            raise e

    def _generate_blocking(self, job_id, prompt):
        """Blocking method designed to run in a thread executor."""
        print(f"[{job_id}] Starting generation thread...")
        
        try:
            # 1. Ensure models are loaded
            self._load_models()
            
            # 2. Setup paths
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"generated_sketch_{timestamp}.png"
            
            # 3. Config
            control_image = Image.new("RGB", (512, 512), "white")
            enhanced_prompt = f"Black and white forensic police sketch, pencil drawing style. {prompt} detailed facial features, front-facing portrait, neutral serious expression, clean line art, no background"
            negative_prompt = "tilted face, side view, color, artistic, cartoon, anime, distorted, blurry"
            
            num_steps = 10
            
            # 4. Progress Callback
            def progress_callback(step, timestep, latents):
                # Update progress in the shared dict
                # Note: This is thread-safe enough for a dict update in CPython (GIL)
                # but for perfect safety we usually blindly update.
                p = int((step / num_steps) * 100)
                self.jobs[job_id]["progress"] = p
                print(f"[{job_id}] Step {step}/{num_steps} ({p}%)")

            # 5. Run Inference
            result = self.pipe(
                prompt=enhanced_prompt,
                negative_prompt=negative_prompt,
                image=control_image,
                num_inference_steps=num_steps,
                guidance_scale=6.0,
                controlnet_conditioning_scale=1.0,
                callback=progress_callback,
                callback_steps=1
            )
            
            # 6. Save
            image = result.images[0]
            image.save(output_filename)
            print(f"[{job_id}] Saved to {output_filename}")
            
            # 7. Complete
            self.jobs[job_id]["output_path"] = output_filename
            self.jobs[job_id]["progress"] = 100
            self.jobs[job_id]["status"] = "completed"
            
        except Exception as e:
            print(f"[{job_id}] Error: {e}")
            import traceback
            traceback.print_exc()
            self.jobs[job_id]["status"] = "failed"
            self.jobs[job_id]["error"] = str(e)

    async def start_generation(self, prompt: str) -> str:
        """Start async generation job"""
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {"status": "processing", "progress": 0}
        
        # Run blocking generation in default executor (Thread pool)
        # This keeps the main event loop free to answer API requests
        loop = asyncio.get_running_loop()
        
        # We don't await this! We want it to run in background.
        # But run_in_executor returns a Future. We wrap it in a Task to let it run.
        # Actually, creating a task that awaits run_in_executor is the way to fire-and-forget properly
        # if we want to catch top-level exceptions, but _generate_blocking handles its own exceptions.
        
        loop.run_in_executor(None, self._generate_blocking, job_id, prompt)
        
        return job_id

    def get_job_status(self, job_id: str):
        return self.jobs.get(job_id)

    # Legacy method kept for compatibility
    async def generate_image(self, prompt: str):
        return None
