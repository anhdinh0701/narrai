"""
Story Memory Module
"""
import json
import uuid


class StoryBible:
    def __init__(self, title="", genre="", characters=None, world_setting="",
                 main_plot="", writing_style="", refined_prompt=""):
        self.title = title
        self.genre = genre
        self.characters = characters or []
        self.world_setting = world_setting
        self.main_plot = main_plot
        self.writing_style = writing_style
        self.refined_prompt = refined_prompt

    def to_prompt_block(self):
        chars_text = ""
        for c in self.characters:
            name = c.get("name", "?")
            appearance = c.get("appearance", "")
            personality = c.get("personality", "")
            role = c.get("role", "")
            chars_text += f"\n  - {name}: {role}. Ngoai hinh: {appearance}. Tinh cach: {personality}."
        return f"=== STORY BIBLE ===\nTieu de: {self.title}\nThe loai: {self.genre}\nBoi canh: {self.world_setting}\nNhan vat chinh:{chars_text}\nCot truyen chinh: {self.main_plot}\nPhong cach viet: {self.writing_style}\n"

    def to_dict(self):
        return {"title": self.title, "genre": self.genre, "characters": self.characters,
                "world_setting": self.world_setting, "main_plot": self.main_plot,
                "writing_style": self.writing_style, "refined_prompt": self.refined_prompt}

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class StoryMemory:
    def __init__(self, story_bible=None):
        self.session_id = str(uuid.uuid4())
        self.story_bible = story_bible or StoryBible()
        self.chapter_summaries = []
        self.character_states = {}
        self.unresolved_threads = []
        self.relationship_map = {}
        self.current_chapter = 0
        self.full_text = ""

    def to_prompt_block(self):
        summaries = ""
        for i, s in enumerate(self.chapter_summaries, 1):
            summaries += f"\n  Chuong {i}: {s}"
        states = ""
        for name, state in self.character_states.items():
            states += f"\n  - {name}: {state}"
        threads = ""
        for t in self.unresolved_threads:
            threads += f"\n  - {t}"
        relations = ""
        for pair, desc in self.relationship_map.items():
            relations += f"\n  - {pair}: {desc}"
        return f"=== LONG-TERM MEMORY ===\nSo chuong da viet: {self.current_chapter}\nTom tat cac chuong:{summaries or ' (Chua co)'}\nTrang thai nhan vat:{states or ' (Chua co)'}\nTuyen truyen chua giai quyet:{threads or ' (Chua co)'}\nMoi quan he nhan vat:{relations or ' (Chua co)'}\n"

    def get_short_context(self, max_chars=6000):
        if len(self.full_text) <= max_chars:
            return self.full_text
        return self.full_text[-max_chars:]

    def append_chapter(self, chapter_text):
        self.current_chapter += 1
        if self.full_text:
            self.full_text += "\n\n" + chapter_text
        else:
            self.full_text = chapter_text

    def to_dict(self):
        return {"session_id": self.session_id, "story_bible": self.story_bible.to_dict(),
                "chapter_summaries": self.chapter_summaries, "character_states": self.character_states,
                "unresolved_threads": self.unresolved_threads, "relationship_map": self.relationship_map,
                "current_chapter": self.current_chapter, "full_text": self.full_text}

    @classmethod
    def from_dict(cls, d):
        mem = cls()
        mem.session_id = d.get("session_id", str(uuid.uuid4()))
        mem.story_bible = StoryBible.from_dict(d.get("story_bible", {}))
        mem.chapter_summaries = d.get("chapter_summaries", [])
        mem.character_states = d.get("character_states", {})
        mem.unresolved_threads = d.get("unresolved_threads", [])
        mem.relationship_map = d.get("relationship_map", {})
        mem.current_chapter = d.get("current_chapter", 0)
        mem.full_text = d.get("full_text", "")
        return mem
