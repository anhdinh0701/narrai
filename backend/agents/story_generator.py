from llm.groq_client import GroqClient
from agents.story_memory import StoryMemory


WRITING_RULES = """Quy tac sang tac BAT BUOC:
1. CAU TRUC 3 HOI: Setup (25%) -> Confrontation (50%) -> Resolution (25%).
2. KIEN TRUC CHUONG: Moi chuong la cau chuyen thu nho co tu tri. Cau truc: Mo dau loi cuon -> Xung dot leo thang -> Cao trao -> Ket thuc hap dan. Toi thieu 800 tu/chuong.
3. CHUOI NHAN QUA: Khong ket noi su kien bang "Va roi...". Moi su kien phai la "Vi vay..." hoac "Nhung...".
4. SCENE & SEQUEL: Luan phien canh chu dong (muc tieu -> xung dot -> that bai) va canh phan ung (soc -> lua chon -> quyet dinh moi).
5. VALUE SHIFT: Cuoi moi chuong, trang thai nhan vat BAT BUOC thay doi (Tich cuc <-> Tieu cuc).
6. MO DAU: Bat dau ngay giua hanh dong (In medias res). Neo nguoi doc bang giac quan cu the.
7. KET THUC: Luon ket bang Cliffhanger - moi de doa moi, cau hoi chua loi dap, hoac lat nguoc tinh the.
8. VAN PHONG: Show don't tell. Ta qua hanh dong va doi thoai. TUYET DOI KHONG in ra nhan ky thuat nhu "Canh Chu Dong", "Muc tieu:", "Xung dot:", "Value Shift". Viet VAN XUOI THUAN TUY."""


class StoryGenerator:
    def __init__(self):
        self.llm = GroqClient(model_name="openai/gpt-oss-120b")

    def _get_config(self, story_length: str):
        config = {
            "short": {"word_range": "Khoang 1200 den 2200 tu", "max_tokens": 5500, "chapter_mode": False},
            "medium": {"word_range": "Khoang 2500 den 4000 tu", "max_tokens": 6000, "chapter_mode": False},
            "long": {"word_range": "Khoang 1800 den 2500 tu cho CHUONG NAY", "max_tokens": 6000, "chapter_mode": True}
        }
        return config.get(story_length, config["medium"])

    def _build_prompt(self, refined_prompt: str, story_length: str):
        cfg = self._get_config(story_length)

        system_prompt = f"""Ban la mot tieu thuyet gia xuat chung tam co quoc te, chuyen sang tac truyen bang tieng Viet.
TUYET DOI CHI VIET BANG TIENG VIET, khong duoc pha tron tieng Anh.
Nhiem vu: Dua vao "Ban Phac Thao Cot Truyen", hay viet cau chuyen hoan chinh, bam sat tuyet doi vao cot truyen. Khong doi ten nhan vat hay chech huong.

{WRITING_RULES}

DO DAI: Khoang {cfg['word_range']}. Khai trien chi tiet tung tinh huong.
"""
        if cfg['chapter_mode']:
            system_prompt += """
CHE DO VIET TUNG CHUONG:
- Chi duoc viet DUY NHAT 1 CHUONG (1800-2500 tu).
- Chuong co tieu de: ## Chuong X: [Ten chuong]
- KET THUC bang Cliffhanger manh me.
- KHONG viet them chuong nao khac."""
        else:
            system_prompt += """
QUY TAC CHUONG:
- Moi chuong co Tieu de: ## Chuong X: [Ten chuong]
- Toi thieu 800 tu/chuong. Truyen ngan: toi da 3-4 chuong. Truyen trung binh: toi da 5-6 chuong."""

        system_prompt += """

Ban Phac Thao Cot Truyen:
Quy tac dinh dang:
- Dung markdown (##) cho tieu de Chuong.
- Bat dau NGAY LAP TUC bang: **[TEN TIEU DE TRUYEN]** o dong dau tien.
- TUYET DOI KHONG them loi mo dau hay ket thuc mang tinh tro chuyen."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"BAN PHAC THAO COT TRUYEN YEU CAU:\n---\n{refined_prompt}\n---\n\nHay bat dau viet ngay bay gio:"}
        ]
        return messages, cfg["max_tokens"]

    # ===== LEGACY METHODS (giữ tương thích ngược) =====
    def generate_story(self, refined_prompt: str, story_length: str = "medium") -> str:
        messages, max_tokens = self._build_prompt(refined_prompt, story_length)
        return self.llm.chat(messages, temperature=0.8, max_tokens=max_tokens)

    def generate_story_stream(self, refined_prompt: str, story_length: str = "medium"):
        messages, max_tokens = self._build_prompt(refined_prompt, story_length)
        return self.llm.chat_stream(messages, temperature=0.8, max_tokens=max_tokens)

    # ===== NEW: Memory-based Chapter Generation =====
    def generate_chapter_stream(self, memory: StoryMemory, user_instruction: str = ""):
        """Viết 1 chương mới dựa trên Memory System (streaming)."""
        bible_block = memory.story_bible.to_prompt_block()
        memory_block = memory.to_prompt_block()
        short_context = memory.get_short_context(max_chars=6000)
        next_chapter = memory.current_chapter + 1

        system_prompt = f"""Ban la tac gia dang truc tiep viet mot chuong tieu thuyet bang tieng Viet.
    NHIEM VU CUA BAN LA VIET VAN XUOI NGAY BAY GIO, khong phan tich va khong hoi lai nguoi dung.
    TUYET DOI KHONG viet loi xin loi, khong nhac lai chi dan, khong noi rang ban chi duoc viet mot chuong,
    khong mo ta nhiem vu cua ban, va khong tra loi theo dang tro chuyen.
    TUYET DOI CHI VIET BANG TIENG VIET.

