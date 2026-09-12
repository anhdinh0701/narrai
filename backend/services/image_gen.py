import urllib.request
import urllib.parse
import json
import time
import base64

import os

COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")

def get_first_checkpoint():
    """Fetch available checkpoints and return the first one."""
    try:
        req = urllib.request.Request(f"{COMFYUI_URL}/object_info/CheckpointLoaderSimple")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            ckpt_list = data.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {}).get("ckpt_name", [[]])[0]
            if isinstance(ckpt_list, list) and len(ckpt_list) > 0:
                return ckpt_list[0]
    except Exception as e:
        print(f"Error fetching checkpoints: {e}")
    return None

def generate_comic_panel_image(prompt: str, seed: int = 42) -> str:
    """Generate comic panel image using local ComfyUI via API"""
    ckpt = get_first_checkpoint()
    if not ckpt:
        print("Warning: Could not connect to ComfyUI or no checkpoints found. Using Pollinations fallback.")
        safe_prompt = urllib.parse.quote(prompt.strip() or "comic manga scene")
        return f"https://image.pollinations.ai/prompt/{safe_prompt}?width=800&height=800&nologo=true&seed={seed}"

    # Basic workflow (KSampler + Checkpoint + CLIPTextEncode + VAE)
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed, "steps": 20, "cfg": 7, "sampler_name": "euler", "scheduler": "normal",
                "denoise": 1, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]
            }
        },
        "4": { "class_type": "CheckpointLoaderSimple", "inputs": { "ckpt_name": ckpt } },
        "5": { "class_type": "EmptyLatentImage", "inputs": { "width": 832, "height": 1216, "batch_size": 1 } },
        "6": { "class_type": "CLIPTextEncode", "inputs": { "text": prompt + ", masterpiece, best quality, highly detailed, comic, manga", "clip": ["4", 1] } },
        "7": { "class_type": "CLIPTextEncode", "inputs": { "text": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, username, blurry", "clip": ["4", 1] } },
        "8": { "class_type": "VAEDecode", "inputs": { "samples": ["3", 0], "vae": ["4", 2] } },
        "9": { "class_type": "SaveImage", "inputs": { "filename_prefix": "narrai", "images": ["8", 0] } }
    }

    try:
        # Submit prompt
        data = json.dumps({"prompt": workflow}).encode("utf-8")
        req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            prompt_id = res_json.get("prompt_id")

        if not prompt_id:
            raise Exception("No prompt_id returned")

        # Poll history
        start_time = time.time()
        while time.time() - start_time < 300: # 5 mins timeout
            time.sleep(1)
            hist_req = urllib.request.Request(f"{COMFYUI_URL}/history/{prompt_id}")
            with urllib.request.urlopen(hist_req) as hist_res:
                hist_data = json.loads(hist_res.read().decode("utf-8"))
                
                entry = hist_data.get(prompt_id)
                if entry and "outputs" in entry:
                    # Find image
                    for node_id, node_output in entry["outputs"].items():
                        if "images" in node_output and len(node_output["images"]) > 0:
                            img_info = node_output["images"][0]
                            # Fetch image
                            filename = urllib.parse.quote(img_info.get("filename", ""))
                            subfolder = urllib.parse.quote(img_info.get("subfolder", ""))
                            img_type = img_info.get("type", "output")
                            view_url = f"{COMFYUI_URL}/view?filename={filename}&subfolder={subfolder}&type={img_type}"
                            
                            with urllib.request.urlopen(view_url) as img_res:
                                img_bytes = img_res.read()
                                b64 = base64.b64encode(img_bytes).decode('utf-8')
                                return f"data:image/png;base64,{b64}"

                if entry and entry.get("status", {}).get("status_str") == "error":
                    raise Exception("ComfyUI reported an error")
                    
    except Exception as e:
        print(f"Error during ComfyUI generation: {e}")
        # Fallback to pollinations
        safe_prompt = urllib.parse.quote(prompt.strip() or "comic manga scene")
        return f"https://image.pollinations.ai/prompt/{safe_prompt}?width=800&height=800&nologo=true&seed={seed}"

    # Timeout fallback
    safe_prompt = urllib.parse.quote(prompt.strip() or "comic manga scene")
    return f"https://image.pollinations.ai/prompt/{safe_prompt}?width=800&height=800&nologo=true&seed={seed}"
