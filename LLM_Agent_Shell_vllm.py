# -*- coding: utf-8 -*-
"""
LLM_Agent_Shell_vllm.py
- 支持 PROVIDER=local / api 一键切换
- OpenAI Chat Completions 兼容在线接口
- 命令严格白名单 + 控制符/危险词阻断
- 子进程超时与输出大小限制
- 对话上下文裁剪，回复解析更稳
- 执行解释使用临时上下文，避免污染主会话

使用前：
1) 如走在线API，请在同目录创建 .env（：
   PROVIDER=api
   API_BASE=https://your-endpoint.example.com/v1
   API_KEY=sk-xxxxxxxxxxxxxxxx
   API_MODEL=gpt-4o-mini  # 或 qwen2.5-7b-instruct / llama-3.1-70b-instruct 等
   API_TIMEOUT=30

2) 如走本地模型（默认 PROVIDER=local），请改 MODEL_PATH 为你的权重路径。
"""

import os
import re
import json
import time
import shlex
import subprocess
from dataclasses import dataclass
from typing import List, Dict, Any

# ========== 可选：读取 .env ==========
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv()
except Exception:
    pass

# ========== 提供商选择 ==========
PROVIDER = os.getenv("PROVIDER", "local").lower()

# ========== 本地模型配置（仅当 PROVIDER=local） ==========
MODEL_PATH = os.getenv("MODEL_PATH", "/home/Users/SharedFile/Models/Qwen/Qwen3-8B/")
USE_BF16_ON_CUDA = True

# ========== 在线 API 配置（仅当 PROVIDER=api） ==========
API_BASE = os.getenv("API_BASE", "").rstrip("/")
API_KEY = os.getenv("API_KEY", "")
API_MODEL = os.getenv("API_MODEL", "gpt-4o-mini")
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "30"))

# ========== 回复解析 ==========
ASSISTANT_BLOCK_RE = re.compile(r"(?:<\|assistant\|>|\nassistant:)\s*(.*)", re.DOTALL)
def extract_assistant_text(decoded: str) -> str:
    m = ASSISTANT_BLOCK_RE.search(decoded)
    text = m.group(1) if m else decoded
    # 去掉 <think>...</think>
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return text

# ========== 系统提示（强约束协议） ==========
SYSTEM_PROMPT = """
你是一个智能 Shell 代理。当且仅当需要执行系统命令时，输出如下格式（不要输出其他多余字符）：
EXECUTE:
<单行命令>

规则：
1) 如果不需要执行命令，直接用自然语言回答，不要出现 EXECUTE:。
2) 如果需要执行命令，<单行命令> 必须是单行，且禁止包含：分号 ;、管道 |、与/或 && ||、反引号 `...`、$()、重定向 > >> < << | tee、换行、多条命令等控制符。
3) 坚决避免一切危险操作（删除/格式化/关机/重启/权限/挂载/网络破坏等）。
4) 尽量选择只读、信息查询类命令，例如：ls, head, tail, grep(只读路径), wc, df, free, uname, whoami, pwd, du -sh <safe>, nvidia-smi 等。
"""

# ========== 消息与上下文裁剪 ==========
MAX_TURNS = 8  # 最近保留 8 轮 user/assistant
def trim_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if not messages:
        return messages
    sys = messages[0:1]
    tail = messages[1:]
    if len(tail) > 2 * MAX_TURNS:
        tail = tail[-2 * MAX_TURNS:]
    return sys + tail

# ========== 命令安全校验（白名单 + 阻断） ==========
ALLOWED_CMDS = {
    "ls","cat","head","tail","wc","df","free","nvidia-smi",
    "uname","whoami","pwd","du","grep","find"
}
FORBIDDEN_TOKENS = {";", "|", "||", "&&", "`", "$(", ")", ">", ">>", "<", "<<", "&", "\n", "\r", "\t"}
FORBIDDEN_WORDS  = {"sudo","rm","reboot","shutdown","mkfs","dd","kill","pkill","killall","mount","umount","chmod","chown","curl","nohup"}

