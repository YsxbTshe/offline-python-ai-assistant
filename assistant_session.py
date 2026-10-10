"""Local conversation state; never treat model output as a file operation."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Conversation:
    storage: Path
    messages: list[dict[str, str]] = field(default_factory=list)
    last_code: str = ""
    last_path: str = ""
    save_dir: str = ""
    pending_save: str = ""
    notes: str = ""

    @classmethod
    def load(cls, storage: Path) -> "Conversation":
        session = cls(storage)
        if not storage.exists():
            return session
        try:
            data = json.loads(storage.read_text(encoding="utf-8"))
            messages = data.get("messages", [])
            if not isinstance(messages, list) or any(
                not isinstance(m, dict) or m.get("role") not in ("user", "assistant")
                or not isinstance(m.get("content"), str) for m in messages
            ):
                raise ValueError("会话格式不正确")
            session.messages = [{"role": m["role"], "content": m["content"]} for m in messages]
            for key in ("last_code", "last_path", "save_dir", "pending_save", "notes"):
                value = data.get(key, "")
                if not isinstance(value, str):
                    raise ValueError("会话格式不正确")
                setattr(session, key, value)
            session.trim()
        except (OSError, ValueError, AttributeError) as exc:
            print(f"未能恢复上次会话，将从新对话开始：{exc}")
            session = cls(storage)
        return session

    def trim(self) -> None:
        # Keep whole recent turns, with the active program separately preserved.
        while len(self.messages) > 24 or (
            sum(len(m["content"]) for m in self.messages) > 60000 and len(self.messages) > 2
        ):
            del self.messages[:2]

    def save(self) -> None:
        self.trim()
        data = {key: getattr(self, key) for key in
                ("messages", "last_code", "last_path", "save_dir", "pending_save", "notes")}
        self.storage.parent.mkdir(parents=True, exist_ok=True)
        temp = self.storage.with_suffix(".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.storage)

    def remember(self, user: str, answer: str) -> None:
        self.messages.extend([{"role": "user", "content": user},
                              {"role": "assistant", "content": answer}])
        self.save()

    def clear(self) -> None:
        self.messages.clear()
        self.last_code = self.last_path = self.save_dir = self.pending_save = ""
        self.notes = ""
        self.save()


def token_estimate(text: str) -> int:
    # Conservative estimate for mixed Chinese instructions and Python code.
    non_ascii = sum(ord(c) > 127 for c in text)
    return int(non_ascii * 1.5 + (len(text) - non_ascii) / 3) + 12


def recent_messages(history: list[dict[str, str]], budget: int) -> list[dict[str, str]]:
    """Keep recent complete turns rather than silently truncating source code."""
    selected: list[dict[str, str]] = []
    for i in range(len(history) - 2, -1, -2):
        turn = history[i:i + 2]
        cost = sum(token_estimate(m["content"]) for m in turn)
        if cost > budget:
            break
        selected[:0] = turn
        budget -= cost
    return selected
