#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_vllm.py
兼容两种调用模式：
1) local_addr 指向 HTTP 推理服务 -> 以 HTTP 请求方式调用（兼容 /chat/completions 或 /generate）
2) local_addr 为空或不是 URL -> 在本地加载 HF 模型进行推理（延迟加载）
接口： get_command_from_llm(prompt, system_type, local_addr=None)
"""
import os
import re
import json
import requests

from utils.prompt_loader import load_system_prompt

# 本地 HF 模型相关（延迟加载）
_tokenizer = None
_model = None
_torch = None
_transformers = None
_model_path = os.getenv("LOCAL_MODEL_PATH", "/data/SharedFile/deepseek/DeepSeek-R1-Distill-Qwen-32B")
# 可通过 env 控制设备
os.environ.setdefault("CUDA_VISIBLE_DEVICES", os.getenv("CUDA_VISIBLE_DEVICES", "0,1"))
_DEVICE = None  # will set on load
_DEFAULT_HTTP_TIMEOUT = int(os.getenv("LOCAL_API_TIMEOUT", "60"))

def _is_http_addr(addr: str) -> bool:
    if not addr:
        return False
    return bool(re.match(r"^(https?://|http://|unix://)", addr, flags=re.I))

def _call_remote_inference_http(addr: str, full_prompt: str, max_new_tokens=256, temperature=0.6, timeout=_DEFAULT_HTTP_TIMEOUT):
    """
    调用本地/远程 HTTP 推理服务，自动尝试常见路径：
    - {addr}/chat/completions  (OpenAI-style)
    - {addr}/v1/chat/completions
    - {addr}/generate
    返回字符串或抛出异常。
    """
    addr = addr.rstrip("/")
    candidates = [
        f"{addr}/chat/completions",
        f"{addr}/v1/chat/completions",
        f"{addr}/generate",
        f"{addr}/v1/generate"
    ]

    payload_chat = {
        "model": os.getenv("LOCAL_API_MODEL", ""),
        "messages": [
            {"role": "system", "content": ""},
            {"role": "user", "content": full_prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_new_tokens,
        "stream": False
    }
    # fill system prompt into messages[0] externally by caller if needed

    for url in candidates:
        try:
            # construct a permissive JSON payload; different servers will ignore unknown fields
            data = {
                "model": os.getenv("LOCAL_API_MODEL", ""),
                "messages": [
                    {"role": "system", "content": ""},
                    {"role": "user", "content": full_prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_new_tokens
            }
            resp = requests.post(url, json=data, timeout=timeout)
            if resp.status_code >= 200 and resp.status_code < 300:
                try:
                    j = resp.json()
                    # try extract like OpenAI
                    if "choices" in j and len(j["choices"]) > 0:
                        ch0 = j["choices"][0]
                        if isinstance(ch0, dict) and "message" in ch0 and "content" in ch0["message"]:
                            return ch0["message"]["content"].strip()
                        if "text" in ch0:
                            return ch0["text"].strip()
                    # fallback to other fields
                    if "result" in j and isinstance(j["result"], str):
                        return j["result"].strip()
                    # last resort: response text
                    return resp.text.strip()
                except Exception:
                    return resp.text.strip()
            # else try next candidate
        except Exception:
            # try next candidate
            continue
    raise RuntimeError("无法通过 HTTP 地址调用到推理接口（尝试过常见路径但都失败）")

def _ensure_local_model_loaded():
    """
    延迟加载 HF 模型（只有在需要 CPU/GPU 本地推理时才加载）
    """
    global _tokenizer, _model, _torch, _transformers, _DEVICE
    if _model is not None and _tokenizer is not None:
        return

    try:
        import torch as _torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        _transformers = True
    except Exception as e:
        raise RuntimeError(f"本地模型推理所需依赖未安装：{e}")

    # 设备选择
    _DEVICE = "cuda" if _torch.cuda.is_available() else "cpu"

    # load tokenizer & model (trust_remote_code may be needed for some models)
    try:
        _tokenizer = AutoTokenizer.from_pretrained(_model_path, trust_remote_code=True)
        # use half precision if GPU available
        dtype = _torch.float16 if _DEVICE == "cuda" else _torch.float32
        _model = AutoModelForCausalLM.from_pretrained(
            _model_path,
            torch_dtype=dtype,
            device_map="auto" if _DEVICE == "cuda" else None,
            trust_remote_code=True
        )
        _model.eval()
    except Exception as e:
        raise RuntimeError(f"加载本地模型失败：{e}")

def _run_local_model_inference(full_prompt: str, max_new_tokens=256, temperature=0.6):
    """
    在已加载的本地模型上运行推理，返回文本
    """
    global _tokenizer, _model, _torch, _DEVICE
    _ensure_local_model_loaded()
    import torch
    inputs = _tokenizer(full_prompt, return_tensors="pt")
    # move tensors to device
    if _DEVICE == "cuda":
        inputs = {k: v.cuda() for k, v in inputs.items()}
    else:
        inputs = {k: v for k, v in inputs.items()}

    with torch.no_grad():
        outputs = _model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=0.9,
            do_sample=True,
            eos_token_id=_tokenizer.eos_token_id,
        )
    text = _tokenizer.decode(outputs[0], skip_special_tokens=True)
    # 只返回助手回答部分（按 prompt 中的分隔符）
    if "助手：" in text:
        return text.split("助手：", 1)[-1].strip()
    return text.strip()

def get_command_from_llm(prompt: str, system_type: str = None, local_addr: str = None, max_new_tokens: int = 256, temperature: float = 0.6) -> str:
    """
    统一接口：若 local_addr 是 HTTP 地址则走 HTTP 推理；否则使用本地 HF 模型（延迟加载）。
    返回：字符串生成结果或以 '❌' 开头的错误信息。
    """
    try:
        SYSTEM_PROMPT = load_system_prompt(system_type)
        full_prompt = f"{SYSTEM_PROMPT}\n用户：{prompt}\n助手："

        if local_addr and _is_http_addr(local_addr):
            # 调用本地/远程 HTTP 推理服务
            try:
                return _call_remote_inference_http(local_addr, full_prompt, max_new_tokens, temperature, timeout=_DEFAULT_HTTP_TIMEOUT)
            except Exception as e:
                return f"❌ 本地推理服务调用失败: {e}"

        # 否则走本地 HF 模型（延迟加载）
        try:
            return _run_local_model_inference(full_prompt, max_new_tokens, temperature)
        except Exception as e:
            return f"❌ 本地模型推理失败: {e}"

    except Exception as e:
        return f"❌ get_command_from_llm 异常: {e}"

if __name__ == "__main__":
    # 测试（如果你本地有模型会实际加载，谨慎运行）
    print(get_command_from_llm("列出当前目录并说明文件类型", "Linux", local_addr=None))