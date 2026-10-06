# 本地 Python AI 助手新手说明书

## 1. 安装与启动

安装 Python 3.10 或以上版本和 Ollama，在项目目录执行 `python -m pip install -r requirements.txt`。首次联网下载模型：

```powershell
ollama pull qwen2.5-coder:3b
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5vl:3b
```

双击 `start_local_python_ai.cmd`，等待出现“你>”。安装和模型下载完成后可断网使用。7B 占用更多内存，在 CPU 上生成大段代码可能较慢。

## 2. 文件保存位置

启动时的“项目目录”显示实际保存位置。新安装默认使用用户主目录下的 `OfflinePythonAI`。复制 `local-ai.config.example.json` 为 `local-ai.config.json` 可修改输出目录；已有本地配置会继续生效。指定“桌面”时保存到当前用户桌面。

```text
请写一个 Python 计算器，并保存为 calculator.py
请写一个统计偶数个数的 Python 程序，把代码保存到桌面，文件名叫 answer.py
```

不指定文件名时保存为 `generated_program.py`。覆盖前备份为 `.bak`。保存后进行语法检查并尝试修复一次，仍需测试实际功能。不要把生成的 Python 文件当作无需检查即可执行的程序。

## 3. 3B、7B 与截图识题

```text
/model 3b
/model 7b
/model auto
/model
```

3B 通常较快，7B 用于更复杂的代码。自动模式根据关键词和请求长度选择，不保证每次选择最合适。截图使用独立视觉模型：

```text
"C:\Users\YOUR_USER\Pictures\question.png" 帮我把这道题的代码保存到桌面
```

路径含空格时使用引号。助手先转写题目，再生成源码。图片应清晰，题目约束和样例应完整；需要人工核对识别结果。当前截图入口会生成文件，适合编程题。

## 4. 代码风格

通用偏好包括中文提示、简短中文注释、英文变量名、基础循环和条件判断。小题使用直接脚本，必要时才定义函数或类；题目输入输出格式优先。

在 `local-ai.config.json` 的 `style_reference` 中填写自己的参考目录。当前生成流程会读取其中 `5.py`、`15.py` 两个短示例；没有示例时只使用通用规则。也可以设置环境变量 `LOCAL_AI_STYLE_REFERENCE`，或在输出目录的 `local-ai-style-path.txt` 中写入参考目录路径。个人示例和本地配置不要提交到公共仓库。

```text
查看我的代码风格
关闭代码风格模仿
按我的代码风格写
```

开关只影响当前命令行窗口，重新启动默认启用。这是提示词参考，不是训练模型，生成风格不保证完全一致。

## 5. 修改、审查与运行

```text
/fix calculator.py 修复除零错误
/review calculator.py
/read calculator.py
/run calculator.py
/files
/help
/quit
```

这些命令中的相对路径位于输出目录。`/read` 将文件加入后续普通问答的参考上下文。`/run` 执行真实本地代码并显示输出、错误和退出码，不是隔离沙箱。需要键盘交互的程序建议在 VS Code 终端单独运行。

## 6. VS Code Continue

安装 Continue 和 Python 扩展，先备份用户目录下 `.continue/config.yaml`，再合并项目中的 `work/continue-config.yaml`。重新加载 VS Code 并保证 Ollama 正在运行。

在 Continue 中选择快速 3B 或 7B；需要看图时选 Qwen2.5-VL 并附加图片。要修改文件，使用 Edit/Apply；单纯 Chat 不等于已保存。命令行的自动路由与风格开关不控制 Continue。

## 7. Word、PDF、PPT

将文件放在输出目录，用以下命令读取文字并追加回答到副本：

```text
/文档 题目.docx 完成里面的题目并给出答案
/文档 报告.pdf 总结重点
/文档 讲稿.pptx 给出讲解建议
```

结果带 `_AI完成` 后缀。当前不支持任意位置的精确原位编辑；扫描 PDF 需要另行 OCR。图片、复杂公式、长文档可能提取不全，PDF 中文字体和 PPT 长回答排版需要检查。

## 8. 机器学习和深度学习科研

先说明数据、任务、依赖和硬件限制，按“数据检查、基线、训练、评估、消融、复现记录”分步骤生成代码。固定随机种子，区分训练/验证/测试集，检查数据泄漏，保存配置和结果。

[科研提示词模板](../科研研究提示词模板.md) 可以直接使用。离线模型无法核实新论文；引用、实验结果和结论需要人工验证。训练依赖如 PyTorch、数据集和驱动需要另行安装准备。

## 9. 常见问题

**连接失败**：重新运行启动脚本；检查 Ollama 是否监听本机 11434 端口。

**启动报错**：保留错误窗口；`.cmd` 使用 Windows CRLF 换行，PowerShell 中文脚本使用 UTF-8 BOM。

**中文乱码**：在 VS Code 选择 UTF-8 编码；启动器已设置 Python UTF-8 环境。

**生成慢或不完整**：切换 `/model 3b` 或拆小任务。语法修复只能处理部分问题，不能代替功能测试。

**结束服务**：`/quit` 关闭助手；Ollama 可能仍在后台，可通过 Ollama 应用退出。不要关闭其他正在使用模型的任务所依赖的服务。

## 10. 本地与公开配置

公开仓库只包含源码、通用配置、说明书和示例，不包含模型权重、个人路径、参考作业或截图。本机 `local-ai.config.json`、风格路径文件、缓存和备份已加入忽略规则。运行时请求默认发送本机 Ollama；改用远程地址时，数据发送范围也会改变。

在仓库目录运行 `python work/create_manual_docx.py` 可在桌面生成本说明书的 Word 版本。
