import os
import json
import re
from typing import List, Dict, Any, Optional

try:
    from llm.groq_client import GroqClient
except (ImportError, ModuleNotFoundError):
    from backend.llm.groq_client import GroqClient

MODEL = "qwen/qwen3.8-27b"

PRO_COMIC_SYSTEM_PROMPT = """Bạn là một Đạo diễn Truyện tranh (Comic Director) chuyên nghiệp cấp cao.

NHIỆM VỤ:
1. Phân tích nội dung cốt truyện tiếng Việt.
2. Xây dựng BẢNG THIẾT KẾ NHÂN VẬT (Character Bible) chi tiết, nhất quán (ID, Tên nhân vật bằng tiếng Việt, tuổi, ngoại hình, trang phục, tính cách).
3. Phân rã câu chuyện thành danh sách ÍT NHẤT 10 đến 16 KHUNG TRANH (Panels). KHÔNG ĐƯỢC làm quá ít khung tranh (phải từ 10 đến 16 khung để truyền tải trọn vẹn diễn biến).
4. Mỗi khung tranh PHẢI CÓ LỜI THOẠI RIÊNG CỦA NHÂN VẬT (dialogue) hoặc lời dẫn truyện (narration), ghi rõ người nói (speaker: tên nhân vật tiếng Việt), cảm xúc, và loại bong bóng thoại (bubble_type).

OUTPUT FORMAT (strict JSON ONLY, không có text dẫn dụ trước hoặc sau):
{
  "character_bible": [
    {
      "char_id": "CHAR_001",
      "name": "Nguyễn Minh",
      "gender": "male",
      "age": "20",
      "appearance": "short black spiky hair, sharp dark blue eyes, athletic build, scar on left cheek",
      "costume": "dark navy martial arts robe with silver dragon trims, leather belt",
      "personality": "kiên định, dũng cảm",
      "base_prompt": "CHAR_001, young handsome Vietnamese hero, short black spiky hair, sharp dark blue eyes, scar on left cheek, wearing dark navy martial arts robe with silver trims, highly detailed manga illustration"
    }
  ],
  "story_setting": "Mô tả bối cảnh thế giới",
  "panels": [
    {
      "panel_index": 1,
      "scene_id": "S01",
      "location": "Đỉnh núi Vân Phong lúc bình minh",
      "time_of_day": "dawn",
      "weather": "misty",
      "characters": ["CHAR_001"],
      "action": "Đứng bên bờ vực ngắm ngôi đền bay trên mây",
      "emotion": "kinh ngạc",
      "camera_angle": "cinematic wide angle low shot",
      "shot_type": "wide",
      "prev_state": "",
      "speaker": "Nguyễn Minh",
      "dialogue": "Cuối cùng ta cũng đã tìm thấy Đền Thượng Cổ...",
      "bubble_type": "speech",
      "narration": "Sau ba ngày ba đêm vượt qua biển mây hiểm trở...",
      "layout_type": "wide",
      "image_prompt": "CHAR_001, young handsome hero, short black spiky hair, sharp blue eyes, dark navy martial arts robe, standing heroically on jagged mountain cliff edge at dawn, looking toward massive celestial floating temple among clouds, golden sunrise rays, cinematic wide angle, detailed manga webtoon art style, 8k"
    }
  ]
}

QUY TẮC QUAN TRỌNG:
- Số lượng panels: BẮT BUỘC TỪ 10 ĐẾN 16 KHUNG TRANH (minimum 10, target 12-16).
- bubble_type: "speech" (nói chuyện thông thường) | "shout" (hét to, ra chiêu) | "thought" (suy nghĩ trong đầu) | "narration" (hộp thoại dẫn truyện).
- speaker: Ghi rõ TÊN NHÂN VẬT tiếng Việt (ví dụ "Nguyễn Minh", "Linh Nhi", "Lão Tiên Sinh", v.v.).
- dialogue: Lời thoại tiếng Việt chuẩn ngữ pháp, cảm xúc tự nhiên, đúng ngữ cảnh câu chuyện.
- layout_type: "wide" | "tall" | "square".
- image_prompt: Tiếng Anh siêu chi tiết, manga/anime webtoon style, LUÔN kèm mô tả base_prompt của nhân vật trong khung đó.
"""

