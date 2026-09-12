from llm.groq_client import GroqClient

class EditorAgent:
    def __init__(self):
        self.llm = GroqClient(model_name="openai/gpt-oss-120b")
        
    def edit_text(self, original_text: str, instruction: str) -> str:
        """
        Agent 3 (Editor): Nhận đoạn văn bị bôi đen và yêu cầu sửa, trả về đoạn văn mới.
        """
        system_prompt = """Bạn là một biên tập viên tiểu thuyết chuyên nghiệp và một nhà văn lão luyện.
Nhiệm vụ của bạn là đọc một "Đoạn văn gốc" (do người dùng bôi đen) và một "Chỉ thị sửa đổi", sau đó viết lại đoạn văn đó sao cho đáp ứng ĐÚNG CHỈ THỊ, mượt mà và tự nhiên nhất.
TUYỆT ĐỐI CHỈ TRẢ VỀ ĐOẠN VĂN ĐÃ SỬA. KHÔNG giải thích, KHÔNG thêm lời chào, KHÔNG dùng dấu ngoặc kép thừa."""

        user_content = f"""ĐOẠN VĂN GỐC:
{original_text}

CHỈ THỊ SỬA ĐỔI CỦA TÁC GIẢ:
{instruction}

Hãy viết lại đoạn văn trên:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        # We use a slightly lower temperature for editing to keep it focused on the instruction
        response = self.llm.chat(messages, temperature=0.6, max_tokens=1000)
        return response.strip()
