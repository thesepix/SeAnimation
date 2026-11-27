"""Konsolen-Einstiegspunkt — wird von seanimation.spec (PyInstaller) als
Entry-Skript verwendet und kann auch direkt ausgeführt werden:
    python seanimation_cli.py --selftest
"""

from seanimation.main import main

if __name__ == "__main__":
    main()
