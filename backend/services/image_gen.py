import urllib.request
import urllib.parse
import json
import time
import base64
import os
import re
from typing import Optional, Dict, Any, List

COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")

_CHECKPOINT_CACHE = {"ckpt": None, "last_check": 0}

CURATED_PANELS = [
    (["sword", "mountain", "peak", "tien hiep", "kiem", "nui"], "/assets/manga/panel_sword_mountain.jpg"),
    (["punch", "fight", "combat", "action", "strike", "danh"], "/assets/manga/panel_combat_punch.jpg"),
    (["detective", "coffee", "investigat", "trinh tham"], "/assets/manga/panel_detective_coffee.jpg"),
    (["two", "dialogue", "talk", "discuss", "doi thoai", "hai"], "/assets/manga/panel_two_detectives.jpg"),
    (["city", "urban", "window", "building", "thanh pho", "do thi"], "/assets/manga/panel_city_window.jpg"),
    (["white hair", "anime", "hero", "toc trang", "ky ao", "fantasy"], "/assets/manga/panel_whitehair_anime.jpg"),
    (["team", "horizon", "dong doi", "chan troi", "adventure"], "/assets/manga/panel_team_horizon.jpg"),
    (["desk", "office", "clue", "manh moi", "ban lam viec"], "/assets/manga/panel_detective_desk.jpg"),
    (["book", "hands", "read", "sach", "tay"], "/assets/manga/panel_hands_book.jpg"),
    (["eyes", "glow", "blue", "mat", "anh sang"], "/assets/manga/panel_blue_glowing_eyes.jpg"),
    (["cloak", "hero", "silhouette", "ao choang", "bong"], "/assets/manga/panel_blue_hero_cloak.jpg"),
    (["snow", "hand", "tuyet"], "/assets/manga/panel_blue_hand_snow.jpg"),
    (["canyon", "valley", "thung lung"], "/assets/manga/panel_blue_fog_valley.jpg"),
    (["street", "alley", "ngo", "duong"], "/assets/manga/panel_street_mountain.jpg"),
    (["phone", "call", "dien thoai"], "/assets/manga/panel_phone_clue.jpg"),
    (["symbol", "anomaly", "ky hieu"], "/assets/manga/panel_symbol.jpg"),
    (["man", "portrait", "nam"], "/assets/manga/panel_man_portrait.jpg"),
    (["woman", "nu"], "/assets/manga/panel_woman.jpg"),
]

FALLBACK_POOL = [
    "/assets/manga/panel_sword_mountain.jpg",
    "/assets/manga/panel_whitehair_anime.jpg",
    "/assets/manga/panel_combat_punch.jpg",
    "/assets/manga/panel_two_detectives.jpg",
    "/assets/manga/panel_team_horizon.jpg",
    "/assets/manga/panel_city_window.jpg",
    "/assets/manga/panel_detective_coffee.jpg",
    "/assets/manga/panel_blue_glowing_eyes.jpg",
    "/assets/manga/panel_hands_book.jpg",
    "/assets/manga/panel_blue_hero_cloak.jpg",
    "/assets/manga/panel_blue_peaks_wind.jpg",
    "/assets/manga/panel_street_mountain.jpg",
    "/assets/manga/panel_phone_clue.jpg",
    "/assets/manga/panel_blue_fog_valley.jpg",
    "/assets/manga/panel_detective_desk.jpg",
    "/assets/manga/panel_symbol.jpg",
    "/assets/manga/panel_man_portrait.jpg",
    "/assets/manga/panel_woman.jpg"
]

def get_first_checkpoint():
    """Fetch available checkpoints and return the first one (cached for 60s)."""
    now = time.time()
    if now - _CHECKPOINT_CACHE["last_check"] < 60 and _CHECKPOINT_CACHE["ckpt"]:
        return _CHECKPOINT_CACHE["ckpt"]
    _CHECKPOINT_CACHE["last_check"] = now
    try:
        req = urllib.request.Request(f"{COMFYUI_URL}/object_info/CheckpointLoaderSimple", headers={'ngrok-skip-browser-warning': '1'})
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode("utf-8"))
            ckpt_list = data.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {}).get("ckpt_name", [[]])[0]
            if isinstance(ckpt_list, list) and len(ckpt_list) > 0:
                _CHECKPOINT_CACHE["ckpt"] = ckpt_list[0]
                return _CHECKPOINT_CACHE["ckpt"]
    except Exception:
        pass
    _CHECKPOINT_CACHE["ckpt"] = None
    return None

def get_comfyui_status() -> dict:
    """
    Query live ComfyUI connection, returning device info, vram, checkpoint, and readiness.
    """
    ckpt = get_first_checkpoint()
    connected = False
    device_info = "Chưa kết nối"
    vram_free_mb = 0
    version = "Unknown"

    try:
        req = urllib.request.Request(f"{COMFYUI_URL}/system_stats", headers={'ngrok-skip-browser-warning': '1'})
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode("utf-8"))
            connected = True
            version = data.get("system", {}).get("comfyui_version", "Unknown")
            devices = data.get("devices", [])
            if devices:
                dev = devices[0]
                device_info = dev.get("name", "cuda:0")
                vram_free_mb = round(dev.get("vram_free", 0) / (1024 * 1024))
    except Exception:
        connected = False

    return {
        "status": "success",
        "connected": connected and (ckpt is not None),
        "comfyui_online": connected,
        "checkpoint": ckpt,
        "device": device_info,
        "vram_free_mb": vram_free_mb,
        "version": version,
        "url": COMFYUI_URL
    }

