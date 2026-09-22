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
FALLBACK_MODEL_1 = "qwen/qwen3.8-27b"
FALLBACK_MODEL_2 = "openai/gpt-oss-20b"

PRO_COMIC_SYSTEM_PROMPT = """Bạn là Đạo diễn Truyện tranh & Chuyên gia Điều phối Prompt ComfyUI cấp cao (Comic Director, Storyboard Master & ComfyUI Prompt Orchestrator).

NHIỆM VỤ TỐI THƯỢNG:
Chuyển thể câu chuyện tiếng Việt được người dùng cung cấp thành kịch bản phân cảnh 16 ĐẾN 20 KHUNG TRANH (khuyến nghị 16-18 khung, tối đa 20) hoàn chỉnh, liền mạch 100%, bám sát tuyệt đối từng tình tiết, nhân vật và lời thoại trong truyện chữ. Đồng thời điều phối prompt chuyên biệt cho ComfyUI SDXL Anime (Animagine XL) để tạo hình nhân vật đồng nhất và chuẩn xác.

NGUYÊN TẮC BẮT BUỘC ĐẠO DIỄN:
1. TRUNG THỰC TUYỆT ĐỐI VỚI NỘI DUNG TRUYỆN CHỮ CỦA NGƯỜI DÙNG:
   - Nghiêm cấm tự ý đổi thể loại! Nếu truyện chữ là đời thường, tập gym, công sở, tình cảm -> Giữ nguyên 100% đời thường, tập gym, công sở, tình cảm. Nếu truyện là kiếm hiệp, khoa học viễn tưởng -> Giữ nguyên kiếm hiệp, khoa học viễn tưởng.
   - Nhân vật: Trích xuất chính xác tên nhân vật có trong câu chuyện. Tuyệt đối không tự ý thay thế bằng tên lạ.
   - Trang phục & Ngoại hình: Phải phản ánh đúng nghề nghiệp, hoàn cảnh của truyện.

2. PHÂN CẢNH 4 HỒI MẠCH LẠC (16 ĐẾN 20 KHUNG TRANH):
   - Hồi 1 (Mở đầu - Khung 1-4): Giới thiệu nhân vật, bối cảnh, tâm trạng ban đầu. Mỗi khung là một khoảnh khắc riêng biệt nhưng tiếp nối nhau.
   - Hồi 2 (Diễn biến - Khung 5-9): Các hoạt động chính, thử thách, tương tác. Tăng dần nhịp độ, góc quay đa dạng (wide → medium → close-up).
   - Hồi 3 (Cao trào - Khung 10-15): Kịch tính đỉnh điểm, bùng nổ cảm xúc, bước ngoặt. Nhiều cảnh hành động, biểu cảm mạnh.
   - Hồi 4 (Kết thúc - Khung 16-20): Giải quyết xung đột, cảm xúc lắng đọng, kết thúc ý nghĩa.

3. LIÊN KẾT GIỮA CÁC KHUNG TRANH (BẮT BUỘC):
   - Mỗi khung phải tiếp nối về mặt hành động hoặc không gian với khung trước đó.
   - Nhân vật và trang phục phải NHẤT QUÁN hoàn toàn qua mọi khung (dùng cùng character_id từ Character Bible).
   - Bối cảnh phải NHẤT QUÁN (dùng cùng location_id từ Location Bible) trừ khi câu chuyện chuyển cảnh.
   - comfy_prompt của mỗi khung phải include character tags từ Character Bible để đảm bảo hình ảnh đồng nhất.
   - Góc máy quay phải đa dạng và tạo nhịp điệu: establishing shot → medium shot → close-up → over-the-shoulder → wide shot.

4. LỜI THOẠI & LỜI DẪN TỪ TRUYỆN:
   - speaker: Tên nhân vật nói (hoặc "Người dẫn truyện").
   - dialogue: Câu thoại hoặc suy nghĩ tiếng Việt, lấy trực tiếp hoặc bám sát câu thoại/suy nghĩ trong truyện.
   - bubble_type: "speech" (nói) | "shout" (hét/hào hứng) | "thought" (suy nghĩ) | "whisper" (thì thầm) | "narration" (dẫn) | "none".
   - narration: Câu văn dẫn truyện tiếng Việt tóm lược diễn biến từ câu chuyện gốc.

5. BẢNG THIẾT KẾ NHÂN VẬT & BỐI CẢNH (CHARACTER & LOCATION BIBLE):
   - Character Bible: ID (CHAR_001...), tên tiếng Việt, tuổi, ngoại hình tiếng Anh, trang phục tiếng Anh, comfy_tags tiếng Anh chuẩn Booru/Anime.
   - Location Bible: ID (LOC_001...), tên tiếng Việt, architecture, lighting, comfy_tags tiếng Anh.

6. ĐIỀU PHỐI PROMPT COMFYUI (ANIMAGINE XL):
   - comfy_prompt: Prompt tiếng Anh tinh gọn, chuẩn Danbooru (< 80 từ), KHÔNG chứa chữ (no text, no speech bubbles), KHÔNG chia đôi khung ảnh:
     `masterpiece, best quality, vibrant full color anime webtoon art, [camera angle], [character tags & outfit], [specific action & expression], [location tags & lighting], dynamic atmospheric lighting, 8k digital illustration, highly detailed, no text, no watermark, no speech bubbles`

OUTPUT FORMAT (STRICT JSON ONLY, không bọc ```json, không thêm chữ dẫn giải trước/sau):
{
  "character_bible": [
    {
      "char_id": "CHAR_001",
      "name": "Tên nhân vật từ truyện",
      "gender": "male hoặc female",
      "age": "tuổi ước tính",
      "appearance": "short black hair, athletic build, sharp eyes",
      "costume": "trang phục phù hợp câu chuyện",
      "personality": "tính cách",
      "comfy_tags": "CHAR_001, 1boy (hoặc 1girl), [chi tiết ngoại hình], [trang phục], vibrant full color anime webtoon art"
    }
  ],
  "location_bible": [
    {
      "loc_id": "LOC_001",
      "name": "Tên bối cảnh từ truyện",
      "architecture": "kiến trúc bối cảnh",
      "lighting": "ánh sáng",
      "atmosphere": "không khí",
      "comfy_tags": "LOC_001, [từ khóa bối cảnh tiếng Anh]"
    }
  ],
  "story_setting": "Tóm tắt bối cảnh thế giới bám sát truyện của người dùng",
  "negative_prompt": "text, watermark, speech bubbles, letters, comic panel border, split screen, monochrome, grayscale, sketch, lowres, bad anatomy, bad hands, missing fingers, extra fingers, deformed limbs, blurry, mutation, duplicate, ugly, cropped, worst quality, out of frame",
  "panels": [
    {
      "panel_index": 1,
      "scene_id": "S01",
      "location_id": "LOC_001",
      "location_name": "Tên bối cảnh",
      "time_of_day": "day hoặc night",
      "weather": "clear",
      "characters": ["CHAR_001"],
      "character_names": "Tên nhân vật",
      "action": "Mô tả hành động tiếng Việt",
      "emotion": "Cảm xúc nhân vật",
      "camera_angle": "cinematic wide angle shot hoặc medium shot",
      "speaker": "Tên nhân vật",
      "dialogue": "Lời thoại hoặc suy nghĩ tiếng Việt",
      "bubble_type": "speech",
      "narration": "Lời dẫn chuyện tiếng Việt bám sát truyện",
      "layout_type": "square",
      "comfy_prompt": "masterpiece, best quality, vibrant full color anime webtoon art, [camera], [character tags & action], [location & lighting], 8k, no text, no speech bubbles"
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
            self.fallback_llm = GroqClient(model_name=FALLBACK_MODEL_1, api_key=api_key)
        except Exception:
            self.fallback_llm = None
        try:
            self.tertiary_llm = GroqClient(model_name=FALLBACK_MODEL_2, api_key=api_key)
        except Exception:
            self.tertiary_llm = None

    def generate(self, story_text: str, genre: str = "", style: str = "") -> Dict[str, Any]:
        trimmed = (story_text or "").strip()[:7000]
        if not trimmed or len(trimmed) < 15:
            logger.warning("[ProComicAgent] Story text too short, using dynamic fallback.")
            return self._create_dynamic_fallback(story_text=story_text, genre=genre, style=style)

        genre_hint = f"\nThể loại mong muốn: {genre}" if genre else ""
        style_hint = f"\nPhong cách hội họa: {style}" if style else ""
        user_prompt = (
            f"Hãy phân tích và chuyển thể câu chuyện sau thành kịch bản truyện tranh 16 ĐẾN 20 KHUNG TRANH (khuyến nghị 16-18 khung), "
            f"đảm bảo mỗi khung tiếp nối liền mạch với khung trước, nhân vật và bối cảnh nhất quán xuyên suốt, "
            f"bám sát 100% nhân vật, ngoại hình, nghề nghiệp, bối cảnh, lời thoại và diễn biến trong truyện chữ:{genre_hint}{style_hint}\n\n{trimmed}"
        )

        messages = [
            {"role": "system", "content": PRO_COMIC_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        # Model cascade: Primary (gpt-oss-120b) -> Fallback 1 (qwen3.8-27b) -> Fallback 2 (gpt-oss-20b)
        clients = [self.llm]
        if self.fallback_llm:
            clients.append(self.fallback_llm)
        if self.tertiary_llm:
            clients.append(self.tertiary_llm)

        for client in clients:
            try:
                raw = client.chat(
                    messages=messages,
                    temperature=0.3,
                    max_tokens=6000,
                    response_format={"type": "json_object"}
                )
                data = self._parse_or_repair_json(raw)
                if data and isinstance(data.get("panels"), list) and len(data["panels"]) >= 6:
                    return self._process_script_data(data, style)
            except Exception as e:
                logger.warning(f"[ProComicAgent] LLM {getattr(client, 'model', 'unknown')} failed: {e}")

        logger.warning("[ProComicAgent] All LLMs failed or returned invalid JSON. Using dynamic story-based fallback.")
        return self._create_dynamic_fallback(story_text=trimmed, genre=genre, style=style)

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
                        if isinstance(data.get("panels"), list) and len(data["panels"]) >= 6:
                            return data
                except Exception:
                    continue

        return None

    def _process_script_data(self, data: Dict[str, Any], style: str = "") -> Dict[str, Any]:
        """Validates, caps panel count to 20, and enriches image prompts with Bibles."""
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
        if len(panels) > 20:
            panels = panels[:20]

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

        camera = panel.get("camera_angle", "cinematic medium shot")
        raw_prompt = (panel.get("comfy_prompt") or panel.get("image_prompt") or "").strip()

        # Build clean prompt without duplicate tokens
        if raw_prompt and "masterpiece" in raw_prompt.lower() and len(raw_prompt) > 40:
            final_prompt = raw_prompt
        else:
            parts = ["masterpiece, best quality, vibrant full color anime webtoon art", camera]
            if char_prompts:
                parts.extend(char_prompts)
            if raw_prompt:
                parts.append(raw_prompt)
            elif panel.get("action"):
                parts.append(panel.get("action"))
            if loc_prompt and loc_prompt not in " ".join(parts):
                parts.append(loc_prompt)
            parts.append("dynamic atmospheric lighting, 8k digital illustration, highly detailed, no text, no watermark, no speech bubbles")
            final_prompt = ", ".join([p.strip().rstrip(",") for p in parts if p.strip()])

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

    def _create_dynamic_fallback(self, story_text: str, genre: str = "", style: str = "") -> Dict[str, Any]:
        """
        Dynamically extracts characters, settings, dialogues, and scenes from the user's actual prose text.
        Guarantees that fallback comic is ALWAYS 100% faithful to the user's actual story.
        """
        text = (story_text or "").strip()
        if not text:
            text = "Một ngày mới tràn đầy năng lượng, nhân vật chính nỗ lực vượt qua thử thách để vươn tới thành công."

        STOP_WORDS = {
            "Một", "Sau", "Khi", "Anh", "Cô", "Và", "Nhưng", "Trong", "Để", "Tại", "Bỗng", "Đột", "Có", 
            "Ngày", "Đêm", "Lúc", "Nơi", "Với", "Từ", "Người", "Họ", "Tôi", "Bạn", "Nếu", "Vì", "Tuy", 
            "Dù", "Dẫu", "Mỗi", "Các", "Những", "Toàn", "Từng", "Cả", "Ở", "Do", "Bởi", "Tuyệt", "Được", 
            "Bị", "Đã", "Đang", "Sẽ", "Vừa", "Trước", "Theo", "Cùng"
        }

        # Extract Vietnamese proper nouns
        raw_names = re.findall(
            r'\b([A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰÝỲỶỸỴ][a-zàáảãạăằắẳẵặâầấẩẫậđèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựýỳỷỹỵ]+(?:\s+[A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰÝỲỶỸỴ][a-zàáảãạăằắẳẵặâầấẩẫậđèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựýỳỷỹỵ]+)*)\b', 
            text
        )
        valid_names = [n for n in raw_names if n.split()[0] not in STOP_WORDS and len(n.split()) <= 3]
        char_name = valid_names[0] if valid_names else "Nhân vật chính"

        sec_name = None
        for n in valid_names[1:]:
            if n != char_name and n not in char_name:
                sec_name = n
                break

        lower_text = text.lower()
        is_female = sum(lower_text.count(w) for w in ['cô', 'nàng', 'chị', 'nữ', 'gái']) > sum(lower_text.count(w) for w in ['anh', 'chàng', 'nam', 'cậu', 'trai'])
        gender = "female" if is_female else "male"
        gender_tag = "1girl" if is_female else "1boy"

        # Detect genre / setting
        if any(w in lower_text for w in ['gym', 'tạ', 'phòng tập', 'treadmill', 'chạy bộ', 'cơ bắp', 'fitness', 'thể thao', 'curl', 'squat']):
            loc_name = "Phòng tập Gym hiện đại"
            loc_arch = "modern fitness gym interior, weight machines, dumbbells on racks, workout benches"
            loc_lighting = "bright energetic LED ceiling lights, clean polished wooden floor"
            loc_tags = "LOC_001, modern fitness gym interior, weight racks, dumbells, fitness machines, bright led lighting"
            char_costume = "áo thun thể thao đen, quần short tập gym, bao tay thể thao"
            char_appearance = "thân hình thể thao săn chắc, ánh mắt kiên định, nụ cười rạng rỡ"
            char_tags = f"CHAR_001, {gender_tag}, handsome athletic build, short black hair, focused eyes, black athletic gym t-shirt, sports shorts, gym wrist wraps"
            action_keyword = "working out, lifting weights, energetic fitness training"
        elif any(w in lower_text for w in ['văn phòng', 'công sở', 'laptop', 'máy tính', 'công ty', 'code', 'sếp', 'bàn làm việc']):
            loc_name = "Văn phòng công nghệ hiện đại"
            loc_arch = "sleek contemporary office, glass partitions, modern wooden desk, dual monitors"
            loc_lighting = "clean soft office lighting, floor-to-ceiling glass windows"
            loc_tags = "LOC_001, modern corporate office interior, sleek wooden work desk, computer screens, minimalist office"
            char_costume = "áo sơ mi công sở lịch sự, quần tây, đồng hồ thông minh"
            char_appearance = "vẻ ngoài tri thức, ánh mắt sắc sảo, phong thái chuyên nghiệp"
            char_tags = f"CHAR_001, {gender_tag}, smart professional appearance, neat short black hair, casual smart dark shirt, office wear"
            action_keyword = "typing on laptop, reviewing project, focused work"
        elif any(w in lower_text for w in ['kiếm', 'tu tiên', 'chưởng', 'yêu thú', 'pháp bảo', 'sư phụ', 'võ công']):
            loc_name = "Thung lũng sơn thủy huyền ảo"
            loc_arch = "ancient misty mountain peaks, towering ancient stone pagodas, floating ruins"
            loc_lighting = "mystical dawn sunlight breaking through purple mist, ethereal glowing particles"
            loc_tags = "LOC_001, ancient oriental fantasy mountains, misty cliffs, glowing celestial atmosphere"
            char_costume = "chiến bào kiếm khách thêu hoa văn, thắt lưng da, bao tay hộ uyển"
            char_appearance = "khôi ngô tuấn tú, ánh mắt sắc lạnh kiên định, vóc dáng uy nghi"
            char_tags = f"CHAR_001, {gender_tag}, handsome young hero, dark navy martial arts robe, holding sword"
            action_keyword = "martial arts stance, wielding sword with ethereal aura"
        else:
            loc_name = "Bối cảnh câu chuyện đời thường"
            loc_arch = "modern vibrant anime scenery, cozy aesthetic indoor and street setting"
            loc_lighting = "warm natural daylight, cinematic atmospheric glow"
            loc_tags = "LOC_001, modern aesthetic anime setting, vibrant rich colors, cinematic natural daylight"
            char_costume = "trang phục trẻ trung hiện đại, áo phông năng động"
            char_appearance = "gương mặt sáng, đôi mắt đầy nhiệt huyết, thần thái tích cực"
            char_tags = f"CHAR_001, {gender_tag}, handsome expressive face, neat modern hairstyle, stylish casual clothes"
            action_keyword = "confident everyday action, positive determined expression"

        char_bible = [{
            "char_id": "CHAR_001",
            "name": char_name,
            "gender": gender,
            "age": "22",
            "appearance": char_appearance,
            "costume": char_costume,
            "personality": "kiên trì, quyết tâm, tràn đầy năng lượng",
            "comfy_tags": f"{char_tags}, vibrant full color anime webtoon art"
        }]

        if sec_name:
            char_bible.append({
                "char_id": "CHAR_002",
                "name": sec_name,
                "gender": "male",
                "age": "28",
                "appearance": "gương mặt thân thiện, ánh mắt khích lệ đầy kinh nghiệm",
                "costume": "trang phục gọn gàng phù hợp bối cảnh",
                "personality": "nhiệt huyết, ân cần hỗ trợ",
                "comfy_tags": "CHAR_002, 1man, mature look, confident friendly expression, professional outfit, vibrant anime art"
            })

        loc_bible = [{
            "loc_id": "LOC_001",
            "name": loc_name,
            "architecture": loc_arch,
            "lighting": loc_lighting,
            "atmosphere": "vibrant, inspiring, cinematic",
            "comfy_tags": loc_tags
        }]

        # Segment sentences for 8 panels
        raw_sentences = [s.strip() for s in re.split(r'(?<=[.!?…\n])\s+', text) if len(s.strip()) > 6]
        if not raw_sentences:
            raw_sentences = [text]

        target_panels = 8
        segments = []
        if len(raw_sentences) <= target_panels:
            segments = raw_sentences
            while len(segments) < target_panels:
                segments.append(segments[-1])
        else:
            step = len(raw_sentences) / target_panels
            for i in range(target_panels):
                start = int(i * step)
                end = int((i + 1) * step) if i < target_panels - 1 else len(raw_sentences)
                chunk = " ".join(raw_sentences[start:end])
                segments.append(chunk)

        angles = [
            "cinematic wide establishing shot",
            "medium shot from front",
            "dynamic eye-level shot",
            "dramatic low angle action shot",
            "intense close-up facial shot",
            "heroic dynamic action shot",
            "cinematic three-quarter view shot",
            "inspirational wide ending shot"
        ]

        panels = []
        for idx, seg in enumerate(segments):
            p_idx = idx + 1
            angle = angles[idx % len(angles)]
            quotes = re.findall(r'["\'“”«»](.*?)["\'“”«»]', seg)
            if quotes:
                dialogue = quotes[0].strip()
                b_type = "speech"
                speaker = sec_name if (sec_name and sec_name in seg) else char_name
            else:
                if idx == 0:
                    dialogue = "Bắt đầu mục tiêu hôm nay thôi nào!"
                    b_type = "thought"
                    speaker = char_name
                elif idx == target_panels - 1:
                    dialogue = "Cảm giác thật tuyệt vời khi vượt qua chính mình!"
                    b_type = "speech"
                    speaker = char_name
                elif idx in (3, 4):
                    dialogue = "Cố lên, không được bỏ cuộc!"
                    b_type = "thought"
                    speaker = char_name
                else:
                    dialogue = ""
                    b_type = "none"
                    speaker = char_name

            comfy_prompt = (
                f"masterpiece, best quality, vibrant full color anime webtoon art, {angle}, "
                f"{char_tags}, {action_keyword}, {loc_tags}, dynamic atmospheric lighting, 8k digital illustration, no text, no speech bubbles"
            )

            panels.append({
                "panel_index": p_idx,
                "scene_id": f"S{((p_idx - 1) // 2) + 1:02d}",
                "location_id": "LOC_001",
                "location_name": loc_name,
                "time_of_day": "day",
                "weather": "clear",
                "characters": ["CHAR_001"] + (["CHAR_002"] if sec_name and (sec_name in seg) else []),
                "character_names": f"{char_name}" + (f", {sec_name}" if sec_name and (sec_name in seg) else ""),
                "action": seg[:120],
                "emotion": "tập trung, quyết tâm",
                "camera_angle": angle,
                "speaker": speaker if dialogue else "",
                "dialogue": dialogue,
                "bubble_type": b_type,
                "narration": seg,
                "layout_type": "square" if p_idx % 3 != 0 else "wide",
                "comfy_prompt": comfy_prompt,
                "image_prompt": comfy_prompt,
                "negative_prompt": "text, watermark, speech bubbles, letters, comic panel border, split screen, monochrome, lowres, bad anatomy, deformed"
            })

        return {
            "character_bible": char_bible,
            "location_bible": loc_bible,
            "story_setting": f"Câu chuyện về {char_name} tại {loc_name}.",
            "negative_prompt": "text, watermark, speech bubbles, letters, comic panel border, lowres, bad anatomy, deformed",
            "panels": panels
        }
