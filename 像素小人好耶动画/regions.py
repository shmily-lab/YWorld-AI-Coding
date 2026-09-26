"""定位主要色块的包围盒，用于判断屏幕/人物/键盘的位置。"""
import sys
from collections import Counter
from PIL import Image
import numpy as np

path = sys.argv[1] if len(sys.argv) > 1 else r"C:/Users/24426/Downloads/像素小人坐在电脑前.png"
im = Image.open(path).convert("RGB")
a = np.asarray(im).astype(int)
H, W, _ = a.shape
print("size:", W, "x", H)

q = (a // 24 * 24)
flat = q.reshape(-1, 3)
cnt = Counter(map(tuple, flat))
total = W * H

print("\n%-16s %8s %6s  %-28s %s" % ("color", "pixels", "share", "bbox(x0,y0,x1,y1)", "fill%"))
for col, n in cnt.most_common(18):
    if n / total < 0.002:
        break
    r, g, b = col
    mask = np.all(q == np.array([r, g, b]), axis=-1)
    ys, xs = np.nonzero(mask)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    fill = n / (bw * bh) * 100
    print("%-16s %8d %5.1f%%  (%4d,%4d,%4d,%4d) w=%4d h=%4d  %5.1f%%" %
          (str(col), n, n / total * 100, x0, y0, x1, y1, bw, bh, fill))

# 按九宫格统计平均色，帮助判断布局
print("\n=== 3x3 网格平均色 ===")
for gy in range(3):
    row = []
    for gx in range(3):
        sub = a[gy * H // 3:(gy + 1) * H // 3, gx * W // 3:(gx + 1) * W // 3]
        m = sub.reshape(-1, 3).mean(axis=0).astype(int)
        row.append("(%3d,%3d,%3d)" % tuple(m))
    print("  " + "  ".join(row))
