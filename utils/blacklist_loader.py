#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
blacklist_loader.py
从配置文件加载危险命令关键字列表，按系统类型选择并合并默认项。
文件格式：每行一个关键字（或短语），支持以 # 注释。
"""

import os
import platform
from typing import List, Set

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "dangerous_keys")
WINDOWS_FILE = "blacklist_windows.txt"
LINUX_FILE = "blacklist_linux.txt"
DEFAULT_FILE = "blacklist_default.txt"

def _read_lines(filepath: str) -> List[str]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = []
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                lines.append(line)
            return lines
    except FileNotFoundError:
        return []

def load_blacklist(system_type: str = None, include_default: bool = True) -> List[str]:
    """
    加载黑名单关键字（按系统类型）。
    - system_type: "Windows"/"Linux"/"Darwin"/None；None 表示自动检测本地系统
    - include_default: 是否同时合并 default 文件中的关键字
    返回按插入顺序去重后的列表（lowercased）。
    """
    if system_type is None:
        system_type = platform.system()

    sys_lower = system_type.lower()
    files = []
    if "windows" in sys_lower:
        files.append(WINDOWS_FILE)
    elif "linux" in sys_lower:
        files.append(LINUX_FILE)
    elif "darwin" in sys_lower or "mac" in sys_lower:
        # macOS 按 linux 处理，也可以另建文件
        files.append(LINUX_FILE)
    else:
        # 未知系统时仅加载 default（或加载 linux 作为保守策略）
        files.append(DEFAULT_FILE)

    if include_default:
        files.append(DEFAULT_FILE)

    seen: Set[str] = set()
    result: List[str] = []
    for fname in files:
        path = os.path.join(CONFIG_DIR, fname)
        #print("🔒 Loading blacklist from:", path)
        for kw in _read_lines(path):
            kw_lower = kw.lower()
            if kw_lower not in seen:
                seen.add(kw_lower)
                result.append(kw_lower)
    return result

# 辅助判断函数（直接可用）
def is_dangerous_by_blacklist(command: str, system_type: str = None) -> bool:
    cmd = command.lower()
    for kw in load_blacklist(system_type):
        if kw in cmd:
            return True
    return False

# 可选：缓存版本以减少每次 IO（若你在长期运行程序中频繁调用）
_global_cache = {}
def load_blacklist_cached(system_type: str = None, reload: bool = False) -> List[str]:
    key = (system_type or platform.system(), )
    if reload or key not in _global_cache:
        _global_cache[key] = load_blacklist(system_type)
    return _global_cache[key]
