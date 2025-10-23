#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_api.py
兼容 OpenAI / vLLM / 其他聚合服务的在线调用模式
"""
import platform
import requests
import os
import json
from dotenv import load_dotenv

# ========= 配置区域 =========
load_dotenv()
API_BASE = os.getenv("API_BASE", "https://api.deepseek.com/v1")          # 或 "http://127.0.0.1:8000/v1"
API_KEY  = os.getenv("API_KEY", "")                                     # 在本地用 .env 或系统环境变量设置
API_MODEL = os.getenv("API_MODEL", "deepseek-chat")                    # 模型名称，如 "deepseek-chat"
API_TIMEOUT = 60                                                     # 请求超时秒数



# 检测当前系统
SYSTEM = platform.system()
# 根据系统动态调整提示
if SYSTEM == "Windows":
    SYSTEM_PROMPT = """你是一个自然语言操作系统助手，当前运行在 Windows 系统。

你的任务：
1. 理解用户的自然语言；
2. 输出你要执行的任务说明；
3. 最后给出可以直接执行的 Windows CMD 命令。

请严格按以下格式输出：
我将为你做：<简短任务说明>。
对应的命令是：
<命令>

不要输出多余的解释、上下文或代码。
"""
else:
    SYSTEM_PROMPT = """你是一个自然语言操作系统助手，当前运行在 Linux 系统。

你的任务：
1. 理解用户的自然语言；
2. 输出你要执行的任务说明；
3. 最后给出可以直接执行的 Linux 命令。

请严格按以下格式输出：
我将为你做：<简短任务说明>。
对应的命令是：
<命令>

不要输出多余的解释、上下文或代码。
"""

# ========= 核心函数 =========
def get_command_from_api(prompt: str, max_new_tokens=512, temperature=0.7) -> str:
    """
    调用兼容 OpenAI Chat Completions API 的远程模型。
    """
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    payload = {
        "model": API_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_new_tokens,
        "stream": False
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"❌ API 请求失败: {e}"

# ========= 测试调用 =========
if __name__ == "__main__":
    user_input = "查看当前目录下的所有文件"
    print("🧠 输入：", user_input)
    print("💬 输出：")
    print(get_command_from_api(user_input))
