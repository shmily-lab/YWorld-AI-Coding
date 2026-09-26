"""把图片拆成可读的字符网格，用于在无视觉输入的情况下判断构图。"""
import sys
from PIL import Image
import numpy as np

path = sys.argv[1] if len(sys.argv) > 1 else r"C:/Users/24426/Downloads/像素小人坐在电脑前.png"
im = Image.open(path).convert("RGB")
print("size:", im.size, "mode:", im.mode)

a = np.asarray(im).astype(int)
print("unique-ish colors (quantized):")
q = (a // 32 * 32)
flat = q.reshape(-1, 3)
# 统计
from collections import Counter
c = Counter(map(tuple, flat))
for col, n in c.most_common(12):
    print("   ", col, n)

# ---- 亮度 ASCII ----
W = 96
h = max(1, int(W * im.size[1] / im.size[0] * 0.5))
small = im.resize((W, h), Image.LANCZOS)
sa = np.asarray(small).astype(int)
lum = (0.299 * sa[:, :, 0] + 0.587 * sa[:, :, 1] + 0.114 * sa[:, :, 2])
chars = " .:-=+*#%@"
print("\n=== 亮度图 (ASCII) ===")
for row in lum:
    print("".join(chars[min(9, int(v / 256 * 10))] for v in row))

# ---- 颜色分类图 ----
def classify(p):
    r, g, b = p
    mx, mn = max(r, g, b), min(r, g, b)
    v = mx
    s = 0 if mx == 0 else (mx - mn) / mx
    if v < 45:
        return "K"          # 黑/深背景
    if s < 0.18:
        return "." if v < 100 else ("o" if v < 200 else "W")   # 灰阶
    if r > g + 40 and r > b + 40:
        return "R"          # 红
    if g > r + 30 and g > b + 20:
        return "N"          # 绿
    if b > r + 25 and b > g + 15:
        return "B"          # 蓝
    if r > 150 and g > 120 and b < 110:
        return "S"          # 肤色/橙黄
    if r > 130 and g > 130 and b < 100:
        return "Y"          # 黄
    if r > 110 and b > 110 and g < 110:
        return "P"          # 紫/品红
    if g > 120 and b > 120 and r < 130:
        return "C"          # 青
    return "?"

CW = 80
ch = max(1, int(CW * im.size[1] / im.size[0] * 0.5))
cs = np.asarray(im.resize((CW, ch), Image.NEAREST)).astype(int)
print("\n=== 颜色分类图 (K黑 .暗 o灰 W白 R红 N绿 B蓝 S肤 Y黄 P紫 C青) ===")
for row in cs:
    print("".join(classify(p) for p in row))
