# CatppuccinCursors

[Catppuccin cursors](https://github.com/catppuccin/cursors) on Windows.

The Catppuccin theme ships in the XCursor format that Linux uses, and there is no Windows build. This converts it: it reads the XCursor files and writes real Windows `.cur` and `.ani` files, then installs them as a cursor scheme you can switch away from in Settings.

Pure Python, nothing to install besides Python itself.

## Install

```
install.bat
```

It downloads `catppuccin-mocha-dark-cursors.zip` from the Catppuccin release page, converts it, installs to `%LOCALAPPDATA%\Programs\CatppuccinCursors` and applies it right away.

Other flavors and accents:

```
install.bat --flavor latte --accent mauve
```

Flavors: `mocha`, `macchiato`, `frappe`, `latte`. Accents: `dark`, `light`, `blue`, `flamingo`, `green`, `lavender`, `maroon`, `mauve`, `peach`, `pink`, `red`, `rosewater`, `sapphire`, `sky`, `teal`, `yellow`.

To convert a theme you already have on disk, point at its `cursors` folder:

```
install.bat --theme "C:\path\to\catppuccin-mocha-dark-cursors\cursors"
```

`uninstall.bat` puts the previous cursors back and deletes the installed files. The previous setting is saved during install, so this is not just a reset to the Windows default.

## Resolution

Each file holds 32, 48, 64 and 96 px images, and Windows picks the one that fits the screen. This matters on a scaled display: at 200% Windows asks for a 64 px cursor, and a file holding only 32 px gets stretched and looks soft.

Change the set with `--sizes 32,48,64,128`.

## How it works

- `src/xcursor.py` reads the XCursor format: a header, a table of contents and one image chunk per size, plus one per frame for animated cursors. Theme files are often aliases, a small file holding the name of another, and those are followed.
  The size a theme gives an image is nominal, so the images are matched on their real width: Catppuccin's "30" is a 40x40 image.
- `src/wincursor.py` writes the Windows formats. A `.cur` is an `.ico` whose color-planes and bit-depth fields hold the hotspot instead, and whose images must be uncompressed bottom-up DIBs with an AND mask. An `.ani` is a RIFF file with a header chunk, an optional table of per-frame delays in 1/60 s, and one complete `.cur` per animation step.
- `src/install.py` maps the theme's names to the 15 Windows cursor roles, writes the files, saves what was set before, and registers the scheme under `HKEY_CURRENT_USER\Control Panel\Cursors`. `SystemParametersInfo` applies it without a sign-out.

## Credit

The artwork is [catppuccin/cursors](https://github.com/catppuccin/cursors) (MIT), which is built on [Bibata](https://github.com/ful1e5/Bibata_Cursor). This project only converts it.
