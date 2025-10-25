#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prompt_loader.py
系统提示词加载器（根据系统类型动态加载 SYSTEM_PROMPT）。

功能说明：
- 自动根据系统类型（Windows / Linux / macOS）加载对应的 prompt 文件；
- 可显式传入 system_type（如来自远程 SSH 检测结果）；
- 若文件不存在，则使用默认提示。
import platform
import os
"""

def load_system_prompt(system_type: str = None) -> str:
    import os, platform

    if system_type is None:
        system_type = platform.system()

    prompt_dir = os.path.join(os.path.dirname(__file__), "prompts")

    sys_lower = system_type.lower()
    print("这个系统类型是:", sys_lower)
    if "windows" in sys_lower:
        prompt_file = os.path.join(prompt_dir, "system_windows.txt")
    elif "linux" in sys_lower:
        prompt_file = os.path.join(prompt_dir, "system_linux.txt")
    elif "darwin" in sys_lower or "unix" in sys_lower:
        prompt_file = os.path.join(prompt_dir, "system_Unix.txt")
    else:
        prompt_file = os.path.join(prompt_dir, "system_default.txt")

    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            # print("prompt_file:", prompt_file)
            return f.read().strip()
    except FileNotFoundError:
        return "你是一个自然语言操作助手。请输出相应的系统命令。"

