"""对若干候选特征色做密度分布图，定位人物脸部/手部与显示器屏幕。"""
import sys
from PIL import Image
import numpy as np

path = sys.argv[1] if len(sys.argv) > 1 else r"C:/Users/24426/Downloads/像素小人坐在电脑前.png"
im = Image.open(path).convert("RGB")
a = np.asarray(im).astype(int)
H, W, _ = a.shape
r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]

defs = {
    "SKIN  肤色(亮、R>G>B, R-B 20~50)": (r > 170) & (r > g + 8) & (g >= b) & ((r - b) > 18) & ((r - b) < 60),
    "DARK-BLUE 屏幕蓝(暗、B>R)": (b > r + 18) & (b > g + 8) & (b < 150),
    "PURE-BRIGHT 高亮白": (r > 230) & (g > 230) & (b > 230),
    "MID-GRAY 中灰": (abs(r - g) < 12) & (abs(g - b) < 12) & (r > 90) & (r < 170),
}

CW, CH = 72, 46
for name, mask in defs.items():
    print("\n=== %s  共 %d px (%.1f%%) ===" % (name, mask.sum(), mask.sum() / (W * H) * 100))
    m = mask.astype(float)
    ch, cw = H // CH, W // CW
    grid = m[:CH * ch, :CW * cw].reshape(CH, ch, CW, cw).sum(axis=(1, 3))
    mx = grid.max() if grid.max() > 0 else 1
    for row in grid:
        print("".join("0123456789"[min(9, int(v / mx * 9.99))] for v in row))

# 屏幕候选：找最大面积的连通暗蓝/暗色矩形近似
m = defs["DARK-BLUE 屏幕蓝(暗、B>R)"]
ys, xs = np.nonzero(m)
if len(xs):
    print("\n暗蓝像素 bbox: x %d~%d, y %d~%d  重心 (%d,%d)" %
          (xs.min(), xs.max(), ys.min(), ys.max(), int(xs.mean()), int(ys.mean())))
    # 每行/每列的分布，找主聚集区
    hist_x = np.bincount(xs // 48, minlength=W // 48 + 1)
    hist_y = np.bincount(ys // 48, minlength=H // 48 + 1)
    print("列分布(每48px):", " ".join(str(v) for v in hist_x))
    print("行分布(每48px):", " ".join(str(v) for v in hist_y))
