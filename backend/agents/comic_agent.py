import os
import json
import re
from llm.groq_client import GroqClient

MODEL = "qwen/qwen3.8-27b"

COMIC_DIRECTOR_SYSTEM_PROMPT = """Bạn là một Đạo diễn Truyện tranh (Comic Director) chuyên nghiệp cấp cao.

VAI TRÒ DUY NHẤT: Đọc hiểu nội dung tiểu thuyết tiếng Việt và chuyển thể thành kịch bản truyện tranh (Comic Script) dưới dạng JSON.

QUY TẮC NGHIÊM NGẶT:
1. TÍNH NHẤT QUÁN NHÂN VẬT (Character Consistency):
   - Trước khi phân cảnh, bạn PHẢI xác định ngoại hình chi tiết của từng nhân vật chính (tóc, mắt, trang phục, đặc điểm nhận dạng).
   - TRONG MỌI KHUNG TRANH có nhân vật, bạn PHẢI lặp lại mô tả ngoại hình đó trong image_prompt. Ví dụ: "A young woman with long black hair, wearing a white ao dai and red scarf..."
   
2. SỐ LƯỢNG PANEL: Phân rã TOÀN BỘ nội dung thành ÍT NHẤT 15 đến 20 khung tranh (Panels). KHÔNG ĐƯỢC ít hơn 10 khung.

3. CHẤT LƯỢNG IMAGE PROMPT:
   - Viết bằng TIẾNG ANH, siêu chi tiết.
   - Luôn bao gồm: Ngoại hình nhân vật + Bối cảnh + Góc máy + Ánh sáng + Phong cách nghệ thuật.
   - Thêm "manga style, high quality, detailed" vào cuối mỗi prompt.

4. ĐẦU RA: CHỈ trả về MỘT MẢNG JSON HỢP LỆ. KHÔNG được viết bất kỳ text giải thích nào trước hoặc sau JSON.
   Mỗi Object gồm:
   - "panel_index": số thứ tự (1, 2, 3...)
   - "image_prompt": mô tả ảnh tiếng Anh (có ngoại hình nhân vật)
   - "dialogue_text": lời thoại tiếng Việt (ngắn gọn, dưới 50 từ)
   - "layout_type": "square", "wide", hoặc "tall"
"""

class ComicDirectorAgent:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY_COMIC") or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Thiếu GROQ_API_KEY_COMIC hoặc GROQ_API_KEY")
        self.llm = GroqClient(model_name=MODEL, api_key=api_key)

    def generate_comic_script(self, story_text: str):
        try:
            response = self.llm.chat(
                messages=[
                    {
                        "role": "system",
                        "content": COMIC_DIRECTOR_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": f"Hãy chuyển thể nội dung tiểu thuyết sau thành kịch bản truyện tranh JSON:\n\n{story_text}"
                    }
                ],
                temperature=0.7,
                max_tokens=3500
            )
            raw_output = response
            
            # Clean up markdown formatting or text preamble
            match = re.search(r'\[.*\]', raw_output, re.DOTALL)
            if match:
                raw_output = match.group(0)
                
            script_data = json.loads(raw_output.strip())
            return script_data
        except Exception as e:
            print("Error parsing comic script:", e)
            return [
                {"panel_index": 1, "image_prompt": "A cinematic wide shot of a beautiful landscape, manga style, high quality", "dialogue_text": "Ngày xửa ngày xưa...", "layout_type": "wide"},
                {"panel_index": 2, "image_prompt": "Close up of a mysterious character with dark eyes, manga style, detailed", "dialogue_text": "Có một bí mật...", "layout_type": "tall"},
                {"panel_index": 3, "image_prompt": "An action scene with sword clash, dynamic angle, manga style", "dialogue_text": "KENG!", "layout_type": "square"},
                {"panel_index": 4, "image_prompt": "A character walking away into the sunset, wide angle, manga style", "dialogue_text": "Cuộc hành trình bắt đầu.", "layout_type": "wide"}
            ]