# 可选：限制只读路径根（防止遍历全盘）。为空表示不启用。
READONLY_ROOT = os.getenv("READONLY_ROOT", "").rstrip("/")

def is_under_readonly_root(path: str) -> bool:
    if not READONLY_ROOT:
        return True  # 未启用限制
    try:
        full = os.path.realpath(path)
        base = os.path.realpath(READONLY_ROOT)
        return full.startswith(base + os.sep) or (full == base)
    except Exception:
        return False

def is_safe_command(cmd: str) -> bool:
    # 控制符阻断
    if any(t in cmd for t in FORBIDDEN_TOKENS):
        return False
    # 拆词检查
    try:
        parts = shlex.split(cmd)
    except Exception:
        return False
    if not parts:
        return False
    # 白名单命令
    if parts[0] not in ALLOWED_CMDS:
        return False
    low = cmd.lower()
    if any(w in low for w in FORBIDDEN_WORDS):
        return False
    # 简单只读路径限制（对 cat/grep/find/du 等常见带路径的命令约束）
    def check_paths(args: List[str]) -> bool:
        paths = []
        skip_next = False
        for a in args:
            if skip_next:
                skip_next = False
                continue
            if a in {"-r","-R","-h","-s","-l","-a","-n","-m","-i","-v","-k","-H"}:
                continue
            if a in {"-C","-d","-p"}:  # 某些命令参数带值
                skip_next = True
                continue
            if a.startswith("-"):
                continue
            paths.append(a)
        for p in paths:
            # 忽略明显非路径（比如纯关键字）
            if p in {".",".."}:
                continue
            if not is_under_readonly_root(p):
                return False
        return True

    if parts[0] in {"cat","grep","find","du"}:
        if not check_paths(parts[1:]):
            return False
    return True

# ========== 子进程执行（超时 + 输出限流） ==========
def execute_shell_command(command: str, timeout: int = 15, max_bytes: int = 1_000_000) -> str:
    try:
        result = subprocess.run(
            command, shell=True,
            capture_output=True, text=False,
            timeout=timeout,
        )
        out = (result.stdout or b"")[:max_bytes]
        err = (result.stderr or b"")[:max_bytes]
        text_out = out.decode(errors="replace").strip()
        text_err = err.decode(errors="replace").strip()
        if result.returncode == 0:
            return text_out if text_out else "(no output)"
        else:
            return f"❌ 错误：{text_err or '(empty stderr)'}"
    except subprocess.TimeoutExpired:
        return "⏰ 命令执行超时（已中止）"
    except Exception as e:
        return f"⚠️ 执行异常：{e}"

# ========== LLM Provider 抽象 ==========
class BaseProvider:
    def chat(self, messages: List[Dict[str,str]], max_new_tokens: int = 512, temperature: float = 0.7) -> str:
        raise NotImplementedError

# ---- 在线 API 提供商（OpenAI 兼容） ----
class OpenAICompatAPIProvider(BaseProvider):
    def __init__(self, api_base: str, api_key: str, model: str, timeout: float):
        assert api_base and api_key, "API_BASE 或 API_KEY 未配置"
        self.base = api_base.rstrip("/")
        self.key = api_key
        self.model = model
        self.timeout = timeout

    def chat(self, messages: List[Dict[str,str]], max_new_tokens: int = 512, temperature: float = 0.7) -> str:
        import requests
        url = f"{self.base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": max(0.0, float(temperature)),
            "max_tokens": int(max_new_tokens),
        }
        for attempt in range(3):
            try:
                r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=self.timeout)
                if r.status_code == 200:
                    data = r.json()
                    return data["choices"][0]["message"]["content"]
                err = r.text[:500]
                if 400 <= r.status_code < 500:
                    return f"❌ API 错误 {r.status_code}: {err}"
                time.sleep(1.5 * (attempt + 1))
            except Exception as e:
                if attempt == 2:
                    return f"⚠️ API 请求异常：{e}"
                time.sleep(1.5 * (attempt + 1))
        return "⚠️ API 未返回有效结果"

