$ErrorActionPreference = 'Stop'

$packageName = 'ai-auto-commit'

Write-Host "Uninstalling $packageName..." -ForegroundColor Cyan

# Uninstall ai-auto-commit via pip
try {
    & python -m pip uninstall -y ai-auto-commit

    if ($LASTEXITCODE -eq 0) {
        Write-Host "$packageName has been uninstalled successfully." -ForegroundColor Green
    } else {
        Write-Warning "Failed to uninstall $packageName"
    }
} catch {
    Write-Warning "Could not uninstall $packageName via pip: $_"
}

Write-Host ""
Write-Host "Note: Your configuration file has been preserved at:" -ForegroundColor Yellow
Write-Host "  $env:USERPROFILE\.config\ai_auto_commit\config.json" -ForegroundColor White
Write-Host ""
Write-Host "To completely remove all data, delete the config directory:" -ForegroundColor Yellow
Write-Host "  Remove-Item -Recurse -Force $env:USERPROFILE\.config\ai_auto_commit" -ForegroundColor White
Write-Host ""
