"""Puts the previous mouse cursors back and removes the installed files."""

import ctypes
import json
import shutil
import winreg

from install import BACKUP, CURSORS_KEY, INSTALL_DIR, ROLES, SPIF_UPDATE, SPI_SETCURSORS

SCHEME = "Catppuccin"


def main():
    previous = {}
    if BACKUP.exists():
        previous = json.loads(BACKUP.read_text(encoding="utf-8"))
        print("Setter tilbake forrige oppsett")
    else:
        print("Fant ingen sikkerhetskopi, setter Windows-standard (tomme verdier)")

    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, CURSORS_KEY, 0, winreg.KEY_ALL_ACCESS) as key:
        for role, _ in ROLES:
            winreg.SetValueEx(key, role, 0, winreg.REG_EXPAND_SZ, previous.get(role, ""))
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, previous.get("(Default)", ""))

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CURSORS_KEY + r"\Schemes", 0,
                            winreg.KEY_ALL_ACCESS) as key:
            i = 0
            while True:
                try:
                    name = winreg.EnumValue(key, i)[0]
                except OSError:
                    break
                if name.startswith(SCHEME):
                    winreg.DeleteValue(key, name)
                    print(f"Fjernet oppsettet «{name}»")
                else:
                    i += 1
    except FileNotFoundError:
        pass

    ctypes.windll.user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, SPIF_UPDATE)

    shutil.rmtree(INSTALL_DIR, ignore_errors=True)
    print(f"Slettet {INSTALL_DIR}")
    print("Ferdig.")


if __name__ == "__main__":
    main()
