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

MODEL = "qwen/qwen3.8-27b"

PRO_COMIC_SYSTEM_PROMPT = """Bạn là một Đạo diễn Truyện tranh & Nghệ sĩ Kịch bản Phân cảnh (Comic Director & Storyboard Artist) chuyên nghiệp cấp cao.

NHIỆM VỤ CỦA BẠN:
1. Phân tích cốt truyện tiếng Việt được cung cấp.
2. Xây dựng BẢNG THIẾT KẾ NHÂN VẬT (Character Bible) chi tiết, nhất quán (ID, tên tiếng Việt, tuổi, ngoại hình chi tiết về tóc/mắt/khuôn mặt/vóc dáng, trang phục đặc trưng với màu sắc rõ ràng, tính cách, base_prompt bằng tiếng Anh).
3. Xây dựng BẢNG THIẾT KẾ BỐI CẢNH (Location Bible) chi tiết (ID, tên bối cảnh tiếng Việt, kiến trúc, ánh sáng, bầu không khí, base_prompt bằng tiếng Anh).
4. Phân rã câu chuyện thành từ 6 ĐẾN 8 KHUNG TRANH (Panels) mạch lạc, có sự phát triển liên tục (Story Progression).
5. Đảm bảo tính LIÊN TỤC VÀ ĐỒNG NHẤT (Continuity):
   - Nhân vật xuất hiện trong các khung tranh phải giữ nguyên trang phục, màu tóc, đặc điểm nhận diện.
   - Bối cảnh phải duy trì ánh sáng, thời gian và không gian hợp lý.
   - Ghi rõ previous_panel_summary và continuity_rules giữa các khung tranh liên tiếp.
6. Mỗi khung tranh PHẢI CÓ LỜI THOẠI RIÊNG (dialogue) hoặc LỜI DẪN TRUYỆN (narration) bằng tiếng Việt chuẩn ngữ pháp, cảm xúc tự nhiên, đúng người nói (speaker).
7. image_prompt: PHẢI VIẾT BẰNG TIẾNG ANH, mô tả phong cách FULL COLOR ANIME / WEBTOON, TUYỆT ĐỐI KHÔNG chứa chữ/text hay bong bóng thoại trong ảnh (speech bubbles và text sẽ do hệ thống frontend render bằng HTML/CSS đè lên tranh).

OUTPUT FORMAT (STRICT JSON ONLY, không có markdown code blocks ```json, không có text dẫn dụ trước hoặc sau):
{
  "character_bible": [
    {
      "char_id": "CHAR_001",
      "name": "Nguyễn Minh",
      "gender": "male",
      "age": "20",
      "appearance": "handsome young man, short spiky jet-black hair, determined dark blue eyes, athletic lean muscular build, small scar on left cheek",
      "costume": "dark navy blue martial arts combat robe with silver dragon embroidery, silver clasps, high collar, black leather belt, fingerless gloves",
      "personality": "kiên định, dũng cảm, trọng nghĩa khí",
      "base_prompt": "CHAR_001, handsome young hero, short spiky jet-black hair, sharp dark blue eyes, scar on left cheek, wearing dark navy blue martial arts robe with silver dragon trims, black leather bracers, vibrant full color anime webtoon art"
    }
  ],
  "location_bible": [
    {
      "loc_id": "LOC_001",
      "name": "Đỉnh núi Vân Phong",
      "architecture": "ancient celestial mountain peak with floating stone monoliths",
      "lighting": "golden dawn sunlight breaking through purple misty clouds",
      "atmosphere": "mystic, epic, breathtaking, ethereal atmosphere",
      "base_prompt": "LOC_001, ancient mountain cliff summit above sea of clouds, floating ancient stone ruins, radiant golden sunrise rays breaking through purple morning mist, ethereal fantasy world, vibrant colors"
    }
  ],
  "story_setting": "Thế giới huyền huyễn tu tiên nơi đan xen giữa bí ẩn thượng cổ và chí khí anh hùng.",
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
      "previous_panel_summary": "Bắt đầu câu chuyện, nhân vật vừa đặt chân lên đỉnh núi thiêng.",
      "continuity_rules": "Nguyễn Minh mặc chiến bào xanh đen thêu rồng bạc, tóc đen ngắn bay nhẹ trong gió sớm.",
      "speaker": "Nguyễn Minh",
      "dialogue": "Cuối cùng ta cũng đã tìm thấy Đền Thượng Cổ...",
      "bubble_type": "speech",
      "narration": "Sau ba ngày ba đêm vượt biển mây hiểm trở, cánh cửa định mệnh đã hiện ra trước mắt.",
      "layout_type": "wide",
      "image_prompt": "Masterpiece full color anime webtoon illustration, cinematic wide angle low shot. CHAR_001 handsome young hero, short spiky jet-black hair, sharp dark blue eyes, dark navy martial arts robe with silver trims, standing heroically on jagged mountain cliff edge at dawn looking toward massive floating ancient celestial temple in golden clouds, breathtaking sunrise lighting, vibrant colors, highly detailed digital art, 8k, no text, no watermark"
    }
  ]
}

QUY TẮC BẮT BUỘC:
- Số lượng panels: BẮT BUỘC TỪ 6 ĐẾN 8 KHUNG TRANH (minimum 6, target 6-8).
- bubble_type: "speech" (nói thông thường) | "shout" (hét to, ra chiêu) | "thought" (suy nghĩ) | "whisper" (thì thầm) | "narration" (lời dẫn) | "none" (không có thoại).
- layout_type: "wide" (khung phong cảnh, đại cảnh) | "tall" (khung dọc, toàn thân, nhân vật đứng) | "square" (trung cảnh, cận cảnh).
- image_prompt: Đầy đủ màu sắc (FULL COLOR), phong cách anime/webtoon, TUYỆT ĐỐI KHÔNG chứa bong bóng thoại hay chữ trong ảnh (no text, no speech bubbles).
"""

