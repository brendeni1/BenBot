# Get the current script's directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Define paths
$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"
$ScriptFile = Join-Path $ScriptDir "main.py"

# Run the Python script using the virtual environment's Python
& $VenvPython $ScriptFile