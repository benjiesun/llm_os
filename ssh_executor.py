#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ssh_executor.py
支持长连接、系统检测、远程命令复用。
"""

import paramiko
import os
from dotenv import load_dotenv

from utils.blacklist_loader import load_blacklist

load_dotenv()

SSH_HOST = os.getenv("SSH_HOST", "10.8.8.8")
SSH_PORT = int(os.getenv("SSH_PORT", "22"))
SSH_USER = os.getenv("SSH_USER", "zhangsan")
SSH_PASS = os.getenv("SSH_PASS", "")


_ssh_client = None        # 全局连接对象
_remote_system = "Unknown"  # 远程系统类型



# 防止多个命令串联执行（简单策略）
DANGEROUS_INJECTION_PATTERNS = [";", "&&", "||", "|", "`", "$(", ">${", "> /dev", "2>&1"]
def is_safe_command(command: str,system_type: str = None) -> bool:
    """判断命令是否安全（简单黑名单 + 注入符号检测）"""
    DANGEROUS_KEYWORDS = load_blacklist(system_type)
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

def connect_ssh(timeout=10):
    """建立 SSH 长连接（若已连接则复用）"""
    global _ssh_client, _remote_system
    if _ssh_client and _ssh_client.get_transport() and _ssh_client.get_transport().is_active():
        return _ssh_client, _remote_system

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASS, timeout=timeout)

    _remote_system = detect_remote_system(ssh)
    print(f"🌐 Connected to {SSH_HOST} ({_remote_system})")

    _ssh_client = ssh
    return ssh, _remote_system


def close_ssh():
    """关闭 SSH 连接"""
    global _ssh_client
    if _ssh_client:
        _ssh_client.close()
        _ssh_client = None
        print("🔌 SSH connection closed.")


def detect_remote_system(ssh_client):
    """检测远程系统类型"""
    try:
        stdin, stdout, _ = ssh_client.exec_command("uname", timeout=3)
        out = stdout.read().decode().strip().lower()
        if "linux" in out:
            return "Linux"
        elif "darwin" in out:
            return "macOS"

        stdin, stdout, _ = ssh_client.exec_command("ver", timeout=3)
        out = stdout.read().decode().strip().lower()
        if "windows" in out:
            return "Windows"
        return "Unknown"
    except Exception:
        return "Unknown"


def execute_remote_command(command,system_type: str = None, timeout=15):
    """在持久连接上执行命令"""

    if not is_safe_command(command,system_type):
        return f"⚠️ 检测到危险命令：{command}\n已阻止执行。"

    ssh, _ = connect_ssh()
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        out = stdout.read().decode("utf-8").strip()
        err = stderr.read().decode("utf-8").strip()
        if err:
            return f"❌ Remote error:\n{err}"
        return out or "✅ 命令执行成功，无输出。"
    except Exception as e:
        return f"❌ SSH 执行失败：{e}"
