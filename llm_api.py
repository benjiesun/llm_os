#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_api.py
兼容 OpenAI / vLLM / 其他聚合服务的在线调用模式
"""
import requests
import os
from dotenv import load_dotenv
from utils.prompt_loader import load_system_prompt


# ========= 配置区域 =========
load_dotenv()
API_BASE = os.getenv("API_BASE", "https://api.deepseek.com/v1")          # 或 "http://127.0.0.1:8000/v1"
API_KEY  = os.getenv("API_KEY", "")                                     # 在本地用 .env 或系统环境变量设置
API_MODEL = os.getenv("API_MODEL", "deepseek-chat")                    # 模型名称，如 "deepseek-chat"
API_TIMEOUT = 60                                                     # 请求超时秒数

messages = []

def init_api_prompt(system_type: str = None):
    """加载系统提示词"""
    SYSTEM_PROMPT = load_system_prompt(system_type)
    return [{"role": "system", "content": SYSTEM_PROMPT}]

# ========= 核心函数 =========
def get_command_from_api(prompt: str,system_type: str = None, max_new_tokens=512, temperature=0.7) -> str:
    """
    调用兼容 OpenAI Chat Completions API 的远程模型。
    """
    global messages
    if not messages:
        messages = init_vllm_prompt(system_type)
    
    # 将用户输入加入上下文
    messages.append({"role": "user", "content": prompt})

    url = f"{API_BASE}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    payload = {
        "model": API_MODEL,
        "messages": messages,
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
