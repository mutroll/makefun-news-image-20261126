#!/usr/bin/env python3
"""news-image-20261126 — poster edition.

Draws "The World in One Day — Thursday 26 November 2026": a giant date
masthead, six news panels (picture + headline + one short factual sub-line)
and an also-today footer. Pure Python 3.13 standard library only: no PIL,
no network, no fonts from disk. Text is rendered with a small built-in
5x7 bitmap font, supersampled at 2048x2048 and downscaled to 1024x1024
so headlines and sub-lines stay legible in a 300 px downscale.

Output: writes entry.png into MAKEFUN_OUTPUT_DIR (default /output).
Deterministic: two runs write byte-identical PNGs.
"""

import os
import struct
import zlib

# ---------------------------------------------------------------- font -----
# 5x7 bitmap font. Each glyph is 7 rows of 5 bits ("1" = filled).
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "\u2022": ("00000", "00000", "01100", "01100", "00000", "00000", "00000"),
}

# Characters that appear in poster copy but are not in FONT.
SANITIZE = {
    "\u2019": "'", "\u2018": "'", "\u2013": "-", "\u2014": "-",
    "\u00b7": "\u2022", "\u00d7": "x", "\u00b0": "o",
}


def clean(text):
    out = []
    for ch in text:
        ch = SANITIZE.get(ch, ch)
        ch = ch.upper()
        out.append(ch if ch in FONT else " ")
    return "".join(out)


