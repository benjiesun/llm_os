#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_api.py
兼容 OpenAI / 兼容型聚合服务的在线调用模式
支持被前端以 (prompt, system_type, api_base, api_key, api_model) 调用
支持短期上下文记忆（messages）
"""
import os
import requests
from dotenv import load_dotenv
from utils.prompt_loader import load_system_prompt

load_dotenv()

# 默认配置（可被前端覆盖）
API_BASE = os.getenv("API_BASE", "https://api.deepseek.com/v1")
API_KEY = os.getenv("API_KEY", "")
API_MODEL = os.getenv("API_MODEL", "deepseek-chat")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "60"))

# ========= 全局上下文消息缓存（短期记忆） =========
CONVERSATION_MEMORY = {}  # key = system_type, value = list[dict(role, content)]


def init_conversation(system_type: str):
    """初始化对话上下文"""
    SYSTEM_PROMPT = load_system_prompt(system_type)
    CONVERSATION_MEMORY[system_type] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return CONVERSATION_MEMORY[system_type]


def get_messages(system_type: str):
    """获取（或初始化）指定类型的上下文消息"""
    if system_type not in CONVERSATION_MEMORY:
        return init_conversation(system_type)
    return CONVERSATION_MEMORY[system_type]


def append_message(system_type: str, role: str, content: str):
    """将消息追加到上下文"""
    msgs = get_messages(system_type)
    msgs.append({"role": role, "content": content})
    # 限制上下文长度，避免消息爆炸（只保留最近 10 轮）
    if len(msgs) > 20:
        CONVERSATION_MEMORY[system_type] = msgs[:1] + msgs[-18:]


def clear_memory(system_type: str = None):
    """清空某一系统类型或全部记忆"""
    if system_type:
        CONVERSATION_MEMORY.pop(system_type, None)
    else:
        CONVERSATION_MEMORY.clear()


# ========= OpenAI 风格调用 =========
def _choose_url_and_payload(api_base: str, model: str, messages: list, max_new_tokens: int, temperature: float, api_key: str):
    """构造兼容 OpenAI Chat Completions 的 payload"""
    url = api_base.rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_new_tokens,
        "stream": False
    }
    return url, payload, headers


def _extract_text_from_response_json(data: dict) -> str:
    """兼容多种返回格式"""
    try:
        if "choices" in data and data["choices"]:
            ch0 = data["choices"][0]
            if isinstance(ch0, dict):
                if "message" in ch0 and "content" in ch0["message"]:
                    return ch0["message"]["content"].strip()
                if "text" in ch0:
                    return ch0["text"].strip()
        if "text" in data and isinstance(data["text"], str):
            return data["text"].strip()
    except Exception:
        pass
    return repr(data)


def get_command_from_api(prompt: str,
                         system_type: str = None,
                         api_base: str = None,
                         api_key: str = None,
                         api_model: str = None,
                         max_new_tokens: int = 512,
                         temperature: float = 0.7,
                         clear: bool = False) -> str:
    """
    调用远端 API（兼容 OpenAI-style chat completions），支持上下文记忆。
    """
    try:
        base = api_base or API_BASE
        key = api_key or API_KEY
        model = api_model or API_MODEL
        sys_type = system_type or "default"

        if not base:
            return "❌ 未配置 API_BASE（请在前端或 .env 中设置）"
        if not key:
            return "❌ 未配置 API_KEY（请在前端或 .env 中设置）"

        # 清空记忆（如果需要）
        if clear:
            clear_memory(sys_type)

        # 获取或初始化上下文
        messages = get_messages(sys_type)

        # 添加用户输入
        append_message(sys_type, "user", prompt)

        # 构造请求
        url, payload, headers = _choose_url_and_payload(base, model, messages, max_new_tokens, temperature, key)

        resp = requests.post(url, headers=headers, json=payload, timeout=API_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        text = _extract_text_from_response_json(data)

        # 保存模型回答
        append_message(sys_type, "assistant", text)
        return text
    except requests.exceptions.HTTPError as e:
        return f"❌ API HTTP 错误: {e} | 响应: {getattr(e.response, 'text', '')}"
    except Exception as e:
        return f"❌ API 请求失败: {e}"


# ========= 测试调用 =========
if __name__ == "__main__":
    print("🧠 第一次调用")
    print(get_command_from_api("列出当前目录下的文件", system_type="Linux"))
    print("\n🧠 第二次调用（带记忆）")
    print(get_command_from_api("再帮我解释一下这些文件的作用", system_type="Linux"))
