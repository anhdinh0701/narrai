import io
import logging
import os
import time
from typing import Optional
from PIL import Image
import requests

logger = logging.getLogger(__name__)

class StabilityImageService:
    """
    Service for enhancing and upscaling images using Stability AI REST API v2beta.
    Acts as a post-processor for ComfyUI / fallback image pipelines.
    """

    def __init__(self):
        self.api_key = os.environ.get("STABILITY_API_KEY", "").strip()
        self.enabled = os.environ.get("STABILITY_ENABLED", "true").lower() in ("true", "1", "yes")
        self.default_mode = os.environ.get("STABILITY_DEFAULT_MODE", "upscale").strip().lower()
        self.img2img_endpoint = os.environ.get(
            "STABILITY_IMAGE_TO_IMAGE_ENDPOINT",
            "https://api.stability.ai/v2beta/stable-image/generate/sd3"
        ).strip()
        self.upscale_endpoint = os.environ.get(
            "STABILITY_UPSCALE_ENDPOINT",
            "https://api.stability.ai/v2beta/stable-image/upscale/fast"
        ).strip()

    def is_available(self) -> bool:
        return self.enabled and bool(self.api_key)

    def _sanitize_image_bytes(self, image_bytes: bytes, max_pixels: int = 4194304) -> bytes:
        """
        Validates, converts to RGB PNG, and resizes if exceeding max_pixels.
        Stability API requires RGB format and specific pixel constraints.
        """
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Convert palette or RGBA to RGB for maximum compatibility
                if img.mode != "RGB":
                    img = img.convert("RGB")

                width, height = img.size
                total_pixels = width * height

                if total_pixels > max_pixels:
                    ratio = (max_pixels / float(total_pixels)) ** 0.5
                    new_w = max(64, int(width * ratio))
                    new_h = max(64, int(height * ratio))
                    logger.info("Resizing image from %sx%s to %sx%s to fit Stability API limits", width, height, new_w, new_h)
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                elif width < 64 or height < 64:
                    new_w = max(64, width)
                    new_h = max(64, height)
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                out_io = io.BytesIO()
                img.save(out_io, format="PNG", optimize=True)
                return out_io.getvalue()
        except Exception as e:
            logger.warning("Image preprocessing warning: %s. Using original bytes.", e)
            return image_bytes

    def upscale_image(self, image_bytes: bytes) -> Optional[bytes]:
        """
        Fast 4x Upscale via Stability AI Fast Upscale endpoint.
        Returns upscaled PNG bytes or None if failed.
        """
        if not self.is_available():
            logger.info("Stability AI upscale skipped: service disabled or missing API key.")
            return None

        clean_bytes = self._sanitize_image_bytes(image_bytes, max_pixels=4194304)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "image/*"
        }
        files = {
            "image": ("panel.png", clean_bytes, "image/png")
        }
        data = {
            "output_format": "png"
        }

        retries = 2
        for attempt in range(retries + 1):
            try:
                response = requests.post(
                    self.upscale_endpoint,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=60
                )
                if response.status_code == 200:
                    logger.info("Stability AI upscale succeeded (%d bytes).", len(response.content))
                    return response.content
                elif response.status_code >= 500 and attempt < retries:
                    logger.warning("Stability upscale 5xx error (%d). Retrying in %ds...", response.status_code, attempt + 1)
                    time.sleep(attempt + 1)
                    continue
                else:
                    logger.error("Stability upscale failed with status %d: %s", response.status_code, response.text[:300])
                    return None
            except requests.RequestException as e:
                if attempt < retries:
                    logger.warning("Stability request exception: %s. Retrying in %ds...", e, attempt + 1)
                    time.sleep(attempt + 1)
                    continue
                logger.error("Stability upscale network failure: %s", e)
                return None

        return None

    def generate_image_to_image(
        self,
        image_bytes: bytes,
        prompt: str,
        strength: float = 0.35,
        model: str = "sd3.5-large-turbo"
    ) -> Optional[bytes]:
        """
        Enhance image details/lighting via SD3 Image-to-Image while preserving composition.
        strength: 0.2 (very subtle) to 0.6 (more transformative). Default 0.35.
        """
        if not self.is_available():
            logger.info("Stability AI img2img skipped: service disabled or missing API key.")
            return None

        clean_bytes = self._sanitize_image_bytes(image_bytes, max_pixels=2097152)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "image/*"
        }
        files = {
            "image": ("panel.png", clean_bytes, "image/png")
        }

        clamped_strength = max(0.1, min(0.7, float(strength)))
        effective_prompt = (prompt.strip() or "masterpiece anime manga illustration, highly detailed, crisp lineart, cinematic lighting")

        data = {
            "mode": "image-to-image",
            "prompt": effective_prompt,
            "strength": str(clamped_strength),
            "model": model,
            "output_format": "png"
        }

        retries = 2
        for attempt in range(retries + 1):
            try:
                response = requests.post(
                    self.img2img_endpoint,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=90
                )
                if response.status_code == 200:
                    logger.info("Stability AI img2img enhance succeeded (%d bytes).", len(response.content))
                    return response.content
                elif response.status_code >= 500 and attempt < retries:
                    logger.warning("Stability img2img 5xx error (%d). Retrying in %ds...", response.status_code, attempt + 1)
                    time.sleep(attempt + 1)
                    continue
                else:
                    logger.error("Stability img2img failed with status %d: %s", response.status_code, response.text[:300])
                    return None
            except requests.RequestException as e:
                if attempt < retries:
                    logger.warning("Stability request exception: %s. Retrying in %ds...", e, attempt + 1)
                    time.sleep(attempt + 1)
                    continue
                logger.error("Stability img2img network failure: %s", e)
                return None

        return None

    def process_image(
        self,
        image_bytes: bytes,
        mode: str,
        prompt: str = "",
        strength: float = 0.35
    ) -> Optional[bytes]:
        """
        Dispatch to appropriate Stability AI enhancement method based on mode.
        Supported modes: 'upscale', 'enhance', 'image-to-image'
        """
        clean_mode = (mode or self.default_mode).strip().lower()
        if clean_mode in ("none", "original", ""):
            return None

        if clean_mode in ("upscale", "4x", "fast-upscale"):
            return self.upscale_image(image_bytes)
        elif clean_mode in ("enhance", "img2img", "image-to-image"):
            return self.generate_image_to_image(image_bytes, prompt, strength)
        else:
            logger.warning("Unknown enhancement mode '%s'. Skipping Stability processing.", mode)
            return None
