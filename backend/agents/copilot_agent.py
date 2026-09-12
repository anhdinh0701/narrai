import os
import json
import re
from llm.groq_client import GroqClient
from agents.story_memory import StoryMemory

class CopilotAgent:
    def __init__(self):
        # Master Controller dung Key VIP va Model manh nhat
        self.llm = GroqClient(model_name="openai/gpt-oss-120b", api_key=os.environ.get("GROQ_API_KEY_COPILOT"))

    def process_event(self, event_type: str, event_data: str, memory: StoryMemory = None) -> dict:
        short_context = memory.get_short_context(max_chars=3000) if memory else "Chua co truyen."
        summaries = "\n".join(memory.chapter_summaries) if memory and memory.chapter_summaries else "Chua co."

        system_prompt = f"""Ban la TONG CHI HUY (Master Controller / AI Co-pilot) cua he thong tao truyen NarrAI.
Nhiem vu cua ban la giam sat, phan tich loi, va dieu phoi cac AI Agent khac de mang lai trai nghiem hoan hao cho nguoi dung.

THONG TIN HE THONG:
- Tom tat cot truyen da qua: {summaries}
- Noi dung truyen hien tai (cuoi): {short_context[-2000:] if short_context else 'Trong'}
- Gioi han he thong (Limit Awareness): Agent Viet Truyen bi gioi han toi da 6000 tokens/lan goi. Do do, neu nguoi dung yeu cau viet mot chuong QUA DAI, hay chia nho ra.

CAC LOAI SU KIEN (EVENTS) BAN CO THE NHAN:
- USER_CHAT: Nguoi dung go tin nhan.
- SYS_IMG_ERROR: Anh truyen tranh bi loi hien thi (404/502).
- SYS_LATENCY: He thong dang bi cham, qua 15s chua phan hoi.
- WRITER_DRAFT_READY: Agent Viet Truyen vua viet xong ban nhap, can ban DUYET.

QUY TAC DUYET BAI (PUSH-BACK):
- Khi nhan su kien WRITER_DRAFT_READY, neu van phong do, sai logic, lap tu, ban CO QUYEN bac bo va goi lenh `reject_and_rewrite`. Chi cho qua (`approve_draft`) neu chat luong xuat sac.

BAN PHAI TRA VE CHINH XAC JSON VOI CAU TRUC SAU (Va chi JSON):
{{
    "thought": "Suy nghi phan tich su kien, kiem tra gioi han he thong, danh gia chat luong.",
    "action": "reply_user" | "command_writer" | "reject_and_rewrite" | "heal_image" | "approve_draft",
    "action_params": {{
        "message": "(Neu action=reply_user) Tin nhan gui cho nguoi dung.",
        "instruction": "(Neu action=command_writer) Lenh cu the gui cho Agent Viet Truyen (chu y dan do dai de tranh hit limit).",
        "critique": "(Neu action=reject_and_rewrite) Loi che bai, bat loi ban nhap.",
        "panel_id": "(Neu action=heal_image) ID cua anh bi loi.",
        "new_prompt": "(Neu action=heal_image) Prompt moi toi uu hon de ve lai anh."
    }}
}}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"[EVENT: {event_type}]\nPAYLOAD: {event_data}"}
        ]

        try:
            response = self.llm.chat(messages, temperature=0.3, max_tokens=2000)
            json_match = re.search(r'\{.*\}', response.replace('\n', ' '), re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(response)
        except Exception as e:
            print(f"Master Controller Error: {e}")
            return {
                "thought": f"Loi he thong khi phan tich event: {str(e)}",
                "action": "reply_user",
                "action_params": {"message": "Xin loi, He thong chi huy dang gap truc trac nhe. Hay thu lai."}
            }
