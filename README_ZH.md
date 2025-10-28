# 🪶 言道 OS (YanDao OS)—自然语言操作系统

> “言有尽，而道无穷。” —— 《道德经》

**言道 OS** 是一款融合 **大语言模型（LLM）** 与 **Linux 命令行** 的新型自然语言操作系统。  
它让你能够**用自然语言直接与系统对话**，完成各种操作命令。

<div align="center">

*[English](reademe.md) | [中文文档]*  
<br>

[![zread](https://img.shields.io/badge/Ask_Zread-_.svg?style=flat&color=00b0aa&labelColor=000000&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuOTYxNTYgMS42MDAxSDIuMjQxNTZDMS44ODgxIDEuNjAwMSAxLjYwMTU2IDEuODg2NjQgMS42MDE1NiAyLjI0MDFWNC45NjAxQzEuNjAxNTYgNS4zMTM1NiAxLjg4ODEgNS42MDAxIDIuMjQxNTYgNS42MDAxSDQuOTYxNTZDNS4zMTUwMiA1LjYwMDEgNS42MDE1NiA1LjMxMzU2IDUuNjAxNTYgNC45NjAxVjIuMjQwMUM1LjYwMTU2IDEuODg2NjQgNS4zMTUwMiAxLjYwMDEgNC45NjE1NiAxLjYwMDFaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00Ljk2MTU2IDEwLjM5OTlIMi4yNDE1NkMxLjg4ODEgMTAuMzk5OSAxLjYwMTU2IDEwLjY4NjQgMS42MDE1NiAxMS4wMzk5VjEzLjc1OTlDMS42MDE1NiAxNC4xMTM0IDEuODg4MSAxNC4zOTk5IDIuMjQxNTYgMTQuMzk5OUg0Ljk2MTU2QzUuMzE1MDIgMTQuMzk5OSA1LjYwMTU2IDE0LjExMzQgNS42MDE1NiAxMy43NTk5VjExLjAzOTlDNS42MDE1NiAxMC42ODY0IDUuMzE1MDIgMTAuMzk5OSA0Ljk2MTU2IDEwLjM5OTlaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik0xMy43NTg0IDEuNjAwMUgxMS4wMzg0QzEwLjY4NSAxLjYwMDEgMTAuMzk4NCAxLjg4NjY0IDEwLjM5ODQgMi4yNDAxVjQuOTYwMUMxMC4zOTg0IDUuMzEzNTYgMTAuNjg1IDUuNjAwMSAxMS4wMzg0IDUuNjAwMUgxMy43NTg0QzE0LjExMTkgNS42MDAxIDE0LjM5ODQgNS4zMTM1NiAxNC4zOTg0IDQuOTYwMVYyLjI0MDFDMTQuMzk4NCAxLjg4NjY0IDE0LjExMTkgMS42MDAxIDEzLjc1ODQgMS42MDAxWiIgZmlsbD0iI2ZmZiIvPgo8cGF0aCBkPSJNNCAxMkwxMiA0TDQgMTJaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00IDEyTDEyIDQiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K&logoColor=ffffff)](https://zread.ai/benjiesun/YanDao-OS)
</div>

---
## 📋 目录

- [🌌 Overview | 概述](#overview)
- [✨ Features | 特性](#features)
- [🧩 Project Structure | 项目结构](#project-structure)
- [🚀 Quick Start | 快速开始](#quick-start)
- [💭 Philosophy | 哲学](#philosophy)
- [📜 License | 许可](#license)

---
## 🌌 项目简介

在言道 OS 中，你不再需要记住复杂的命令行语法。  
你可以直接输入：
我想创建一个名为 os.py 的 Python 文件
系统会自动理解你的意图，生成并执行对应的命令，就像：
touch os.py

通过这种方式，**语言即命令，道法自然。**

---

## 🌱 特性

- 🧠 **自然语言理解**：支持中文、英文及混合语言输入。  
- ⚙️ **命令生成与执行**：由大语言模型生成系统命令，并自动执行。
- 💻 **脚本生成**：根据自然语言指令自动生成可执行脚本或代码片段。
- 💬 **普通对话**: 支持超越命令执行的自然对话，实现更流畅的人机交流。
- 🔒 **安全确认机制**：所有命令与脚本操作均需用户确认后才会执行或保存，确保安全可控。 
- 📜 **短期上下文记忆**：保留最近对话上下文，实现多轮指令的连贯理解与执行，让交互更自然流畅。 
- 🌐 **多模型兼容**：支持本地 LLM（如 Qwen、DeepSeek）与远程 API（如 OpenAI GPT）。
- 💻 **跨平台适配** — 自动检测系统类型并生成适合平台的命令（Linux或 Windows）。
- 🎙️ **语音转文本输入** — 支持自然语言命令输入的实时语音识别。
- 🔗 **持久 SSH 远程执行** — 支持安全 SSH 长连接模式，用于远程终端控制。
- 🧩 **动态黑名单配置** — 危险命令现在由文件管理并按系统类型加载。
- 🪟 **交互式 GUI 界面** — 提供直观的可视化终端和模型控制面板便于操作。

---

## 🧩 项目结构
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
## 🚀 快速开始

```bash
git clone https://github.com/benjiesun/YanDao/YanDao-os.git
cd yandao-os
pip install -r requirements.txt
python main.py
``` 

## 🤖 使用示例
1️⃣ **自然语言命令执行**

输入：

列出当前目录下的文件

系统回应：

即将执行命令：ls
是否继续执行？(y/n)

2️⃣ **脚本生成**

输入：

帮我生成一个名为 os 的 Python 脚本，输出 1 到 1000 的所有质数

系统回应：

即将生成脚本文件：os.py
生成位置：./
脚本说明：输出 1 到 1000 的所有质数
内容预览：
----------------------------------------
for n in range(2, 1001):
    if all(n % i != 0 for i in range(2, int(n**0.5) + 1)):
        print(n)
----------------------------------------
是否保存脚本文件？(y/n)
是否立即执行该脚本？(y/n)

3️⃣ **普通对话模式**

输入：

你好，你是谁？

系统回应：

你好！我是言道，你的自然语言 LINUX 终端助手。我可以帮你执行命令、生成脚本或回答问题。请告诉我你需要什么帮助。

## 💭 设计哲学

“无为而无不为。”

言道 OS 的设计理念是：
让语言成为操作之道，让思维直接驱动机器。
不再拘泥于命令行语法，而是以自然语言通达计算之本。

📜 许可

MIT License © 2025 YanDao Project