class ProComicAgent:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY_COMIC") or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Missing GROQ_API_KEY")
        self.llm = GroqClient(model_name=MODEL, api_key=api_key)

    def generate(self, story_text: str, genre: str = "", style: str = "") -> Dict[str, Any]:
        trimmed = (story_text or "").strip()[:5000]
        if not trimmed:
            trimmed = "Mot chang trai tre buoc vao the gioi tu tien, phat hien bi mat ve nguon goc cua minh."

        genre_hint = f"\nGenre: {genre}" if genre else ""
        style_hint = f"\nArt Style: {style}" if style else ""
        user_prompt = f"Create a comic script for this story:{genre_hint}{style_hint}\n\n{trimmed}"

        try:
            raw = self.llm.chat(
                messages=[
                    {"role": "system", "content": PRO_COMIC_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.65,
                max_tokens=4000
            )
            json_match = re.search(r'\{[\s\S]*\}', raw)
            if json_match:
                data = json.loads(json_match.group(0))
                if isinstance(data.get("panels"), list) and len(data["panels"]) > 0:
                    data["panels"] = self._validate_panels(data["panels"])
                    return data
        except Exception as e:
            print(f"[ProComicAgent] Error: {e}")

        return self._get_fallback()

    def _validate_panels(self, panels: List[Dict]) -> List[Dict]:
        defaults = {
            "scene_id": "S01", "location": "Unknown", "time_of_day": "day",
            "weather": "clear", "characters": [], "action": "Standing",
            "emotion": "neutral", "camera_angle": "medium shot", "shot_type": "square",
            "prev_state": "", "dialogue": "", "speaker": "", "bubble_type": "none",
            "narration": "", "layout_type": "square",
            "image_prompt": "manga style, high quality illustration"
        }
        validated = []
        for i, p in enumerate(panels):
            panel = {**defaults, **p}
            panel["panel_index"] = i + 1
            if panel["layout_type"] not in ("wide", "tall", "square"):
                panel["layout_type"] = "square"
            if panel["bubble_type"] not in ("speech", "shout", "thought", "narration", "none"):
                panel["bubble_type"] = "speech" if panel.get("dialogue") else "none"
            validated.append(panel)
        return validated

    def _get_fallback(self) -> Dict[str, Any]:
        return {
            "character_bible": [
                {
                    "char_id": "CHAR_001", "name": "Nguyễn Minh",
                    "gender": "male", "age": "20",
                    "appearance": "tóc đen ngắn vuốt nhọn, mắt xanh thẫm kiên nghị, dáng vóc săn chắc",
                    "costume": "chiến bào võ hiệp xanh lam thêu vân mây bạc, đai da",
                    "personality": "kiên định, dũng cảm, trọng nghĩa khí",
                    "base_prompt": "CHAR_001, handsome young hero Nguyen Minh, short spiky black hair, sharp deep blue eyes, wearing dark navy martial arts robe with silver clouds, athletic build, detailed manga webtoon illustration"
                },
                {
                    "char_id": "CHAR_002", "name": "Linh Nhi",
                    "gender": "female", "age": "19",
                    "appearance": "tóc nâu dài cài trâm hoa ngọc, mắt hổ phách lanh lợi, gương mặt thanh tú",
                    "costume": "y phục tiên hiệp màu trắng viền cánh sen hồng nhạt",
                    "personality": "thông minh, nhanh nhẹn, chu đáo",
                    "base_prompt": "CHAR_002, beautiful anime girl Linh Nhi, long brown hair with jade flower hairpin, bright amber eyes, elegant white and soft pink celestial hanfu dress, gentle yet determined expression, detailed anime art"
                }
            ],
            "story_setting": "Thế giới huyền huyễn tu tiên nơi đan xen giữa bí ẩn thượng cổ và hiểm nguy trùng trùng.",
            "panels": [
                {"panel_index": 1, "scene_id": "S01", "location": "Đỉnh núi Vân Phong lúc bình minh",
                 "time_of_day": "dawn", "weather": "misty", "characters": ["CHAR_001"],
                 "action": "Đứng bên bờ vực ngắm ngôi đền bay trên mây", "emotion": "kinh ngạc",
                 "camera_angle": "cinematic wide shot", "shot_type": "wide", "prev_state": "",
                 "speaker": "Nguyễn Minh", "dialogue": "Cuối cùng ta cũng đã tìm thấy Đền Thượng Cổ...",
                 "bubble_type": "speech", "narration": "Sau ba ngày ba đêm vượt biển mây hiểm trở...", "layout_type": "wide",
                 "image_prompt": "CHAR_001, young handsome hero, short spiky black hair, deep blue eyes, dark navy martial arts robe, standing on mountain cliff edge at dawn looking at celestial floating temple in clouds, golden sunrise, manga style, high quality, 8k"},
                {"panel_index": 2, "scene_id": "S01", "location": "Bờ vực mây mù",
                 "time_of_day": "morning", "weather": "clear", "characters": ["CHAR_001"],
                 "action": "Nắm chặt chuôi kiếm, ánh mắt quyết tâm", "emotion": "kiên định",
                 "camera_angle": "close up dramatic", "shot_type": "square",
                 "prev_state": "Nhìn về phía đền", "speaker": "Nguyễn Minh",
                 "dialogue": "Bất luận phía trước là cạm bẫy hay cơ duyên, ta quyết không lùi bước!",
                 "bubble_type": "shout", "narration": "", "layout_type": "square",
                 "image_prompt": "CHAR_001, close up of determined young man face, sharp blue eyes glowing with resolve, hand gripping silver sword hilt, wind blowing hair, dramatic lighting, manga style, highly detailed"},
                {"panel_index": 3, "scene_id": "S01", "location": "Cầu đá treo lơ lửng",
                 "time_of_day": "morning", "weather": "windy", "characters": ["CHAR_002"],
                 "action": "Linh Nhi xuất hiện nhẹ nhàng nơi đầu cầu", "emotion": "mỉm cười cảnh báo",
                 "camera_angle": "medium shot", "shot_type": "tall",
                 "prev_state": "Nguyễn Minh chuẩn bị bước qua", "speaker": "Linh Nhi",
                 "dialogue": "Đợi đã! Đừng hấp tấp, cây cầu này chứa trận pháp ngàn năm đấy.",
                 "bubble_type": "speech", "narration": "Một giọng nói trong trẻo bỗng vang lên từ màn sương...", "layout_type": "tall",
                 "image_prompt": "CHAR_002, beautiful anime girl Linh Nhi, long brown hair, jade hairpin, amber eyes, white and soft pink robe flowing in wind, standing gracefully at entrance of ancient floating stone bridge, manga style, highly detailed"},
                {"panel_index": 4, "scene_id": "S01", "location": "Đầu cầu đá cổ",
                 "time_of_day": "morning", "weather": "clear", "characters": ["CHAR_001", "CHAR_002"],
                 "action": "Nguyễn Minh quay phắt lại phòng thủ, ngạc nhiên", "emotion": "cảnh giác",
                 "camera_angle": "two-shot over the shoulder", "shot_type": "wide",
                 "prev_state": "Linh Nhi xuất hiện", "speaker": "Nguyễn Minh",
                 "dialogue": "Nàng là ai? Sao lại xuất hiện ở cấm địa này?",
                 "bubble_type": "speech", "narration": "", "layout_type": "wide",
                 "image_prompt": "Two anime characters facing each other on ancient stone bridge: CHAR_001 in dark navy robe on guard with hand on sword, facing CHAR_002 in white-pink robe, misty mountain background, cinematic two-shot, manga style"},
                {"panel_index": 5, "scene_id": "S02", "location": "Trước cổng Đền Thượng Cổ",
                 "time_of_day": "noon", "weather": "mystical", "characters": ["CHAR_002"],
                 "action": "Linh Nhi lấy ra một viên cổ ngọc phát sáng", "emotion": "nghiêm túc",
                 "camera_angle": "medium close-up", "shot_type": "square",
                 "prev_state": "Hai người đồng ý đi cùng nhau", "speaker": "Linh Nhi",
                 "dialogue": "Ta là người bảo hộ cổ ngọc. Chìa khóa mở cửa đền chính là vật này!",
                 "bubble_type": "speech", "narration": "", "layout_type": "square",
                 "image_prompt": "CHAR_002, medium close-up, holding glowing emerald jade artifact in both hands, divine green light reflecting on her gentle face, amber eyes, intricate runes, manga style, beautiful lighting"},
                {"panel_index": 6, "scene_id": "S02", "location": "Cổng cấm địa đền thượng",
                 "time_of_day": "noon", "weather": "ominous", "characters": ["CHAR_001"],
                 "action": "Mặt đất rung chuyển dữ dội, cự thạch trận thức tỉnh", "emotion": "bất ngờ",
                 "camera_angle": "low angle dynamic", "shot_type": "tall",
                 "prev_state": "Cổ ngọc phát sáng", "speaker": "Nguyễn Minh",
                 "dialogue": "Cẩn thận! Thạch thú thủ hộ thức tỉnh rồi!",
                 "bubble_type": "shout", "narration": "Mặt đất ầm ầm rung chuyển...", "layout_type": "tall",
                 "image_prompt": "CHAR_001, dynamic action stance, sword drawn with blue energy aura, stepping in front to protect companion, massive stone guardian statue awakening behind, glowing eyes, dust flying, intense manga action scene"},
                {"panel_index": 7, "scene_id": "S02", "location": "Chiến trường trước điện",
                 "time_of_day": "noon", "weather": "stormy", "characters": ["CHAR_001"],
                 "action": "Nguyễn Minh vung kiếm chém ra luồng kiếm khí xé gió", "emotion": "quyết liệt",
                 "camera_angle": "dramatic dynamic kinetic shot", "shot_type": "wide",
                 "prev_state": "Thạch thú tấn công", "speaker": "Nguyễn Minh",
                 "dialogue": "PHÁ THIÊN NHẤT KIẾM! ĐỠ LẤY!",
                 "bubble_type": "shout", "narration": "", "layout_type": "wide",
                 "image_prompt": "CHAR_001, dynamic sword slash pose, unleashed giant glowing blue sword energy wave cutting through stone debris, electric sparks, manga speedlines, high impact kinetic composition, top tier webtoon art"},
                {"panel_index": 8, "scene_id": "S02", "location": "Bên cạnh trụ đá",
                 "time_of_day": "noon", "weather": "mystical", "characters": ["CHAR_002"],
                 "action": "Linh Nhi kết ấn phong ấn trận pháp hỗ trợ", "emotion": "tập trung cao độ",
                 "camera_angle": "close-up hands and face", "shot_type": "square",
                 "prev_state": "Nguyễn Minh thu hút đòn tấn công", "speaker": "Linh Nhi",
                 "dialogue": "Nguyễn Minh, giữ chân nó thêm ba khắc nữa thôi!",
                 "bubble_type": "shout", "narration": "", "layout_type": "square",
                 "image_prompt": "CHAR_002, close-up, fast hand signs forming glowing magic seal, cherry blossom energy petals swirling, determined expression, sweat drop on brow, glowing pink runes, manga style, detailed"},
                {"panel_index": 9, "scene_id": "S03", "location": "Cửa đền mở ra",
                 "time_of_day": "afternoon", "weather": "golden divine light", "characters": ["CHAR_001", "CHAR_002"],
                 "action": "Thạch thú hóa thành tượng đá, cổng đền từ từ hé mở", "emotion": "thở phào nhẹ nhõm",
                 "camera_angle": "wide cinematic establishing shot", "shot_type": "wide",
                 "prev_state": "Trận pháp kích hoạt thành công", "speaker": "Linh Nhi",
                 "dialogue": "Thành công rồi... Cánh cổng dẫn vào cội nguồn sức mạnh đã mở!",
                 "bubble_type": "speech", "narration": "Khói bụi dần lắng xuống...", "layout_type": "wide",
                 "image_prompt": "Vast ancient temple doors swinging open, brilliant golden heavenly light pouring out onto two standing heroes CHAR_001 and CHAR_002, majestic stone pillars, mist, wide cinematic manga composition"},
                {"panel_index": 10, "scene_id": "S03", "location": "Điện Thần Thượng Cổ",
                 "time_of_day": "timeless", "weather": "starlight", "characters": ["CHAR_001"],
                 "action": "Bước vào điện, nhìn thấy cuộn bí kíp lơ lửng giữa trời sao", "emotion": "choáng ngợp",
                 "camera_angle": "low angle looking up", "shot_type": "tall",
                 "prev_state": "Cửa đền mở", "speaker": "Nguyễn Minh",
                 "dialogue": "Đây chính là... 'Cửu Thiên Thần Lục' mà phụ thân từng nhắc tới?",
                 "bubble_type": "thought", "narration": "Không gian bên trong như một dải ngân hà vô tận...", "layout_type": "tall",
                 "image_prompt": "CHAR_001, seen from behind and side, gazing in awe up at ancient glowing scroll floating in center of starlit celestial chamber, cosmic nebula colors, sparkling particles, manga style, stunning visual"},
                {"panel_index": 11, "scene_id": "S03", "location": "Tâm điện Thượng Cổ",
                 "time_of_day": "timeless", "weather": "divine light", "characters": ["CHAR_001", "CHAR_002"],
                 "action": "Hai người nhìn nhau gật đầu đồng thuận", "emotion": "tin tưởng gắn kết",
                 "camera_angle": "medium two-shot", "shot_type": "square",
                 "prev_state": "Bí kíp tỏa sáng", "speaker": "Linh Nhi",
                 "dialogue": "Từ giờ, chúng ta sẽ cùng nhau đồng hành trên con đường này.",
                 "bubble_type": "speech", "narration": "", "layout_type": "square",
                 "image_prompt": "CHAR_001 and CHAR_002 standing side by side looking at each other with warm trusting smiles, divine golden starlight ambient glow, elegant manga art style, emotive expression, detailed"},
                {"panel_index": 12, "scene_id": "S03", "location": "Bậc thềm Đền Thượng Cổ",
                 "time_of_day": "sunset", "weather": "golden dusk", "characters": ["CHAR_001", "CHAR_002"],
                 "action": "Đứng cạnh nhau ngắm nhìn giang sơn hùng vĩ phía chân trời", "emotion": "hào hùng",
                 "camera_angle": "epic wide landscape shot", "shot_type": "wide",
                 "prev_state": "Tiếp nhận bí kíp", "speaker": "Nguyễn Minh",
                 "dialogue": "Giang sơn vạn dặm... Hành trình vĩ đại của chúng ta chính thức bắt đầu!",
                 "bubble_type": "shout", "narration": "Một huyền thoại mới chuẩn bị khai sinh khắp lục địa...", "layout_type": "wide",
                 "image_prompt": "Two heroes CHAR_001 and CHAR_002 standing heroically side by side on grand temple balcony looking out at vast endless mountains and skies painted in breathtaking golden sunset, epic wide cinematic view, masterpiece manga style"}
            ]
        }
