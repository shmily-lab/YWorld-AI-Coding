# -*- coding: utf-8 -*-
"""用本机 SAPI(COM) 合成「好耶！」，挑中文音色。"""
import os
import comtypes.client as cc
from comtypes import CoInitialize

CoInitialize()
OUT = r"D:/y'world/像素小人好耶动画/voice.wav"

voice = cc.CreateObject("SAPI.SpVoice")
voices = voice.GetVoices()
print("可用音色数:", voices.Count)
picked = None
for i in range(voices.Count):
    v = voices.Item(i)
    desc = v.GetDescription()
    lang = v.GetAttribute("Language")
    print("  -", desc, "|", lang)
    if lang and str(lang).lower().startswith("804"):   # 804 = zh-CN
        picked = v
if picked is None:
    for i in range(voices.Count):
        v = voices.Item(i)
        if "Chinese" in v.GetDescription() or "Huihui" in v.GetDescription() \
           or "Yaoyao" in v.GetDescription() or "Xiaoxiao" in v.GetDescription():
            picked = v
            break

if picked is None:
    print("NO_CN_VOICE")
    raise SystemExit(1)

voice.Voice = picked
voice.Rate = 2
voice.Volume = 100
print("选用音色:", picked.GetDescription())

stream = cc.CreateObject("SAPI.SpFileStream")
stream.Open(OUT, 3, False)      # SSFMCreateForWrite
voice.AudioOutputStream = stream
voice.Speak("好耶！")
stream.Close()
print("saved:", OUT, os.path.getsize(OUT), "bytes")
