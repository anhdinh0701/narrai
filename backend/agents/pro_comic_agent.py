import os
import json
import re
import logging
from typing import List, Dict, Any, Optional

try:
    from llm.groq_client import GroqClient
except (ImportError, ModuleNotFoundError):
    from backend.llm.groq_client import GroqClient

logger = logging.getLogger(__name__)

PRIMARY_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "qwen/qwen3.8-27b"

PRO_COMIC_SYSTEM_PROMPT = """Bạn là Đạo diễn Truyện tranh & Chuyên gia Điều phối Prompt ComfyUI / AI Generation cấp cao (Comic Director, Storyboard Master & ComfyUI Prompt Orchestrator).

NHIỆM VỤ TỐI THƯỢNG:
Chuyển thể cốt truyện tiếng Việt thành kịch bản phân cảnh 10 ĐẾN 16 KHUNG TRANH (Panels) hoàn chỉnh, liền mạch 100%, bám sát diễn biến câu chuyện, đồng thời điều phối prompt chuyên biệt cho mô hình ComfyUI / Stable Diffusion Anime Webtoon để tranh sinh ra chuẩn xác từng chi tiết, không bị đứt đoạn, nhân vật nhất quán và lời thoại ăn khớp nhịp nhàng.

NGUYÊN TẮC BẮT BUỘC ĐẠO DIỄN:
1. PHÂN CẢNH 3 HỒI MẠCH LẠC (STORY PROGRESSION):
   - Hồi 1 (Khởi nguồn & Gặp gỡ - Khung 1 đến 3/4): Đại cảnh thiết lập bối cảnh, giới thiệu mục tiêu của nhân vật chính, biến cố kích hoạt, cuộc hội ngộ hoặc phát hiện đầu tiên.
   - Hồi 2 (Thử thách & Cao trào xung đột - Khung 4/5 đến 8/10): Đối mặt cạm bẫy, kẻ thù thức tỉnh, cận cảnh giao tranh, nhân vật thi triển chiêu thức võ công/phép thuật, biểu cảm căng thẳng dồn dập.
   - Hồi 3 (Hóa giải & Vươn tới tương lai - Khung 9/11 đến 12/16): Đòn đánh quyết định hoặc sự hòa giải phong ấn, thu nhận bí kíp/bảo vật, niềm vui chiến thắng, đại cảnh kết màn hướng về giang sơn vạn dặm.

2. BẢNG THIẾT KẾ NHÂN VẬT BẤT BIẾN (CHARACTER BIBLE):
   - Mỗi nhân vật có ID riêng (CHAR_001, CHAR_002), tên tiếng Việt, tuổi, tính cách.
   - Ngoại hình chi tiết (tóc, mắt, khuôn mặt, vóc dáng, vết sẹo/đặc điểm nhận dạng).
   - Trang phục đặc trưng cố định (màu sắc chiến bào, thắt lưng, găng tay, ngọc bội, vũ khí).
   - comfy_tags: Tập hợp từ khóa tiếng Anh đặc tả nhân vật dạng Booru/Danbooru + Natural prompt cho ComfyUI (VD: `CHAR_001, 1boy, athletic lean build, short spiky black hair, sharp dark blue eyes, small scar on left cheek, dark navy blue martial arts combat robe, silver dragon embroidery, black leather bracers, holding glowing silver sword`).

3. BẢNG THIẾT KẾ BỐI CẢNH (LOCATION BIBLE):
   - ID bối cảnh (LOC_001, LOC_002), tên tiếng Việt, kiến trúc, ánh sáng, bầu không khí.
   - comfy_tags: Từ khóa tiếng Anh mô tả bối cảnh cho ComfyUI (VD: `LOC_001, ancient mountain cliff summit above sea of clouds, floating ancient stone ruins, radiant golden sunrise rays breaking through purple morning mist, ethereal fantasy world, vibrant colors`).

4. ĐỒNG NHẤT TUYỆT ĐỐI GIỮA CÁC KHUNG TRANH (CONTINUITY):
   - Mỗi khung tranh PHẢI ghi rõ `previous_panel_summary` (tóm tắt logic kết nối từ khung trước) và `continuity_rules` (kiểm tra trang phục, vũ khí, vị trí nhân vật không bị lệch).

5. LỜI THOẠI & DẪN TRUYỆN SẮC SẢO:
   - `speaker`: Người nói (hoặc "Người dẫn truyện").
   - `dialogue`: Lời thoại tiếng Việt giàu cảm xúc, tự nhiên, thể hiện rõ thần thái nhân vật.
   - `bubble_type`: "speech" (nói) | "shout" (hét/ra chiêu) | "thought" (suy nghĩ) | "whisper" (thì thầm) | "narration" (lời dẫn) | "none".
   - `narration`: Lời dẫn truyện tiếng Việt tăng chiều sâu văn học.

6. ĐIỀU PHỐI PROMPT COMFYUI CHUYÊN SÂU (COMFYUI PROMPT ORCHESTRATION):
   - `comfy_prompt`: Prompt tiếng Anh được cấu trúc chuẩn mực cho ComfyUI:
     `masterpiece, best quality, vibrant full color anime webtoon art, [camera angle], [character comfy_tags], [specific physical action & facial expression], [location comfy_tags & lighting], dynamic atmospheric lighting, 8k digital illustration, highly detailed, no text, no watermark, no speech bubbles`
   - TUYỆT ĐỐI KHÔNG chứa chữ (text, letters), bong bóng thoại, hay chia đôi khung ảnh (split screen). Frontend sẽ tự động vẽ bong bóng thoại HTML/CSS đè lên tranh!

OUTPUT FORMAT (STRICT JSON ONLY, không bọc ```json, không thêm chữ dẫn giải trước hoặc sau):
{
  "character_bible": [
    {
      "char_id": "CHAR_001",
      "name": "Nguyễn Minh",
      "gender": "male",
      "age": "20",
      "appearance": "handsome young man, short spiky jet-black hair, sharp deep blue eyes, athletic build, scar on left cheek",
      "costume": "dark navy martial arts combat robe with silver dragon embroidery, black leather belt, fingerless bracers",
      "personality": "kiên định, dũng cảm, trọng nghĩa khí",
      "comfy_tags": "CHAR_001, 1boy, handsome young hero, short spiky jet-black hair, sharp deep blue eyes, small scar on left cheek, dark navy martial arts robe with silver dragon embroidery, athletic build, vibrant full color anime webtoon art"
    }
  ],
  "location_bible": [
    {
      "loc_id": "LOC_001",
      "name": "Đỉnh núi Vân Phong",
      "architecture": "ancient celestial mountain peak with floating stone monoliths",
      "lighting": "golden dawn sunlight breaking through purple misty clouds",
      "atmosphere": "mystic, epic, breathtaking, ethereal atmosphere",
      "comfy_tags": "LOC_001, ancient mountain cliff summit above sea of clouds, floating ancient stone ruins, radiant golden sunrise rays breaking through purple morning mist, ethereal fantasy world, vibrant colors"
    }
  ],
  "story_setting": "Thế giới huyền huyễn tu tiên nơi đan xen giữa bí ẩn thượng cổ và chí khí anh hùng.",
  "negative_prompt": "text, watermark, speech bubbles, letters, comic panel border, split screen, monochrome, grayscale, sketch, lowres, bad anatomy, bad hands, missing fingers, extra fingers, deformed limbs, blurry, mutation, duplicate, ugly, cropped, worst quality, out of frame",
  "panels": [
    {
      "panel_index": 1,
      "scene_id": "S01",
      "location_id": "LOC_001",
      "location_name": "Đỉnh núi Vân Phong lúc bình minh",
      "time_of_day": "dawn",
      "weather": "misty sunrise",
      "characters": ["CHAR_001"],
      "character_names": "Nguyễn Minh",
      "action": "Nguyễn Minh đứng trên mỏm đá ngắm nhìn ngôi đền bay thượng cổ lấp lánh giữa biển mây",
      "emotion": "kinh ngạc, xúc động",
      "camera_angle": "cinematic wide angle low shot",
      "continuity_rules": "Nguyễn Minh mặc chiến bào xanh đen thêu rồng bạc, tóc đen ngắn bay nhẹ trong gió sớm.",
      "speaker": "Nguyễn Minh",
      "dialogue": "Cuối cùng ta cũng đã tìm thấy Đền Thượng Cổ...",
      "bubble_type": "speech",
      "narration": "Sau ba ngày ba đêm vượt biển mây hiểm trở, cánh cửa định mệnh đã hiện ra trước mắt.",
      "layout_type": "wide",
      "comfy_prompt": "masterpiece, best quality, vibrant full color anime webtoon art, cinematic wide angle low shot, CHAR_001 handsome young hero, short spiky jet-black hair, sharp dark blue eyes, dark navy martial arts robe with silver trims, standing heroically on jagged mountain cliff edge at dawn looking toward massive floating ancient celestial temple in golden clouds, breathtaking sunrise lighting, vibrant colors, 8k digital illustration, no text, no speech bubbles"
    }
  ]
}
"""

