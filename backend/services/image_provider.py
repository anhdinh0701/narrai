"""
Image Generation Provider Abstraction Module for NarrAI.
Primary Provider: Stability AI (Cloud REST API, 100% independent from local hardware)
Secondary / Local Enhancer: ComfyUI (Local GPU Image-to-Image / Inpainting / Style Transfer)
"""

from abc import ABC, abstractmethod
import io
import logging
import os
import time
from typing import Optional, Dict, Any
from PIL import Image
import requests

logger = logging.getLogger(__name__)


class ImageGenerationProvider(ABC):
    """Abstract Base Class for Image Generation Providers."""

    @abstractmethod
    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        aspect_ratio: str = "1:1",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate image from text prompt.
        Returns dict:
        {
            "success": bool,
            "image_bytes": Optional[bytes],
            "error_code": Optional[str],
            "error_message": Optional[str],
            "provider": str,
            "cost_credits": Optional[int]
        }
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        pass


class StabilityImageProvider(ImageGenerationProvider):
    """
    Primary Image Generation Provider via Stability AI REST API v2beta.
    100% Cloud-based: Generates high-res, vibrant full-color manga/anime panels
    without any dependency on local hardware or GPUs.
    """

    CORE_ENDPOINT = "https://api.stability.ai/v2beta/stable-image/generate/core"
    SD3_ENDPOINT = "https://api.stability.ai/v2beta/stable-image/generate/sd3"

    def __init__(self):
        self.api_key = os.environ.get("STABILITY_API_KEY", "").strip()
        self.enabled = os.environ.get("STABILITY_ENABLED", "true").lower() in ("true", "1", "yes")
        # Allowed models: 'core' (default, 3 credits), 'sd3.5-large-turbo' (4 credits), 'sd3.5-medium'
        self.model = os.environ.get("STABILITY_MODEL", "core").strip().lower()

    def is_available(self) -> bool:
        return self.enabled and bool(self.api_key)

    @staticmethod
    def normalize_aspect_ratio(layout: str) -> str:
        """
        Maps layout types to Stability AI supported aspect ratios:
        16:9, 1:1, 21:9, 2:3, 3:2, 4:5, 5:4, 9:16, 9:21
        """
        clean = (layout or "square").strip().lower()
        if clean in ("wide", "16:9", "landscape", "horizontal"):
            return "16:9"
        elif clean in ("tall", "2:3", "9:16", "portrait", "vertical"):
            return "2:3"
        return "1:1"

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        aspect_ratio: str = "1:1",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Call Stability AI REST API Text-to-Image.
        Full color anime/webtoon guaranteed.
        """
        if not self.is_available():
            return {
                "success": False,
                "image_bytes": None,
                "error_code": "STABILITY_DISABLED_OR_NO_KEY",
                "error_message": "Stability AI chưa được cấu hình STABILITY_API_KEY trong file .env",
                "provider": "stability"
            }

        norm_ratio = self.normalize_aspect_ratio(aspect_ratio)
        effective_prompt = (prompt or "masterpiece full color anime manga illustration").strip()

        # Build clean negative prompt to enforce vibrant color art and prevent artifacts
        default_negative = (
            "monochrome, grayscale, black and white, lowres, bad anatomy, bad hands, "
            "text, watermark, signature, error, blurry, duplicate character, modern artifacts, extra limbs"
        )
        effective_negative = f"{default_negative}, {negative_prompt}".strip(", ") if negative_prompt else default_negative

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "image/*"
        }

        # Select endpoint based on configured model
        if self.model in ("sd3", "sd3.5-large", "sd3.5-large-turbo", "sd3.5-medium"):
            endpoint = self.SD3_ENDPOINT
            data = {
                "prompt": effective_prompt,
                "negative_prompt": effective_negative,
                "aspect_ratio": norm_ratio,
                "model": self.model if self.model != "sd3" else "sd3.5-large-turbo",
                "output_format": "png",
                "mode": "text-to-image"
            }
        else:
            # Default: Stable Image Core (fast, vibrant, high artistic adherence)
            endpoint = self.CORE_ENDPOINT
            data = {
                "prompt": effective_prompt,
                "negative_prompt": effective_negative,
                "aspect_ratio": norm_ratio,
                "output_format": "png"
            }

        if seed is not None and seed > 0:
            data["seed"] = seed % 4294967295

        # Stability multipart request requires files dict
        files = {"none": ""}

        retries = 2
        last_error_msg = ""
        last_error_code = ""

        for attempt in range(retries + 1):
            try:
                logger.info(
                    "[StabilityProvider] Generating image (aspect=%s, model=%s, attempt=%d)...",
                    norm_ratio, self.model, attempt + 1
                )
                resp = requests.post(
                    endpoint,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=45
                )

                if resp.status_code == 200 and resp.content:
                    logger.info("[StabilityProvider] Successfully generated image (%d bytes).", len(resp.content))
                    return {
                        "success": True,
                        "image_bytes": resp.content,
                        "error_code": None,
                        "error_message": None,
                        "provider": "stability",
                        "aspect_ratio": norm_ratio
                    }

                # Handle insufficient credits (402 Payment Required)
                if resp.status_code == 402:
                    last_error_code = "INSUFFICIENT_CREDITS"
                    last_error_msg = (
                        "Tài khoản Stability AI của bạn không đủ credits để tạo ảnh. "
                        "Vui lòng nạp thêm credits tại https://platform.stability.ai/account/credits rồi thử lại."
                    )
                    logger.error("[StabilityProvider] 402 Payment Required: %s", last_error_msg)
                    break  # Don't retry on 402

                # Handle rate limit (429) or temporary server errors (5xx)
                if resp.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                    wait_time = (attempt + 1) * 2
                    logger.warning("[StabilityProvider] Received HTTP %d. Retrying in %ds...", resp.status_code, wait_time)
                    time.sleep(wait_time)
                    continue

                # Other HTTP errors (400, 403, etc.)
                last_error_code = f"HTTP_{resp.status_code}"
                try:
                    err_json = resp.json()
                    errors = err_json.get("errors", [])
                    last_error_msg = "; ".join(errors) if isinstance(errors, list) else str(err_json)
                except Exception:
                    last_error_msg = resp.text[:300]

                logger.error("[StabilityProvider] Generation failed (%s): %s", last_error_code, last_error_msg)
                break

            except requests.RequestException as e:
                last_error_code = "NETWORK_ERROR"
                last_error_msg = str(e)
                if attempt < retries:
                    logger.warning("[StabilityProvider] Network exception: %s. Retrying...", e)
                    time.sleep(2)
                    continue
                logger.error("[StabilityProvider] Network failed after %d retries: %s", retries, e)

        return {
            "success": False,
            "image_bytes": None,
            "error_code": last_error_code or "UNKNOWN_ERROR",
            "error_message": last_error_msg or "Không thể kết nối tới Stability AI API",
            "provider": "stability"
        }


class ComfyUIProvider(ImageGenerationProvider):
    """
    Optional Local Enhancer / Generator Provider.
    Only active when ComfyUI is explicitly online on user's machine (http://127.0.0.1:8188).
    Does NOT block or break production when offline.
    """

    def __init__(self):
        self.base_url = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")

    def is_available(self) -> bool:
        """Fast non-blocking check if local ComfyUI is listening."""
        try:
            resp = requests.get(f"{self.base_url}/system_stats", timeout=1.2)
            return resp.status_code == 200
        except Exception:
            return False

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        aspect_ratio: str = "1:1",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate or enhance image via local ComfyUI instance."""
        if not self.is_available():
            return {
                "success": False,
                "image_bytes": None,
                "error_code": "COMFYUI_OFFLINE",
                "error_message": "ComfyUI cục bộ hiện đang tắt (chỉ khả dụng khi bạn bật ComfyUI trên máy tính cá nhân).",
                "provider": "comfyui"
            }

        try:
            from services.image_gen import generate_comic_panel_image
            result = generate_comic_panel_image(prompt, seed=seed or 42)
            if result and isinstance(result, str) and result.startswith("data:image/"):
                parts = result.split(",", 1)
                import base64
                img_bytes = base64.b64decode(parts[1])
                return {
                    "success": True,
                    "image_bytes": img_bytes,
                    "error_code": None,
                    "error_message": None,
                    "provider": "comfyui"
                }
        except Exception as e:
            logger.error("[ComfyUIProvider] Local execution error: %s", e)

        return {
            "success": False,
            "image_bytes": None,
            "error_code": "COMFYUI_ERROR",
            "error_message": "Lỗi khi xử lý qua ComfyUI cục bộ",
            "provider": "comfyui"
        }


class ImageProviderFactory:
    """
    Factory to retrieve appropriate image provider.
    Enforces Stability AI as Primary Cloud Provider.
    """

    _stability_provider = None
    _comfyui_provider = None

    @classmethod
    def get_primary_provider(cls) -> ImageGenerationProvider:
        """Always returns Stability AI as primary provider."""
        if cls._stability_provider is None:
            cls._stability_provider = StabilityImageProvider()
        return cls._stability_provider

    @classmethod
    def get_local_enhancer(cls) -> ComfyUIProvider:
        """Returns ComfyUI provider for optional local enhancements."""
        if cls._comfyui_provider is None:
            cls._comfyui_provider = ComfyUIProvider()
        return cls._comfyui_provider
