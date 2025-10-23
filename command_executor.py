#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
executor.py
安全命令执行器（带黑名单与基本注入检测）。
"""

import subprocess
import shlex

# 黑名单关键字（包含一些常见危险形式）
DANGEROUS_KEYWORDS = [
    "rm ", "rm -", "reboot", "shutdown", "init 0",
    "mkfs", "dd ", ":(){:|:&};:", "mv /", "chmod 777 /",
    "chown root", "userdel", "poweroff", "halt", "shutdown -h"
]

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
    """安全执行命令并返回执行结果字符串"""
    if not is_safe_command(command):
        return f"⚠️ 检测到危险或不安全的命令：{command}\n已阻止执行。"

    try:
        # shlex.split 会把命令拆为列表（不经过 shell），降低注入风险
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
    except Exception as e:
        return f"❌ 命令执行失败：{e}"
