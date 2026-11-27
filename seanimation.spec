# PyInstaller-Spec für SeAnimation (onefile, Dateiname trägt die Version)
#
# Bauen (Windows, nach pip install -r requirements.txt pyinstaller):
#   pyinstaller seanimation.spec --clean --noconfirm  # -> dist\SeAnimation-vX.Y.Z.exe
# oder: scripts\build_exe.ps1
#
# Ergebnis: dist\SeAnimation-vX.Y.Z.exe (onefile — eine einzige Datei).
# Konsole bleibt sichtbar für --selftest/--file.

import os
import re

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

with open(os.path.join(SPECPATH, "seanimation", "__init__.py"), encoding="utf-8") as _f:
    VERSION = re.search(r'__version__ = "([^"]+)"', _f.read()).group(1)
EXE_NAME = f"SeAnimation-{VERSION}"

datas = [("seanimation/render/shaders", "seanimation/render/shaders")]
for pkg in ("sounddevice", "soundfile"):
    try:
        # gebundelte Binaries mitnehmen: PortAudio-DLL (sounddevice),
        # libsndfile (soundfile) für WAV/FLAC/MP3/OGG-Dekodierung
        datas += collect_data_files(pkg)
    except Exception:
        pass

# Die meisten Imports (cv2, sounddevice, moderngl, ...) werden von der statischen
# Analyse automatisch gefunden; pyglet braucht Submodules (inkl. GL-Backends).
hiddenimports = ["numpy", "soundfile", "sounddevice"]
try:
    hiddenimports += collect_submodules("pyglet")
except Exception:
    pass

a = Analysis(
    ["seanimation_cli.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=EXE_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
