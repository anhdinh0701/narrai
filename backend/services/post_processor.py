import base64
import io
import logging
import os
import re
import shutil
import time
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import requests

try:
    from services.stability_service import StabilityImageService
except (ImportError, ModuleNotFoundError):
    from backend.services.stability_service import StabilityImageService

logger = logging.getLogger(__name__)

class ImagePostProcessor:
    """
    Manages image storage pipeline stages:
    1. Original: ComfyUI or fallback generator output
    2. Processed: Stability AI enhancement/upscale output
    3. Final: Production-ready image delivered to user
    """

    def __init__(self, base_outputs_dir: Optional[str] = None):
        if not base_outputs_dir:
            # Default to backend/outputs
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            base_outputs_dir = os.path.join(backend_dir, "outputs")

        self.base_dir = os.path.abspath(base_outputs_dir)
        self.original_dir = os.path.join(self.base_dir, "original")
        self.processed_dir = os.path.join(self.base_dir, "processed")
        self.final_dir = os.path.join(self.base_dir, "final")

        for d in (self.original_dir, self.processed_dir, self.final_dir):
            os.makedirs(d, exist_ok=True)

        self.stability = StabilityImageService()

    def extract_image_bytes(self, image_data: Any) -> Optional[bytes]:
        """
        Converts base64 data URI, HTTP URL, or raw bytes into PNG/JPEG bytes.
        """
        if not image_data:
            return None

        if isinstance(image_data, bytes):
            return image_data

        if isinstance(image_data, str):
            image_data = image_data.strip()
            # 1. Base64 data URL
            if image_data.startswith("data:image/"):
                try:
                    parts = image_data.split(",", 1)
                    if len(parts) == 2:
                        return base64.b64decode(parts[1])
                except Exception as e:
                    logger.error("Failed to decode base64 image: %s", e)
                    return None

            # 2. HTTP/HTTPS URL
            if image_data.startswith("http://") or image_data.startswith("https://"):
                try:
                    resp = requests.get(image_data, timeout=20, headers={"User-Agent": "NarrAI-PostProcessor/1.0"})
                    if resp.status_code == 200:
                        return resp.content
                    logger.warning("Failed to download image from URL %s (status %d)", image_data, resp.status_code)
                except Exception as e:
                    logger.warning("Exception downloading image from URL %s: %s", image_data, e)
                return None

            # 3. Local asset or relative web path (/assets/...)
            clean_path = image_data.lstrip("/")
            frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "frontend")
            candidate = os.path.normpath(os.path.join(frontend_dir, clean_path))
            if os.path.isfile(candidate):
                try:
                    with open(candidate, "rb") as f:
                        return f.read()
                except Exception as e:
                    logger.error("Failed to read local asset %s: %s", candidate, e)

            # 4. Local file path
            if os.path.isfile(image_data):
                try:
                    with open(image_data, "rb") as f:
                        return f.read()
                except Exception as e:
                    logger.error("Failed to read local file %s: %s", image_data, e)
                    return None

        return None

    def save_bytes_to_stage(self, stage: str, filename: str, data: bytes) -> str:
        """
        Saves raw bytes into outputs/{stage}/{filename} and returns relative API URL.
        """
        target_dir = os.path.join(self.base_dir, stage)
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, filename)
        with open(file_path, "wb") as f:
            f.write(data)
        return f"/api/images/{stage}/{filename}"

    def process_panel_image(
        self,
        comic_id: int,
        panel_index: int,
        raw_image: Any,
        prompt: str = "",
        mode: str = "none",
        strength: float = 0.35
    ) -> Dict[str, Any]:
        """
        Process a comic panel through the multi-stage pipeline:
        Stage 1: Save original image
        Stage 2: Run Stability AI (if requested & available)
        Stage 3: Produce final image (enhanced, or clean fallback to original)
        """
        timestamp = int(time.time() * 1000)
        clean_mode = (mode or "none").strip().lower()

        # Instant zero-latency return if no enhancement requested and image is already a relative URL
        if clean_mode in ("none", "original", ""):
            if isinstance(raw_image, str) and (raw_image.startswith("/assets/") or raw_image.startswith("assets/")):
                url = "/" + raw_image.lstrip("/")
                return {
                    "original_url": url,
                    "processed_url": None,
                    "final_url": url,
                    "provider": "comfyui",
                    "mode": "none",
                    "status": "original_only"
                }

        img_bytes = self.extract_image_bytes(raw_image)

        if not img_bytes:
            # Fallback if raw_image is a URL that couldn't be downloaded synchronously
            if isinstance(raw_image, str) and (raw_image.startswith("http://") or raw_image.startswith("https://") or raw_image.startswith("/")):
                return {
                    "original_url": raw_image,
                    "processed_url": None,
                    "final_url": raw_image,
                    "provider": "external",
                    "mode": "none",
                    "status": "external_url"
                }
            raise ValueError("Unable to read image bytes from input")

        # Stage 1: Original
        orig_filename = f"c{comic_id}_p{panel_index}_{timestamp}_orig.png"
        original_url = self.save_bytes_to_stage("original", orig_filename, img_bytes)

        # Determine enhancement
        processed_url = None
        final_url = None
        provider = "comfyui"
        status = "original_only"

        if clean_mode in ("upscale", "4x", "fast-upscale", "enhance", "img2img", "image-to-image") and self.stability.is_available():
            logger.info("Running Stability AI post-processing (mode=%s, strength=%.2f) for panel %d...", clean_mode, strength, panel_index)
            enhanced_bytes = self.stability.process_image(
                image_bytes=img_bytes,
                mode=clean_mode,
                prompt=prompt,
                strength=strength
            )

            if enhanced_bytes:
                proc_filename = f"c{comic_id}_p{panel_index}_{timestamp}_{clean_mode}.png"
                processed_url = self.save_bytes_to_stage("processed", proc_filename, enhanced_bytes)

                final_filename = f"c{comic_id}_p{panel_index}_{timestamp}_final.png"
                final_url = self.save_bytes_to_stage("final", final_filename, enhanced_bytes)

                provider = "stability-ai"
                status = "completed"
            else:
                logger.warning("Stability AI failed or returned None. Falling back to original ComfyUI image.")
                final_filename = f"c{comic_id}_p{panel_index}_{timestamp}_final.png"
                final_url = self.save_bytes_to_stage("final", final_filename, img_bytes)
                status = "fallback"
        else:
            # No enhancement requested or Stability unavailable
            final_filename = f"c{comic_id}_p{panel_index}_{timestamp}_final.png"
            final_url = self.save_bytes_to_stage("final", final_filename, img_bytes)
            status = "original_only"

        return {
            "original_url": original_url,
            "processed_url": processed_url,
            "final_url": final_url,
            "provider": provider,
            "mode": clean_mode,
            "status": status
        }
