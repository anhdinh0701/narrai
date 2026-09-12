import os
from llm.groq_client import GroqClient
import json

class QARefiner:
    def __init__(self):
        self.llm = GroqClient(model_name="qwen/qwen3.8-27b", api_key=os.environ.get("GROQ_API_KEY_BIBLE"))
    
    def chat_interview(self, chat_history: list) -> str:
        """
        Agent 1 Phase 1 (Interactive): Chat với người dùng để hỏi và gợi ý phát triển ý tưởng.
        chat_history: list of dicts [{'role': 'user'/'assistant', 'content': '...'}]
        """
        system_prompt = """Bạn là một người đồng sáng tác truyện (Co-writer) thân thiện, thấu hiểu và giàu trí tưởng tượng.
Nhiệm vụ của bạn là trò chuyện với người dùng để phác thảo cốt truyện. Hãy Đặt Từng Câu Hỏi Một. Đừng hỏi dồn dập.

Quy tắc giao tiếp:
1. Mỗi lần trả lời, chỉ hỏi TỐI ĐA 1 ĐẾN 2 CÂU HỎI. Luôn kèm theo các ví dụ/gợi ý cụ thể (trong ngoặc đơn) để người dùng dễ dàng chọn hoặc trả lời.
2. Tránh xa các thuật ngữ chuyên ngành văn học (như inciting incident, plot twist, character arc). Dùng ngôn từ bình dị, thân thiện.
3. Liên tục khen ngợi và tạo cảm hứng.
4. ĐÁNH GIÁ ĐỘ ĐỦ CỦA CỐT TRUYỆN: Nếu bạn cảm thấy cốt truyện đã đủ nhân vật, bối cảnh, biến cố, và kết thúc (hoặc nếu người dùng muốn dừng việc hỏi đáp), hãy kết thúc tin nhắn bằng từ khóa đặc biệt: [READY]
Từ khóa [READY] sẽ báo hiệu cho hệ thống tự động chuyển sang bước viết truyện.

Ví dụ về một tin nhắn tốt:
"Ý tưởng xuyên không này tuyệt quá! Cô gái này tính cách thế nào vậy bạn? (Ví dụ: thông minh lanh lợi, hay vụng về đáng yêu?)"

TUYỆT ĐỐI KHÔNG dùng tiếng Anh trộn lẫn vào tiếng Việt."""
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        
        response = self.llm.chat(
            messages, 
            temperature=0.7, 
            max_tokens=300
        )
        return response
    
    def refine_prompt(self, chat_history: list) -> str:
        """
        Agent 1 Phase 2: Cô đọng toàn bộ đoạn chat thành Story Brief.
        """
        system_prompt = """Bạn là chuyên gia thẩm định và biên soạn kịch bản truyện chuyên nghiệp.
TUYỆT ĐỐI CHỈ SỬ DỤNG TIẾNG VIỆT, không được pha trộn tiếng Anh hoặc bất kỳ ngôn ngữ nào khác.
Dựa trên toàn bộ lịch sử trò chuyện giữa người dùng và người hỏi đáp, hãy tổng hợp thành một "Bản Phác Thảo Cốt Truyện" mạch lạc. Giữ nguyên 100% ý muốn cốt lõi của tác giả đã thống nhất trong khung chat. Không tự ý bịa thêm chi tiết.

YÊU CẦU TRỌNG TÂM: Mạch truyện phải được thiết kế XUYÊN SUỐT, logic chặt chẽ, đi thẳng vào các biến cố cốt truyện thay vì lan man hoa mỹ.

Cấu trúc Bản Phác Thảo Cốt Truyện bắt buộc gồm:
1. TIÊU ĐỀ CHÍNH THỨC: Chọn 1 tiêu đề hay nhất, sát với nội dung nhất.
2. THỂ LOẠI VÀ KHÔNG KHÍ: Liệt kê các thể loại và cảm xúc chủ đạo.
3. NHÂN VẬT CHÍNH: Tên gọi, tính cách, hoàn cảnh hiện tại (tập trung vào hành động và chiều sâu tâm lý, bớt tả ngoại hình hoa mỹ).
4. BỐI CẢNH: Không gian và thời gian diễn ra câu chuyện.
5. TIẾN TRÌNH CỐT TRUYỆN (Sườn logic nghiêm ngặt):
   - Mở đầu: Câu chuyện bắt đầu thế nào. Khởi mào sự kiện.
   - Diễn biến: Các sự kiện chính xảy ra, xung đột và hành động thực tế.
   - Cao trào: Điểm căng thẳng nhất, bùng nổ logic, không dùng phép màu vô lý.
   - Kết thúc: Hướng giải quyết.

YÊU CẦU:
- KHÔNG dùng từ tiếng Anh.
- Tôn trọng tuyệt đối các tình tiết đã được chốt trong cuộc trò chuyện."""
        
        # We wrap the chat history into a string representation for the Refiner agent
        chat_text = ""
        for msg in chat_history:
            role = "Tác giả (Người dùng)" if msg["role"] == "user" else "Co-writer (AI)"
            chat_text += f"\n{role}: {msg['content']}"
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""LỊCH SỬ TRÒ CHUYỆN ĐÃ CHỐT:
{chat_text}

Hãy tổng hợp và viết Bản Phác Thảo Cốt Truyện chi tiết bằng Tiếng Việt:"""}
        ]
        
        response = self.llm.chat(messages, temperature=0.6, max_tokens=1500)
        return response
