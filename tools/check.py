#!/usr/bin/env python3
"""Ein Befehl für alles: Syntax + Unit-Tests + Beat-Selftest.

Vor jedem Commit nur diesen einen Befehl laufen lassen:

    python tools/check.py

Exit-Code 0 = alles PASS, 1 = etwas FAIL (Details siehe Ausgabe).
Läuft headless (braucht nur numpy/soundfile/cv2/pillow — kein GPU/Audio nötig).
"""

from __future__ import annotations

import compileall
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check_syntax() -> bool:
    print("== 1/3 py_compile (seanimation/, seanimation_cli.py, tools/, tests/) ==")
    ok = compileall.compile_dir(str(ROOT / "seanimation"), quiet=1, force=True)
    for f in (ROOT / "seanimation_cli.py", ROOT / "tools" / "check.py", ROOT / "tools" / "make_test_asset.py"):
        try:
            py_compile.compile(str(f), doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  SYNTAX-FEHLER in {f}: {e}")
            ok = False
    ok = compileall.compile_dir(str(ROOT / "tests"), quiet=1, force=True) and ok
    print("  Syntax: " + ("OK" if ok else "FAIL"))
    return ok


def check_tests() -> bool:
    print("== 2/3 unittest (tests/) ==")
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT)
    return r.returncode == 0


def check_selftest() -> bool:
    print("== 3/3 Beat-Selftest (python -m seanimation --selftest) ==")
    r = subprocess.run([sys.executable, "-m", "seanimation", "--selftest"], cwd=ROOT)
    return r.returncode == 0


def main() -> int:
    ok = check_syntax() and check_tests() and check_selftest()
    print("CHECK: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
