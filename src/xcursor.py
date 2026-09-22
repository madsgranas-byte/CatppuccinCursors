"""Reads XCursor files, the cursor format used on Linux.

A file is a header, a table of contents and a series of chunks. The chunks we
care about are the images: one per size, and for animated cursors one per frame.
"""

import struct
from pathlib import Path

MAGIC = b"Xcur"
CHUNK_IMAGE = 0xFFFD0002


class Frame:
    def __init__(self, size, width, height, xhot, yhot, delay, pixels):
        self.size = size          # the size the theme calls this image
        self.width = width
        self.height = height
        self.xhot = xhot
        self.yhot = yhot
        self.delay = delay        # milliseconds, 0 for still cursors
        self.pixels = pixels      # BGRA bytes, top row first

    def __repr__(self):
        return f"<Frame {self.width}x{self.height} hot={self.xhot},{self.yhot} delay={self.delay}>"


def resolve(path):
    """Theme files may be aliases: a tiny file holding the name of another."""
    path = Path(path)
    for _ in range(5):
        data = path.read_bytes()
        if data[:4] == MAGIC:
            return path
        name = data.decode("utf-8", "ignore").strip()
        if not name or "/" in name or "\\" in name:
            raise ValueError(f"{path} is neither a cursor nor an alias")
        path = path.parent / name
    raise ValueError("alias chain too long")


def read(path):
    """Returns every image in the file, in file order."""
    data = resolve(path).read_bytes()
    magic, header_size, _version, ntoc = struct.unpack_from("<4sIII", data, 0)
    if magic != MAGIC:
        raise ValueError("not an XCursor file")

    frames = []
    for i in range(ntoc):
        chunk_type, subtype, position = struct.unpack_from("<III", data, header_size + i * 12)
        if chunk_type != CHUNK_IMAGE:
            continue
        _size, _type, _subtype, _version, width, height, xhot, yhot, delay = \
            struct.unpack_from("<IIIIIIIII", data, position)
        start = position + 36
        pixels = data[start:start + width * height * 4]
        frames.append(Frame(subtype, width, height, xhot, yhot, delay, pixels))
    return frames


def pick(frames, size):
    """The frames whose images come closest to `size` pixels wide.

    A theme's own size labels are only nominal: Catppuccin's "30" holds a 40x40
    image, since the drawing does not fill the square. Matching on the real
    width is what keeps the cursor the size Windows expects.
    """
    widths = sorted({f.width for f in frames})
    chosen = min(widths, key=lambda w: (abs(w - size), w))
    return [f for f in frames if f.width == chosen]
