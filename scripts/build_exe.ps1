# Baut die standalone Exe: dist\SeAnimation-vX.Y.Z.exe (onefile, Version aus __init__.py)
#
# Einmalig auf dem Build-PC nötig: Python 3.11+ von python.org installieren
# (NICHT über den Microsoft Store — dort fehlt pip), dabei den Haken
# "Add python.exe to PATH" setzen. git/gh sind nur fürs Clonen nötig.
#
# Ausführen aus dem Repo-Root:
#   powershell -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1

$ErrorActionPreference = "Stop"

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt pyinstaller
pyinstaller seanimation.spec --clean --noconfirm

$exe = Get-ChildItem dist\SeAnimation-*.exe
Write-Host ("Fertig: dist\" + $exe.Name)
Write-Host ("Test:  .\dist\" + $exe.Name + " --selftest")
