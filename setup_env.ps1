<#
PowerShell helper to create a virtual environment and install requirements
Usage:
    powershell -ExecutionPolicy Bypass -File .\setup_env.ps1
#>

$venvPath = ".venv"
if (-Not (Test-Path $venvPath)) {
    python -m venv $venvPath
}

Write-Host "Activating venv..."
. $venvPath\Scripts\Activate.ps1

Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

Write-Host "Installing requirements..."
python -m pip install -r requirements.txt

Write-Host "Environment setup complete. Activate with: .\\.venv\\Scripts\\Activate.ps1"
