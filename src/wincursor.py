"""Writes Windows cursors: .cur for still ones, .ani for animated ones.

A .cur file is an .ico with the hotspot stored where an icon keeps its color
planes and bit depth. Like an icon it can hold several sizes, and Windows picks
the one that matches the screen. That matters: on a 200% display Windows asks
for a 64 px cursor, and a file holding only 32 px is stretched and looks soft.

Unlike icons, cursors must hold an uncompressed DIB, so the pixels go in as a
bottom-up bitmap followed by an (unused) AND mask.

An .ani file is a RIFF file: a header chunk, an optional list of per-frame
delays, and one complete .cur file per animation step.
"""

import struct

JIFFY = 1000 / 60  # .ani measures time in 1/60 of a second


def dib(frame):
    """One image as a bottom-up 32-bit DIB with an empty AND mask."""
    header = struct.pack("<IiiHHIIiiII", 40, frame.width, frame.height * 2, 1, 32,
                         0, 0, 0, 0, 0, 0)
    stride = frame.width * 4
    rows = [frame.pixels[y * stride:(y + 1) * stride] for y in range(frame.height)]
    xor = b"".join(reversed(rows))
    mask_stride = ((frame.width + 31) // 32) * 4   # 1 bit per pixel, 4-byte rows
    return header + xor + b"\x00" * (mask_stride * frame.height)


def cur_bytes(frames):
    """frames: the same cursor in one or more sizes."""
    frames = sorted(frames, key=lambda f: f.width)
    images = [dib(f) for f in frames]
    offset = 6 + 16 * len(frames)
    entries = b""
    for frame, image in zip(frames, images):
        entries += struct.pack("<BBBBHHII",
                               frame.width % 256, frame.height % 256, 0, 0,
                               frame.xhot, frame.yhot, len(image), offset)
        offset += len(image)
    return struct.pack("<HHH", 0, 2, len(frames)) + entries + b"".join(images)


def _chunk(tag, payload):
    data = tag + struct.pack("<I", len(payload)) + payload
    return data + (b"\x00" if len(payload) % 2 else b"")


def ani_bytes(steps):
    """steps: one list of same-size-set frames per animation step, in order."""
    rates = [max(1, round(step[0].delay / JIFFY)) for step in steps]
    anih = struct.pack("<IIIIIIIII", 36, len(steps), len(steps), 0, 0, 0, 0,
                       rates[0], 0x1)                      # 0x1: frames are icons
    body = _chunk(b"anih", anih)
    if len(set(rates)) > 1:
        body += _chunk(b"rate", b"".join(struct.pack("<I", r) for r in rates))
    icons = b"".join(_chunk(b"icon", cur_bytes(step)) for step in steps)
    body += b"LIST" + struct.pack("<I", len(icons) + 4) + b"fram" + icons
    return b"RIFF" + struct.pack("<I", len(body) + 4) + b"ACON" + body


def write(path, steps):
    """steps: a list of animation steps, each a list of frames (one per size).

    Writes .ani when there is more than one step, .cur otherwise.
    """
    if len(steps) > 1:
        path = path.with_suffix(".ani")
        path.write_bytes(ani_bytes(steps))
    else:
        path = path.with_suffix(".cur")
        path.write_bytes(cur_bytes(steps[0]))
    return path
