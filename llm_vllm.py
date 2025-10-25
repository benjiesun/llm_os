#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_vllm.py
言道 OS — 调用服务器上自建 vLLM 服务的模块
功能：
- 仅通过 HTTP 接口与服务器上的 llm_vllm_server.py 交互
- 支持短期上下文记忆（session-based chat）
"""

import os
import requests
from dotenv import load_dotenv
from utils.prompt_loader import load_system_prompt

# ========= 加载环境变量 =========
load_dotenv()
LOCAL_ADDR = os.getenv("LOCAL_ADDR", "http://127.0.0.1:8000/v1")   # 默认本机端口
LOCAL_TIMEOUT = int(os.getenv("LOCAL_TIMEOUT", "60"))

# ========= 全局会话缓存（用于上下文） =========
# 格式: { session_id: [ {"role": "system"/"user"/"assistant", "content": "..."}, ... ] }
CONTEXT_CACHE = {}

# ========= 核心函数 =========
def get_command_from_llm(prompt: str,
                         system_type: str = None,
                         local_addr: str = None,
                         session_id: str = "default",
                         max_new_tokens: int = 512,
                         temperature: float = 0.7,
                         keep_context: bool = True) -> str:
    """
    调用服务器上的 llm_vllm_server.py 服务。
    参数：
        prompt: 用户输入
        system_type: 系统类型（Linux/Windows/...）
        local_addr: API 地址
        session_id: 当前会话标识符
        keep_context: 是否保留上下文
    返回：
        大模型的回复文本
    """
    addr = local_addr or LOCAL_ADDR
    base = addr.rstrip("/")
    url = f"{base}/chat/completions" if not base.endswith("/chat/completions") else base

    # === 初始化上下文 ===
    if session_id not in CONTEXT_CACHE or not keep_context:
        SYSTEM_PROMPT = load_system_prompt(system_type)
        CONTEXT_CACHE[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # === 添加当前用户输入 ===
    CONTEXT_CACHE[session_id].append({"role": "user", "content": prompt})

    # === 发送请求 ===
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "local-DeepSeek",
        "messages": CONTEXT_CACHE[session_id],
        "temperature": temperature,
        "max_tokens": max_new_tokens,
        "stream": False
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=LOCAL_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                reply = choice["message"]["content"].strip()
            elif "text" in choice:
                reply = choice["text"].strip()
            else:
                reply = str(data)
        else:
            reply = str(data)

        # === 存入对话上下文 ===
        CONTEXT_CACHE[session_id].append({"role": "assistant", "content": reply})

        return reply

    except Exception as e:
        return f"❌ 本地 vLLM API 请求失败: {e}"


# ========= 辅助函数 =========
def clear_context(session_id: str = "default"):
    """清除指定会话的上下文"""
    if session_id in CONTEXT_CACHE:
        del CONTEXT_CACHE[session_id]


# ========= 测试调用 =========
if __name__ == "__main__":
    user_input1 = "列出当前目录下的所有文件"
    user_input2 = "再给我看看其中最大的文件"

    print("🧠 输入1:", user_input1)
    print("💬 输出1:", get_command_from_llm(user_input1, system_type="Linux", session_id="test2"))

    print("\n🧠 输入2:", user_input2)
    print("💬 输出2:", get_command_from_llm(user_input2, system_type="Linux", session_id="test2"))
