#!/usr/bin/env python3
"""Draw the 20 November 2026 world-news poster as a 1024x1024 PNG.

Pure standard library: the PNG is encoded by hand (zlib + struct) and all
text is drawn with a small built-in 5x7 bitmap font. No network, no fonts
from disk, fully deterministic output.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (247, 243, 234)
INK = (17, 17, 17)
RED = (163, 31, 31)
BLUE = (31, 78, 121)
BOX = (232, 224, 204)
GREY = (90, 86, 76)

# 5x7 bitmap font. Each glyph is 7 rows of 5 characters ('#' = on).
FONT = {
    'A': (" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    'B': ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
    'C': (" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"),
    'D': ("#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "),
    'E': ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    'F': ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    'G': (" ####", "#    ", "#    ", "# ###", "#   #", "#   #", " ### "),
    'H': ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    'I': ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"),
    'J': ("  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "),
    'K': ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
    'L': ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
    'M': ("#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"),
    'N': ("#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"),
    'O': (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    'P': ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
    'Q': (" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
    'R': ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
    'S': (" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "),
    'T': ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    'U': ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    'V': ("#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "),
    'W': ("#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"),
    'X': ("#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"),
    'Y': ("#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
    'Z': ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
    '0': (" ### ", "#  ##", "# # #", "##  #", "#   #", "#   #", " ### "),
    '1': ("  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    '2': (" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"),
    '3': ("#### ", "    #", "    #", " ### ", "    #", "    #", "#### "),
    '4': ("   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "),
    '5': ("#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "),
    '6': (" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "),
    '7': ("#####", "    #", "   # ", "  #  ", "  #  ", "  #  ", "  #  "),
    '8': (" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "),
    '9': (" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "),
    ' ': ("     ", "     ", "     ", "     ", "     ", "     ", "     "),
    '.': ("     ", "     ", "     ", "     ", "     ", " ##  ", " ##  "),
    ',': ("     ", "     ", "     ", "     ", " ##  ", " ##  ", " #   "),
    ':': ("     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", "     "),
    ';': ("     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", " #   "),
    "'": ("  #  ", "  #  ", " #   ", "     ", "     ", "     ", "     "),
    '"': (" # # ", " # # ", "     ", "     ", "     ", "     ", "     "),
    '-': ("     ", "     ", "     ", " ### ", "     ", "     ", "     "),
    '(': ("   # ", "  #  ", " #   ", " #   ", " #   ", "  #  ", "   # "),
    ')': (" #   ", "  #  ", "   # ", "   # ", "   # ", "  #  ", " #   "),
    '!': ("  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "     ", "  #  "),
    '?': (" ### ", "#   #", "    #", "   # ", "  #  ", "     ", "  #  "),
    '%': ("##  #", "## # ", "   # ", "  #  ", " #   ", "# ## ", "#  ##"),
    '$': ("  #  ", " ####", "# #  ", " ### ", "  # #", "#### ", "  #  "),
    '&': (" ##  ", "#  # ", "# #  ", " #   ", "# # #", "#  # ", " ## #"),
    '/': ("    #", "    #", "   # ", "  #  ", " #   ", "#    ", "#    "),
    '+': ("     ", "  #  ", "  #  ", "#####", "  #  ", "  #  ", "     "),
    '=': ("     ", "     ", "#####", "     ", "#####", "     ", "     "),
}


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect_outline(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def hline(self, x0, x1, y, c, t=1):
        self.fill_rect(min(x0, x1), y, abs(x1 - x0) + 1, t, c)

    def vline(self, x, y0, y1, c, t=1):
        self.fill_rect(x, min(y0, y1), t, abs(y1 - y0) + 1, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            for a in range(t):
                for b in range(t):
                    self.set(x0 + a, y0 + b, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, filled=False):
        if filled:
            for yy in range(-r, r + 1):
                half = int(math.sqrt(max(0, r * r - yy * yy)))
                self.hline(cx - half, cx + half, cy + yy, c)
            return
        x, y, d = 0, r, 3 - 2 * r
        while x <= y:
            for sx, sy in ((x, y), (-x, y), (x, -y), (-x, -y),
                           (y, x), (-y, x), (y, -x), (-y, -x)):
                self.set(cx + sx, cy + sy, c)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def disc(self, cx, cy, r, c):
        self.circle(cx, cy, r, c, filled=True)

    def triangle(self, pts, c, filled=False):
        (x0, y0), (x1, y1), (x2, y2) = pts
        if filled:
            ymin, ymax = min(y0, y1, y2), max(y0, y1, y2)
            for yy in range(ymin, ymax + 1):
                xs = []
                for (ax, ay), (bx, by) in (((x0, y0), (x1, y1)),
                                           ((x1, y1), (x2, y2)),
                                           ((x2, y2), (x0, y0))):
                    if ay == by:
                        continue
                    if min(ay, by) <= yy < max(ay, by):
                        xs.append(ax + (yy - ay) * (bx - ax) / (by - ay))
                if len(xs) >= 2:
                    self.hline(int(min(xs)), int(max(xs)), yy, c)
            return
        self.line(x0, y0, x1, y1, c)
        self.line(x1, y1, x2, y2, c)
        self.line(x2, y2, x0, y0, c)

    def spiral(self, cx, cy, c):
        steps = 620
        for i in range(steps):
            ang = i * 0.024
            r = 3 + ang * 3.1
            x = int(cx + r * math.cos(ang))
            y = int(cy + r * math.sin(ang))
            self.set(x, y, c)
            self.set(x + 1, y, c)
            self.set(x, y + 1, c)

    def star4(self, cx, cy, r, c):
        self.line(cx - r, cy, cx + r, cy, c, 2)
        self.line(cx, cy - r, cx, cy + r, c, 2)
        self.line(cx - r // 2, cy - r // 2, cx + r // 2, cy + r // 2, c)
        self.line(cx - r // 2, cy + r // 2, cx + r // 2, cy - r // 2, c)

    # ---- text ----
    def text_width(self, text, scale):
        return len(text) * 6 * scale

    def draw_text(self, x, y, text, scale, c):
        cx = x
        for ch in text.upper():
            glyph = FONT.get(ch, FONT[' '])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == '#':
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, c)
            cx += 6 * scale
        return cx - x

    def draw_text_centered(self, y, text, scale, c):
        w = self.text_width(text, scale)
        self.draw_text((self.w - w) // 2, y, text, scale, c)

    def wrap(self, text, scale, max_w):
        lines, cur = [], ""
        for word in text.split(" "):
            trial = (cur + " " + word).strip()
            if self.text_width(trial, scale) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
            chunk(b"IEND", b""))


# ---------------- pictograms ----------------

def pic_cyclone(cv, x, y, s):
    cv.fill_rect(x, y, s, s, BOX)
    cv.rect_outline(x, y, s, s, INK, 2)
    cv.spiral(x + s // 2, y + s // 2, INK)
    cv.disc(x + s // 2, y + s // 2, 7, RED)
    cv.line(x + 14, y + s - 22, x + 52, y + s - 22, BLUE, 3)
    cv.line(x + s - 52, y + 18, x + s - 14, y + 18, BLUE, 3)


def pic_globe(cv, x, y, s):
    cv.fill_rect(x, y, s, s, BOX)
    cv.rect_outline(x, y, s, s, INK, 2)
    cx, cy, r = x + s // 2, y + s // 2 + 4, s // 3
    cv.circle(cx, cy, r, INK)
    cv.line(cx - r, cy, cx + r, cy, INK)
    cv.circle(cx, cy, r // 2, INK)
    cv.star4(cx - r - 2, cy - r - 2, 6, RED)
    cv.star4(cx + r + 2, cy - r + 2, 6, BLUE)
    cv.star4(cx + r - 2, cy + r + 2, 5, RED)


def pic_capitol(cv, x, y, s):
    cv.fill_rect(x, y, s, s, BOX)
    cv.rect_outline(x, y, s, s, INK, 2)
    cx = x + s // 2
    cv.triangle(((cx - 26, y + 52), (cx + 26, y + 52), (cx, y + 26)), INK, True)
    cv.fill_rect(cx - 30, y + 52, 60, 6, INK)
    for dx in (-24, -8, 8, 24):
        cv.fill_rect(cx + dx - 3, y + 58, 6, 26, INK)
    cv.fill_rect(cx - 34, y + 84, 68, 5, INK)
    cv.fill_rect(cx - 38, y + 89, 76, 4, INK)


def pic_voyager(cv, x, y, s):
    cv.fill_rect(x, y, s, s, BOX)
    cv.rect_outline(x, y, s, s, INK, 2)
    cx, cy = x + s // 2, y + s // 2
    cv.circle(cx + 16, cy - 18, 16, BLUE)
    cv.line(cx - 4, cy - 34, cx + 36, cy - 2, BLUE, 2)
    cv.line(cx + 6, cy + 6, cx + 26, cy - 14, INK, 3)
    cv.line(cx + 26, cy - 14, cx + 34, cy - 22, INK, 3)
    cv.disc(cx + 34, cy - 22, 3, RED)
    cv.disc(cx - 26, cy + 26, 2, INK)
    cv.disc(cx - 14, cy - 30, 2, INK)
    cv.disc(cx + 30, cy + 28, 2, INK)


def pic_scales(cv, x, y, s):
    cv.fill_rect(x, y, s, s, BOX)
    cv.rect_outline(x, y, s, s, INK, 2)
    cx = x + s // 2
    cv.vline(cx, y + 16, y + s - 22, INK, 3)
    cv.hline(cx - 32, cx + 32, y + 20, INK, 3)
    cv.disc(cx, y + 16, 4, RED)
    for dx in (-32, 32):
        cv.line(cx + dx, y + 20, cx + dx - 12, y + 48, INK, 2)
        cv.line(cx + dx, y + 20, cx + dx + 12, y + 48, INK, 2)
        cv.hline(cx + dx - 14, cx + dx + 14, y + 48, INK, 3)
    cv.fill_rect(cx - 30, y + s - 18, 60, 4, INK)


def pic_document(cv, x, y, s):
    cv.fill_rect(x, y, s, s, BOX)
    cv.rect_outline(x, y, s, s, INK, 2)
    cv.rect_outline(x + 26, y + 20, 52, 64, INK, 3)
    for i, yy in enumerate((34, 46, 58)):
        cv.hline(x + 34, x + 70, y + yy, INK, 3)
    cv.circle(x + 62, y + 76, 10, RED)
    cv.disc(x + 62, y + 76, 4, RED)
    cv.line(x + 20, y + 78, x + 44, y + 58, BLUE, 3)


# ---------------- layout ----------------

def story_cell(cv, x, y, w, pic, headline, sub):
    pic(cv, x, y, 104)
    tx = x + 116
    tw = w - 116
    lines = cv.wrap(headline, 3, tw)
    yy = y
    for ln in lines:
        cv.draw_text(tx, yy, ln, 3, INK)
        yy += 25
    yy += 6
    for ln in cv.wrap(sub, 2, tw):
        cv.draw_text(tx, yy, ln, 2, INK)
        yy += 19


def main():
    cv = Canvas(W, H, PAPER)
    cv.rect_outline(14, 14, W - 28, H - 28, INK, 3)

    # Masthead
    cv.fill_rect(26, 26, W - 52, 92, INK)
    cv.draw_text_centered(44, "THE WORLD TODAY", 7, PAPER)

    # Date line with red rules
    cv.hline(36, 288, 146, RED, 3)
    cv.hline(736, 988, 146, RED, 3)
    cv.draw_text_centered(134, "FRIDAY, 20 NOVEMBER 2026", 3, INK)
    cv.hline(36, 988, 172, INK, 2)

    # ---- Lead story: Cyclone Akvan ----
    pic_cyclone(cv, 36, 190, 216)
    lx = 272
    cv.draw_text(lx, 194, "LANDFALL IN INDIA", 2, RED)
    cv.draw_text(lx, 226, "CYCLONE AKVAN", 4, INK)
    cv.draw_text(lx, 262, "SLAMS INTO ODISHA", 4, INK)
    yy = 312
    lead_sub = ("Winds of 100 km/h as the storm crosses the coast near "
                "Gopalpur. More than 100,000 people moved to safety. "
                "Red alert in 11 districts.")
    for ln in cv.wrap(lead_sub, 2, 988 - lx):
        cv.draw_text(lx, yy, ln, 2, INK)
        yy += 19
    cv.draw_text(lx, yy + 10, "IMD: LANDFALL AROUND NOON IST", 2, GREY)

    cv.hline(36, 988, 446, INK, 2)

    # ---- Grid: stories 2-5 ----
    story_cell(cv, 36, 462, 458, pic_globe,
               "TRUMP, XI AND PUTIN SIGN PEACE PACT",
               "First three-way summit in Shenzhen ends with a "
               "four-point 'Peace Declaration' on nuclear risk.")
    story_cell(cv, 530, 462, 458, pic_capitol,
               "SENATE REJECTS BID TO END IRAN WAR",
               "The 51-48 vote is the first Iran vote since the "
               "Nov. 3 midterms. The war has cost $48.3bn.")
    story_cell(cv, 36, 628, 458, pic_voyager,
               "VOYAGER 1 REACHES ONE LIGHT-DAY",
               "The probe is 16.1 billion miles out. A radio "
               "message now takes 24 hours to reach it.")
    story_cell(cv, 530, 628, 458, pic_scales,
               "SEOUL COURT VOIDS EX-PM'S TERM",
               "The court sends the 2024 martial-law case back "
               "for retrial. Yoon's wife keeps a 4-year term.")

    cv.hline(36, 988, 804, INK, 2)

    # ---- Story 6, full width ----
    pic_document(cv, 36, 820, 120)
    tx = 172
    cv.draw_text(tx, 828, "US AND VENEZUELA SIGN MILITARY DEAL", 3, INK)
    yy = 862
    sub6 = ("Hegseth signs the pact in Caracas: joint training and "
            "intelligence sharing, 10 months after Maduro was captured.")
    for ln in cv.wrap(sub6, 2, 988 - tx):
        cv.draw_text(tx, yy, ln, 2, INK)
        yy += 19

    # Footer
    cv.hline(36, 988, 962, INK, 2)
    cv.draw_text_centered(974, "Sources: IMD, Reuters, AP, USA Today, CNN, NASA", 2, GREY)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    with open(out, "wb") as f:
        f.write(png_bytes(cv))
    print("wrote", out)


if __name__ == "__main__":
    main()
