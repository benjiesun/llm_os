#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
executor.py
安全命令执行器（带黑名单与基本注入检测）。
"""

import subprocess
import shlex
import platform
from utils.blacklist_loader import load_blacklist

SYSTEM = platform.system()   # 'Windows', 'Linux', or 'Darwin'
DANGEROUS_KEYWORDS = load_blacklist(SYSTEM)
# 防止多个命令串联执行（简单策略）
DANGEROUS_INJECTION_PATTERNS = [";", "&&", "||", "|", "`", "$(", ">${", "> /dev", "2>&1"]

def is_safe_command(command: str) -> bool:
    """判断命令是否安全（简单黑名单 + 注入符号检测）"""
    cmd_lower = command.lower()
    for kw in DANGEROUS_KEYWORDS:
        if kw in cmd_lower:
            return False
    for pat in DANGEROUS_INJECTION_PATTERNS:
        if pat in command:
            return False
    # 不允许空命令
    if not command.strip():
        return False
    return True


def execute_command(command: str, timeout: int = 15) -> str:
    """安全执行命令并返回执行结果字符串（最小改动版：遇到 WinError 2 时回退到 shell=True）"""
    if not is_safe_command(command):
        return f"⚠️ 检测到危险或不安全的命令：{command}\n已阻止执行。"

    try:
        # 尝试用非 shell 的方式执行（更安全）
        cmd_list = shlex.split(command)
        result = subprocess.run(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            out = result.stdout.strip()
            return out or "✅ 命令执行成功，无输出。"
        else:
            return f"❌ 命令执行出错（returncode={result.returncode}）：\n{result.stderr.strip()}"
    except FileNotFoundError:
        # Windows 常见：内建命令（如 dir）不是可执行文件，会抛 FileNotFoundError
        # 在确认已通过 is_safe_command 后，回退一次使用 shell=True（谨慎回退）
        try:
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            if result.returncode == 0:
                out = result.stdout.strip()
                return out or "✅ 命令执行成功（shell 模式），无输出。"
            else:
                return f"❌ Shell 执行出错（returncode={result.returncode}）：\n{result.stderr.strip()}"
        except Exception as e:
            return f"❌ 回退到 shell 模式执行失败：{e}"
    except Exception as e:
        return f"❌ 命令执行失败：{e}"

