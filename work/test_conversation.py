"""Regression tests for user intent, real file effects, context and recovery."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import local_python_ai as ai
from assistant_intents import file_intent
from assistant_session import Conversation, recent_messages
from assistant_knowledge import reference_notes


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "默认目录"
        self.root.mkdir()
        self.desktop = self.base / "Desktop"
        self.session = Conversation(self.base / "private" / "conversation.json")
        self.output = io.StringIO()
        for context in (patch.object(ai, "ROOT", self.root), patch.object(ai, "DESKTOP", self.desktop),
                        patch.object(ai, "STYLE_REFERENCE", self.base / "missing"),
                        contextlib.redirect_stdout(self.output)):
            context.__enter__()
            self.addCleanup(context.__exit__, None, None, None)

    def seed(self):
        code = 'print("中文原稿")\n'
        path = self.root / "original.py"
        path.write_text(code, encoding="utf-8")
        self.session.last_code, self.session.last_path = code, str(path)
        self.session.remember("写一个问候程序", f"```python\n{code}```")
        return path, code

    def test_save_exact_code_outside_default_without_model(self):
        original, code = self.seed()
        destination = self.base / "中文 new folder"
        raw = f'把代码保存到这个目录：“{destination}”，文件名叫 你好.py'
        with patch.object(ai, "ask", side_effect=AssertionError("保存已有代码无需再次生成")):
            ai.handle_natural_turn(raw, self.session)
        target = destination / "你好.py"
        self.assertIn(code, target.read_text(encoding="utf-8"))
        self.assertEqual(original.read_text(encoding="utf-8"), code)
        self.assertEqual(self.session.last_path, str(target))
        self.assertIn(str(target), self.output.getvalue())

    def test_missing_directory_then_next_message(self):
        _, code = self.seed()
        with patch.object(ai, "ask", side_effect=AssertionError("不需要模型")):
            ai.handle_natural_turn("把代码保存到这个目录：", self.session)
            self.assertTrue(self.session.pending_save)
            ai.handle_natural_turn(str(self.base / "另外的目录"), self.session)
        self.assertEqual(Path(self.session.last_path).parent, self.base / "另外的目录")
        self.assertIn(code, self.session.last_code)
        self.assertFalse(self.session.pending_save)

    def test_generation_with_delayed_directory_keeps_task(self):
        self.seed()
        ai.handle_natural_turn("帮我写一个 Python 求和程序，保存到这个目录：", self.session)
        with patch.object(ai, "ask", return_value='print(sum(range(10)))\n') as ask:
            ai.handle_natural_turn(str(self.base / "求和"), self.session)
        self.assertIn("求和程序", ask.call_args.args[0])
        self.assertIn("sum(range(10))", self.session.last_code)

    def test_edit_uses_history_source_and_backs_up_actual_disk_bytes(self):
        path, code = self.seed()
        revised = '#外部编辑\n' + code
        path.write_text(revised, encoding="utf-8")
        with patch.object(ai, "ask", return_value='print("你好，世界")\n') as ask:
            ai.handle_natural_turn("把提示改成你好世界，加上中文注释", self.session)
        self.assertIn(revised, ask.call_args.args[0])
        self.assertTrue(ask.call_args.kwargs["history"])
        self.assertEqual(path.with_suffix(".py.bak").read_text(encoding="utf-8"), revised)
        self.assertEqual(self.session.last_path, str(path))

    def test_invalid_generation_never_overwrites_existing_file(self):
        path, code = self.seed()
        with patch.object(ai, "ask", return_value='print("broken"'):
            with self.assertRaises(SyntaxError):
                ai.handle_natural_turn("修改代码加上欢迎语", self.session)
        self.assertEqual(path.read_text(encoding="utf-8"), code)
        self.assertFalse(path.with_suffix(".py.bak").exists())

    def test_chat_context_is_sent_with_general_model_and_survives_restart(self):
        bodies = []
        def response(request, timeout):
            bodies.append(json.loads(request.data))
            return io.BytesIO(json.dumps({"message": {"content": "这是第一轮讨论的圆形盾牌。"}}).encode())
        with patch.object(ai.urllib.request, "urlopen", side_effect=response):
            ai.handle_natural_turn("我们讨论圆形盾牌", self.session)
            restored = Conversation.load(self.session.storage)
            ai.handle_natural_turn("它是什么形状？", restored)
        self.assertEqual(bodies[-1]["model"], ai.GENERAL_MODEL)
        self.assertEqual([m["role"] for m in bodies[-1]["messages"]],
                         ["system", "user", "assistant", "user"])
        self.assertIn("我们讨论圆形盾牌", str(bodies[-1]))
        self.assertNotIn("style_examples", bodies[-1]["messages"][0]["content"])
        restored.clear()
        empty = Conversation.load(self.session.storage)
        self.assertEqual(empty.messages, [])
        self.assertEqual(empty.last_code, "")

    def test_general_questions_and_negative_requests_do_not_write(self):
        self.seed()
        for text in ("美国队长的盾牌是什么样的？", "不要保存，给我解释一下代码",
                     "怎么给它加上注释？", "请告诉我如何修改代码", "先讨论怎么改，不要修改"):
            with self.subTest(text=text):
                self.assertIsNone(file_intent(text, self.root, self.desktop, has_code=True))

    def test_paths_names_and_input_paths(self):
        location = self.base / "output with spaces"
        cases = [
            (f'请写一个 Python 程序，保存到 {location}，文件名叫 答案.py', location / "答案.py"),
            (f'把代码存到 {location}\\test.py', location / "test.py"),
            ('请写一个 Python 程序，保存为 hello.py', self.root / "hello.py"),
            ('把代码放到桌面，文件名叫 绘图.py', self.desktop / "绘图.py"),
            (f'请写一个 Python 程序，读取 C:\\data\\in.csv，输出统计结果，保存到 {location}，文件名叫 result.py', location / "result.py"),
            (f'把代码保存到 {location}，保存为 最终.py', location / "最终.py"),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(file_intent(raw, self.root, self.desktop).path, expected)
        with self.assertRaises(ValueError):
            ai.target_path("../outside.py")
        with self.assertRaises(ValueError):
            ai.target_path(str(location / "bad.exe"))

    def test_rolling_history_keeps_whole_turns(self):
        messages = [{"role": role, "content": str(i)} for i in range(20) for role in ("user", "assistant")]
        kept = recent_messages(messages, 80)
        self.assertLess(len(kept), len(messages))
        self.assertEqual(kept[0]["role"], "user")
        self.assertEqual(kept[-1]["role"], "assistant")
        self.assertEqual(kept[-1]["content"], "19")

    def test_code_given_in_chat_can_then_be_saved(self):
        with patch.object(ai, "ask", return_value='示例：\n```python\nprint("测试")\n```'):
            ai.handle_natural_turn("不要保存，给我一段打印测试的代码", self.session)
        self.assertEqual(self.session.last_path, "")
        with patch.object(ai, "ask", side_effect=AssertionError("不可重新生成")):
            ai.handle_natural_turn("保存为 test.py", self.session)
        self.assertTrue((self.root / "test.py").is_file())

    def test_truncated_response_is_rejected(self):
        response = io.BytesIO(json.dumps({"done_reason": "length", "message": {"content": "print(1)"}}).encode())
        with patch.object(ai.urllib.request, "urlopen", return_value=response):
            with self.assertRaisesRegex(ValueError, "长度上限"):
                ai.ask("test")

    def test_notes_survive_restart_and_are_sent_to_model(self):
        ai.handle_natural_turn("记住：这次所有图形背景用黑色。", self.session)
        restored = Conversation.load(self.session.storage)
        with patch.object(ai, "ask", return_value="明白。") as ask:
            ai.handle_natural_turn("继续刚才的话题", restored)
        self.assertIn("背景用黑色", ask.call_args.args[0])
        restored.clear()
        self.assertEqual(Conversation.load(self.session.storage).notes, "")

    def test_local_references_follow_subject_without_polluting_other_topics(self):
        directory = ai.APP_DIR / "knowledge"
        history = [{"role": "user", "content": "美国队长的盾牌是什么样？"},
                   {"role": "assistant", "content": "圆形。"}]
        self.assertIn("白色五角星", reference_notes(directory, "它中央是什么？", history))
        self.assertEqual(reference_notes(directory, "如何煮米饭？", history), "")


if __name__ == "__main__":
    unittest.main()
