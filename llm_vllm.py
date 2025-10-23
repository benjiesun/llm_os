#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_agent.py
言道 OS — 自然语言命令解释模块（双卡版）
"""
import platform
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import os

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

# 🔹 强化 Prompt 规范，让模型输出更可控
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

def get_command_from_llm(prompt: str) -> str:
    """
    调用本地 DeepSeek 模型，根据自然语言返回解释 + 命令。
    """
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
