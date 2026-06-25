#!/usr/bin/env python3
"""Generate original open-friendly placeholder images for the local mirror."""

from __future__ import annotations

import hashlib
import math
import random
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PALETTES = [
    {
        "paper": (246, 244, 235),
        "ink": (18, 20, 21),
        "muted": (105, 113, 108),
        "line": (222, 218, 205),
        "lime": (192, 254, 4),
        "cyan": (20, 144, 211),
        "coral": (255, 105, 80),
        "gold": (242, 191, 65),
    },
    {
        "paper": (14, 16, 18),
        "ink": (239, 237, 226),
        "muted": (138, 144, 136),
        "line": (46, 50, 48),
        "lime": (185, 255, 0),
        "cyan": (84, 175, 231),
        "coral": (255, 120, 91),
        "gold": (249, 204, 76),
    },
    {
        "paper": (230, 236, 226),
        "ink": (27, 31, 31),
        "muted": (111, 119, 117),
        "line": (198, 205, 194),
        "lime": (178, 246, 43),
        "cyan": (24, 121, 178),
        "coral": (239, 84, 72),
        "gold": (231, 173, 56),
    },
]


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return (900, 900)
    return struct.unpack(">II", data[16:24])


def clamp(v: int) -> int:
    return 0 if v < 0 else 255 if v > 255 else v


def mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (
        round(a[0] * (1 - t) + b[0] * t),
        round(a[1] * (1 - t) + b[1] * t),
        round(a[2] * (1 - t) + b[2] * t),
    )


