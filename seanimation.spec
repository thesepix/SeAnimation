# PyInstaller-Spec für SeAnimation (onefile -> dist/SeAnimation.exe)
#
# Bauen (Windows, nach pip install -r requirements.txt pyinstaller):
#   pyinstaller seanimation.spec --clean --noconfirm  # -> dist\SeAnimation.exe
# oder: scripts\build_exe.ps1
#
# Ergebnis: dist\SeAnimation.exe (onefile — eine einzige Datei
# bei numpy/cv2/sounddevice). Konsole bleibt sichtbar für --selftest/--wav.

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = [("seanimation/render/shaders", "seanimation/render/shaders")]
try:
    # PortAudio-DLL aus dem sounddevice-Wheel mitnehmen
    datas += collect_data_files("sounddevice")
except Exception:
    pass

# Die meisten Imports (cv2, sounddevice, moderngl, ...) werden von der statischen
# Analyse automatisch gefunden; pyglet braucht Submodules (inkl. GL-Backends).
hiddenimports = ["numpy"]
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
    name="SeAnimation",
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
