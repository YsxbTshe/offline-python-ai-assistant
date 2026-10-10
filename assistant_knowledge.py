"""Small, editable offline reference notes; no network or executable content."""
import json
from pathlib import Path
import re


def reference_notes(directory: Path, prompt: str, history: list[dict[str, str]]) -> str:
    recent = "\n".join(m["content"] for m in history[-4:])
    text = prompt.lower()
    # Bring in the previous subject only for a follow-up referring to it.
    if re.search(r"它|刚才|上面|这个|那个|继续|背景|改成|改为|换成|颜色|中央", prompt):
        text += "\n" + recent.lower()
    entries = []
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, list):
            continue
        for note in data:
            if not isinstance(note, dict) or not isinstance(note.get("content"), str):
                continue
            keywords = note.get("keywords", [])
            score = sum(word.lower() in text for word in keywords if isinstance(word, str) and word)
            if score:
                entries.append((score, str(note.get("title", "参考")), note["content"]))
    entries.sort(key=lambda row: row[0], reverse=True)
    return "\n".join(title + "：" + content for _, title, content in entries[:3])[:3500]
