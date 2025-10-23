#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
voice_input.py
语音转文字模块（本地识别版）
"""

import speech_recognition as sr

def record_once():
    """录制一次语音并识别为文字"""
    r = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("🎙️ 请开始说话（按 Ctrl+C 退出）...")
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
        print("🧠 正在识别...")

    try:
        text = r.recognize_google(audio, language="zh-CN")
        print(f"💬 识别结果：{text}")
        return text
    except sr.UnknownValueError:
        print("😕 无法识别语音")
    except sr.RequestError:
        print("❌ 网络错误（Google 语音服务无法访问）")
    return ""
