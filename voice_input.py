#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
voice_input.py
语音转文字模块（无 PyAudio 版，使用 sounddevice）
"""

import sounddevice as sd
import numpy as np
import speech_recognition as sr

def record_once(duration=5, samplerate=16000):
    """录制一次语音并识别为文字"""
    r = sr.Recognizer()

    print("🎙️ 请开始说话（默认录制 5 秒，可修改 duration 参数）...")
    audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    print("🧠 正在识别...")

    # 将 numpy 数组转换为 speech_recognition 可识别的格式
    audio_bytes = audio_data.tobytes()
    audio = sr.AudioData(audio_bytes, samplerate, 2)  # 2 字节 = 16 位精度

    try:
        text = r.recognize_google(audio, language="zh-CN")
        print(f"💬 识别结果：{text}")
        return text
    except sr.UnknownValueError:
        print("😕 无法识别语音")
    except sr.RequestError:
        print("❌ 网络错误（Google 语音服务无法访问）")
    return ""


if __name__ == "__main__":
    record_once()
