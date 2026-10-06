"""Run reviewed, benign model output against independent input/output cases."""
from pathlib import Path
import re
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
example = root / "outputs/代码风格示例_统计偶数.py"
cases = [
    ("-4 -1 0 2 3\n", r"偶数的个数[：:]\s*3"),
    ("1 3 5\n", r"偶数的个数[：:]\s*0"),
    ("0\n", r"偶数的个数[：:]\s*1"),
    ("\n", r"不能为空"),
    ("2 abc 4\n", r"不是有效的整数"),
]
for data, expected in cases:
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(example)],
        input=data, encoding="utf-8", capture_output=True, timeout=5,
        cwd=example.parent,
    )
    assert result.returncode == 0, result.stderr
    assert re.search(expected, result.stdout), (data, result.stdout)
    print("PASS", repr(data.strip()), result.stdout.strip())

print("Verified bundled example:", example.name)
