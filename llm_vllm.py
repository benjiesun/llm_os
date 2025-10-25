#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_vllm.py
言道 OS — 自然语言命令解释模块（双卡版）
"""
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
from utils.prompt_loader import load_system_prompt


# ✅ 设置可见 GPU（0 和 1）
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"

MODEL_PATH = "/data/SharedFile/deepseek/DeepSeek-R1-Distill-Qwen-32B"

print(f"🚀 正在加载本地模型：{MODEL_PATH}")

# 自动检测 CUDA
device = "cuda" if torch.cuda.is_available() else "cpu"

# 初始化分词器和模型
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float16,
    device_map="balanced",   # ✅ 让模型自动平衡分布到两张 GPU
    trust_remote_code=True
)

model.eval()

def get_command_from_llm(prompt: str,system_type: str = None,) -> str:
    """
    调用本地 DeepSeek 模型，根据自然语言返回解释 + 命令。
    """

    # 根据系统类型加载prompt
    SYSTEM_PROMPT = load_system_prompt(system_type)

    full_prompt = f"{SYSTEM_PROMPT}\n用户：{prompt}\n助手："
    inputs = tokenizer(full_prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.6,
            top_p=0.9,
            do_sample=True,
            eos_token_id=tokenizer.eos_token_id,
        )

    result = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # 提取助手回答部分
    if "助手：" in result:
        result = result.split("助手：", 1)[-1].strip()
    return result
