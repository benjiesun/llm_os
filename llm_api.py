#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_api.py
兼容 OpenAI / 兼容型聚合服务的在线调用模式
支持被前端以 (prompt, system_type, api_base, api_key, api_model) 调用
"""
import os
import requests
from dotenv import load_dotenv
from utils.prompt_loader import load_system_prompt

load_dotenv()

# 默认配置（可被前端覆盖）
API_BASE = os.getenv("API_BASE", "https://api.openai.com/v1")
API_KEY = os.getenv("API_KEY", "")
API_MODEL = os.getenv("API_MODEL", "gpt-4o-mini")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "60"))

def _choose_url_and_payload(api_base: str, model: str, system_prompt: str, user_prompt: str, max_new_tokens: int, temperature: float):
    """
    返回 (url, json_payload, headers)
    尝试构造兼容 OpenAI Chat Completions 的 payload。
    """
    url = api_base.rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY or ''}",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_new_tokens,
        "stream": False
    }
    return url, payload, headers

def _extract_text_from_response_json(data: dict) -> str:
    """
    兼容多种返回格式，优先尝试 OpenAI Chat response schema，
    其次尝试 simpler 'choices[0].text'。
    """
    try:
        # Chat-like structure
        if "choices" in data and len(data["choices"]) > 0:
            ch0 = data["choices"][0]
            if isinstance(ch0, dict):
                # Chat completions style
                if "message" in ch0 and isinstance(ch0["message"], dict) and "content" in ch0["message"]:
                    return ch0["message"]["content"].strip()
                # Older style: choices[].text
                if "text" in ch0:
                    return ch0["text"].strip()
        # Fallbacks
        if "text" in data and isinstance(data["text"], str):
            return data["text"].strip()
    except Exception:
        pass
    # If nothing matched, return repr
    return repr(data)

def get_command_from_api(prompt: str,
                         system_type: str = None,
                         api_base: str = None,
                         api_key: str = None,
                         api_model: str = None,
                         max_new_tokens: int = 512,
                         temperature: float = 0.7) -> str:
    """
    调用远端 API（兼容 OpenAI-style chat completions）。
    前端可以传入 api_base/api_key/api_model 覆盖环境变量。
    返回：字符串（模型回答）或以 "❌" 开头的错误消息。
    """
    try:
        base = api_base or API_BASE
        key = api_key or API_KEY
        model = api_model or API_MODEL

        if not base:
            return "❌ 未配置 API_BASE（请在前端或 .env 中设置）"
        if not key:
            return "❌ 未配置 API_KEY（请在前端或 .env 中设置）"

        SYSTEM_PROMPT = load_system_prompt(system_type)
        url, payload, headers = _choose_url_and_payload(base, model, SYSTEM_PROMPT, prompt, max_new_tokens, temperature)
        # 使用传入的 key（覆盖 headers）
        headers["Authorization"] = f"Bearer {key}"

        resp = requests.post(url, headers=headers, json=payload, timeout=API_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        text = _extract_text_from_response_json(data)
        return text
    except requests.exceptions.HTTPError as e:
        return f"❌ API HTTP 错误: {e} | 响应: {getattr(e.response, 'text', '')}"
    except Exception as e:
        return f"❌ API 请求失败: {e}"

if __name__ == "__main__":
    # 简单测试（使用 .env 或传参）
    print(get_command_from_api("列出当前目录下的文件并给出解释", system_type="Linux"))
