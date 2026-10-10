"""Interpret explicit user destinations without delegating disk writes to an LLM."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


NEGATIVE = r"(?:不要|不用|别|不必|暂不|先不|无需).{0,5}(?:保存|写入|生成文件|存盘)"
LIBRARIES = r"python|turtle|numpy|pandas|matplotlib|jieba|wordcloud|opencv|cv2|pytorch|tensorflow"


@dataclass
class FileIntent:
    path: Path | None
    task: str
    save_only: bool = False
    edit: bool = False
    needs_directory: bool = False


def absolute_path(text: str) -> str:
    quoted = re.search(r'["“\'‘]([A-Za-z]:[\\/][^"”\'’\r\n]+)["”\'’]', text)
    if quoted:
        return quoted.group(1).strip()
    match = re.search(r"[A-Za-z]:[\\/][^\r\n\"“”'‘’，。；;！？!?<>|]*", text)
    if not match:
        return ""
    value = re.split(r"[,，]|\s+(?=并|然后|文件名|命名|名字|保存|请|帮我|要求|用)", match.group())[0]
    # A .py filename can be immediately followed by Chinese instructions.
    value = re.split(r"(?<=\.py)(?=\s|并|然后|，|。)", value, flags=re.I)[0]
    return value.strip().rstrip("：:")


def named_python_file(text: str) -> str:
    named = re.search(
        r"(?:文件名(?:叫做|叫|为|是)?|命名为?|名字(?:叫|为|是)|保存为|另存为)\s*[：:]?\s*"
        r"[\"“'‘]?([^\r\n\"”'’，,。；;：:]+?\.py)", text, re.I,
    )
    if named:
        return Path(named.group(1).strip()).name
    match = re.search(r"(?<![\w\\/])([A-Za-z0-9_\-]+\.py)\b", text, re.I)
    return match.group(1) if match else ""


def user_target(value: str, root: Path, desktop: Path) -> Path:
    value = value.strip().strip('"“”\'‘’')
    if value.lower() in ("桌面", "desktop"):
        return desktop / "generated_program.py"
    if value.startswith(("\\\\", "//")):
        raise ValueError("请使用本机磁盘路径，例如 D:\\works\\项目。")
    path = Path(value).expanduser()
    if path.is_absolute():
        result = path.resolve()
    else:
        result = (root / path).resolve()
        if result != root and root not in result.parents:
            raise ValueError("相对路径不能越出默认目录；其他磁盘请给出完整路径。")
    if result.suffix.lower() != ".py":
        raise ValueError("代码文件名需要以 .py 结尾；可以只告诉我保存目录。")
    return result


def file_intent(raw: str, root: Path, desktop: Path, *, last_path: str = "",
                has_code: bool = False, save_dir: str = "", pending: str = "") -> FileIntent | None:
    text = raw.strip()
    if re.search(NEGATIVE, text):
        return None
    # Questions about an operation must not trigger that operation.
    if re.match(r"^(?:请问|我想知道)?(?:如何|怎么|为什么|什么是)", text) or re.search(
        r"(?:解释|告诉我|讲解).{0,8}(?:怎么|如何)|(?:只|先)(?:解释|讨论|讲解)|不要修改|别改", text
    ):
        return None
    matches = list(re.finditer(r"(?:保存|另存|存放|存到|存为|存进|存下来|放到|放在|写入|输出到)(?:代码|程序|文件|它)?(?:到|在|为|进|下)?", text))
    save_match = matches[-1] if matches else None
    save = bool(save_match and any(w in text for w in ("保存", "存到", "存为", "存进", "放到", "放在", "写入", "输出到", "存下来")))
    edit = has_code and bool(re.search(r"改成|改为|换成|换为|修改|改一下|改一改|修复|重写|优化|完善|加上|加个|加入|增加|添加|去掉|删掉|调整|继续写|接着写|再画|让它", text))
    generation = bool(re.search(r"写一个|写一份|帮我写|请写|编写|生成|创建|开发|实现|写段|写个|做一个|做个", text)
                      and re.search(LIBRARIES + r"|程序|脚本|代码|\.py", text, re.I))
    generation = generation or bool(re.search(r"用.{0,24}(?:画|绘制)|(?:帮我|请)(?:画|绘制)", text))
    path_only = bool(re.fullmatch(r'["“\'‘]?[A-Za-z]:[\\/][^\r\n]+', text))
    if path_only and (pending or has_code):
        if pending:
            return file_intent(pending + "\n" + text, root, desktop, last_path=last_path,
                               has_code=has_code, save_dir=save_dir)
        save = True
    if has_code and re.match(r"(?:文件名|命名|另存)", text):
        save = True
    if not (save or generation or edit):
        return None
    task = text
    # Resolve destinations only from the user's save clause, never from a model response.
    destination_text = text[matches[0].end():] if matches else (text if path_only else "")
    location = absolute_path(destination_text)
    desktop_requested = "桌面" in destination_text
    name = named_python_file(text)
    previous = Path(last_path) if last_path else None
    default_name = previous.name if previous and (edit or (save and not generation)) else "generated_program.py"
    name = name or default_name
    missing = bool(save and not location and not desktop_requested and re.search(
        r"(?:目录|文件夹|路径)\s*[：:]?\s*$|(?:保存|放|存)(?:到|在)\s*[：:]\s*$", text))
    if missing:
        return FileIntent(None, task, save_only=not (generation or edit), edit=edit, needs_directory=True)
    if location:
        candidate = Path(location)
        if candidate.suffix.lower() == ".py":
            destination = user_target(str(candidate), root, desktop)
        else:
            if candidate.suffix.lower() in (".docx", ".pdf", ".pptx", ".exe", ".dll", ".json"):
                raise ValueError("这里保存的是 Python 源码，请指定目录或 .py 文件。")
            destination = user_target(str(candidate / name), root, desktop)
    elif desktop_requested:
        destination = user_target(str(desktop / name), root, desktop)
    elif previous and edit and not named_python_file(text):
        destination = previous
    else:
        destination = user_target(str(Path(save_dir) / name) if save_dir else name, root, desktop)
    if "默认目录" in destination_text:
        destination = user_target(name, root, desktop)
    return FileIntent(destination, task, save_only=save and not (generation or edit), edit=edit)