class ProComicAgent:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY_COMIC") or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Missing GROQ_API_KEY")
        self.llm = GroqClient(model_name=MODEL, api_key=api_key)

    def generate(self, story_text: str, genre: str = "", style: str = "") -> Dict[str, Any]:
        trimmed = (story_text or "").strip()[:6000]
        if not trimmed:
            trimmed = "Một chàng trai trẻ tu tiên dũng cảm bước vào di tích thượng cổ, tìm kiếm bảo vật giải cứu sư môn."

        genre_hint = f"\nThể loại: {genre}" if genre else ""
        style_hint = f"\nPhong cách hội họa: {style}" if style else ""
        user_prompt = (
            f"Hãy chuyển thể câu chuyện sau thành kịch bản truyện tranh hoàn chỉnh 6-8 khung tranh, "
            f"kèm Character Bible, Location Bible và continuity rules:{genre_hint}{style_hint}\n\n{trimmed}"
        )

        try:
            raw = self.llm.chat(
                messages=[
                    {"role": "system", "content": PRO_COMIC_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6,
                max_tokens=4000
            )

            json_match = re.search(r'\{[\s\S]*\}', raw)
            if json_match:
                data = json.loads(json_match.group(0))
                if isinstance(data.get("panels"), list) and len(data["panels"]) >= 4:
                    return self._process_script_data(data, style)
        except Exception as e:
            logger.warning("[ProComicAgent] LLM generation failed or returned invalid JSON: %s. Using structured fallback.", e)

        return self._get_fallback()

    def _process_script_data(self, data: Dict[str, Any], style: str = "") -> Dict[str, Any]:
        """Validates, caps panel count to 6-8, and enriches image prompts with Bibles."""
        char_bible = data.get("character_bible", [])
        if not isinstance(char_bible, list):
            char_bible = []
        loc_bible = data.get("location_bible", [])
        if not isinstance(loc_bible, list):
            loc_bible = []

        char_map = {c.get("char_id", f"CHAR_{i+1:03d}"): c for i, c in enumerate(char_bible)}
        loc_map = {l.get("loc_id", f"LOC_{i+1:03d}"): l for i, l in enumerate(loc_bible)}

        panels = data.get("panels", [])
        if len(panels) > 8:
            panels = panels[:8]

        validated_panels = []
        for i, p in enumerate(panels):
            enriched = self._enrich_panel(p, i + 1, char_map, loc_map, style)
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
        style: str = ""
    ) -> Dict[str, Any]:
        """Ensures panel has all required fields and assembles a consistent, full-color prompt."""
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
                char_prompts.append(c_info.get("base_prompt") or f"{c_info.get('name')}, {c_info.get('appearance')}, {c_info.get('costume')}")

        # Location references
        loc_id = panel.get("location_id", "")
        loc_prompt = ""
        if loc_id in loc_map:
            l_info = loc_map[loc_id]
            loc_prompt = l_info.get("base_prompt") or f"{l_info.get('architecture')}, {l_info.get('lighting')}"

        # Build comprehensive English prompt for Stability AI
        raw_prompt = panel.get("image_prompt", "").strip()
        camera = panel.get("camera_angle", "cinematic medium shot")
        action_en = panel.get("action", "")

        # Base style tokens enforcing full-color webtoon/anime illustration without text
        style_tokens = "masterpiece, vibrant full color anime manga illustration, detailed webtoon art, dynamic lighting, 8k digital painting, no text, no watermark, no speech bubbles"
        
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
            "image_prompt": final_prompt
        }

    def _get_fallback(self) -> Dict[str, Any]:
        """Rich 6-panel fallback ensuring coherent story, full-color prompts, and consistent characters."""
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
                    "location_name": "Tâm Điện Thần Thượng Cổ",
                    "time_of_day": "timeless",
                    "weather": "cosmic starlight aura",
                    "characters": ["CHAR_001", "CHAR_002"],
                    "character_names": "Nguyễn Minh, Linh Nhi",
                    "action": "Nguyễn Minh và Linh Nhi kề vai ngắm nhìn cuộn bí kíp thần thoại lơ lửng giữa trời sao",
                    "emotion": "hào hùng, tin tưởng",
                    "camera_angle": "epic wide landscape shot",
                    "previous_panel_summary": "Cánh cổng mở ra, cả hai bước vào tâm điện.",
                    "continuity_rules": "Cả hai nhân vật đứng song song, hướng ánh mắt về bí kíp tỏa sáng rực rỡ.",
                    "speaker": "Nguyễn Minh",
                    "dialogue": "Giang sơn vạn dặm... Hành trình vĩ đại của chúng ta chính thức bắt đầu!",
                    "bubble_type": "shout",
                    "narration": "Một huyền thoại mới chính thức khai sinh trên lục địa huyền bí.",
                    "layout_type": "wide",
                    "image_prompt": "masterpiece, vibrant full color anime manga illustration, epic wide landscape shot. CHAR_001 in dark navy robe and CHAR_002 in flowing white-pink dress standing proudly side by side inside grand celestial sanctuary, gazing up at magnificent golden glowing sacred scroll floating amid cosmic starlight nebula, breathtaking masterpiece, vibrant colors, 8k, no text, no speech bubbles"
                }
            ]
        }