class Canvas:
    def __init__(self, w: int, h: int, palette: dict[str, tuple[int, int, int]], seed: int):
        self.w = w
        self.h = h
        self.p = palette
        self.rng = random.Random(seed)
        self.data = bytearray(w * h * 3)

    def set_px(self, x: int, y: int, color: tuple[int, int, int], alpha: float = 1.0) -> None:
        if x < 0 or y < 0 or x >= self.w or y >= self.h:
            return
        i = (y * self.w + x) * 3
        if alpha >= 1:
            self.data[i] = color[0]
            self.data[i + 1] = color[1]
            self.data[i + 2] = color[2]
        else:
            inv = 1 - alpha
            self.data[i] = clamp(round(self.data[i] * inv + color[0] * alpha))
            self.data[i + 1] = clamp(round(self.data[i + 1] * inv + color[1] * alpha))
            self.data[i + 2] = clamp(round(self.data[i + 2] * inv + color[2] * alpha))

    def gradient(self, a: tuple[int, int, int], b: tuple[int, int, int], c: tuple[int, int, int]) -> None:
        w1 = max(1, self.w - 1)
        h1 = max(1, self.h - 1)
        for y in range(self.h):
            ty = y / h1
            row_a = mix(a, b, ty)
            row_b = mix(a, c, ty)
            base = y * self.w * 3
            for x in range(self.w):
                tx = x / w1
                col = mix(row_a, row_b, tx * 0.72)
                j = base + x * 3
                self.data[j] = col[0]
                self.data[j + 1] = col[1]
                self.data[j + 2] = col[2]

    def rect(self, x: float, y: float, w: float, h: float, color: tuple[int, int, int], alpha: float = 1.0) -> None:
        x0, y0 = max(0, round(x)), max(0, round(y))
        x1, y1 = min(self.w, round(x + w)), min(self.h, round(y + h))
        if x1 <= x0 or y1 <= y0:
            return
        if alpha >= 1:
            for yy in range(y0, y1):
                start = (yy * self.w + x0) * 3
                for xx in range(x0, x1):
                    j = start + (xx - x0) * 3
                    self.data[j] = color[0]
                    self.data[j + 1] = color[1]
                    self.data[j + 2] = color[2]
        else:
            for yy in range(y0, y1):
                for xx in range(x0, x1):
                    self.set_px(xx, yy, color, alpha)

    def stroke_rect(self, x: float, y: float, w: float, h: float, color: tuple[int, int, int], t: int = 2, alpha: float = 1.0) -> None:
        self.rect(x, y, w, t, color, alpha)
        self.rect(x, y + h - t, w, t, color, alpha)
        self.rect(x, y, t, h, color, alpha)
        self.rect(x + w - t, y, t, h, color, alpha)

    def circle(self, cx: float, cy: float, r: float, color: tuple[int, int, int], alpha: float = 1.0) -> None:
        x0, x1 = round(cx - r), round(cx + r)
        y0, y1 = round(cy - r), round(cy + r)
        rr = r * r
        for y in range(y0, y1 + 1):
            dy = y - cy
            for x in range(x0, x1 + 1):
                dx = x - cx
                if dx * dx + dy * dy <= rr:
                    self.set_px(x, y, color, alpha)

    def line(self, x0: float, y0: float, x1: float, y1: float, color: tuple[int, int, int], width: int = 4, alpha: float = 1.0) -> None:
        dx = x1 - x0
        dy = y1 - y0
        steps = max(1, round(max(abs(dx), abs(dy))))
        half = max(1, width // 2)
        for i in range(steps + 1):
            t = i / steps
            x = round(x0 + dx * t)
            y = round(y0 + dy * t)
            self.rect(x - half, y - half, width, width, color, alpha)

    def shadow_panel(self, x: float, y: float, w: float, h: float, fill: tuple[int, int, int], line: tuple[int, int, int], alpha: float = 1.0) -> None:
        self.rect(x + w * 0.025, y + h * 0.035, w, h, self.p["ink"], 0.14)
        self.rect(x, y, w, h, fill, alpha)
        self.stroke_rect(x, y, w, h, line, max(2, round(min(self.w, self.h) * 0.004)), 0.9)

    def save(self, path: Path) -> None:
        raw = bytearray()
        row_len = self.w * 3
        for y in range(self.h):
            raw.append(0)
            raw.extend(self.data[y * row_len : (y + 1) * row_len])
        def chunk(kind: bytes, payload: bytes) -> bytes:
            return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        out = bytearray(b"\x89PNG\r\n\x1a\n")
        out += chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
        out += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
        out += chunk(b"IEND", b"")
        path.write_bytes(out)


def grid(c: Canvas, step: int, alpha: float = 0.16) -> None:
    for x in range(0, c.w, step):
        c.rect(x, 0, 1, c.h, c.p["line"], alpha)
    for y in range(0, c.h, step):
        c.rect(0, y, c.w, 1, c.p["line"], alpha)


def bars(c: Canvas, x: float, y: float, w: float, rows: int, color: tuple[int, int, int], alpha: float = 0.8) -> None:
    h = max(4, c.h * 0.012)
    gap = h * 1.35
    for i in range(rows):
        ww = w * (0.35 + 0.55 * ((i * 7) % 11) / 10)
        c.rect(x, y + i * gap, ww, h, color, alpha)


def scene_dashboard(c: Canvas) -> None:
    p = c.p
    c.gradient(mix(p["paper"], p["cyan"], 0.12), p["paper"], mix(p["paper"], p["coral"], 0.14))
    grid(c, max(26, c.w // 24), 0.12)
    pad = c.w * 0.07
    c.shadow_panel(pad, c.h * 0.12, c.w - pad * 2, c.h * 0.72, mix(p["paper"], p["ink"], 0.04), p["line"], 0.96)
    c.rect(pad, c.h * 0.12, c.w - pad * 2, c.h * 0.08, p["ink"], 0.92)
    for i, col in enumerate([p["coral"], p["gold"], p["lime"]]):
        c.circle(pad + c.w * (0.035 + i * 0.028), c.h * 0.16, c.w * 0.01, col)
    side = c.w * 0.16
    c.rect(pad, c.h * 0.20, side, c.h * 0.64, mix(p["ink"], p["paper"], 0.12), 0.95)
    for i in range(7):
        c.rect(pad + side * 0.18, c.h * (0.25 + i * 0.07), side * (0.42 + (i % 3) * 0.11), c.h * 0.012, p["ink"] if i == 0 else p["muted"], 0.55)
    main_x = pad + side + c.w * 0.04
    card_w = (c.w - pad * 2 - side - c.w * 0.09) / 3
    for i, col in enumerate([p["lime"], p["cyan"], p["coral"]]):
        x = main_x + i * (card_w + c.w * 0.018)
        c.rect(x, c.h * 0.25, card_w, c.h * 0.13, p["ink"], 0.88)
        c.rect(x + card_w * 0.08, c.h * 0.285, card_w * 0.52, c.h * 0.016, col, 0.95)
        c.rect(x + card_w * 0.08, c.h * 0.325, card_w * 0.72, c.h * 0.02, p["paper"], 0.75)
    chart_x, chart_y, chart_w, chart_h = main_x, c.h * 0.44, c.w - main_x - pad * 0.9, c.h * 0.28
    c.rect(chart_x, chart_y, chart_w, chart_h, p["paper"], 0.78)
    for i in range(6):
        y = chart_y + chart_h * (i + 1) / 7
        c.rect(chart_x, y, chart_w, 1, p["line"], 0.5)
    pts = []
    for i in range(9):
        x = chart_x + chart_w * i / 8
        y = chart_y + chart_h * (0.70 - 0.44 * math.sin(i * 0.62 + 0.3) * (0.4 + i / 14))
        pts.append((x, y))
    for a, b in zip(pts, pts[1:]):
        c.line(a[0], a[1], b[0], b[1], p["cyan"], max(4, c.w // 145), 0.9)
    for x, y in pts:
        c.circle(x, y, max(4, c.w * 0.008), p["lime"], 0.98)
    for i in range(5):
        c.rect(main_x, c.h * (0.755 + i * 0.036), chart_w * (0.82 - i * 0.08), c.h * 0.012, p["ink"], 0.28)


def scene_mobile(c: Canvas) -> None:
    p = c.p
    c.gradient(mix(p["paper"], p["gold"], 0.16), mix(p["paper"], p["cyan"], 0.08), mix(p["paper"], p["lime"], 0.13))
    grid(c, max(28, c.w // 20), 0.13)
    for i, offset in enumerate([-0.13, 0.17]):
        fw = c.w * 0.34
        fh = c.h * 0.70
        x = c.w * (0.5 + offset) - fw / 2
        y = c.h * (0.15 + i * 0.03)
        c.shadow_panel(x, y, fw, fh, p["ink"], p["line"], 0.98)
        c.rect(x + fw * 0.08, y + fh * 0.07, fw * 0.84, fh * 0.86, mix(p["paper"], p["cyan"], 0.06), 1)
        c.rect(x + fw * 0.18, y + fh * 0.105, fw * 0.38, fh * 0.018, p["ink"], 0.55)
        c.rect(x + fw * 0.12, y + fh * 0.18, fw * 0.76, fh * 0.17, p["lime" if i == 0 else "coral"], 0.95)
        c.rect(x + fw * 0.16, y + fh * 0.40, fw * 0.31, fh * 0.18, p["paper"], 0.9)
        c.rect(x + fw * 0.53, y + fh * 0.40, fw * 0.31, fh * 0.18, p["cyan"], 0.88)
        c.circle(x + fw * 0.31, y + fh * 0.49, fw * 0.055, p["ink"], 0.45)
        c.rect(x + fw * 0.16, y + fh * 0.64, fw * 0.68, fh * 0.035, p["ink"], 0.35)
        c.rect(x + fw * 0.16, y + fh * 0.70, fw * 0.48, fh * 0.026, p["ink"], 0.24)
    c.line(c.w * 0.12, c.h * 0.80, c.w * 0.88, c.h * 0.18, p["cyan"], max(5, c.w // 120), 0.42)
    c.line(c.w * 0.12, c.h * 0.22, c.w * 0.82, c.h * 0.86, p["lime"], max(5, c.w // 150), 0.55)


def scene_editor(c: Canvas) -> None:
    p = c.p
    c.gradient(p["ink"], mix(p["ink"], p["cyan"], 0.14), mix(p["ink"], p["coral"], 0.14))
    grid(c, max(32, c.w // 18), 0.18)
    x, y, w, h = c.w * 0.08, c.h * 0.12, c.w * 0.84, c.h * 0.70
    c.shadow_panel(x, y, w, h, mix(p["ink"], p["paper"], 0.08), p["line"], 0.96)
    c.rect(x, y, w, h * 0.10, p["paper"], 0.88)
    for i, col in enumerate([p["coral"], p["gold"], p["lime"]]):
        c.circle(x + w * (0.04 + i * 0.035), y + h * 0.05, w * 0.011, col)
    c.rect(x, y + h * 0.10, w * 0.28, h * 0.90, mix(p["ink"], p["paper"], 0.04), 0.94)
    bars(c, x + w * 0.05, y + h * 0.17, w * 0.17, 10, p["paper"], 0.46)
    code_x = x + w * 0.32
    for i in range(15):
        yy = y + h * (0.16 + i * 0.045)
        col = [p["lime"], p["cyan"], p["paper"], p["coral"]][i % 4]
        c.rect(code_x, yy, w * (0.20 + ((i * 5) % 8) * 0.045), h * 0.016, col, 0.72)
    c.rect(code_x, y + h * 0.74, w * 0.58, h * 0.17, p["paper"], 0.86)
    for i in range(5):
        c.rect(code_x + w * 0.04, y + h * (0.78 + i * 0.025), w * (0.18 + i * 0.055), h * 0.01, p["ink"], 0.45)
    c.circle(c.w * 0.77, c.h * 0.27, c.w * 0.055, p["lime"], 0.85)
    c.line(c.w * 0.70, c.h * 0.58, c.w * 0.88, c.h * 0.31, p["cyan"], max(4, c.w // 150), 0.8)


def scene_board(c: Canvas) -> None:
    p = c.p
    c.gradient(mix(p["paper"], p["coral"], 0.10), p["paper"], mix(p["paper"], p["cyan"], 0.12))
    grid(c, max(24, c.w // 26), 0.16)
    for i in range(4):
        x = c.w * (0.10 + i * 0.18)
        y = c.h * (0.15 + (i % 2) * 0.12)
        c.shadow_panel(x, y, c.w * 0.22, c.h * 0.33, p["paper"], p["line"], 0.92)
        c.rect(x + c.w * 0.025, y + c.h * 0.035, c.w * 0.17, c.h * 0.06, [p["lime"], p["cyan"], p["coral"], p["gold"]][i], 0.96)
        c.rect(x + c.w * 0.025, y + c.h * 0.13, c.w * 0.13, c.h * 0.018, p["ink"], 0.35)
        c.rect(x + c.w * 0.025, y + c.h * 0.18, c.w * 0.16, c.h * 0.018, p["ink"], 0.22)
    nodes = [(0.16, 0.72), (0.34, 0.62), (0.52, 0.74), (0.72, 0.57), (0.88, 0.69)]
    for a, b in zip(nodes, nodes[1:]):
        c.line(c.w * a[0], c.h * a[1], c.w * b[0], c.h * b[1], p["cyan"], max(4, c.w // 140), 0.7)
    for i, (nx, ny) in enumerate(nodes):
        c.circle(c.w * nx, c.h * ny, c.w * 0.022, [p["lime"], p["coral"], p["gold"], p["cyan"], p["ink"]][i], 0.95)


def scene_ops(c: Canvas) -> None:
    p = c.p
    c.gradient(mix(p["paper"], p["lime"], 0.10), mix(p["paper"], p["cyan"], 0.12), mix(p["paper"], p["gold"], 0.14))
    grid(c, max(30, c.w // 22), 0.12)
    c.circle(c.w * 0.52, c.h * 0.48, min(c.w, c.h) * 0.31, p["lime"], 0.14)
    c.circle(c.w * 0.52, c.h * 0.48, min(c.w, c.h) * 0.21, p["cyan"], 0.13)
    for i in range(10):
        x = c.w * (0.10 + (i * 0.087) % 0.78)
        y = c.h * (0.18 + ((i * 13) % 61) / 100)
        c.shadow_panel(x, y, c.w * (0.12 + (i % 3) * 0.035), c.h * 0.10, p["paper"], p["line"], 0.93)
        c.rect(x + c.w * 0.018, y + c.h * 0.025, c.w * (0.055 + (i % 4) * 0.012), c.h * 0.012, [p["lime"], p["cyan"], p["coral"], p["gold"]][i % 4], 0.9)
    for i in range(6):
        c.line(c.w * (0.12 + i * 0.12), c.h * 0.80, c.w * (0.22 + i * 0.11), c.h * 0.21, p["ink"], max(2, c.w // 230), 0.22)


def scene_stack(c: Canvas) -> None:
    p = c.p
    c.gradient(mix(p["paper"], p["cyan"], 0.10), mix(p["paper"], p["gold"], 0.12), p["paper"])
    grid(c, max(30, c.w // 20), 0.10)
    for i in range(5):
        x = c.w * (0.12 + i * 0.095)
        y = c.h * (0.18 + i * 0.055)
        w = c.w * 0.54
        h = c.h * 0.42
        c.shadow_panel(x, y, w, h, mix(p["paper"], [p["lime"], p["cyan"], p["coral"], p["gold"], p["paper"]][i], 0.14), p["line"], 0.95)
        c.rect(x + w * 0.08, y + h * 0.12, w * 0.42, h * 0.06, [p["lime"], p["cyan"], p["coral"], p["gold"], p["ink"]][i], 0.85)
        bars(c, x + w * 0.08, y + h * 0.26, w * 0.74, 4, p["ink"], 0.25)
    c.line(c.w * 0.08, c.h * 0.22, c.w * 0.90, c.h * 0.82, p["lime"], max(4, c.w // 130), 0.5)


def scene_symbol(c: Canvas) -> None:
    p = c.p
    c.gradient(p["paper"], mix(p["paper"], p["cyan"], 0.18), mix(p["paper"], p["lime"], 0.20))
    grid(c, max(24, c.w // 20), 0.12)
    cx, cy = c.w * 0.50, c.h * 0.50
    for i, col in enumerate([p["lime"], p["cyan"], p["coral"], p["gold"]]):
        r = min(c.w, c.h) * (0.12 + i * 0.075)
        c.line(cx - r, cy, cx, cy - r, col, max(7, c.w // 70), 0.72)
        c.line(cx, cy - r, cx + r, cy, col, max(7, c.w // 70), 0.72)
        c.line(cx + r, cy, cx, cy + r, col, max(7, c.w // 70), 0.72)
        c.line(cx, cy + r, cx - r, cy, col, max(7, c.w // 70), 0.72)
    c.circle(cx, cy, min(c.w, c.h) * 0.10, p["ink"], 0.85)
    c.circle(cx, cy, min(c.w, c.h) * 0.05, p["paper"], 1)


SCENES = [scene_dashboard, scene_mobile, scene_editor, scene_board, scene_ops, scene_stack]


def cap_size(path: Path, w: int, h: int) -> tuple[int, int]:
    if path.name == "apple-icon.png":
        return (512, 512)
    if path.parent.name == "sticker_img":
        cap = 520
    elif path.parent.name == "img":
        cap = 1024
    else:
        cap = 1100
    scale = min(1.0, cap / max(w, h))
    return (max(160, round(w * scale)), max(160, round(h * scale)))


def generate(path: Path, idx: int) -> None:
    old_w, old_h = png_size(path) if path.exists() else (900, 900)
    w, h = cap_size(path, old_w, old_h)
    seed = int(hashlib.sha1(path.as_posix().encode()).hexdigest()[:8], 16)
    palette = PALETTES[(seed + idx) % len(PALETTES)]
    c = Canvas(w, h, palette, seed)
    if path.name == "apple-icon.png":
        scene_symbol(c)
    elif path.parent.name == "img":
        scene_ops(c)
    elif path.parent.name == "sticker_img":
        scene_symbol(c) if idx % 3 == 0 else SCENES[(idx + 1) % len(SCENES)](c)
    else:
        SCENES[idx % len(SCENES)](c)
    path.parent.mkdir(parents=True, exist_ok=True)
    c.save(path)
    print(f"wrote {path.relative_to(ROOT)} {w}x{h}")


def main() -> None:
    targets: list[Path] = []
    for pattern in ("work/*.png", "img/*.png", "sticker_img/*.png"):
        targets.extend(sorted(ROOT.glob(pattern)))
    targets.append(ROOT / "apple-icon.png")
    for idx, path in enumerate(targets):
        generate(path, idx)


if __name__ == "__main__":
    main()
