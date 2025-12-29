$ErrorActionPreference = 'Stop'

$packageName = 'ai-auto-commit'
$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"

Write-Host "Installing $packageName..." -ForegroundColor Cyan

# Check if Python is installed
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Error "Python is not installed or not in PATH. Please install Python 3.8 or higher."
    throw
}

# Check if pip is available
try {
    & python -m pip --version | Out-Null
    Write-Host "Found pip" -ForegroundColor Green
} catch {
    Write-Error "pip is not available. Please ensure pip is installed."
    throw
}

# Install ai-auto-commit via pip
Write-Host "Installing ai-auto-commit via pip..." -ForegroundColor Cyan
& python -m pip install --user ai-auto-commit

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install ai-auto-commit"
    throw "Installation failed"
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  AI Auto Commit has been installed successfully!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "To get started, run the interactive setup wizard:" -ForegroundColor White
Write-Host "  autocommit init" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "This will guide you through:" -ForegroundColor White
Write-Host "  • Configuring AI provider API keys" -ForegroundColor White
Write-Host "  • Setting your default model" -ForegroundColor White
Write-Host "  • Configuring token budget" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "For more information:" -ForegroundColor White
Write-Host "  autocommit --help" -ForegroundColor White
Write-Host ""

# Add Python Scripts directory to PATH if not already there
$pythonScriptsPath = & python -c "import site; print(site.USER_BASE + '\\Scripts')" 2>$null
if ($pythonScriptsPath -and (Test-Path $pythonScriptsPath)) {
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentPath -notlike "*$pythonScriptsPath*") {
        Write-Host "Adding Python Scripts directory to PATH..." -ForegroundColor Cyan
        [Environment]::SetEnvironmentVariable(
            "Path",
            "$currentPath;$pythonScriptsPath",
            "User"
        )
        Write-Host "Python Scripts directory added to PATH. You may need to restart your terminal." -ForegroundColor Yellow
    }
}