# ---- 本地 HF 模型提供商 ----
class LocalHFProvider(BaseProvider):
    def __init__(self, model_path: str):
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        self.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
        self.DTYPE = torch.bfloat16 if (self.DEVICE == "cuda" and USE_BF16_ON_CUDA) else torch.float32
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path, torch_dtype=self.DTYPE, trust_remote_code=True
        ).to(self.DEVICE).eval()

    def chat(self, messages: List[Dict[str,str]], max_new_tokens: int = 512, temperature: float = 0.7) -> str:
        import torch
        with torch.no_grad():
            text = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
            )
            inputs = self.tokenizer(text, return_tensors="pt").to(self.DEVICE)
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=(temperature > 0.0),
                temperature=float(temperature) if temperature > 0.0 else 0.0,
                pad_token_id=self.tokenizer.eos_token_id,
            )
            decoded = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return extract_assistant_text(decoded)

# ========== Provider 实例 ==========
if PROVIDER == "api":
    provider: BaseProvider = OpenAICompatAPIProvider(API_BASE, API_KEY, API_MODEL, API_TIMEOUT)
else:
    provider: BaseProvider = LocalHFProvider(MODEL_PATH)

# ========== 统一 LLM 调用 ==========
def llm_chat(messages: List[Dict[str,str]], exec_mode: bool = False) -> str:
    # 执行命令判别更稳定：temperature=0, tokens小些
    if exec_mode:
        return provider.chat(messages, max_new_tokens=200, temperature=0.0)
    # 普通聊天/解释：保留一定多样性
    return provider.chat(messages, max_new_tokens=700, temperature=0.7)

# ========== 解释输出：临时上下文 ==========
def explain_output(cmd: str, output: str) -> str:
    local_msgs = [
        {"role": "system", "content": "你是一个简洁、准确的运维解释助手。"},
        {"role": "user", "content": f"命令: {cmd}\n输出:\n{output[:5000]}\n请用简洁自然语言说明关键点。"}
    ]
    return llm_chat(local_msgs, exec_mode=False)

# ========== 主循环 ==========
def main():
    messages: List[Dict[str,str]] = [
        {"role": "system", "content": SYSTEM_PROMPT.strip()}
    ]
    print("✨ Shell 智能代理已启动（输入 exit/quit 退出）。")
    if PROVIDER == "api":
        print(f"🔗 模式：在线 API  -> {API_BASE}  模型：{API_MODEL}")
    else:
        print(f"🧩 模式：本地模型  -> {MODEL_PATH}")

    while True:
        try:
            user_input = input("\n你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 已退出。")
            break

        if user_input.lower() in {"exit","quit"}:
            print("👋 再见～")
            break
        if not user_input:
            continue

        # 组装消息并裁剪
        messages.append({"role": "user", "content": user_input})
        messages[:] = trim_messages(messages)

        # 第一次生成：执行判别（确定性）
        reply = llm_chat(messages, exec_mode=True).strip()
        messages.append({"role": "assistant", "content": reply})
        messages[:] = trim_messages(messages)

        if reply.startswith("EXECUTE:"):
            cmd = reply.split("EXECUTE:", 1)[1].strip()
            print(f"🤖 建议执行命令: {cmd}")

            # 安全校验
            if not is_safe_command(cmd):
                print("⛔ 命令未通过安全校验，已拒绝执行。")
                continue

            confirm = input("是否执行？(y/n): ").strip().lower()
            if confirm != "y":
                print("✅ 已取消执行。")
                continue

            # 执行
            result = execute_shell_command(cmd)
            print("📄 命令输出：\n", result)

            # 解释（临时上下文，不污染主对话）
            explanation = explain_output(cmd, result)
            print(f"📝 输出解释：{explanation}")

        else:
            print(f"🤖：{reply}")

if __name__ == "__main__":
    main()
