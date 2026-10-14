$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$modelBinary = Join-Path $projectRoot 'runtime\llama\llama-server.exe'
$modelWeights = Join-Path $projectRoot 'runtime\Qwen3-0.6B-Q8_0.gguf'
if (!(Test-Path -LiteralPath $modelBinary) -or !(Test-Path -LiteralPath $modelWeights)) {
    throw 'Run python scripts/setup_windows_model.py first.'
}
& $modelBinary -m $modelWeights --host 127.0.0.1 --port 8095 -c 4096 -t 4 --parallel 1 --jinja --alias invoice-qwen --no-webui
