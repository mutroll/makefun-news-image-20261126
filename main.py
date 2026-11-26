#!/usr/bin/env python3
"""news-image-20261126 r2: poster of Thursday 26 November 2026 world news.

Draws a 1024x1024 PNG newspaper poster (supersampled 2048 -> 1024) with a
giant date masthead, six outcome-based news panels verified against
26 November 2026 reporting, and an also-today footer. Pure Python 3.13
standard library. Deterministic: two runs write identical bytes.

Six stories (all happened / first reported Thu 26 Nov 2026):
 1. Asian stocks rally as new US tariffs look milder than feared (Reuters)
 2. Bank of Korea raises base rate to 3.25% (Bank of Korea)
 3. UK signs GBP 8bn submarine deal with Babcock (Reuters / GOV.UK)
 4. EU leaders meet in Brussels over EUR 45bn Ukraine loan (Reuters / AP)
 5. Indonesia mine: 13 dead confirmed, search resumes for 13 trapped (Reuters)
 6. Israel kills Hamas economy chief Khaled Abu Nada in overnight Gaza
    strike; at least 5 killed (Xinhua, 26 Nov 08:42 UTC)
"""

import binascii
import hashlib
import math
import os
import struct
import sys
import zlib

# ---------------------------------------------------------------- font -----
# 5x7 pixel font, uppercase only. Each glyph is 7 rows of 5 bits, written
# as strings so the shapes are readable. Only the characters the poster
# uses are defined; text is uppercased before drawing.
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
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "/": ("00001", "00001", "00010", "00100", "01000", "10000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "£": ("00111", "01000", "01000", "11110", "01000", "01000", "11111"),
    "€": ("01110", "10001", "11111", "10000", "11111", "10001", "01110"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "•": ("00000", "00100", "01110", "01110", "01110", "00100", "00000"),
    "—": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "–": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
}

# Characters that map onto a defined glyph.
ALIASES = {"·": "•", "’": "'", "‘": "'", "“": '"', "”": '"'}


def normalise(text):
    out = []
    for ch in text.upper():
        out.append(ALIASES.get(ch, ch))
    return "".join(out)


def text_width(text, scale):
    """Pixel width of text at the given scale (advance 6 units per char)."""
    return len(normalise(text)) * 6 * scale


# -------------------------------------------------------------- canvas -----
class Canvas:
    def __init__(self, size):
        self.size = size
        self.px = bytearray(size * size * 3)

    def set_px(self, x, y, color):
        if 0 <= x < self.size and 0 <= y < self.size:
            i = (y * self.size + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.size, x + w), min(self.size, y + h)
        for yy in range(y0, y1):
            base = (yy * self.size + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = color

    def outline_rect(self, x, y, w, h, color, t=3):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            for a in range(-(t // 2), t // 2 + 1):
                for b in range(-(t // 2), t // 2 + 1):
                    self.set_px(x + a, y + b, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def fill_ellipse(self, cx, cy, rx, ry, color):
        for yy in range(cy - ry, cy + ry + 1):
            if ry == 0:
                continue
            dx = int(rx * (1 - ((yy - cy) / ry) ** 2) ** 0.5)
            for xx in range(cx - dx, cx + dx + 1):
                self.set_px(xx, yy, color)

    def fill_circle(self, cx, cy, r, color):
        self.fill_ellipse(cx, cy, r, r, color)

    def fill_triangle(self, x0, y0, x1, y1, x2, y2, color):
        minx, maxx = min(x0, x1, x2), max(x0, x1, x2)
        miny, maxy = min(y0, y1, y2), max(y0, y1, y2)
        d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if d == 0:
            return
        for yy in range(miny, maxy + 1):
            for xx in range(minx, maxx + 1):
                a = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / d
                b = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / d
                c = 1 - a - b
                if a >= 0 and b >= 0 and c >= 0:
                    self.set_px(xx, yy, color)

    def draw_text(self, x, y, scale, color, text):
        """Draw text at top-left (x, y). Returns the drawn width."""
        text = normalise(text)
        cx = x
        for ch in text:
            glyph = FONT.get(ch)
            if glyph is None:
                cx += 6 * scale
                continue
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.fill_rect(
                            cx + col * scale, y + row * scale,
                            scale, scale, color,
                        )
            cx += 6 * scale
        return cx - x

    def draw_text_centred(self, cx, y, scale, color, text):
        w = text_width(text, scale)
        return self.draw_text(cx - w // 2, y, scale, color, text)


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines fitting max_width px."""
    words = normalise(text).split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------ png out -----
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def downsample(canvas):
    """Box-average 2048 canvas down to a 1024 RGB image (deterministic)."""
    big = canvas.size
    small = big // 2
    out = bytearray(small * small * 3)
    src = canvas.px
    for y in range(small):
        for x in range(small):
            acc = [0, 0, 0]
            for dy in (0, 1):
                for dx in (0, 1):
                    i = ((2 * y + dy) * big + (2 * x + dx)) * 3
                    acc[0] += src[i]
                    acc[1] += src[i + 1]
                    acc[2] += src[i + 2]
            j = (y * small + x) * 3
            out[j] = (acc[0] + 2) // 4
            out[j + 1] = (acc[1] + 2) // 4
            out[j + 2] = (acc[2] + 2) // 4
    return bytes(out), small


def encode_png(rgb, size):
    raw = bytearray()
    stride = size * 3
    for y in range(size):
        raw.append(0)  # filter: none
        raw += rgb[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return png


# ------------------------------------------------------------- palette -----
CREAM = (244, 239, 227)
PAPER = (252, 250, 245)
PAGE = (233, 228, 213)
INK = (20, 32, 54)
NAVY = (18, 35, 63)
RED = (192, 57, 43)
SUB = (64, 68, 74)
WHITE = (255, 255, 255)

S = 2048          # supersampled canvas
MARGIN = 64
PANEL_W = 936
PANEL_H = 436
GAP_X = 48
GAP_Y = 44
GRID_TOP = 472

# (kicker, accent, tint, headline line 1, headline line 2, sub text,
#  illustration kind)
PANELS = [
    ("MARKETS · ASIA", (46, 125, 50), (232, 245, 233),
     "ASIAN STOCKS RALLY", "AS TARIFFS LOOK MILDER",
     "NIKKEI +1.6%, KOSPI +1.9% AS MARKETS SHRUG OFF NEW US TARIFFS",
     "chart"),
    ("ECONOMY · SEOUL", (21, 101, 192), (227, 238, 250),
     "KOREA RAISES RATES", "TO 3.25%",
     "BANK OF KOREA RESUMES HIKES AS CHIP BOOM LIFTS 2027 GROWTH TO 4.1%",
     "bank"),
    ("DEFENCE · LONDON", (69, 90, 120), (222, 232, 240),
     "UK SIGNS £8BN", "SUBMARINE DEAL",
     "BABCOCK PACT TO GET NUCLEAR SUBS BACK TO SEA FASTER; 3,000 JOBS",
     "sub"),
    ("POLITICS · BRUSSELS", (0, 51, 153), (226, 232, 248),
     "EU SUMMIT OPENS", "OVER UKRAINE AID",
     "27 LEADERS WEIGH €45BN LOAN FOR KYIV AND A €1.6TN BUDGET",
     "stars"),
    ("DISASTER · JAVA", (146, 94, 20), (245, 235, 214),
     "13 DEAD IN JAVA", "GOLD MINE FLOOD",
     "RESCUERS RESUME SEARCH FOR 13 STILL TRAPPED 100M DOWN IN BOGOR",
     "mine"),
    ("CONFLICT · GAZA", (140, 40, 40), (248, 231, 228),
     "ISRAEL KILLS HAMAS", "ECONOMY CHIEF",
     "KHALED ABU NADA DIES IN OVERNIGHT GAZA STRIKE; AT LEAST 5 KILLED",
     "burst"),
]


# ------------------------------------------------------- illustrations -----
def draw_chart(cv, x, y, w, h, accent):
    # Rising bars and a rising line with an arrowhead.
    base = y + h - 26
    bar_w = 64
    heights = (34, 58, 82)
    for i, bh in enumerate(heights):
        bx = x + 90 + i * 150
        cv.fill_rect(bx, base - bh, bar_w, bh, accent)
    pts = [(x + 90, base - 20), (x + 260, base - 52),
           (x + 430, base - 44), (x + 600, base - 96), (x + 800, base - 118)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], (20, 90, 30), 10)
    tip = pts[-1]
    cv.fill_triangle(tip[0], tip[1] - 26, tip[0] + 44, tip[1] - 6,
                     tip[0] - 6, tip[1] + 10, (20, 90, 30))
    cv.line(x + 60, base, x + w - 60, base, INK, 6)


def draw_bank(cv, x, y, w, h, accent):
    # A bank front: pediment, columns, steps; big rate figure on the right.
    bx, by = x + 80, y + 18
    cv.fill_triangle(bx, by, bx + 300, by, bx + 150, by + 34, accent)
    for i in range(4):
        cx = bx + 22 + i * 72
        cv.fill_rect(cx, by + 42, 26, 66, accent)
    cv.fill_rect(bx, by + 108, 300, 10, accent)
    cv.fill_rect(bx - 14, by + 118, 328, 12, accent)
    cv.draw_text(x + 470, y + 34, 12, NAVY, "3.25%")


def draw_sub(cv, x, y, w, h, accent):
    # Submarine silhouette over two wave lines.
    cy = y + 62
    cv.fill_ellipse(x + 430, cy, 330, 42, accent)
    cv.fill_rect(x + 330, cy - 74, 130, 40, accent)
    cv.fill_rect(x + 380, cy - 96, 14, 26, accent)
    cv.fill_triangle(x + 760, cy - 20, x + 760, cy + 20, x + 812, cy, accent)
    for wy in (y + 124, y + 138):
        for xx in range(x + 60, x + w - 60, 96):
            cv.line(xx, wy, xx + 48, wy, (120, 150, 180), 5)


def draw_stars(cv, x, y, w, h, accent):
    # Ring of twelve gold stars around a euro sign; big figure on the right.
    cx, cy = x + 210, y + 75
    gold = (201, 162, 39)
    for k in range(12):
        a = 2 * math.pi * k / 12 - math.pi / 2
        sx = int(cx + 96 * math.cos(a))
        sy = int(cy + 62 * math.sin(a))
        cv.fill_circle(sx, sy, 9, gold)
    cv.draw_text(cx - 21, cy - 26, 7, accent, "€")
    cv.draw_text(x + 470, y + 34, 12, NAVY, "€45BN")


def draw_mine(cv, x, y, w, h, accent):
    # A mine shaft with a ladder and a miner's helmet.
    sx = x + 300
    cv.fill_rect(sx, y, 150, h, (52, 40, 26))
    for i in range(5):
        ry = y + 14 + i * 28
        cv.fill_rect(sx + 18, ry, 114, 8, (210, 180, 120))
    cv.fill_rect(sx - 60, y, 60, h, (30, 24, 16))
    cv.fill_rect(sx + 150, y, 60, h, (30, 24, 16))
    # Helmet: dome + brim + lamp.
    hx, hy = x + 640, y + 96
    cv.fill_ellipse(hx, hy, 74, 40, (232, 180, 20))
    cv.fill_rect(hx - 92, hy + 28, 184, 12, (200, 150, 10))
    cv.fill_circle(hx, hy - 6, 12, WHITE)
    cv.draw_text(x + 560, y + 8, 6, accent, "100M DOWN")


def draw_burst(cv, x, y, w, h, accent):
    # City skyline with a blast burst above it.
    base = y + h - 10
    heights = (52, 88, 64, 104, 72, 46)
    bx = x + 90
    for i, bh in enumerate(heights):
        cv.fill_rect(bx + i * 110, base - bh, 78, bh, (52, 52, 60))
    cx, cy = x + 800, y + 58
    for k in range(12):
        a = 2 * math.pi * k / 12
        x1 = int(cx + 26 * math.cos(a))
        y1 = int(cy + 26 * math.sin(a))
        x2 = int(cx + 62 * math.cos(a))
        y2 = int(cy + 62 * math.sin(a))
        cv.line(x1, y1, x2, y2, accent, 9)
    cv.fill_circle(cx, cy, 24, accent)
    cv.fill_circle(cx, cy, 12, (255, 214, 64))


ILLUSTRATIONS = {
    "chart": draw_chart,
    "bank": draw_bank,
    "sub": draw_sub,
    "stars": draw_stars,
    "mine": draw_mine,
    "burst": draw_burst,
}


# ------------------------------------------------------------ poster -------
def draw_panel(cv, px, py, panel):
    kicker, accent, tint, head1, head2, sub, kind = panel
    cv.fill_rect(px, py, PANEL_W, PANEL_H, PAPER)
    cv.outline_rect(px, py, PANEL_W, PANEL_H, INK, 3)
    # Kicker bar.
    cv.fill_rect(px, py, PANEL_W, 58, accent)
    cv.draw_text(px + 36, py + 12, 5, WHITE, kicker)
    # Illustration strip.
    iy = py + 58
    cv.fill_rect(px, iy, PANEL_W, 150, tint)
    ILLUSTRATIONS[kind](cv, px, iy, PANEL_W, 150, accent)
    cv.fill_rect(px, iy + 150, PANEL_W, 4, accent)
    # Headline, two lines.
    cv.draw_text(px + 36, py + 228, 6, INK, head1)
    cv.draw_text(px + 36, py + 282, 6, INK, head2)
    # Sub lines, wrapped.
    lines = wrap_text(sub, 4, PANEL_W - 72)
    yy = py + 346
    for line in lines[:2]:
        cv.draw_text(px + 36, yy, 4, SUB, line)
        yy += 38


def build_poster():
    cv = Canvas(S)
    cv.fill_rect(0, 0, S, S, PAGE)

    # Masthead.
    cv.fill_rect(0, 0, S, 440, NAVY)
    cv.draw_text_centred(S // 2, 44, 5, CREAM, "THE WORLD IN ONE DAY")
    cv.draw_text_centred(S // 2, 96, 17, CREAM, "THURSDAY")
    cv.draw_text_centred(S // 2, 232, 11, CREAM, "26 NOVEMBER 2026")
    cv.fill_rect(MARGIN, 330, S - 2 * MARGIN, 12, RED)
    cv.draw_text_centred(S // 2, 364, 5, CREAM,
                         "SIX STORIES THAT DEFINED THE DAY")

    # Six panels, 2 columns x 3 rows.
    for i, panel in enumerate(PANELS):
        px = MARGIN + (i % 2) * (PANEL_W + GAP_X)
        py = GRID_TOP + (i // 2) * (PANEL_H + GAP_Y)
        draw_panel(cv, px, py, panel)

    # Footer.
    cv.fill_rect(0, 1892, S, S - 1892, NAVY)
    cv.draw_text_centred(S // 2, 1916, 4, CREAM,
                         "ALSO TODAY: GOLD STEADIES AFTER A ONE-YEAR LOW")
    cv.draw_text_centred(S // 2, 1956, 4, CREAM,
                         "US ARMY DESTROYS AGEING EXPLOSIVES STOCKPILE IN IOWA")
    cv.draw_text_centred(S // 2, 1996, 4, (190, 196, 205),
                         "SOURCES: REUTERS · AP · BANK OF KOREA · GOV.UK · XINHUA")
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = build_poster()
    rgb, size = downsample(cv)
    png = encode_png(rgb, size)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(png)
    digest = hashlib.sha256(png).hexdigest()
    print("wrote %s (%d bytes, %dx%d, sha256 %s)"
          % (path, len(png), size, size, digest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
