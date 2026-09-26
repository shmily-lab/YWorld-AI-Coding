# -*- coding: utf-8 -*-
"""生成音轨：敲键盘声 + 成功提示音 + 欢呼音效（如有 TTS 人声则混入）。"""
import os
import subprocess
import numpy as np
import wave

SR = 44100
DUR = 5.0
n = int(SR * DUR)
audio = np.zeros(n, dtype=np.float64)


def add(buf, start, sig):
    i = int(start * SR)
    j = min(len(buf), i + len(sig))
    if i < len(buf):
        buf[i:j] += sig[: j - i]


def env(n_samples, attack=0.002, decay=0.06):
    t = np.arange(n_samples) / SR
    a = np.clip(t / attack, 0, 1)
    d = np.exp(-t / decay)
    return a * d


# ---- 1. 敲键盘：0~2s，每 ~0.13s 一次清脆敲击 ----
rng = np.random.default_rng(3)
tt = 0.05
while tt < 2.0:
    L = int(0.03 * SR)
    click = rng.normal(0, 1, L) * env(L, 0.001, 0.008)
    click *= 0.35 * (0.7 + 0.3 * rng.random())
    # 加一点低频"哒"感
    tone = np.sin(2 * np.pi * (1600 + 400 * rng.random()) * np.arange(L) / SR)
    click += tone * env(L, 0.001, 0.006) * 0.18
    add(audio, tt, click)
    tt += 0.10 + 0.06 * rng.random()

# ---- 2. 成功提示音：t=2.0 屏幕转绿 ----
for k, (freq, delay, amp) in enumerate([(523.25, 0.00, 0.30),
                                        (659.25, 0.09, 0.28),
                                        (783.99, 0.18, 0.30),
                                        (1046.5, 0.30, 0.22)]):
    L = int(0.5 * SR)
    t = np.arange(L) / SR
    s = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t))
    s *= np.exp(-t / 0.22) * amp
    s *= np.clip(t / 0.005, 0, 1)
    add(audio, 2.0 + delay, s)

# ---- 3. 欢呼音效：t=2.95 起，星光叮咚 ----
for k, (freq, delay) in enumerate([(1318.5, 0.00), (1567.9, 0.07),
                                   (2093.0, 0.14), (1567.9, 0.22)]):
    L = int(0.35 * SR)
    t = np.arange(L) / SR
    s = np.sin(2 * np.pi * freq * t) * np.exp(-t / 0.10) * 0.16
    s *= np.clip(t / 0.004, 0, 1)
    add(audio, 2.95 + delay, s)

# ---- 4. 混入人声（若有） ----
VOICE = r"D:/y'world/像素小人好耶动画/voice.wav"
if os.path.exists(VOICE) and os.path.getsize(VOICE) > 1000:
    with wave.open(VOICE, "rb") as wf:
        sr_v = wf.getframerate()
        ch = wf.getnchannels()
        raw = wf.readframes(wf.getnframes())
    v = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    if ch == 2:
        v = v.reshape(-1, 2).mean(axis=1)
    if sr_v != SR:
        idx = np.arange(int(len(v) * SR / sr_v)) * sr_v / SR
        v = np.interp(idx, np.arange(len(v)), v)
    add(audio, 3.05, v * 1.6)
    print("已混入人声:", VOICE, len(v) / sr_v, "秒")
else:
    print("未找到人声文件，仅输出音效轨")

# ---- 归一化 & 写 wav ----
peak = np.max(np.abs(audio))
if peak > 0:
    audio = audio / peak * 0.92
audio = np.clip(audio, -1, 1)
pcm = (audio * 32767).astype(np.int16)
out = r"D:/y'world/像素小人好耶动画/soundtrack.wav"
with wave.open(out, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(SR)
    wf.writeframes(pcm.tobytes())
print("音轨已生成:", out, DUR, "秒")

# ---- 合成到视频 ----
import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
VID_IN = r"D:/y'world/像素小人好耶动画/好耶_720p_silent.mp4"
VID_OUT = r"D:/y'world/像素小人好耶动画/好耶_720p.mp4"
cmd = [FFMPEG, "-y", "-i", VID_IN, "-i", out, "-c:v", "copy",
       "-c:a", "aac", "-b:a", "192k", "-shortest", VID_OUT]
r = subprocess.run(cmd, capture_output=True, text=True)
print("ffmpeg rc:", r.returncode)
if r.returncode != 0:
    print(r.stderr[-1200:])
else:
    print("成片:", VID_OUT)