class ProComicAgent:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY_COMIC") or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Missing GROQ_API_KEY")
        self.api_key = api_key
        self.llm = GroqClient(model_name=PRIMARY_MODEL, api_key=api_key)
        try:
            self.fallback_llm = GroqClient(model_name=FALLBACK_MODEL, api_key=api_key)
        except Exception:
            self.fallback_llm = self.llm

    def generate(self, story_text: str, genre: str = "", style: str = "") -> Dict[str, Any]:
        trimmed = (story_text or "").strip()[:6000]
        if not trimmed:
            trimmed = "Một chàng trai trẻ tu tiên dũng cảm bước vào di tích thượng cổ, tìm kiếm bảo vật giải cứu sư môn."

        genre_hint = f"\nThể loại: {genre}" if genre else ""
        style_hint = f"\nPhong cách hội họa: {style}" if style else ""
        user_prompt = (
            f"Hãy phân tích và chuyển thể câu chuyện sau thành kịch bản truyện tranh 10-16 khung tranh (khuyến nghị 12-16 khung), "
            f"điều phối Character Bible, Location Bible và ComfyUI prompt chi tiết cho từng khung tranh:{genre_hint}{style_hint}\n\n{trimmed}"
        )

        messages = [
            {"role": "system", "content": PRO_COMIC_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        # 1. Try Primary ChatGPT-Class Model (openai/gpt-oss-120b) with json_object mode
        for client in (self.llm, self.fallback_llm):
            try:
                raw = client.chat(
                    messages=messages,
                    temperature=0.5,
                    max_tokens=6000,
                    response_format={"type": "json_object"}
                )
                data = self._parse_or_repair_json(raw)
                if data and isinstance(data.get("panels"), list) and len(data["panels"]) >= 4:
                    return self._process_script_data(data, style)
            except Exception as e:
                logger.warning(f"[ProComicAgent] LLM {getattr(client, 'model', 'unknown')} failed: {e}")

        logger.warning("[ProComicAgent] All LLMs failed or returned invalid JSON. Using structured 12-panel fallback.")
        return self._get_fallback()

    def _parse_or_repair_json(self, raw: str) -> Optional[Dict[str, Any]]:
        """Parses JSON or repairs truncated JSON response from LLM."""
        if not raw:
            return None
        # 1. Direct parse
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except Exception:
                pass

        # 2. Clean trailing commas
        cleaned = re.sub(r',\s*([\]\}])', r'\1', raw)
        m = re.search(r'\{[\s\S]*\}', cleaned)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass

        # 3. Truncation salvage: close open panel brackets
        lines = raw.splitlines()
        for cut_idx in range(len(lines), max(0, len(lines) - 40), -1):
            candidate = "\n".join(lines[:cut_idx]).strip().rstrip(",")
            for closing in ("]\n}", "\n}", "\"]\n}", "}\n]\n}"):
                try:
                    candidate_fixed = re.sub(r',\s*([\]\}])', r'\1', candidate + closing)
                    m = re.search(r'\{[\s\S]*\}', candidate_fixed)
                    if m:
                        data = json.loads(m.group(0))
                        if isinstance(data.get("panels"), list) and len(data["panels"]) >= 4:
                            return data
                except Exception:
                    continue

        return None

    def _process_script_data(self, data: Dict[str, Any], style: str = "") -> Dict[str, Any]:
        """Validates, caps panel count to 10-16, and enriches image prompts with Bibles."""
        char_bible = data.get("character_bible", [])
        if not isinstance(char_bible, list):
            char_bible = []
        loc_bible = data.get("location_bible", [])
        if not isinstance(loc_bible, list):
            loc_bible = []

        char_map = {c.get("char_id", f"CHAR_{i+1:03d}"): c for i, c in enumerate(char_bible)}
        loc_map = {l.get("loc_id", f"LOC_{i+1:03d}"): l for i, l in enumerate(loc_bible)}

        root_negative = data.get("negative_prompt", "")

        panels = data.get("panels", [])
        if len(panels) > 16:
            panels = panels[:16]

        validated_panels = []
        for i, p in enumerate(panels):
            enriched = self._enrich_panel(p, i + 1, char_map, loc_map, style, root_negative=root_negative)
            validated_panels.append(enriched)

        data["character_bible"] = char_bible
        data["location_bible"] = loc_bible
        data["panels"] = validated_panels
        return data

    def _enrich_panel(
        self,
        panel: Dict[str, Any],
        index: int,
        char_map: Dict[str, Any],
        loc_map: Dict[str, Any],
        style: str = "",
        root_negative: str = ""
    ) -> Dict[str, Any]:
        """Ensures panel has all required fields and assembles a consistent, full-color ComfyUI prompt."""
        panel_index = index
        layout = panel.get("layout_type") or "square"
        if layout not in ("wide", "tall", "square"):
            layout = "square"

        bubble_type = panel.get("bubble_type") or "speech"
        if bubble_type not in ("speech", "shout", "thought", "whisper", "narration", "none"):
            bubble_type = "speech" if panel.get("dialogue") else "none"

        # Character references
        p_chars = panel.get("characters", [])
        if isinstance(p_chars, str):
            p_chars = [p_chars]

        char_prompts = []
        for cid in p_chars:
            if cid in char_map:
                c_info = char_map[cid]
                char_prompts.append(
                    c_info.get("comfy_tags") or c_info.get("base_prompt") or f"{c_info.get('name')}, {c_info.get('appearance')}, {c_info.get('costume')}"
                )

        # Location references
        loc_id = panel.get("location_id", "")
        loc_prompt = ""
        if loc_id in loc_map:
            l_info = loc_map[loc_id]
            loc_prompt = l_info.get("comfy_tags") or l_info.get("base_prompt") or f"{l_info.get('architecture')}, {l_info.get('lighting')}"

        # Orchestrated prompt handling: check comfy_prompt first, then image_prompt
        raw_prompt = (panel.get("comfy_prompt") or panel.get("image_prompt") or "").strip()
        camera = panel.get("camera_angle", "cinematic medium shot")
        action_en = panel.get("action", "")

        # Base style tokens enforcing full-color webtoon/anime illustration without text
        style_tokens = "masterpiece, best quality, vibrant full color anime manga illustration, detailed webtoon art, dynamic lighting, 8k digital painting, clean linework, no text, no watermark, no speech bubbles"
        
        assembled_parts = [style_tokens, camera]
        if char_prompts:
            assembled_parts.extend(char_prompts)
        if raw_prompt and len(raw_prompt) > 20:
            assembled_parts.append(raw_prompt)
        elif action_en:
            assembled_parts.append(f"character action: {action_en}")
        if loc_prompt:
            assembled_parts.append(f"background: {loc_prompt}")

        final_prompt = ", ".join([p.strip().rstrip(",") for p in assembled_parts if p.strip()])

        default_negative = (
            root_negative.strip() if root_negative and root_negative.strip() else (
                "text, watermark, speech bubbles, letters, comic panel border, split screen, monochrome, "
                "grayscale, sketch, lowres, bad anatomy, bad hands, missing fingers, extra fingers, "
                "deformed limbs, blurry, mutation, duplicate, ugly, cropped, worst quality, out of frame"
            )
        )
        negative_prompt = (panel.get("comfy_negative_prompt") or panel.get("negative_prompt") or default_negative).strip()

        return {
            "panel_index": panel_index,
            "scene_id": panel.get("scene_id", f"S{((panel_index - 1) // 3) + 1:02d}"),
            "location_id": loc_id,
            "location_name": panel.get("location_name") or panel.get("location") or "Bối cảnh câu chuyện",
            "time_of_day": panel.get("time_of_day", "day"),
            "weather": panel.get("weather", "clear"),
            "characters": p_chars,
            "character_names": panel.get("character_names") or ", ".join([char_map[c].get("name", c) for c in p_chars if c in char_map]),
            "action": panel.get("action", "Nhân vật hành động"),
            "emotion": panel.get("emotion", "tập trung"),
            "camera_angle": camera,
            "previous_panel_summary": panel.get("previous_panel_summary", ""),
            "continuity_rules": panel.get("continuity_rules", ""),
            "speaker": panel.get("speaker", ""),
            "dialogue": panel.get("dialogue") or panel.get("dialogue_text") or "",
            "bubble_type": bubble_type,
            "narration": panel.get("narration", ""),
            "layout_type": layout,
            "image_prompt": final_prompt,
            "comfy_prompt": final_prompt,
            "comfy_negative_prompt": negative_prompt,
            "negative_prompt": negative_prompt
        }

    def _get_fallback(self) -> Dict[str, Any]:
        """Rich 12-panel fallback ensuring coherent 3-act story, full-color prompts, and consistent characters."""
        return {
            "character_bible": [
                {
                    "char_id": "CHAR_001",
                    "name": "Nguyễn Minh",
                    "gender": "male",
                    "age": "20",
                    "appearance": "handsome young man, short spiky jet-black hair, sharp deep blue eyes, athletic build, scar on left cheek",
                    "costume": "dark navy martial arts combat robe with silver dragon embroidery, black leather belt, fingerless bracers",
                    "personality": "kiên định, dũng cảm, trọng nghĩa khí",
                    "base_prompt": "CHAR_001, handsome young hero, short spiky jet-black hair, sharp deep blue eyes, small scar on left cheek, dark navy martial arts robe with silver dragon embroidery, athletic build, vibrant full color anime webtoon art"
                },
                {
                    "char_id": "CHAR_002",
                    "name": "Linh Nhi",
                    "gender": "female",
                    "age": "19",
                    "appearance": "beautiful young anime woman, long flowing chestnut brown hair with jade lotus hairpin, radiant amber eyes, graceful expression",
                    "costume": "elegant white and soft pink celestial hanfu dress, embroidered lotus patterns, flowing silk ribbons",
                    "personality": "thông minh, nhanh nhẹn, tinh tế",
                    "base_prompt": "CHAR_002, beautiful anime girl, long flowing chestnut brown hair with jade lotus hairpin, luminous amber eyes, elegant white and pastel pink celestial silk dress, gentle yet resolute look, vibrant full color anime webtoon art"
                }
            ],
            "location_bible": [
                {
                    "loc_id": "LOC_001",
                    "name": "Đỉnh núi Vân Phong",
                    "architecture": "ancient celestial mountain cliff overlooking floating ruins",
                    "lighting": "golden dawn sunlight through purple morning mist",
                    "atmosphere": "ethereal, majestic, mystical",
                    "base_prompt": "LOC_001, towering jagged mountain cliff edge, sea of swirling clouds below, ancient floating stone ruins, radiant golden sunrise rays, ethereal mystical fantasy atmosphere, vibrant colors"
                },
                {
                    "loc_id": "LOC_002",
                    "name": "Điện Thần Thượng Cổ",
                    "architecture": "grand ancient palace hall with monumental glowing carved pillars",
                    "lighting": "celestial starry glow and divine golden luminescence",
                    "atmosphere": "sacred, awe-inspiring, cosmic",
                    "base_prompt": "LOC_002, majestic ancient temple interior, towering marble pillars carved with glowing runes, celestial starlight and golden particles, divine sacred aura, vibrant colors"
                }
            ],
            "story_setting": "Thế giới huyền huyễn nơi các bậc anh hùng tìm kiếm bí kíp thất truyền để bảo vệ thái bình lục địa.",
            "panels": [
                {
                    "panel_index": 1,
                    "scene_id": "S01",
                    "location_id": "LOC_001",
                    "location_name": "Đỉnh núi Vân Phong lúc bình minh",
                    "time_of_day": "dawn",
                    "weather": "misty golden sunrise",
                    "characters": ["CHAR_001"],
                    "character_names": "Nguyễn Minh",
                    "action": "Đứng bên bờ vực ngắm ngôi đền bay trên biển mây",
                    "emotion": "kinh ngạc, xúc động",
                    "camera_angle": "cinematic wide angle low shot",
                    "previous_panel_summary": "Khởi đầu hành trình, nhân vật đặt chân lên đỉnh núi thiêng.",
                    "continuity_rules": "Nguyễn Minh mặc chiến bào xanh đen thêu rồng bạc, tóc đen ngắn bay nhẹ trong gió.",
                    "speaker": "Nguyễn Minh",
                    "dialogue": "Cuối cùng ta cũng đã tìm thấy Đền Thượng Cổ...",
                    "bubble_type": "speech",
                    "narration": "Sau ba ngày ba đêm vượt qua biển mây hiểm trở, cánh cổng huyền thoại đã hiện ra.",
                    "layout_type": "wide",
                    "image_prompt": "masterpiece, vibrant full color anime manga illustration, cinematic wide angle low shot. CHAR_001 handsome young hero, short spiky jet-black hair, sharp deep blue eyes, small scar on left cheek, dark navy martial arts robe with silver dragon embroidery, standing heroically on cliff edge looking at glowing celestial floating temple in clouds, golden sunrise rays, highly detailed 8k, no text, no speech bubbles"
                },
                {
                    "panel_index": 2,
                    "scene_id": "S01",
                    "location_id": "LOC_001",
                    "location_name": "Bờ vực mây mù",
                    "time_of_day": "morning",
                    "weather": "clear sunrise",
                    "characters": ["CHAR_001"],
                    "character_names": "Nguyễn Minh",
                    "action": "Nắm chặt chuôi kiếm bạc, ánh mắt bừng sáng quyết tâm",
                    "emotion": "kiên định, quật cường",
                    "camera_angle": "dramatic close-up shot",
                    "previous_panel_summary": "Nguyễn Minh nhìn thấy mục tiêu phía xa.",
                    "continuity_rules": "Giữ nguyên vết sẹo má trái và chiến bào xanh đen.",
                    "speaker": "Nguyễn Minh",
                    "dialogue": "Bất luận phía trước là cạm bẫy hay thử thách, ta quyết không lùi bước!",
                    "bubble_type": "shout",
                    "narration": "",
                    "layout_type": "square",
                    "image_prompt": "masterpiece, vibrant full color anime manga illustration, dramatic close-up shot. CHAR_001 handsome young hero face, sharp glowing deep blue eyes full of resolve, short spiky black hair blown by wind, hand tightly gripping silver sword hilt, dynamic angle, vibrant lighting, highly detailed 8k, no text, no speech bubbles"
                },
                {
                    "panel_index": 3,
                    "scene_id": "S01",
                    "location_id": "LOC_001",
                    "location_name": "Cầu đá lơ lửng giữa trời",
                    "time_of_day": "morning",
                    "weather": "windy misty",
                    "characters": ["CHAR_002"],
                    "character_names": "Linh Nhi",
                    "action": "Linh Nhi bất ngờ xuất hiện nơi đầu cầu đá với tà áo tung bay",
                    "emotion": "thanh thoát, cảnh báo",
                    "camera_angle": "medium full shot",
                    "previous_panel_summary": "Nguyễn Minh chuẩn bị bước vào cây cầu hiểm trở.",
                    "continuity_rules": "Linh Nhi diện y phục tiên hiệp trắng hồng, trâm hoa sen ngọc bích trên tóc.",
                    "speaker": "Linh Nhi",
                    "dialogue": "Khoan đã! Cây cầu này ẩn chứa trận pháp thượng cổ ngàn năm đấy.",
                    "bubble_type": "speech",
                    "narration": "Một giọng nói trong trẻo bỗng vang lên từ phía sau làn sương trắng...",
                    "layout_type": "tall",
                    "image_prompt": "masterpiece, vibrant full color anime manga illustration, medium full shot. CHAR_002 beautiful anime girl, long chestnut brown hair with jade lotus hairpin, luminous amber eyes, elegant white and pastel pink silk dress flowing gracefully in mountain wind, standing at entrance of ancient floating bridge, soft morning mist, vibrant colors, 8k, no text, no speech bubbles"
                },
                {
                    "panel_index": 4,
                    "scene_id": "S01",
                    "location_id": "LOC_001",
                    "location_name": "Đầu cầu đá cổ",
                    "time_of_day": "morning",
                    "weather": "clear",
                    "characters": ["CHAR_001", "CHAR_002"],
                    "character_names": "Nguyễn Minh, Linh Nhi",
                    "action": "Nguyễn Minh xoay người cảnh giác, đối diện với Linh Nhi",
                    "emotion": "ngạc nhiên, đề phòng",
                    "camera_angle": "cinematic two-shot over the shoulder",
                    "previous_panel_summary": "Linh Nhi vừa xuất hiện cảnh báo Nguyễn Minh.",
                    "continuity_rules": "Nguyễn Minh bên trái trong áo xanh đen; Linh Nhi đối diện trong xiêm y trắng hồng.",
                    "speaker": "Nguyễn Minh",
                    "dialogue": "Nàng là ai? Sao lại xuất hiện ở cấm địa hiểm ác này?",
                    "bubble_type": "speech",
                    "narration": "",
                    "layout_type": "wide",
                    "image_prompt": "masterpiece, vibrant full color anime manga illustration, cinematic two-shot over the shoulder. Two characters facing each other on ancient stone bridge: CHAR_001 in dark navy martial arts robe on guard with hand on sword, facing CHAR_002 in flowing white-pink dress with gentle smile, breathtaking cloudscape background, vibrant lighting, highly detailed 8k, no text, no speech bubbles"
                },
                {
                    "panel_index": 5,
                    "scene_id": "S02",
                    "location_id": "LOC_002",
                    "location_name": "Cổng Điện Thần Thượng Cổ",
                    "time_of_day": "noon",
                    "weather": "mystical starlight",
                    "characters": ["CHAR_001", "CHAR_002"],
                    "character_names": "Nguyễn Minh, Linh Nhi",
                    "action": "Linh Nhi kết ấn kích hoạt cổ ngọc mở toang cánh cổng thần bí",
                    "emotion": "tập trung cao độ, hân hoan",
                    "camera_angle": "dynamic medium shot",
                    "previous_panel_summary": "Cả hai hợp sức vượt qua cầu đá tiến đến trước cổng điện.",
                    "continuity_rules": "Giữ nguyên trang phục đặc trưng của cả hai nhân vật.",
                    "speaker": "Linh Nhi",
                    "dialogue": "Trận pháp khai mở! Cánh cửa dẫn vào cội nguồn sức mạnh đã hiện ra!",
                    "bubble_type": "shout",
                    "narration": "Ánh sáng ngọc bích rực rỡ xua tan bóng tối ngàn năm...",
                    "layout_type": "square",
                    "image_prompt": "masterpiece, vibrant full color anime manga illustration, dynamic medium shot. CHAR_002 holding glowing emerald jade artifact emitting brilliant green light runes, CHAR_001 beside her in defensive stance sword drawn, ancient massive temple gates slowly unlocking with divine golden beams, particle effects, vibrant colors, 8k, no text, no speech bubbles"
                },
                {
                    "panel_index": 6,
                    "scene_id": "S02",
                    "location_id": "LOC_002",
                    "location_name": "Đại Điện Cổ",
                    "time_of_day": "noon",
                    "weather": "mystical starlight",
                    "characters": ["CHAR_001", "CHAR_002"],
                    "character_names": "Nguyễn Minh, Linh Nhi",
                    "action": "Cả hai cùng bước vào sảnh điện nguy nga, ánh mắt choáng ngợp trước những cột đá thần tích",
                    "emotion": "kinh ngạc, kính cẩn",
                    "camera_angle": "grand wide angle shot",
                    "previous_panel_summary": "Cánh cổng thần bí vừa mở toang.",
                    "continuity_rules": "Nguyễn Minh và Linh Nhi sánh vai bước qua ngưỡng cửa điện thần.",
                    "speaker": "Nguyễn Minh",
                    "dialogue": "Nơi này... tựa như đã ngủ quên từ vạn kiếp trước.",
                    "bubble_type": "whisper",
                    "narration": "Không gian tĩnh mịch ngập tràn cổ ngữ phát sáng lung linh.",
                    "layout_type": "wide",
                    "image_prompt": "masterpiece, vibrant full color anime manga illustration, grand wide angle shot. CHAR_001 and CHAR_002 stepping together into magnificent ancient temple hall, massive glowing marble pillars, mystical floating runic lanterns, golden stardust in air, breathtaking scale, 8k, no text, no speech bubbles"
                },
                {
                    "panel_index": 7,
                    "scene_id": "S02",
                    "location_id": "LOC_002",
                    "location_name": "Hành lang Thần Cổ",
                    "time_of_day": "afternoon",
                    "weather": "dim mystical light",
                    "characters": ["CHAR_001"],
                    "character_names": "Nguyễn Minh",
                    "action": "Nguyễn Minh vung kiếm chặn đứng cạm bẫy mũi tên ánh sáng để che chắn cho Linh Nhi",
                    "emotion": "quyết liệt, dũng cảm",
                    "camera_angle": "dynamic action shot",
                    "previous_panel_summary": "Cả hai đang di chuyển sâu vào hành lang điện thần.",
                    "continuity_rules": "Chiến bào xanh đen của Nguyễn Minh đón đầu hiểm nguy, kiếm bạc tỏa sáng.",
                    "speaker": "Nguyễn Minh",
                    "dialogue": "Cẩn thận! Trận pháp kích hoạt! Hãy đứng sau lưng ta!",
                    "bubble_type": "shout",
                    "narration": "Cạm bẫy cổ đại đồng loạt bừng tỉnh ngăn chặn kẻ đột nhập.",
                    "layout_type": "tall",
                    "image_prompt": "masterpiece, vibrant full color anime manga illustration, dynamic action shot. CHAR_001 handsome young hero in dark navy robe swinging gleaming silver sword to deflect showers of glowing crystal light arrows, azure sword trail, protective heroic pose, ancient stone corridor, dramatic sparks, 8k, no text, no speech bubbles"
                },
                {
                    "panel_index": 8,
                    "scene_id": "S02",
                    "location_id": "LOC_002",
                    "location_name": "Tiền sảnh Cấm Địa",
                    "time_of_day": "afternoon",
                    "weather": "shadowy ominous glow",
                    "characters": ["CHAR_001", "CHAR_002"],
                    "character_names": "Nguyễn Minh, Linh Nhi",
                    "action": "Thạch tượng thủ vệ khổng lồ mở bừng đôi mắt đỏ rực, chấn động cả sàn đá",
                    "emotion": "căng thẳng, cảnh giác cao độ",
                    "camera_angle": "dramatic low angle shot",
                    "previous_panel_summary": "Nguyễn Minh vừa phá vỡ cạm bẫy mũi tên ánh sáng.",
                    "continuity_rules": "Cả hai nhân vật đối diện với bóng dáng thạch tượng đồ sộ.",
                    "speaker": "Linh Nhi",
                    "dialogue": "Thạch Tượng Cổ Vệ ngàn năm đã thức tỉnh... Không thể đối kháng bằng sức mạnh thông thường!",
                    "bubble_type": "whisper",
                    "narration": "Tiếng gầm rú bằng đá rền vang làm rung chuyển nền móng điện thần.",
                    "layout_type": "wide",
                    "image_prompt": "masterpiece, vibrant full color anime manga illustration, dramatic low angle shot. Enormous ancient stone guardian titan with blazing crimson runic eyes rising from palace floor, CHAR_001 drawing sword and CHAR_002 preparing magic talisman, towering ominous presence, epic fantasy atmosphere, 8k, no text, no speech bubbles"
                },
                {
                    "panel_index": 9,
                    "scene_id": "S02",
                    "location_id": "LOC_002",
                    "location_name": "Chiến trường Thần Điện",
                    "time_of_day": "dusk",
                    "weather": "blazing energy storms",
                    "characters": ["CHAR_001"],
                    "character_names": "Nguyễn Minh",
                    "action": "Nguyễn Minh bật nhảy lên không trung, phóng xuất kiếm khí Thanh Long chém về phía thủ vệ",
                    "emotion": "hào hùng, bùng nổ sức mạnh",
                    "camera_angle": "extreme dynamic action shot",
                    "previous_panel_summary": "Thạch tượng khổng lồ tấn công dồn dập.",
                    "continuity_rules": "Kiếm bạc hóa thành luồng rồng xanh lam bao quanh Nguyễn Minh.",
                    "speaker": "Nguyễn Minh",
                    "dialogue": "Thanh Long Phá Thiên! Hãy mở đường cho chúng ta!",
                    "bubble_type": "shout",
                    "narration": "Kiếm ý tung hoành tạo thành một màn tráng quan tuyệt đỉnh.",
                    "layout_type": "tall",
                    "image_prompt": "masterpiece, vibrant full color anime manga illustration, extreme dynamic action shot. CHAR_001 leaping airborne with sword, radiating massive swirling silver-blue ethereal dragon aura, striking towards massive stone monster, glowing impact fissures, wind pressure tearing robes, highly detailed 8k, no text, no speech bubbles"
                },
                {
                    "panel_index": 10,
                    "scene_id": "S02",
                    "location_id": "LOC_002",
                    "location_name": "Trận Pháp Trung Tâm",
                    "time_of_day": "dusk",
                    "weather": "calm emerald luminescence",
                    "characters": ["CHAR_002"],
                    "character_names": "Linh Nhi",
                    "action": "Linh Nhi niệm phép ấn, hoa sen ngọc bích tỏa sáng xoa dịu cuồng nộ của thủ vệ",
                    "emotion": "tập trung thanh tịnh, từ bi",
                    "camera_angle": "luminous medium shot",
                    "previous_panel_summary": "Nguyễn Minh kìm chân thủ vệ bằng đòn kiếm rồng phá thiên.",
                    "continuity_rules": "Linh Nhi nâng cao ngọc bội hoa sen, dải lụa trắng hồng bồng bềnh trong ánh quang.",
                    "speaker": "Linh Nhi",
                    "dialogue": "Oán niệm ngàn năm... Hãy quy về tĩnh lặng!",
                    "bubble_type": "shout",
                    "narration": "Sự hòa hợp giữa sức mạnh cương trực và nhu thuận đã hóa giải phong ấn.",
                    "layout_type": "square",
                    "image_prompt": "masterpiece, vibrant full color anime manga illustration, luminous medium shot. CHAR_002 beautiful anime girl casting peaceful ancient seal, jade lotus amulet floating above her hands radiating brilliant concentric circles of emerald green light, calming the battle, elegant silk dress fluttering, serene expression, 8k, no text, no speech bubbles"
                },
                {
                    "panel_index": 11,
                    "scene_id": "S02",
                    "location_id": "LOC_002",
                    "location_name": "Tâm Điện Thần Thượng Cổ",
                    "time_of_day": "night",
                    "weather": "divine cosmic starlight",
                    "characters": ["CHAR_001", "CHAR_002"],
                    "character_names": "Nguyễn Minh, Linh Nhi",
                    "action": "Nguyễn Minh tiếp nhận cuộn bí kíp thần thoại tỏa sáng vàng kim đang từ từ hạ xuống bàn tay",
                    "emotion": "thiêng liêng, hạnh phúc, tin tưởng",
                    "camera_angle": "cinematic eye-level shot",
                    "previous_panel_summary": "Thủ vệ đã hóa giải phong ấn, cấm địa hoàn toàn mở lối.",
                    "continuity_rules": "Nguyễn Minh và Linh Nhi đứng bên nhau đón nhận bí kíp thần tích.",
                    "speaker": "Nguyễn Minh",
                    "dialogue": "Bí kíp Thượng Cổ... Cuối cùng ta đã có thể cứu vãn sự tồn vong của sư môn!",
                    "bubble_type": "speech",
                    "narration": "Ánh sáng thiêng liêng rọi sáng lòng dũng cảm và tinh thần nghĩa hiệp bất diệt.",
                    "layout_type": "square",
                    "image_prompt": "masterpiece, vibrant full color anime manga illustration, cinematic eye-level shot. CHAR_001 receiving glowing celestial golden scroll floating into his hands, CHAR_002 beside him smiling warmly with relieved graceful look, floating sacred dust particles and nebula aura, vibrant rich colors, 8k, no text, no speech bubbles"
                },
                {
                    "panel_index": 12,
                    "scene_id": "S02",
                    "location_id": "LOC_001",
                    "location_name": "Đỉnh núi Vân Phong dưới trời sao",
                    "time_of_day": "night",
                    "weather": "infinite starry galaxy sky",
                    "characters": ["CHAR_001", "CHAR_002"],
                    "character_names": "Nguyễn Minh, Linh Nhi",
                    "action": "Cả hai đứng kề vai trên đỉnh núi ngắm vạn dặm sơn hà dưới bầu trời ngàn sao rực rỡ",
                    "emotion": "hào hùng, hy vọng, gắn kết",
                    "camera_angle": "epic ultra-wide landscape shot",
                    "previous_panel_summary": "Hai anh hùng thành công thu nhận bảo vật trở ra đỉnh núi thiêng.",
                    "continuity_rules": "Cả hai nhân vật hướng ánh nhìn về thế gian, áo choàng và xiêm y tung bay trong gió đêm.",
                    "speaker": "Nguyễn Minh",
                    "dialogue": "Đi thôi Linh Nhi! Giang sơn ngoài kia đang chờ đón chúng ta!",
                    "bubble_type": "shout",
                    "narration": "Một trang sử mới đã mở ra. Bản anh hùng ca của họ sẽ còn lưu truyền mãi qua muôn đời.",
                    "layout_type": "wide",
                    "image_prompt": "masterpiece, vibrant full color anime manga illustration, epic ultra-wide landscape shot. CHAR_001 in navy robe and CHAR_002 in celestial white-pink dress standing side by side proudly on mountain cliff peak overlooking boundless glowing fantasy continent below magnificent starry galaxy nebula and crescent moon, breathtaking masterpiece, vibrant colors, 8k, no text, no speech bubbles"
                }
            ]
        }