# -------------------------------------------------------------- canvas -----
class Canvas:
    """RGB canvas with flat-shape drawing and bitmap-font text."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.rect(0, 0, w, h, bg)

    def _idx(self, x, y):
        return (y * self.w + x) * 3

    def set(self, x, y, rgb):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = self._idx(x, y)
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = rgb

    def rect(self, x, y, w, h, rgb):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            i = self._idx(x0, yy)
            row = bytes(rgb) * (x1 - x0)
            self.buf[i:i + (x1 - x0) * 3] = row

    def border(self, x, y, w, h, rgb, t):
        self.rect(x, y, w, t, rgb)
        self.rect(x, y + h - t, w, t, rgb)
        self.rect(x, y, t, h, rgb)
        self.rect(x + w - t, y, t, h, rgb)

    def circle(self, cx, cy, r, rgb):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.rect(cx - dx, cy + dy, 2 * dx + 1, 1, rgb)

    def poly(self, points, rgb):
        """Scanline fill of a simple polygon."""
        if not points:
            return
        ys = [p[1] for p in points]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                xa = int(xs[j] + 0.5)
                xb = int(xs[j + 1] + 0.5)
                self.rect(xa, y, xb - xa + 1, 1, rgb)

    def line(self, x0, y0, x1, y1, rgb, thick=1):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        r = max(1, thick // 2)
        for s in range(steps + 1):
            t = s / steps
            x = int(x0 + t * (x1 - x0))
            y = int(y0 + t * (y1 - y0))
            self.circle(x, y, r, rgb)

    # -- text -------------------------------------------------------------
    def text_width(self, s, scale):
        s = clean(s)
        if not s:
            return 0
        return (len(s) * 6 - 1) * scale

    def text(self, x, y, s, scale, rgb, align="left"):
        s = clean(s)
        w = self.text_width(s, scale)
        if align == "center":
            x = x - w // 2
        elif align == "right":
            x = x - w
        cx = x
        for ch in s:
            glyph = FONT[ch]
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, rgb)
            cx += 6 * scale
        return w

    def wrap(self, s, max_w, scale):
        """Greedy word wrap; returns a list of lines fitting max_w."""
        s = clean(s)
        lines = []
        for word in s.split(" "):
            if not lines:
                lines.append(word)
                continue
            trial = lines[-1] + " " + word
            if self.text_width(trial, scale) <= max_w:
                lines[-1] = trial
            else:
                lines.append(word)
        return lines


# ---------------------------------------------------------------- png ------
def png_bytes(w, h, rgb):
    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    header = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


def downscale2(src, w, h):
    """Box-average a 2x supersampled RGB buffer down by 2."""
    nw, nh = w // 2, h // 2
    out = bytearray(nw * nh * 3)
    for y in range(nh):
        for x in range(nw):
            for c in range(3):
                s = 0
                for dy in (0, 1):
                    for dx in (0, 1):
                        s += src[((2 * y + dy) * w + 2 * x + dx) * 3 + c]
                out[(y * nw + x) * 3 + c] = s // 4
    return bytes(out)


# -------------------------------------------------------------- palette ----
NAVY = (20, 33, 61)
GOLD = (217, 164, 65)
PAPER = (245, 239, 227)
WHITE = (255, 255, 255)
INK = (58, 58, 58)
MUTED = (110, 105, 95)

SS = 2048  # supersampled canvas size
OUT = 1024

# Layout (supersampled coordinates).
MARGIN = 32
MASTHEAD_H = 340
GOLD_STRIP_H = 8
PANEL_W = 980
PANEL_H = 490
PANEL_GUT = 20
FOOTER_H = 99

PANELS = [
    {
        "kicker": "CRICKET \u2022 NEWLANDS",
        "color": (27, 122, 61),
        "headline": ["INGLIS TON PUTS", "AUSTRALIA ON TOP"],
        "sub": "Inglis 102; Australia 429 lead 100; SA 140-4 at stumps.",
        "pic": "cricket",
    },
    {
        "kicker": "MARKETS \u2022 TOKYO",
        "color": (29, 78, 137),
        "headline": ["NIKKEI CLIMBS", "AT THE OPEN"],
        "sub": "Nikkei opens 417 yen up at 57,429; 57,976 by mid-morning.",
        "pic": "markets",
    },
    {
        "kicker": "THANKSGIVING \u2022 USA",
        "color": (192, 86, 33),
        "headline": ["THANKSGIVING DAY", "ACROSS AMERICA"],
        "sub": "Macy's parade in New York; US markets shut for the holiday.",
        "pic": "thanksgiving",
    },
    {
        "kicker": "TRADE \u2022 TAIWAN",
        "color": (14, 124, 123),
        "headline": ["TAIWAN KEEPS ITS", "15% US TARIFF"],
        "sub": "Taipei keeps 15% rate after Washington's tariff plan.",
        "pic": "trade",
    },
    {
        "kicker": "ECONOMY \u2022 SEOUL",
        "color": (91, 45, 142),
        "headline": ["SEOUL LIFTS RATES", "TO 3.25%"],
        "sub": "BOK raises rate to 3.25%, third hike this year.",
        "pic": "economy",
    },
    {
        "kicker": "INDIA \u2022 NEW DELHI",
        "color": (156, 43, 46),
        "headline": ["INDIA MARKS", "CONSTITUTION DAY"],
        "sub": "Adopted 26 Nov 1949; 77 years on today.",
        "pic": "constitution",
    },
]

FOOTER = [
    "ALSO TODAY: GIFT NIFTY ABOVE 26,000 AHEAD OF MUMBAI'S OPEN",
    "SOURCES: BBC SPORT \u2022 REUTERS \u2022 YONHAP \u2022 MONEYTODAY \u2022 A-SPORTS",
]


# ------------------------------------------------------- panel pictures ----
def pic_cricket(cv, x, y, w, h):
    cv.rect(x, y, w, h, (47, 125, 60))
    cv.rect(x + w // 2 - 130, y, 260, h, (201, 160, 108))
    cv.rect(x + w // 2 - 130, y + 8, 260, 4, WHITE)
    cv.rect(x + w // 2 - 130, y + h - 12, 260, 4, WHITE)
    sx = x + w // 2 - 60
    for i in range(3):
        cv.rect(sx + i * 22, y + h // 2 - 34, 10, 46, WHITE)
    cv.rect(sx - 6, y + h // 2 - 40, 76, 6, WHITE)
    cv.circle(x + w - 170, y + h // 2 + 10, 15, (200, 40, 40))
    cv.poly([
        (x + 120, y + h - 16), (x + 168, y + h - 16),
        (x + 210, y + 26), (x + 162, y + 26),
    ], (222, 184, 135))
    cv.poly([
        (x + 162, y + 26), (x + 210, y + 26),
        (x + 222, y + 8), (x + 174, y + 8),
    ], (222, 184, 135))


def pic_markets(cv, x, y, w, h):
    cv.rect(x, y, w, h, (18, 56, 95))
    for gy in (y + 30, y + 65, y + 100):
        cv.rect(x + 20, gy, w - 40, 3, (42, 90, 138))
    bars = [34, 52, 44, 66, 58]
    for i, bh in enumerate(bars):
        cv.rect(x + 60 + i * 46, y + h - 14 - bh, 26, bh, (46, 160, 110))
    pts = [(x + 300, y + h - 26), (x + 470, y + h - 52),
           (x + 620, y + h - 40), (x + 790, y + 52), (x + 920, y + 30)]
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                GOLD, thick=9)
    cv.poly([(x + 920, y + 30), (x + 886, y + 22), (x + 892, y + 56)],
            GOLD)


def pic_thanksgiving(cv, x, y, w, h):
    cv.rect(x, y, w, h, (242, 192, 99))
    cv.circle(x + 210, y + h // 2 - 6, 52, (228, 87, 46))
    cv.circle(x + 192, y + h // 2 - 22, 16, (240, 120, 70))
    for dx in (-26, 0, 26):
        cv.line(x + 210 + dx, y + h // 2 + 44, x + 210 + dx // 2,
                y + h - 14, (120, 70, 30), thick=3)
    cv.rect(x + 184, y + h - 16, 52, 14, (140, 90, 40))
    for lx, ly, lc in ((x + 560, y + 26, (200, 60, 30)),
                        (x + 640, y + 60, (180, 40, 40)),
                        (x + 760, y + 30, (210, 110, 30)),
                        (x + 850, y + 70, (190, 60, 30))):
        cv.circle(lx, ly, 12, lc)
    for cx in range(x + 540, x + w - 40, 46):
        cv.circle(cx, y + h - 10, 7, (90, 50, 30))


def pic_trade(cv, x, y, w, h):
    cv.rect(x, y, w, h, (220, 238, 242))
    cv.rect(x, y + h - 30, w, 30, (127, 179, 200))
    cv.poly([(x + 120, y + h - 30), (x + 860, y + h - 30),
             (x + 800, y + h - 6), (x + 180, y + h - 6)], (40, 60, 90))
    cv.rect(x + 200, y + h - 96, 120, 62, (192, 57, 43))
    cv.rect(x + 330, y + h - 96, 120, 62, (36, 113, 163))
    cv.rect(x + 260, y + h - 158, 120, 62, (30, 132, 73))
    for bx in (200, 330, 260):
        cv.border(x + bx, y + h - 96 if bx != 260 else y + h - 158,
                  120, 62, WHITE, 3)
    for wx in (x + 60, x + 420, x + 700, x + 900):
        cv.circle(wx, y + h - 18, 10, WHITE)


def pic_economy(cv, x, y, w, h):
    cv.rect(x, y, w, h, (232, 228, 216))
    cv.poly([(x + 120, y + 14), (x + 460, y + 14), (x + 290, y + 58)],
            NAVY)
    for i in range(4):
        cx = x + 150 + i * 80
        cv.rect(cx, y + 62, 26, 52, WHITE)
        cv.rect(cx - 4, y + 58, 34, 6, WHITE)
        cv.rect(cx - 4, y + 112, 34, 6, WHITE)
    cv.rect(x + 120, y + 118, 340, 6, (180, 174, 160))
    cv.circle(x + 780, y + 62, 34, GOLD)
    cv.circle(x + 780, y + 62, 24, (232, 184, 90))
    cv.rect(x + 700, y + 108, 160, 6, (180, 174, 160))


def pic_constitution(cv, x, y, w, h):
    cv.rect(x, y, w, h, (251, 227, 194))
    cv.poly([(x + 330, y + 22), (x + 480, y + 34), (x + 480, y + h - 18),
             (x + 330, y + h - 18)], WHITE)
    cv.poly([(x + 500, y + 34), (x + 650, y + 22), (x + 650, y + h - 18),
             (x + 500, y + h - 18)], WHITE)
    for i in range(3):
        cv.rect(x + 350, y + 52 + i * 20, 110, 6, NAVY)
        cv.rect(x + 520, y + 52 + i * 20, 110, 6, NAVY)
    cv.circle(x + 830, y + 46, 20, (230, 120, 40))
    cv.rect(x + 120, y + h - 24, 200, 8, (156, 43, 46))


PIC_DRAW = {
    "cricket": pic_cricket,
    "markets": pic_markets,
    "thanksgiving": pic_thanksgiving,
    "trade": pic_trade,
    "economy": pic_economy,
    "constitution": pic_constitution,
}


# ------------------------------------------------------------- poster ------
def draw_panel(cv, px, py, panel):
    cv.rect(px, py, PANEL_W, PANEL_H, WHITE)
    cv.border(px, py, PANEL_W, PANEL_H, NAVY, 3)
    # Header strip with kicker.
    cv.rect(px, py, PANEL_W, 54, panel["color"])
    cv.text(px + 24, py + 6, panel["kicker"], 6, WHITE)
    # Picture band.
    PIC_DRAW[panel["pic"]](cv, px + 3, py + 57, PANEL_W - 6, 124)
    # Headline, up to two lines.
    hy = py + 57 + 124 + 8
    for i, line in enumerate(panel["headline"]):
        cv.text(px + 24, hy + i * 72, line, 9, NAVY)
    # Sub-line, wrapped to at most three lines.
    sub_lines = cv.wrap(panel["sub"], PANEL_W - 48, 7)[:3]
    sy = py + 57 + 124 + 8 + 144 + 2
    for i, line in enumerate(sub_lines):
        cv.text(px + 24, sy + i * 52, line, 7, INK)


def build_poster():
    cv = Canvas(SS, SS, PAPER)
    # Masthead.
    cv.rect(MARGIN, MARGIN, SS - 2 * MARGIN, MASTHEAD_H, NAVY)
    cv.text(SS // 2, MARGIN + 24, "THURSDAY", 21, WHITE, align="center")
    cv.text(SS // 2, MARGIN + 210, "26 NOVEMBER 2026", 18, GOLD,
            align="center")
    cv.rect(MARGIN, MARGIN + MASTHEAD_H, SS - 2 * MARGIN, GOLD_STRIP_H, GOLD)
    # Panels, 2 columns x 3 rows.
    top = MARGIN + MASTHEAD_H + GOLD_STRIP_H + 16
    for i, panel in enumerate(PANELS):
        px = MARGIN + (i % 2) * (PANEL_W + PANEL_GUT)
        py = top + (i // 2) * (PANEL_H + PANEL_GUT)
        draw_panel(cv, px, py, panel)
    # Footer.
    fy = top + 3 * PANEL_H + 2 * PANEL_GUT + 16
    cv.rect(MARGIN, fy, SS - 2 * MARGIN, 4, GOLD)
    cv.text(SS // 2, fy + 18, FOOTER[0], 5, INK, align="center")
    cv.text(SS // 2, fy + 58, FOOTER[1], 5, MUTED, align="center")
    return downscale2(cv.buf, SS, SS)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    png = png_bytes(OUT, OUT, build_poster())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(png)
    print("wrote %s (%d bytes)" % (path, len(png)))


if __name__ == "__main__":
    main()
