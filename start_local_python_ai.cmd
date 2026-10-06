@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "OLLAMA_HOST=127.0.0.1:11434"
set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
if not exist "%OLLAMA_EXE%" set "OLLAMA_EXE=C:\Program Files\Ollama\ollama.exe"
if not exist "%OLLAMA_EXE%" (
  echo 未找到 Ollama，请先安装 Ollama。
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ensure_ollama.ps1"
if errorlevel 1 (
  echo Ollama 服务启动失败，端口 11434 仍不可用。
  echo 请检查 Ollama 是否被安全软件拦截，或手动运行：ollama serve
  pause
  exit /b 1
)
set "PATH=%LOCALAPPDATA%\Programs\Ollama;%PATH%"
python "%~dp0local_python_ai.py" %*
if errorlevel 1 (
  echo 助手启动或运行失败，请保留上方错误信息。
  pause
  exit /b 1
)
exit /b 0
