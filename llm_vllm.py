#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_vllm.py
言道 OS — 调用服务器上自建 vLLM 服务的模块
功能：
- 仅通过 HTTP 接口与服务器上的 llm_vllm_server.py 交互
- 接口格式兼容 OpenAI Chat Completions (/v1/chat/completions)
"""

import os
import requests
from dotenv import load_dotenv
from utils.prompt_loader import load_system_prompt

# ========= 加载环境变量 =========
load_dotenv()
LOCAL_ADDR = os.getenv("LOCAL_ADDR", "http://127.0.0.1:8000/v1")   # 默认本机端口，可由前端输入
LOCAL_TIMEOUT = int(os.getenv("LOCAL_TIMEOUT", "60"))


# ========= 核心函数 =========
def get_command_from_llm(prompt: str, system_type: str = None,
                         local_addr: str = None,
                         max_new_tokens: int = 512,
                         temperature: float = 0.7) -> str:
    """
    调用服务器上的 llm_vllm_server.py 服务。
    参数：
        prompt: 用户输入
        system_type: 系统类型（Linux/Windows/...）
        local_addr: API 地址，如 http://192.168.1.10:8000/v1
    返回：
        大模型的回复文本
    """
    addr = local_addr or LOCAL_ADDR
    base = addr.rstrip("/")
    url = f"{base}/chat/completions" if not base.endswith("/chat/completions") else base

    SYSTEM_PROMPT = load_system_prompt(system_type)
    headers = {"Content-Type": "application/json"}

    payload = {
        "model": "local-DeepSeek",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_new_tokens,
        "stream": False
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=LOCAL_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        # 尝试从响应中提取文本
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"].strip()
            elif "text" in choice:
                return choice["text"].strip()

        return str(data)
    except Exception as e:
        return f"❌ 本地 vLLM API 请求失败: {e}"


# ========= 测试调用 =========
if __name__ == "__main__":
    user_input = "列出当前目录下的所有文件"
    print("🧠 输入：", user_input)
    print("💬 输出：")
    print(get_command_from_llm(
        user_input,
        system_type="Linux",
        local_addr="http://192.168.1.10:8000/v1"   # 替换为你的服务器地址
    ))
