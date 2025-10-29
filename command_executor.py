#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
executor.py
安全命令执行器（带黑名单与基本注入检测）。
"""
import re
import subprocess
import shlex
import platform
from utils.blacklist_loader import load_blacklist

SYSTEM = platform.system()   # 'Windows', 'Linux', or 'Darwin'
# print(f"🖥️ 当前操作系统：{SYSTEM}")
DANGEROUS_KEYWORDS = load_blacklist(SYSTEM)
DANGEROUS_INJECTION_PATTERNS = [";", "&&", "||", "`", "$(", ">${", "> /dev", "2>&1"]
ALLOWED_PIPELINE_COMMANDS = {
    "df", "grep", "awk", "sed", "cut", "tr", "sort", "uniq", "wc", "head", "tail", "cat"
}
def _strip_quoted(s: str) -> str:
    return re.sub(r'(?s)(\"[^\"]*\"|\'[^\']*\')', '', s)
def _has_dangerous_tokens(s: str) -> bool:
    for pat in DANGEROUS_INJECTION_PATTERNS:
        if pat in s:
            return True
    return False
def _split_pipeline(command: str):
    parts, buf, q, esc = [], [], None, False
    for ch in command:
        if esc:
            buf.append(ch); esc = False; continue
        if ch == '\\':
            buf.append(ch); esc = True; continue
        if q:
            if ch == q:
                q = None
            buf.append(ch); continue
        if ch in ("'", '"'):
            q = ch; buf.append(ch); continue
        if ch == "|":
            parts.append("".join(buf).strip()); buf = []; continue
        buf.append(ch)
    parts.append("".join(buf).strip())
    return [p for p in parts if p]

def _is_safe_pipeline(command: str) -> bool:
    # 快速拒绝逻辑或（防与管道混用绕过）
    if "||" in command:
        return False
    segments = _split_pipeline(command)
    if len(segments) <= 1:
        return True
    for seg in segments:
        # 片段内仍禁止 ;、&&、反引号、子命令、重定向等
        if _has_dangerous_tokens(_strip_quoted(seg)):
            return False
        try:
            tokens = shlex.split(seg, posix=True)
        except Exception:
            return False
        if not tokens or tokens[0] not in ALLOWED_PIPELINE_COMMANDS:
            return False
    return True
def is_safe_command(command: str, system_type: str = None) -> bool:
    cmd_lower = command.lower()
    for kw in DANGEROUS_KEYWORDS:
        if kw in cmd_lower:
            return False
    if not command.strip():
        return False

    # 基础注入检查（不含单个管道）
    cmd_to_check = _strip_quoted(command)
    if _has_dangerous_tokens(cmd_to_check):
        return False

    # 对含管道的命令做白名单校验
    if "|" in command:
        return _is_safe_pipeline(command)

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