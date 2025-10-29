# ssh_executor.py
import paramiko
import socket
import os
import shlex
from dotenv import load_dotenv
import re

from utils.blacklist_loader import load_blacklist

load_dotenv()

# 默认来自 .env（可被 connect_ssh 的参数覆盖）
SSH_HOST = os.getenv("SSH_HOST", "10.8.8.8")
SSH_PORT = int(os.getenv("SSH_PORT", "22"))
SSH_USER = os.getenv("SSH_USER", "zhangsan")
SSH_PASS = os.getenv("SSH_PASS", "")

_ssh_client = None
_remote_system = "Unknown"

# 防止多个命令串联执行（简单策略）
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
    DANGEROUS_KEYWORDS = load_blacklist(system_type)
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

def _close_existing_if_diff(host, port, username):
    """
    如果已有连接但目标不同，关闭旧连接以便建立新连接。
    """
    global _ssh_client
    try:
        if _ssh_client and _ssh_client.get_transport() and _ssh_client.get_transport().is_active():
            # 试图从 transport 获取远程地址信息（部分实现可能缺失）
            # 为简单判断仅比较用户名/host/port存储到 client 的一个属性 (we store attributes on client)
            existing = getattr(_ssh_client, "_connection_info", None)
            if existing:
                old_host, old_port, old_user = existing
                if (old_host, int(old_port), old_user) != (host, int(port), username):
                    try:
                        _ssh_client.close()
                    except Exception:
                        pass
                    _ssh_client = None
            # 如果没有 existing 信息，则保守不关闭（会重用）
    except Exception:
        try:
            _ssh_client.close()
        except Exception:
            pass
        _ssh_client = None

def connect_ssh(host: str = None, port: int = None, username: str = None, password: str = None, timeout: int = 10):
    """
    建立或复用 SSH 长连接。
    接受可选参数：host, port, username, password（若不传则使用 .env 中的配置）。
    返回 (ssh_client, remote_system)
    """
    global _ssh_client, _remote_system, SSH_HOST, SSH_PORT, SSH_USER, SSH_PASS

    # 优先使用传入参数，否则读取 env / 全局
    host = host or SSH_HOST
    port = int(port or SSH_PORT)
    username = username or SSH_USER
    password = password or SSH_PASS

    # 如果已有连接但目标不同，则关闭它
    _close_existing_if_diff(host, port, username)

    # 若已有活跃连接，直接复用
    if _ssh_client and _ssh_client.get_transport() and _ssh_client.get_transport().is_active():
        return _ssh_client, _remote_system

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=timeout,
            banner_timeout=10,
            auth_timeout=10,
            look_for_keys=False,   # 明确不使用密钥（你使用密码登录）
            allow_agent=False
        )
        # 存储一些信息以便复用判断
        client._connection_info = (host, port, username)

        # 检测远程系统
        _remote_system = detect_remote_system(client)
        # 更新全局默认（下一次无参调用使用）
        SSH_HOST, SSH_PORT, SSH_USER, SSH_PASS = host, port, username, password

        _ssh_client = client
        print(f"🌐 Connected to {host}:{port} ({_remote_system})")
        return client, _remote_system

    except socket.timeout:
        raise RuntimeError("连接超时（可能网络不通、防火墙或 IP 填写错误）。")
    except paramiko.AuthenticationException:
        raise RuntimeError("认证失败（用户名或密码错误）。")
    except paramiko.SSHException as e:
        raise RuntimeError(f"SSH 协议错误：{e}")
    except Exception as e:
        raise RuntimeError(f"SSH 连接失败：{e}")

def close_ssh():
    global _ssh_client
    if _ssh_client:
        try:
            _ssh_client.close()
        except Exception:
            pass
        _ssh_client = None
        print("🔌 SSH connection closed.")

def detect_remote_system(ssh_client):
    try:
        stdin, stdout, _ = ssh_client.exec_command("uname", timeout=3)
        out = stdout.read().decode().strip().lower()
        if "linux" in out:
            return "Linux"
        if "darwin" in out:
            return "macOS"
        # windows fallback
        stdin, stdout, _ = ssh_client.exec_command("ver", timeout=3)
        out = stdout.read().decode().strip().lower()
        if "windows" in out:
            return "Windows"
        return "Unknown"
    except Exception:
        return "Unknown"

def execute_remote_command(command, system_type: str = None, timeout: int = 15, client=None):
    """
    在远程主机上执行命令并返回字符串结果。
    如果 client 提供则使用该连接，否则尝试复用全局连接或自动连接（使用 .env / 上次保存的信息）。
    """
    if not is_safe_command(command, system_type):
        return f"⚠️ 检测到危险命令：{command}\n已阻止执行。"

    ssh_client = client
    if ssh_client is None:
        # 如果全局可用复用它
        global _ssh_client
        if _ssh_client and _ssh_client.get_transport() and _ssh_client.get_transport().is_active():
            ssh_client = _ssh_client
        else:
            # 尝试用全局配置建立连接（connect_ssh 使用 env 或上次保存的 SSH_HOST）
            try:
                ssh_client, _ = connect_ssh(timeout=10)
            except Exception as e:
                return f"❌ SSH 连接建立失败：{e}"

    try:
        print("命令*", command,"*")
        stdin, stdout, stderr = ssh_client.exec_command(command, timeout=timeout)
        out = stdout.read().decode("utf-8", errors="ignore").strip()
        err = stderr.read().decode("utf-8", errors="ignore").strip()
        if err:
            return f"❌ Remote error:\n{err}\n---\n{out}"
        return out or "✅ 命令执行成功，无输出。"
    except Exception as e:
        return f"❌ SSH 执行失败：{e}"
