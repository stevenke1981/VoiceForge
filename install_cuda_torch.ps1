# install_cuda_torch.ps1
# Detects NVIDIA driver version and installs the matching CUDA build of PyTorch
# into the project's .venv via uv.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Resolve project root (directory containing this script)
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython  = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

Write-Host ""
Write-Host "============================================"
Write-Host "  PyTorch CUDA Installer for VoiceForge"
Write-Host "============================================"
Write-Host "  Project : $ProjectRoot"
Write-Host ""

# ── 1. Check uv ──────────────────────────────────────────────────────────────
if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Error "uv is not installed. Run:`n  powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`""
    exit 1
}

# Ensure the project venv exists (uv sync creates it)
if (-not (Test-Path $VenvPython)) {
    Write-Host "[PRE] .venv not found — running 'uv sync' to create it..."
    Push-Location $ProjectRoot
    uv sync --extra google
    Pop-Location
    if ($LASTEXITCODE -ne 0) {
        Write-Error "uv sync failed. Fix dependency errors before installing torch."
        exit 1
    }
}

# ── 2. Check nvidia-smi ──────────────────────────────────────────────────────
if (-not (Get-Command "nvidia-smi" -ErrorAction SilentlyContinue)) {
    Write-Error "nvidia-smi not found. Install an NVIDIA driver first:`n  https://www.nvidia.com/Download/index.aspx"
    exit 1
}

# ── 3. Read CUDA version from nvidia-smi header ──────────────────────────────
# nvidia-smi -q returns "N/A" under WDDM; the plain header is reliable.
# Header line: | NVIDIA-SMI 595.97   Driver Version: 595.97   CUDA Version: 13.2 |
Write-Host "[1/3] Querying NVIDIA GPU..."
$nvsmiOut   = nvidia-smi 2>$null
$cudaMatch  = ($nvsmiOut | Select-String 'CUDA Version:\s*(\d+\.\d+)').Matches
if (-not $cudaMatch -or $cudaMatch.Count -eq 0) {
    Write-Error "Could not parse CUDA version from nvidia-smi output."
    exit 1
}
$cudaFull   = $cudaMatch[0].Groups[1].Value          # e.g. "13.2"
$cudaMajor  = [int]($cudaFull.Split(".")[0])
$cudaMinor  = [int]($cudaFull.Split(".")[1])

$driverLine = ($nvsmiOut | Select-String 'Driver Version:\s*([\d.]+)').Matches
$driverVer  = if ($driverLine) { $driverLine[0].Groups[1].Value } else { "unknown" }

Write-Host "      Driver  : $driverVer"
Write-Host "      CUDA    : $cudaFull"

# ── 4. Map CUDA version → torch wheel ────────────────────────────────────────
#
#  CUDA >= 12.8  →  cu128   (RTX 30/40 series, driver >= 522 on Windows)
#  CUDA >= 12.4  →  cu124
#  CUDA >= 12.1  →  cu121
#  CUDA >= 11.8  →  cu118
#  CUDA <  11.8  →  too old
#
$torchBuild = $null
if ($cudaMajor -ge 13 -or ($cudaMajor -eq 12 -and $cudaMinor -ge 8)) {
    $torchBuild = "cu128"
} elseif ($cudaMajor -eq 12 -and $cudaMinor -ge 4) {
    $torchBuild = "cu124"
} elseif ($cudaMajor -eq 12 -and $cudaMinor -ge 1) {
    $torchBuild = "cu121"
} elseif ($cudaMajor -ge 11) {
    $torchBuild = "cu118"
} else {
    Write-Host ""
    Write-Host "[WARN] CUDA $cudaFull is too old for any supported PyTorch build."
    Write-Host "       Update your NVIDIA driver and re-run this script."
    Write-Host "       Download: https://www.nvidia.com/Download/index.aspx"
    exit 1
}

$indexUrl = "https://download.pytorch.org/whl/$torchBuild"
Write-Host "      Selected build  : $torchBuild  ($indexUrl)"

# ── 5. Install into project .venv ────────────────────────────────────────────
Write-Host ""
Write-Host "[2/3] Installing torch ($torchBuild) into project .venv — this may take a few minutes..."
# UV_LINK_MODE=copy avoids the hardlink warning when cache and .venv are on different filesystems
$env:UV_LINK_MODE = "copy"
uv pip install torch --python $VenvPython --index-url $indexUrl --reinstall --reinstall-package markupsafe
if ($LASTEXITCODE -ne 0) {
    Write-Error "torch installation failed."
    exit 1
}

# ── 6. Verify ────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[3/3] Verifying installation..."
$result = & $VenvPython -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)" 2>&1
Write-Host "      torch.cuda.is_available(), torch.version.cuda -> $result"

if ($result -match "^True") {
    Write-Host ""
    Write-Host "[OK] CUDA PyTorch is ready. You can now run start.bat."
} else {
    Write-Host ""
    Write-Host "[WARN] torch installed but CUDA is still not available."
    Write-Host "       Possible causes:"
    Write-Host "         - Driver was updated but a reboot is pending"
    Write-Host "         - GPU does not support CUDA (e.g. some Quadro / old Fermi cards)"
    Write-Host "         - Visual C++ Redistributable missing (install from Microsoft)"
    Write-Host "       Try rebooting, then run start.bat again."
}

Write-Host ""
