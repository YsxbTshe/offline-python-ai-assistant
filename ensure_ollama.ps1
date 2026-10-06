$ErrorActionPreference = "Stop"

$ollamaExe = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
if (-not (Test-Path -LiteralPath $ollamaExe)) {
    $ollamaExe = "C:\Program Files\Ollama\ollama.exe"
}
if (-not (Test-Path -LiteralPath $ollamaExe)) {
    Write-Error "未找到 Ollama，请先安装 Ollama。"
    exit 1
}

$env:OLLAMA_HOST = "127.0.0.1:11434"
$ready = Test-NetConnection -ComputerName 127.0.0.1 -Port 11434 -InformationLevel Quiet
if (-not $ready) {
    Start-Process -FilePath $ollamaExe -ArgumentList "serve" -WindowStyle Hidden
}

Write-Host "正在等待本地 Ollama 服务..."
$deadline = (Get-Date).AddSeconds(20)
do {
    $ready = Test-NetConnection -ComputerName 127.0.0.1 -Port 11434 -InformationLevel Quiet
    if ($ready) { exit 0 }
    Start-Sleep -Milliseconds 500
} while ((Get-Date) -lt $deadline)

Write-Error "Ollama 服务未能启动，端口 11434 不可用。请运行：ollama serve"
exit 1
