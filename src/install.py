"""Converts a Catppuccin XCursor theme to Windows cursors and installs it.

    python src/install.py [--theme <mappe>] [--flavor mocha] [--accent dark] [--size 32]

Without --theme the theme is downloaded from the Catppuccin release page.
"""

import argparse
import ctypes
import json
import os
import shutil
import sys
import tempfile
import urllib.request
import winreg
import zipfile
from pathlib import Path

import wincursor
import xcursor

SRC = Path(__file__).resolve().parent
INSTALL_DIR = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "CatppuccinCursors"
BACKUP = INSTALL_DIR / "forrige-oppsett.json"
CURSORS_KEY = r"Control Panel\Cursors"
SPI_SETCURSORS = 0x0057
SPIF_UPDATE = 0x01 | 0x02

RELEASE_URL = ("https://github.com/catppuccin/cursors/releases/latest/download/"
               "catppuccin-{flavor}-{accent}-cursors.zip")

# Windows role -> the name the theme uses. The order is the one Windows stores
# a cursor scheme in.
ROLES = [
    ("Arrow",      "default"),
    ("Help",       "help"),
    ("AppStarting", "progress"),
    ("Wait",       "wait"),
    ("Crosshair",  "crosshair"),
    ("IBeam",      "text"),
    ("NWPen",      "pencil"),
    ("No",         "not-allowed"),
    ("SizeNS",     "size_ver"),
    ("SizeWE",     "size_hor"),
    ("SizeNWSE",   "size_fdiag"),
    ("SizeNESW",   "size_bdiag"),
    ("SizeAll",    "all-scroll"),
    ("UpArrow",    "center_ptr"),
    ("Hand",       "pointer"),
]


def download(flavor, accent, into):
    url = RELEASE_URL.format(flavor=flavor, accent=accent)
    print(f"Laster ned {url}")
    archive = into / "theme.zip"
    urllib.request.urlretrieve(url, archive)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(into)
    for path in into.rglob("cursors"):
        if path.is_dir():
            return path
    raise SystemExit("Fant ingen cursors-mappe i nedlastingen")


def steps_for(frames, sizes):
    """Groups the images into animation steps, each holding every size.

    An animated cursor has the same number of steps in each size, so step i of
    one size lines up with step i of the others.
    """
    per_size = [xcursor.pick(frames, s) for s in sizes]
    per_size = [p for p in per_size if p]
    count = min(len(p) for p in per_size)
    return [[p[i] for p in per_size] for i in range(count)]


def convert(theme_dir, out_dir, sizes):
    out_dir.mkdir(parents=True, exist_ok=True)
    made = {}
    for role, name in ROLES:
        source = theme_dir / name
        if not source.exists():
            print(f"  mangler i temaet: {name}")
            continue
        steps = steps_for(xcursor.read(source), sizes)
        path = wincursor.write(out_dir / role, steps)
        made[role] = path
        sizes_used = "+".join(str(f.width) for f in steps[0])
        print(f"  {role:12} {name:12} {path.name:18} {len(steps)} steg, {sizes_used} px")
    return made


def install(made, scheme_name):
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, CURSORS_KEY, 0, winreg.KEY_ALL_ACCESS) as key:
        if not BACKUP.exists():                      # remember what was there
            previous = {}
            for role, _ in ROLES:
                try:
                    previous[role] = winreg.QueryValueEx(key, role)[0]
                except FileNotFoundError:
                    previous[role] = ""
            try:
                previous["(Default)"] = winreg.QueryValueEx(key, "")[0]
            except FileNotFoundError:
                previous["(Default)"] = ""
            BACKUP.write_text(json.dumps(previous, indent=2), encoding="utf-8")

        for role, _ in ROLES:
            winreg.SetValueEx(key, role, 0, winreg.REG_EXPAND_SZ, str(made.get(role, "")))
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, scheme_name)

    # Make the scheme selectable in Settings > Mouse.
    entries = [str(made.get(role, "")) for role, _ in ROLES] + ["", ""]  # Pin, Person
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, CURSORS_KEY + r"\Schemes", 0,
                            winreg.KEY_WRITE) as key:
        winreg.SetValueEx(key, scheme_name, 0, winreg.REG_EXPAND_SZ, ",".join(entries))

    ctypes.windll.user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, SPIF_UPDATE)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", help="mappe med XCursor-filer (cursors/)")
    parser.add_argument("--flavor", default="mocha")
    parser.add_argument("--accent", default="dark")
    parser.add_argument("--sizes", default="32,48,64,96",
                        help="bildestørrelser som legges i hver fil")
    args = parser.parse_args()
    sizes = [int(s) for s in args.sizes.split(",")]

    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        theme = Path(args.theme) if args.theme else download(args.flavor, args.accent, Path(tmp))
        print(f"Konverterer fra {theme}")
        made = convert(theme, INSTALL_DIR / "cursors", sizes)

    name = f"Catppuccin {args.flavor.capitalize()} {args.accent.capitalize()}"
    install(made, name)
    print(f"\nInstallert som «{name}». Bytt tilbake under Innstillinger > Bluetooth og enheter > Mus,")
    print("eller kjør uninstall.bat.")


if __name__ == "__main__":
    sys.exit(main())
