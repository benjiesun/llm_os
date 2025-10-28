# 🌎 YanDao OS - Natural Language Operating Shell




“Words have limits, but the Dao is infinite.” — Tao Te Ching

YanDao OS is a new kind of Natural Language Operating Shell that fuses Large Language Models (LLMs) with the Linux command line.
It allows you to interact with your computer through plain language.

 <div align="center">

*English | [中文文档](README_ZH.md)*  
<br>

[![zread](https://img.shields.io/badge/Ask_Zread-_.svg?style=flat&color=00b0aa&labelColor=000000&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuOTYxNTYgMS42MDAxSDIuMjQxNTZDMS44ODgxIDEuNjAwMSAxLjYwMTU2IDEuODg2NjQgMS42MDE1NiAyLjI0MDFWNC45NjAxQzEuNjAxNTYgNS4zMTM1NiAxLjg4ODEgNS42MDAxIDIuMjQxNTYgNS42MDAxSDQuOTYxNTZDNS4zMTUwMiA1LjYwMDEgNS42MDE1NiA1LjMxMzU2IDUuNjAxNTYgNC45NjAxVjIuMjQwMUM1LjYwMTU2IDEuODg2NjQgNS4zMTUwMiAxLjYwMDEgNC45NjE1NiAxLjYwMDFaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00Ljk2MTU2IDEwLjM5OTlIMi4yNDE1NkMxLjg4ODEgMTAuMzk5OSAxLjYwMTU2IDEwLjY4NjQgMS42MDE1NiAxMS4wMzk5VjEzLjc1OTlDMS42MDE1NiAxNC4xMTM0IDEuODg4MSAxNC4zOTk5IDIuMjQxNTYgMTQuMzk5OUg0Ljk2MTU2QzUuMzE1MDIgMTQuMzk5OSA1LjYwMTU2IDE0LjExMzQgNS42MDE1NiAxMy43NTk5VjExLjAzOTlDNS42MDE1NiAxMC42ODY0IDUuMzE1MDIgMTAuMzk5OSA0Ljk2MTU2IDEwLjM5OTlaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik0xMy43NTg0IDEuNjAwMUgxMS4wMzg0QzEwLjY4NSAxLjYwMDEgMTAuMzk4NCAxLjg4NjY0IDEwLjM5ODQgMi4yNDAxVjQuOTYwMUMxMC4zOTg0IDUuMzEzNTYgMTAuNjg1IDUuNjAwMSAxMS4wMzg0IDUuNjAwMUgxMy43NTg0QzE0LjExMTkgNS42MDAxIDE0LjM5ODQgNS4zMTM1NiAxNC4zOTg0IDQuOTYwMVYyLjI0MDFDMTQuMzk4NCAxLjg4NjY0IDE0LjExMTkgMS42MDAxIDEzLjc1ODQgMS42MDAxWiIgZmlsbD0iI2ZmZiIvPgo8cGF0aCBkPSJNNCAxMkwxMiA0TDQgMTJaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00IDEyTDEyIDQiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K&logoColor=ffffff)](https://zread.ai/benjiesun/YanDao-OS)
</div>

---

## 📋 Table of Contents | 目录

- [🌌 Overview | 概述](#overview)
- [✨ Features | 特性](#features)
- [🧩 Project Structure | 项目结构](#project-structure)
- [🚀 Quick Start | 快速开始](#quick-start)
- [💭 Philosophy | 哲学](#philosophy)
- [📜 License | 许可](#license)

---
## 🌌 Overview

In YanDao OS, you don’t need to remember complex shell commands.
Simply say:

Create a Python file named os.py


The system will understand and execute the right command:

touch os.py


In this way, language becomes command, and command follows the Dao.

## 🌱 Features

🧠 Natural language understanding — supports Chinese, English, and mixed input.

⚙️ Command generation & execution — System commands are generated and executed automatically by the large language model.

💻 Script Generation — Creates executable scripts from natural language.

💬 Conversational Dialogue — Supports natural, free-form interaction beyond command execution for smoother human-computer communication.

🔒 Safety confirmation — Confirms all commands and scripts before execution.

📜 Short-term Memory — Maintains recent context for multi-turn dialogue.

🌐 Model flexibility — compatible with both local and remote models (Qwen, DeepSeek, OpenAI, etc.)

💻 Cross-platform adaptation — automatically detects system type and generates platform-appropriate commands (Linux shell or Windows PowerShell / CMD).

🎙️ Voice-to-text input — supports real-time speech recognition for natural language command input.

🔗 Persistent SSH remote execution — supports secure SSH long-connection mode for remote terminal control.

🧩 Dynamic blacklist configuration — dangerous commands are now file-managed and loaded by system type.

🪟 Interactive GUI interface — provides an intuitive visual terminal and model control panel for easier operation.

## 🧩 Project Structure
```text
YanDao-OS/
├── main.py                     # CLI entry point | CLI入口
├── llm_api.py                  # Remote LLM interface | 远程LLM接口
├── llm_vllm.py                 # Local LLM interface | 本地LLM接口
├── command_executor.py         # Local command execution | 本地命令执行
├── ssh_executor.py             # Remote SSH execution | 远程SSH执行
├── voice_input.py              # Voice recognition | 语音识别
├── utils/                      # Utility modules | 工具模块
│   ├── blacklist_loader.py     # Security blacklists | 安全黑名单
│   ├── prompt_loader.py        # Prompt management | 提示词管理
│   ├── dangerous_keys/         # Blacklist files | 黑名单文件
│   │   ├── blacklist_linux.txt
│   │   └── blacklist_windows.txt
│   │   └── blacklist_unix.txt
│   └── prompts/                # System prompts | 系统提示词
│       ├── system_linux.txt
│       └── system_windows.txt
│   │   └── system_unix.txt
├── README.md                   # English documentation | 英文文档
├── README_ZH.md                # Chinese documentation | 中文文档
└── requirements.txt            # Dependencies | 依赖项
```

## 🚀 Quick Start
```bash
git clone https://github.com/yourname/yandao-os.git
cd yandao-os
pip install -r requirements.txt
python main.py
``` 

## Usage Examples
1️⃣ **Natural Command Execution**

Input:

List files in the current directory

System Response:

Command to execute: ls
Proceed? (y/n)

2️⃣ **Script Generation**

Input:

Help me generate a Python script called os that lists all prime numbers from 1 to 1000

System Response:

About to generate script file: os.py
Save location: ./
Description: List all prime numbers from 1 to 1000
Preview:
----------------------------------------
for n in range(2, 1001):
    if all(n % i != 0 for i in range(2, int(n**0.5) + 1)):
        print(n)
----------------------------------------
Save this script file? (y/n)
Execute it now? (y/n)

3️⃣ **Conversational Mode**

Input:

Hello, who are you?

System Response:

Hello! I'm Yandao, your natural language Linux terminal assistant. I can help you execute commands, generate scripts, or answer questions. Please let me know how you can help.


## 💭 Philosophy

“Act without acting, and nothing is left undone.” — Tao Te Ching

YanDao OS embodies the harmony of language and computation.
By merging human intent and system logic, it creates a seamless interface —
where thought becomes command, and words shape reality.

## 📜 License

MIT License © 2025 YanDao Project
