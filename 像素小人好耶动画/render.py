# -*- coding: utf-8 -*-
"""像素小人「敲键盘 -> 屏幕红转绿 -> 欢呼好耶」动画渲染器。
虚拟画布 320x180，4 倍最近邻放大到 1280x720（720p）。
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

VW, VH = 320, 180
SCALE = 4
FPS = 24
DURATION = 5.0
NFRAMES = int(FPS * DURATION)

# ---------------- 调色板 ----------------
BG        = (16, 19, 31)
BG_DEEP   = (10, 12, 22)
STAR      = (58, 68, 104)
FLOOR     = (24, 28, 44)
DESK_TOP  = (138, 111, 78)
DESK_LIP  = (104, 82, 56)
DESK_LEG  = (84, 66, 46)
CASE      = (189, 182, 164)
CASE_DK   = (58, 54, 48)
BEZEL     = (74, 71, 64)
STAND     = (162, 155, 138)
CHAIR     = (47, 47, 58)
CHAIR_DK  = (34, 34, 44)
HOODIE    = (74, 111, 165)
HOODIE_DK = (54, 84, 130)
SKIN      = (240, 200, 168)
SKIN_DK   = (204, 158, 126)
HAIR      = (58, 48, 42)
EYE       = (32, 30, 34)
MOUTH     = (150, 60, 60)
KEYBODY   = (216, 211, 198)
KEYBODY_D = (150, 145, 134)
KEY       = (110, 106, 98)
RED_SCR   = (58, 12, 16)
RED_HI    = (226, 59, 48)
GRN_SCR   = (10, 40, 20)
GRN_HI    = (61, 220, 106)
WHITE     = (245, 245, 240)
BUBBLE_BG = (250, 250, 246)
BUBBLE_FG = (30, 30, 36)

FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/Deng.ttf",
]


def load_font(size):
    for p in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


# ---------------- 基础绘制 ----------------
def rect(px, x, y, w, h, c):
    x0, y0 = int(round(x)), int(round(y))
    x1, y1 = x0 + int(round(w)), y0 + int(round(h))
    x0 = max(0, x0); y0 = max(0, y0)
    x1 = min(VW, x1); y1 = min(VH, y1)
    if x1 > x0 and y1 > y0:
        px[y0:y1, x0:x1] = c


def outline(px, x, y, w, h, c):
    rect(px, x, y, w, 1, c)
    rect(px, x, y + h - 1, w, 1, c)
    rect(px, x, y, 1, h, c)
    rect(px, x + w - 1, y, 1, h, c)


def disc(px, cx, cy, r, c):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                rect(px, cx + dx, cy + dy, 1, 1, c)


def line(px, p0, p1, c, t=1):
    (x0, y0), (x1, y1) = p0, p1
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(steps + 1):
        x = x0 + (x1 - x0) * i / steps
        y = y0 + (y1 - y0) * i / steps
        rect(px, x - t / 2, y - t / 2, t, t, c)


def tint(px, x, y, w, h, c, a):
    """在指定区域叠加半透明色光。"""
    x0, y0 = int(round(x)), int(round(y))
    x1, y1 = min(VW, x0 + int(round(w))), min(VH, y0 + int(round(h)))
    x0 = max(0, x0); y0 = max(0, y0)
    if x1 <= x0 or y1 <= y0:
        return
    sub = px[y0:y1, x0:x1].astype(float)
    px[y0:y1, x0:x1] = (sub * (1 - a) + np.array(c, dtype=float) * a).astype(np.uint8)


# ---------------- 静态背景 ----------------
rng = np.random.default_rng(7)
STARS = [(int(rng.integers(4, VW - 4)), int(rng.integers(4, 130)),
          int(rng.integers(0, 2))) for _ in range(90)]


def draw_background(px):
    px[:, :] = BG
    rect(px, 0, 140, VW, VH - 140, FLOOR)
    for sx, sy, k in STARS:
        rect(px, sx, sy, 1, 1, STAR if k else BG_DEEP)
    # 墙上贴的两张便利贴，增加生活感
    rect(px, 18, 34, 14, 12, (214, 190, 96))
    rect(px, 20, 38, 10, 1, (120, 104, 50))
    rect(px, 20, 42, 7, 1, (120, 104, 50))
    rect(px, 14, 54, 12, 10, (150, 190, 210))
    rect(px, 16, 58, 8, 1, (80, 110, 130))


def draw_desk(px):
    rect(px, 16, 118, VW - 32, 10, DESK_TOP)
    rect(px, 16, 128, VW - 32, 3, DESK_LIP)
    rect(px, 28, 131, 6, 40, DESK_LEG)
    rect(px, VW - 34, 131, 6, 40, DESK_LEG)
    rect(px, 16, 118, VW - 32, 1, (162, 133, 96))


def draw_monitor(px, scr_color, hi_color, mode):
    # 机箱
    rect(px, 176, 36, 110, 76, CASE)
    outline(px, 176, 36, 110, 76, CASE_DK)
    rect(px, 180, 40, 102, 68, BEZEL)
    # 屏幕
    sx, sy, sw, sh = 184, 44, 94, 60
    rect(px, sx, sy, sw, sh, scr_color)
    if mode == "red":
        for i in range(6):
            rect(px, sx + 8, sy + 8 + i * 8, int(sw * (0.7 - 0.07 * i)), 3, (150, 40, 36))
        # 大红叉
        line(px, (sx + 34, sy + 26), (sx + 60, sy + 50), RED_HI, 4)
        line(px, (sx + 60, sy + 26), (sx + 34, sy + 50), RED_HI, 4)
        rect(px, sx + 6, sy + sh - 12, sw - 12, 3, (120, 30, 28))
    else:
        for i in range(6):
            rect(px, sx + 8, sy + 8 + i * 8, int(sw * (0.45 + 0.09 * i)), 3, (30, 120, 56))
        # 大绿勾
        line(px, (sx + 34, sy + 42), (sx + 46, sy + 54), GRN_HI, 4)
        line(px, (sx + 46, sy + 54), (sx + 64, sy + 30), GRN_HI, 4)
        rect(px, sx + 6, sy + sh - 12, sw - 12, 3, (36, 150, 70))
    # 扫描线
    for yy in range(sy, sy + sh, 2):
        tint(px, sx, yy, sw, 1, (0, 0, 0), 0.18)
    # 支架
    rect(px, 222, 112, 18, 6, STAND)
    rect(px, 210, 117, 42, 4, STAND)


def draw_keyboard(px):
    rect(px, 156, 126, 88, 9, KEYBODY)
    rect(px, 156, 133, 88, 2, KEYBODY_D)
    outline(px, 156, 126, 88, 9, (90, 86, 80))
    for i in range(11):
        rect(px, 159 + i * 8, 128, 6, 5, KEY)


# ---------------- 人物 ----------------
def draw_person(px, dy, arms, head_bob, mouth_open, eyes_happy):
    """arms: 'type' | 'up' | 'mid' ; dy: 整体上下偏移"""
    y = lambda v: v + dy

    # 椅子
    rect(px, 62, y(96), 56, 44, CHAIR)
    rect(px, 62, y(96), 56, 3, CHAIR_DK)
    rect(px, 66, y(140), 6, 22, CHAIR_DK)
    rect(px, 108, y(140), 6, 22, CHAIR_DK)

    # 躯干
    rect(px, 70, y(84), 40, 36, HOODIE)
    rect(px, 70, y(84), 40, 3, HOODIE_DK)
    rect(px, 84, y(88), 12, 12, (200, 208, 220))   # 衣服上的图案块
    rect(px, 70, y(116), 40, 4, HOODIE_DK)

    # 脖子 & 头
    rect(px, 84, y(78), 12, 7, SKIN_DK)
    hx, hy = 74, y(52) + head_bob
    rect(px, hx, hy, 28, 27, SKIN)
    outline(px, hx, hy, 28, 27, (196, 152, 122))
    # 头发
    rect(px, hx - 1, hy - 2, 30, 11, HAIR)
    rect(px, hx - 1, hy + 8, 4, 9, HAIR)
    rect(px, hx + 27, hy + 8, 4, 9, HAIR)

    # 眼睛
    if eyes_happy:
        line(px, (hx + 7, hy + 17), (hx + 11, hy + 14), EYE, 2)
        line(px, (hx + 11, hy + 14), (hx + 15, hy + 17), EYE, 2)
        line(px, (hx + 17, hy + 17), (hx + 21, hy + 14), EYE, 2)
        line(px, (hx + 21, hy + 14), (hx + 25, hy + 17), EYE, 2)
    else:
        rect(px, hx + 7, hy + 15, 4, 5, EYE)
        rect(px, hx + 19, hy + 15, 4, 5, EYE)

    # 嘴
    if mouth_open:
        rect(px, hx + 10, hy + 21, 9, 6, MOUTH)
        rect(px, hx + 11, hy + 22, 7, 3, (240, 130, 130))
    else:
        rect(px, hx + 12, hy + 22, 6, 1, MOUTH)

    # 手臂
    if arms == "type":
        for sh_off, hx2, hy2 in ((76, 162, 128), (104, 190, 130)):
            line(px, (sh_off, y(90)), (sh_off + 26, y(118)), HOODIE, 7)
            line(px, (sh_off + 26, y(118)), (hx2, hy2), HOODIE, 6)
            rect(px, hx2 - 3, hy2 - 2, 7, 6, SKIN)
            rect(px, hx2 - 3, hy2 + 3, 7, 2, SKIN_DK)
    elif arms == "mid":
        for sh_off, hx2, hy2 in ((76, 150, 118), (104, 168, 120)):
            line(px, (sh_off, y(90)), (sh_off + 24, y(112)), HOODIE, 7)
            line(px, (sh_off + 24, y(112)), (hx2, hy2), HOODIE, 6)
            rect(px, hx2 - 3, hy2 - 2, 7, 6, SKIN)
    else:  # up
        line(px, (76, y(92)), (58, y(74)), HOODIE, 7)
        line(px, (58, y(74)), (52, y(52)), HOODIE, 6)
        disc(px, 51, int(y(50)), 4, SKIN)
        line(px, (104, y(92)), (122, y(74)), HOODIE, 7)
        line(px, (122, y(74)), (128, y(52)), HOODIE, 6)
        disc(px, 129, int(y(50)), 4, SKIN)


# ---------------- 对话气泡 ----------------
_bubble_cache = {}


def make_bubble(text, size=26):
    key = (text, size)
    if key in _bubble_cache:
        return _bubble_cache[key]
    f = load_font(size)
    # 先在透明层上画字，再阈值化成纯色，保证放大后是硬边像素
    layer = Image.new("L", (200, 60), 0)
    d = ImageDraw.Draw(layer)
    d.text((100, 30), text, font=f, fill=255, anchor="mm")
    m = np.asarray(layer)
    ys, xs = np.nonzero(m > 110)
    if len(xs) == 0:
        res = (np.zeros((26, 60), bool), 60, 26)
        _bubble_cache[key] = res
        return res
    crop = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1] > 110
    _bubble_cache[key] = (crop, crop.shape[1], crop.shape[0])
    return _bubble_cache[key]


def draw_bubble(px, text, cx, cy, pop=1.0):
    mask, tw, th = make_bubble(text)
    bw, bh = tw + 18, th + 14
    bw = int(bw * pop); bh = int(bh * pop)
    x0, y0 = int(cx - bw / 2), int(cy - bh / 2)
    # 圆角白底
    rect(px, x0 + 3, y0, bw - 6, bh, BUBBLE_BG)
    rect(px, x0, y0 + 3, bw, bh - 6, BUBBLE_BG)
    rect(px, x0 + 2, y0 + 1, bw - 4, 2, BUBBLE_BG)
    rect(px, x0 + 2, y0 + bh - 3, bw - 4, 2, BUBBLE_BG)
    rect(px, x0 + 1, y0 + 2, 2, bh - 4, BUBBLE_BG)
    rect(px, x0 + bw - 3, y0 + 2, 2, bh - 4, BUBBLE_BG)
    # 描边
    outline(px, x0 + 2, y0, bw - 4, 1, BUBBLE_FG)
    outline(px, x0 + 2, y0 + bh - 1, bw - 4, 1, BUBBLE_FG)
    outline(px, x0, y0 + 2, 1, bh - 4, BUBBLE_FG)
    outline(px, x0 + bw - 1, y0 + 2, 1, bh - 4, BUBBLE_FG)
    rect(px, x0 + 2, y0 + 1, 1, 1, BUBBLE_FG)
    rect(px, x0 + bw - 3, y0 + 1, 1, 1, BUBBLE_FG)
    rect(px, x0 + 2, y0 + bh - 2, 1, 1, BUBBLE_FG)
    rect(px, x0 + bw - 3, y0 + bh - 2, 1, 1, BUBBLE_FG)
    # 小尾巴
    for i in range(7):
        rect(px, x0 + bw // 2 - 4 + i, y0 + bh - 1 + i, 8 - i, 1, BUBBLE_BG)
    rect(px, x0 + bw // 2 - 4, y0 + bh, 1, 6, BUBBLE_FG)
    # 文字
    sx = int(cx - tw / 2); sy = int(cy - th / 2)
    for j in range(mask.shape[0]):
        for i in range(mask.shape[1]):
            if mask[j, i]:
                rect(px, sx + i, sy + j, 1, 1, BUBBLE_FG)


# ---------------- 单帧合成 ----------------
def render_frame(f):
    t = f / NFRAMES
    px = np.zeros((VH, VW, 3), np.uint8)
    draw_background(px)

    green = t >= 0.44
    flash = 0.40 <= t < 0.46
    cheering = t >= 0.58

    # 人物动作
    if cheering:
        ph = (t - 0.58) / 0.42
        jump = abs(math.sin(ph * math.pi * 2.2)) * 7
        dy = -jump
        arms = "up"
        mouth = True
        happy = True
        bob = 0
    elif t >= 0.40:
        dy = -1 if (f // 3) % 2 else 0
        arms = "mid"
        mouth = False
        happy = False
        bob = 0
    else:
        dy = 0
        arms = "type"
        mouth = False
        happy = False
        bob = 1 if (f // 4) % 2 else 0

    draw_person(px, dy, arms, bob, mouth, happy)
    draw_desk(px)

    scr = GRN_SCR if green else RED_SCR
    hi = GRN_HI if green else RED_HI
    draw_monitor(px, scr, hi, "green" if green else "red")
    draw_keyboard(px)

    # 屏幕光晕（打在小人身上）
    glow_a = 0.10 if not green else 0.13
    if flash:
        glow_a = 0.22
    tint(px, 60, 40, 110, 90, hi, glow_a)
    # 屏幕外溢光
    tint(px, 168, 30, 126, 96, hi, 0.07)

    if flash:
        tint(px, 0, 0, VW, VH, (255, 255, 255), 0.12)

    # 欢呼粒子
    if cheering:
        ph = (t - 0.58) / 0.42
        for i in range(16):
            a = (i / 16) * math.tau + ph * 1.6
            rr = 26 + 16 * math.sin(ph * math.pi + i)
            cx = 90 + math.cos(a) * rr * 1.5
            cy = 78 + math.sin(a) * rr * 0.8 - 12
            c = [(246, 214, 96), (GRN_HI), (WHITE), (120, 200, 246)][i % 4]
            rect(px, cx, cy, 2, 2, c)

    # 对话气泡
    if t >= 0.60:
        bt = (t - 0.60) / 0.10
        pop = 1.0 if bt >= 1 else (0.6 + 0.55 * bt - 0.15 * bt * bt)
        draw_bubble(px, "好耶！", 88, 26, pop)

    # 轻微暗角
    for i in range(14):
        a = 0.05 * (1 - i / 14)
        outline(px, i, i, VW - 2 * i, VH - 2 * i, (0, 0, 0))
        px[i, i:VW - i] = (px[i, i:VW - i].astype(float) * (1 - a)).astype(np.uint8)

    img = Image.fromarray(px).resize((VW * SCALE, VH * SCALE), Image.NEAREST)
    return np.asarray(img)


def main():
    import imageio_ffmpeg
    out = r"D:/y'world/像素小人好耶动画/好耶_720p_silent.mp4"
    w = imageio_ffmpeg.write_frames(
        out, (VW * SCALE, VH * SCALE), fps=FPS, codec="libx264",
        quality=6, macro_block_size=1,
        output_params=["-pix_fmt", "yuv420p", "-crf", "16"],
    )
    w.send(None)  # 启动生成器
    for f in range(NFRAMES):
        w.send(render_frame(f))
        if f % 24 == 0:
            print("frame", f, flush=True)
    w.close()
    print("OK ->", out)


if __name__ == "__main__":
    main()
