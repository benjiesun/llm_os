#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_agent.py
言道 OS — 自然语言命令解释模块（双卡版）
"""
import os
import re
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from utils.prompt_loader import load_system_prompt

# 设置可见 GPU（0 和 1）
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"

MODEL_PATH = "/data/SharedFile/Qwen/Qwen3-8B"

print(f"🚀 正在加载本地模型：{MODEL_PATH}")

device = "cuda" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float16,
    device_map="balanced",
    trust_remote_code=True
)
model.eval()

messages = []

def init_vllm_prompt(system_type: str = None):
    """加载系统提示词"""
    SYSTEM_PROMPT = load_system_prompt(system_type)
    return [{"role": "system", "content": SYSTEM_PROMPT}]

def get_command_from_llm(prompt: str, system_type: str = None) -> str:
    """调用本地模型，根据自然语言返回解释 + 命令"""
    global messages
    if not messages:
        messages = init_vllm_prompt(system_type)

    messages.append({"role": "user", "content": prompt})
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(text, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.6,
            top_p=0.9,
            do_sample=True,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id,
        )

    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    reply = re.sub(r"^.*?assistant", "", result, flags=re.DOTALL)
    reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL).strip()

    return reply
