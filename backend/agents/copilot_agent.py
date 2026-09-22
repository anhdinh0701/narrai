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

    # ── Intent: detect panel-generation requests ────────────────────────
    PANEL_INTENT_PATTERNS = [
        r"tạo\s*(thêm|thêm\s*)?tranh",
        r"vẽ\s*(thêm|thêm\s*)?tranh",
        r"tạo\s*(thêm\s*)?ảnh",
        r"vẽ\s*(thêm\s*)?ảnh",
        r"thêm\s*(tranh|ảnh|panel|khung)",
        r"tạo\s*(thêm\s*)?panel",
        r"generate\s*(more\s*)?panel",
        r"add\s*(more\s*)?panel",
        r"vẽ\s*khung",
        r"tạo\s*khung",
        r"sinh\s*(thêm\s*)?(ảnh|tranh|panel)",
        r"(vẽ|tạo)\s*(minh\s*họa|hình\s*ảnh)",
    ]

    def _detect_panel_intent(self, message: str) -> bool:
        msg_lower = message.lower()
        for pattern in self.PANEL_INTENT_PATTERNS:
            if re.search(pattern, msg_lower):
                return True
        return False

    def _extract_panel_context(self, message: str, story_context: str) -> dict:
        """Extract scene description and panel number hint from user message."""
        # Look for panel/khung number mention
        panel_num_match = re.search(r'(?:khung|panel|tranh|ảnh)\s*(?:số\s*)?(\d+)', message.lower())
        panel_number = int(panel_num_match.group(1)) if panel_num_match else None

        # Build a scene description from the message itself + story context
        scene_description = message.strip()

        return {
            "panel_number": panel_number,
            "scene_description": scene_description,
            "story_context": story_context[-2000:] if story_context else "",
        }

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

            # ── Fast-path: generate_panel intent ──────────────────────
            if self._detect_panel_intent(user_message):
                panel_ctx = self._extract_panel_context(user_message, short_context or story_context)
                # Ask LLM to create a good image prompt from the request + story context
                prompt_messages = [
                    {"role": "system", "content": (
                        "Bạn là chuyên gia tạo prompt ảnh truyện tranh theo phong cách anime/manga.\n"
                        "Dựa vào yêu cầu của người dùng và nội dung truyện, hãy tạo:\n"
                        "1. Một câu trả lời ngắn gọn thân thiện (tiếng Việt) xác nhận bạn đang tạo tranh.\n"
                        "2. Một image_prompt tiếng Anh chi tiết cho Stable Diffusion / Animagine XL:\n"
                        "   - Mô tả nhân vật, cảnh quan, ánh sáng, góc chụp.\n"
                        "   - Style: anime, manga panel, high quality, detailed.\n\n"
                        "TRẢ VỀ JSON:\n"
                        "{\"message\": \"...\", \"image_prompt\": \"...\"}"
                    )},
                    {"role": "user", "content": (
                        f"Yêu cầu: {user_message}\n\n"
                        f"Nội dung truyện:\n{panel_ctx['story_context']}"
                    )}
                ]
                try:
                    llm_resp = self._call_llm(prompt_messages, temperature=0.6, max_tokens=600)
                    parsed_prompt = {}
                    # Try JSON parse
                    try:
                        m = re.search(r'\{.*\}', llm_resp, re.DOTALL)
                        if m:
                            parsed_prompt = json.loads(m.group(0))
                    except Exception:
                        pass

                    image_prompt = parsed_prompt.get("image_prompt") or (
                        f"anime manga panel, {user_message}, high quality, detailed, "
                        f"vibrant colors, dramatic lighting"
                    )
                    confirm_message = parsed_prompt.get("message") or "Đang tạo tranh cho bạn... ⏳"

                    return {
                        "thought": "User requested panel generation",
                        "action": "generate_panel",
                        "action_params": {
                            "message": confirm_message,
                            "image_prompt": image_prompt,
                            "panel_number": panel_ctx.get("panel_number"),
                        }
                    }
                except Exception as e:
                    print(f"[Copilot] Panel intent LLM error: {e}")
                    return {
                        "thought": "Fallback generate_panel",
                        "action": "generate_panel",
                        "action_params": {
                            "message": "Đang tạo tranh cho bạn... ⏳",
                            "image_prompt": (
                                f"anime manga panel, {user_message}, "
                                f"high quality, detailed, vibrant colors"
                            ),
                            "panel_number": panel_ctx.get("panel_number"),
                        }
                    }

            # ── Normal chat flow ───────────────────────────────────────
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
                msg_match = re.search(r'"message"\s*:\s*"(.*?)(?:"\s*,\s*"|\"\s*\}\s*\})', candidate, re.DOTALL)
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

