"""Generate a small benign example with the real local model; inspect before running."""
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import local_python_ai as ai

model = sys.argv[1] if len(sys.argv) > 1 else "3b"
ai.MODEL_MODE = model
ai.ROOT = Path(__file__).resolve().parent / "style-validation"
ai.ROOT.mkdir(exist_ok=True)
task = (
    "请写一个 Python 程序，从键盘输入一行空格分隔的整数，统计其中偶数的个数并输出，"
    "包括负数和 0；空行或非整数要给出中文提示。保存为 style_demo_" + model + ".py"
)
path, request = ai.natural_file_request(task)
print("Generating with", model, "->", path, flush=True)
started = time.monotonic()
ai.save_generated_file(path, request, ai.read_text(path) if path.exists() else "")
print("Elapsed seconds:", round(time.monotonic() - started, 1), flush=True)
