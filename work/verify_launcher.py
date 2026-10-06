"""Check the actual desktop shortcut target without opening a visible window."""
import os
from pathlib import Path
import subprocess
import sys

target, working_directory = sys.argv[1:3]
raw = Path(target).read_bytes()
assert b"\n" not in raw.replace(b"\r\n", b""), "Batch launcher needs CRLF line endings"
result = subprocess.run(
    [os.environ["COMSPEC"], "/d", "/c", target],
    cwd=working_directory,
    input="/model\n/quit\n",
    encoding="utf-8",
    capture_output=True,
    timeout=45,
)
print(result.stdout)
print(result.stderr)
assert result.returncode == 0, result.returncode
assert "项目目录:" in result.stdout
assert "当前任务会选择：" in result.stdout
assert "AI>" not in result.stdout, "Commands must not be sent to the model"
print("PASS: shortcut target, Chinese output, command input and clean exit")
