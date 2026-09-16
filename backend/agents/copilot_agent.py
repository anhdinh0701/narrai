import os
import json
import re
from llm.groq_client import GroqClient
from agents.story_memory import StoryMemory

class CopilotAgent:
    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY_COPILOT") or os.environ.get("GROQ_API_KEY")
        self.llm = GroqClient(model_name="openai/gpt-oss-120b", api_key=self.api_key)
        self.fallback_llm = None

    def _call_llm(self, messages, temperature=0.7, max_tokens=1500):
        try:
            res = self.llm.chat(messages, temperature=temperature, max_tokens=max_tokens)
            if res and res.strip():
                return res.strip()
        except Exception as e:
            print(f"[Copilot] Primary model error: {e}, falling back to qwen3.8-27b")

        if self.fallback_llm is None:
            self.fallback_llm = GroqClient(model_name="qwen/qwen3.8-27b", api_key=self.api_key)
        return self.fallback_llm.chat(messages, temperature=temperature, max_tokens=max_tokens).strip()

    def process_event(self, event_type: str, event_data: str, memory: StoryMemory = None) -> dict:
        user_message = event_data
        story_context = ""
        try:
            parsed = json.loads(event_data)
            if isinstance(parsed, dict):
                user_message = parsed.get("user_message", event_data)
                story_context = parsed.get("current_story", "")
        except:
            pass

        short_context = memory.get_short_context(max_chars=3000) if memory else story_context
        summaries = "\n".join(memory.chapter_summaries) if memory and memory.chapter_summaries else "Chưa có."

        # Xử lý sự kiện trò chuyện trực tiếp (USER_CHAT)
        if event_type == "USER_CHAT":
            system_prompt = f"""Bạn là Trợ lý AI Sáng Tác Thông Minh (NarrAI Co-pilot) và Đồng Tác Giả.
Nhiệm vụ hàng đầu của bạn là GIAO TIẾP VÀ HỖ TRỢ NGƯỜI DÙNG NHƯ MỘT NGƯỜI BẠN SÁNG TÁC THỰC THỤ:
1. Giao tiếp tự nhiên, thân thiện, lịch thiệp, thông thái bằng tiếng Việt tự nhiên.
2. Trả lời chu đáo khi người dùng chào hỏi, hỏi đáp, tâm sự, xin gợi ý ý tưởng, phát triển nhân vật, xây dựng thế giới (world-building), hoặc thảo luận về bất kỳ chủ đề sáng tác nào.
3. Nếu người dùng ra lệnh rõ ràng yêu cầu VIẾT TIẾP một chương truyện mới, THAY ĐỔI trực tiếp văn bản đang viết, hoặc BẺ LÁI cốt truyện trong bản thảo, hãy xuất lệnh `command_writer`.
4. Nếu người dùng chỉ đang trò chuyện, hỏi đáp, yêu cầu tư vấn hoặc lên ý tưởng, hãy xuất `reply_user` với câu trả lời đầy đủ, chi tiết, hấp dẫn.

Thông tin hiện tại:
- Cốt truyện đã ghi nhận: {summaries}
- Nội dung bản thảo gần nhất: {short_context[-1500:] if short_context else 'Chưa có bản thảo.'}

ĐỊNH DẠNG PHẢN HỒI (Ưu tiên JSON chuẩn):
{{
    "thought": "Suy nghĩ phân tích ý định của người dùng",
    "action": "reply_user" | "command_writer",
    "action_params": {{
        "message": "Nội dung phản hồi hoàn chỉnh, ân cần và giàu ý tưởng cho người dùng",
        "instruction": "(Chỉ có khi action=command_writer) Hướng dẫn chi tiết cho Agent viết truyện"
    }}
}}
"""
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]

            try:
                response = self._call_llm(messages, temperature=0.7, max_tokens=1500)
                return self._parse_copilot_response(response)
            except Exception as e:
                print(f"[Copilot] Conversation exception: {e}")
                return {
                    "thought": "Fallback pleasant reply",
                    "action": "reply_user",
                    "action_params": {"message": "Chào bạn! Tôi là trợ lý sáng tác NarrAI. Tôi có thể giúp bạn phát triển ý tưởng, xây dựng cốt truyện hoặc viết tiếp bản thảo. Bạn muốn chúng ta bắt đầu từ đâu?"}
                }

    def _parse_copilot_response(self, response: str) -> dict:
        text = (response or "").strip()
        # 1. Direct JSON parse
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and "action" in parsed:
                return parsed
        except Exception:
            pass

        # 2. Markdown code block ```json ... ```
        block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if block_match:
            try:
                parsed = json.loads(block_match.group(1))
                if isinstance(parsed, dict) and "action" in parsed:
                    return parsed
            except Exception:
                pass

        # 3. Outer { ... }
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            candidate = text[start_idx:end_idx+1]
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict) and "action" in parsed:
                    return parsed
            except Exception:
                # Extract message field if unescaped newlines prevented JSON parsing
                msg_match = re.search(r'"message"\s*:\s*"(.*?)(?:"\s*,\s*"|"\s*\}\s*\})', candidate, re.DOTALL)
                if msg_match:
                    clean_msg = msg_match.group(1).encode().decode('unicode_escape', errors='ignore')
                    return {
                        "thought": "Extracted message",
                        "action": "reply_user",
                        "action_params": {"message": clean_msg}
                    }

        # 4. Natural conversational text
        clean_text = text
        if clean_text.startswith('{') and '"message"' in clean_text:
            m = re.search(r'"message"\s*:\s*"(.*)', clean_text, re.DOTALL)
            if m:
                clean_text = m.group(1).rstrip('"} \n\r\t')

        return {
            "thought": "Direct conversational response",
            "action": "reply_user",
            "action_params": {"message": clean_text}
        }

        # Các sự kiện kỹ thuật khác (SYS_IMG_ERROR, SYS_LATENCY, WRITER_DRAFT_READY...)
        system_prompt = f"""Bạn là TỔNG CHỈ HUY (Master Controller) của hệ thống NarrAI.
Nhiệm vụ của bạn là giám sát, phân tích lỗi, và điều phối các AI Agent khác.

THÔNG TIN HỆ THỐNG:
- Tóm tắt cốt truyện: {summaries}
- Nội dung gần nhất: {short_context[-2000:] if short_context else 'Trống'}

BẠN PHẢI TRẢ VỀ JSON:
{{
    "thought": "Suy nghĩ phân tích sự kiện",
    "action": "reply_user" | "command_writer" | "reject_and_rewrite" | "heal_image" | "approve_draft",
    "action_params": {{
        "message": "(Nếu action=reply_user) Tin nhắn gửi cho người dùng.",
        "instruction": "(Nếu action=command_writer) Lệnh cụ thể gửi cho Agent Viết Truyện.",
        "critique": "(Nếu action=reject_and_rewrite) Lời chê bai, bắt lỗi bản thảo."
    }}
}}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"[EVENT: {event_type}]\nPAYLOAD: {event_data}"}
        ]

        try:
            response = self._call_llm(messages, temperature=0.3, max_tokens=1000)
            json_match = re.search(r'\{.*\}', response.replace('\n', ' '), re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(response)
        except Exception as e:
            print(f"[Copilot] System event error: {e}")
            return {
                "thought": f"Lỗi phân tích: {str(e)}",
                "action": "reply_user",
                "action_params": {"message": "Hệ thống đã ghi nhận yêu cầu và sẵn sàng hỗ trợ bạn."}
            }

