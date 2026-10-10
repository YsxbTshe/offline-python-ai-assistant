"""Real local-model smoke check; writes only to ignored validation directories."""
from pathlib import Path
import json
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import local_python_ai as ai
from assistant_session import Conversation


def main():
    root = ai.APP_DIR / "work" / "conversation-validation"
    root.mkdir(parents=True, exist_ok=True)
    ai.ROOT = root
    ai.STYLE_ENABLED = False
    ai.MODEL_MODE = "auto"
    session = (Conversation.load(root / "live-session.json") if "--drawing-only" in sys.argv
               else Conversation(root / "live-session.json"))
    steps = [
        "美国队长的经典圆盾是什么样的？用两句话说明颜色和图案。",
        "它正中央是什么颜色、什么形状？请用一句话回答。",
        "用 turtle 把刚才说的盾牌画出来，保存为 shield.py。不要图片文件，直接绘制。",
        "把背景改成黑色，保留刚才盾牌的图案和颜色。",
        "把代码保存到这个目录：",
        str(root / "另一处含空格的目录 saved files"),
    ]
    if "--drawing-only" in sys.argv:
        steps = ["用 turtle 重新完整绘制我们讨论的盾牌，保存为 shield.py，黑色背景。不要图片文件，直接绘制。"]
    results = []
    for step in steps:
        print("\nUSER:", step, flush=True)
        start = time.monotonic()
        ai.handle_natural_turn(step, session)
        results.append({"request": step, "seconds": round(time.monotonic() - start, 1),
                        "last_path": session.last_path})
        print("SECONDS:", results[-1]["seconds"], flush=True)
    restored = Conversation.load(session.storage)
    assert restored.last_code == session.last_code
    assert restored.last_path == session.last_path
    assert Path(restored.last_path).is_file()
    assert (root / "shield.py.bak").is_file()
    compile(restored.last_code, restored.last_path, "exec")
    (root / "live-results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("LIVE CHECK COMPLETE", flush=True)


if __name__ == "__main__":
    main()