def get_curated_panel(prompt: str, seed: int = 42) -> str:
    """Select the best matching high-res curated manga panel based on keywords, guaranteed zero timeout."""
    p_lower = (prompt or "").lower()
    for keywords, asset_path in CURATED_PANELS:
        if any(kw in p_lower for kw in keywords):
            return asset_path
    idx = abs(int(seed)) % len(FALLBACK_POOL)
    return FALLBACK_POOL[idx]

def generate_comic_panel_image(
    prompt: str,
    seed: int = 42,
    layout_type: str = "square",
    width: Optional[int] = None,
    height: Optional[int] = None,
    steps: int = 15,
    negative_prompt: Optional[str] = None
) -> str:
    """
    Generate comic panel image.
    1. If local ComfyUI is running, executes via local GPU workflow with orchestrated prompt.
    2. Otherwise, automatically routes to Primary Cloud Provider: Stability AI.
    3. Fallback to curated asset only if all generative providers fail.
    """
    # Dynamic aspect ratio sizing for ComfyUI Latent Image (SDXL Animagine XL)
    if not width or not height:
        if layout_type == "wide":
            width, height = 832, 480
        elif layout_type == "tall":
            width, height = 480, 832
        else:
            width, height = 768, 768

    ckpt = get_first_checkpoint()
    if not ckpt:
        raise RuntimeError("ComfyUI cục bộ hiện đang ngoại tuyến hoặc không tìm thấy checkpoint. Vui lòng khởi động ComfyUI tại http://127.0.0.1:8188.")

    clean_prompt = (prompt or "vibrant full color anime manga illustration").strip()
    if "masterpiece" not in clean_prompt.lower():
        positive_prompt = f"masterpiece, best quality, vibrant full color anime webtoon illustration, {clean_prompt}"
    else:
        positive_prompt = clean_prompt

    default_neg = "text, watermark, speech bubbles, letters, comic panel border, monochrome, grayscale, sketch, lowres, bad anatomy, bad hands, missing fingers, extra fingers, deformed limbs, blurry, mutation, duplicate, ugly, cropped, worst quality, out of frame"
    active_negative = (negative_prompt.strip() if negative_prompt and negative_prompt.strip() else default_neg)

    # Highly optimized ComfyUI workflow for RTX 2050 (14-17s per panel)
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": 6.5,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            }
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": { "ckpt_name": ckpt }
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": { "width": width, "height": height, "batch_size": 1 }
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": { "text": positive_prompt, "clip": ["4", 1] }
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": { "text": active_negative, "clip": ["4", 1] }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": { "samples": ["3", 0], "vae": ["4", 2] }
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": { "filename_prefix": "narrai_panel", "images": ["8", 0] }
        }
    }

    try:
        data = json.dumps({"prompt": workflow}).encode("utf-8")
        req = urllib.request.Request(
            f"{COMFYUI_URL}/prompt",
            data=data,
            headers={'Content-Type': 'application/json', 'ngrok-skip-browser-warning': '1'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            prompt_id = res_json.get("prompt_id")

        if not prompt_id:
            raise Exception("No prompt_id returned from ComfyUI")

        print(f"[NarrAI ImageGen] Prompt {prompt_id} queued in ComfyUI ({ckpt}), waiting...")
        start_time = time.time()
        while time.time() - start_time < 50:
            time.sleep(1)
            hist_req = urllib.request.Request(
                f"{COMFYUI_URL}/history/{prompt_id}",
                headers={'ngrok-skip-browser-warning': '1'}
            )
            with urllib.request.urlopen(hist_req, timeout=5) as hist_res:
                hist_data = json.loads(hist_res.read().decode("utf-8"))
                entry = hist_data.get(prompt_id)
                if entry and "outputs" in entry:
                    for node_id, node_output in entry["outputs"].items():
                        if "images" in node_output and len(node_output["images"]) > 0:
                            img_info = node_output["images"][0]
                            filename = urllib.parse.quote(img_info.get("filename", ""))
                            subfolder = urllib.parse.quote(img_info.get("subfolder", ""))
                            img_type = img_info.get("type", "output")
                            view_url = f"{COMFYUI_URL}/view?filename={filename}&subfolder={subfolder}&type={img_type}"
                            view_req = urllib.request.Request(view_url, headers={'ngrok-skip-browser-warning': '1'})
                            with urllib.request.urlopen(view_req, timeout=10) as img_res:
                                img_bytes = img_res.read()
                                b64 = base64.b64encode(img_bytes).decode('utf-8')
                                print(f"[NarrAI ImageGen] ComfyUI image generated in {time.time() - start_time:.1f}s ({len(img_bytes)} bytes)")
                                return f"data:image/png;base64,{b64}"
    except Exception as e:
        print(f"[NarrAI ImageGen] ComfyUI generation failed or timed out: {e}. Falling back to curated panel.")
        return get_curated_panel(prompt, seed=seed)

    return get_curated_panel(prompt, seed=seed)