{bible_block}

{memory_block}

{WRITING_RULES}

NHIEM VU HIEN TAI: Viet CHUONG {next_chapter} cua cau chuyen, bat dau ngay bang tieu de va van xuoi.
- Chi viet DUY NHAT 1 chuong, dai 2000-3000 tu.
- Bat dau bang: ## Chuong {next_chapter}: [Ten chuong]
- Phai tiep noi tu nhien voi noi dung da viet truoc do.
- GIAI QUYET it nhat 1 tuyen truyen dang mo va TAO RA it nhat 1 tuyen truyen moi.
- Ket thuc bang Cliffhanger manh me.
- TUYET DOI KHONG in ra nhan ky thuat. Viet van xuoi thuan tuy.
- TUYET DOI KHONG them loi mo dau hay ket thuc mang tinh tro chuyen."""

        if user_instruction:
            system_prompt += f"\n\nYEU CAU DAC BIET TU TAC GIA: {user_instruction}"

        user_msg = f"Hay viet CHUONG {next_chapter} ngay bay gio. Dong dau tien phai la: ## Chuong {next_chapter}: [Ten chuong]. Sau do viet ngay van xuoi, khong giai thich."
        if short_context:
            user_msg = f"NOI DUNG GAN NHAT DA VIET:\n---\n{short_context[-3000:]}\n---\n\nHay viet CHUONG {next_chapter} tiep noi tu nhien. Dong dau tien phai la: ## Chuong {next_chapter}: [Ten chuong]. Khong giai thich, chi viet van xuoi:"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]
        return self.llm.chat_stream(messages, temperature=0.8, max_tokens=6000)

    def generate_ending_stream(self, memory: StoryMemory):
        """Viết đoạn kết thúc truyện dựa trên Memory."""
        bible_block = memory.story_bible.to_prompt_block()
        memory_block = memory.to_prompt_block()
        short_context = memory.get_short_context(max_chars=6000)

        system_prompt = f"""Ban la mot tieu thuyet gia xuat chung, chuyen sang tac truyen bang tieng Viet.
TUYET DOI CHI VIET BANG TIENG VIET.

{bible_block}

{memory_block}

{WRITING_RULES}

NHIEM VU: Viet DOAN KET THUC cho cau chuyen.
- Goi gon TAT CA cac tuyen truyen dang mo.
- Giai quyet xung dot chinh.
- Mang lai cam xuc tron ven cho nguoi doc.
- Khong ket thuc dot ngot hay gay mach.
- Dai toi thieu 2000 tu.
- TUYET DOI KHONG in ra nhan ky thuat."""

        user_msg = f"NOI DUNG GAN NHAT:\n---\n{short_context[-3000:]}\n---\n\nHay viet doan ket thuc cau chuyen:"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]
        return self.llm.chat_stream(messages, temperature=0.8, max_tokens=6000)

    # ===== LEGACY: Chat instruction (giữ tương thích) =====
    def handle_chat_instruction(self, current_story: str, user_message: str):
        import json
        import re

        system_prompt = f"""Ban la Tro ly AI dong sang tac tieu thuyet.

NHIEM VU: Doc lenh cua nguoi dung va thuc hien chinh xac.
- Neu ho yeu cau "viet tiep", "them nhan vat", "doi huong": VIET TIEP DOAN TRUYEN MOI.
- Neu ho yeu cau "ket thuc truyen": Viet doan ket thuc mach lac.
- Neu ho chi hoi dap binh thuong: Tra loi than thien.

TRUYEN DA VIET TU TRUOC (5000 ky tu cuoi):
---
{current_story[-5000:] if len(current_story) > 5000 else current_story}
---

LENH CUA NGUOI DUNG: "{user_message}"

DAU RA BAT BUOC LA JSON:
{{
    "chat_reply": "Cau tra loi ngan gon gui cho nguoi dung",
    "new_story_content": "Phan truyen MOI VIET THEM. Neu khong can viet them, de chuoi rong."
}}"""
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Hay thuc hien yeu cau va tra ve JSON."}
            ]
            response = self.llm.chat(messages=messages, temperature=0.7, max_tokens=4000)
            json_match = re.search(r'\{.*\}', response.replace('\n', ' '), re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(response)
        except Exception as e:
            print("Chat Error:", e)
            return {"chat_reply": "Xin loi, da co loi xay ra.", "new_story_content": ""}
