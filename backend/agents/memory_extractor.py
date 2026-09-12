import os
"""
Memory Extractor Agent — Trích xuất và cập nhật bộ nhớ truyện sau mỗi chương.
Dùng model nhẹ qwen/qwen3.8-27b để tiết kiệm token và tốc độ.
"""
import json
import re
from llm.groq_client import GroqClient
from agents.story_memory import StoryBible, StoryMemory


class MemoryExtractor:
    def __init__(self):
        self.llm = GroqClient(model_name="qwen/qwen3.8-27b", api_key=os.environ.get("GROQ_API_KEY_BIBLE"))

    def extract_bible(self, refined_prompt: str) -> StoryBible:
        system_prompt = """Ban la chuyen gia phan tich cot truyen. Doc ban phac thao cot truyen va trich xuat thong tin thanh JSON.

DAU RA BAT BUOC la JSON voi cau truc:
{
    "title": "Tieu de truyen",
    "genre": "The loai (vi du: Fantasy, Romance, Kinh di...)",
    "characters": [
        {"name": "Ten nhan vat", "appearance": "Mo ta ngoai hinh chi tiet", "personality": "Tinh cach", "role": "Vai tro trong truyen"}
    ],
    "world_setting": "Boi canh the gioi va thoi gian",
    "main_plot": "Tom tat cot truyen chinh (timeline su kien)",
    "writing_style": "Phong cach viet mong muon"
}

CHI TRA VE JSON. KHONG GIAI THICH GI THEM."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"BAN PHAC THAO COT TRUYEN:\n{refined_prompt}\n\nHay trich xuat JSON:"}
        ]

        try:
            response = self.llm.chat(messages, temperature=0.3, max_tokens=2000)
            json_match = re.search(r'\{.*\}', response.replace('\n', ' '), re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                data = json.loads(response)

            bible = StoryBible(
                title=data.get("title", ""),
                genre=data.get("genre", ""),
                characters=data.get("characters", []),
                world_setting=data.get("world_setting", ""),
                main_plot=data.get("main_plot", ""),
                writing_style=data.get("writing_style", ""),
                refined_prompt=refined_prompt
            )
            return bible
        except Exception as e:
            print(f"MemoryExtractor.extract_bible error: {e}")
            return StoryBible(
                title="Truyen chua dat ten",
                refined_prompt=refined_prompt,
                main_plot=refined_prompt[:500]
            )

    def extract_memory(self, new_chapter_text: str, current_memory: StoryMemory) -> StoryMemory:
        system_prompt = f"""Ban la chuyen gia phan tich noi dung truyen. Doc chuong truyen moi viet va trich xuat thong tin de cap nhat bo nho.

THONG TIN HIEN TAI:
- So chuong da viet: {current_memory.current_chapter}
- Nhan vat da biet: {json.dumps(current_memory.character_states, ensure_ascii=False) if current_memory.character_states else 'Chua co'}
- Tuyen truyen dang mo: {json.dumps(current_memory.unresolved_threads, ensure_ascii=False) if current_memory.unresolved_threads else 'Chua co'}

DAU RA BAT BUOC la JSON:
{{
    "chapter_summary": "Tom tat chuong nay trong 2-3 cau (duoi 100 tu)",
    "character_states": {{"Ten nhan vat": "Trang thai/cam xuc hien tai sau chuong nay"}},
    "new_threads": ["Tuyen truyen MOI xuat hien trong chuong nay"],
    "resolved_threads": ["Tuyen truyen DA DUOC GIAI QUYET trong chuong nay"],
    "relationships": {{"NhanVat1-NhanVat2": "Mo ta moi quan he hien tai"}}
}}

CHI TRA VE JSON. KHONG GIAI THICH."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"CHUONG MOI VIET:\n{new_chapter_text[:4000]}\n\nHay trich xuat JSON:"}
        ]

        try:
            response = self.llm.chat(messages, temperature=0.3, max_tokens=1500)
            json_match = re.search(r'\{.*\}', response.replace('\n', ' '), re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                data = json.loads(response)

            # Update memory
            current_memory.chapter_summaries.append(
                data.get("chapter_summary", f"Chuong {current_memory.current_chapter}")
            )

            new_states = data.get("character_states", {})
            current_memory.character_states.update(new_states)

            new_threads = data.get("new_threads", [])
            for t in new_threads:
                if t and t not in current_memory.unresolved_threads:
                    current_memory.unresolved_threads.append(t)

            resolved = data.get("resolved_threads", [])
            for t in resolved:
                if t in current_memory.unresolved_threads:
                    current_memory.unresolved_threads.remove(t)

            new_relations = data.get("relationships", {})
            current_memory.relationship_map.update(new_relations)

            return current_memory

        except Exception as e:
            print(f"MemoryExtractor.extract_memory error: {e}")
            current_memory.chapter_summaries.append(
                f"Chuong {current_memory.current_chapter} (tu dong tom tat that bai)"
            )
            return current_memory
