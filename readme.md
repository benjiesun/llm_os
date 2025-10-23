# 🌎 YanDao OS - Natural Language Operating Shell

“Words have limits, but the Dao is infinite.” — Tao Te Ching

YanDao OS is a new kind of Natural Language Operating Shell that fuses Large Language Models (LLMs) with the Linux command line.
It allows you to interact with your computer through plain language.

## 🌌 Overview

In YanDao OS, you don’t need to remember complex shell commands.
Simply say:

Create a Python file named os.py


The system will understand and execute the right command:

touch os.py


In this way, language becomes command, and command follows the Dao.

## 🌱 Features

🧠 Natural language understanding — supports Chinese, English, and mixed input.

⚙️ Command generation & execution — powered by a large language model.

🔒 Safety confirmation — confirm before running any command.

📜 Command history — records user input and results.

🌐 Model flexibility — compatible with both local and remote models (Qwen, DeepSeek, OpenAI, etc.)

💻 Cross-platform adaptation — automatically detects system type and generates platform-appropriate commands (Linux shell or Windows PowerShell / CMD).

🎙️ Voice-to-text input — supports real-time speech recognition for natural language command input.

## 🧩 Project Structure
```text
yandao/
├── main.py              # main entry point
├── llm_agent.py         # language model interface
├── llm_vllm.py          # local llm
├── command_executor.py  # command execution & safety checks
├── prompts/             # system prompt templates
└── history/             # operation logs
```

## 🚀 Quick Start
```bash
git clone https://github.com/yourname/yandao-os.git
cd yandao-os
pip install -r requirements.txt
python main.py
``` 

Then type:

List files in the current directory


The system will respond:

Command to execute: ls
Proceed? (y/n)

## 💭 Philosophy

“Act without acting, and nothing is left undone.” — Tao Te Ching

YanDao OS embodies the harmony of language and computation.
By merging human intent and system logic, it creates a seamless interface —
where thought becomes command, and words shape reality.

## 📜 License

MIT License © 2025 YanDao Project
