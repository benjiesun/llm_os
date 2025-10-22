# 🪶 言道 OS (YanDao OS)—自然语言操作系统

> “言有尽，而道无穷。” —— 《道德经》

**言道 OS** 是一款融合 **大语言模型（LLM）** 与 **Linux 命令行** 的新型自然语言操作系统。  
它让你能够**用自然语言直接与系统对话**，完成各种操作命令。

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
- 🔒 **安全确认机制**：执行前提示用户确认，防止误操作。  
- 📜 **操作历史记录**：保存用户的自然语言输入与命令结果。  
- 🌐 **多模型兼容**：支持本地 LLM（如 Qwen、DeepSeek）与远程 API（如 OpenAI GPT）。

---

## 🧩 项目结构
yandao/
├── main.py # 主程序入口
├── llm_agent.py # 模型接口
├── command_executor.py # 命令执行与安全校验
├── prompts/ # 系统提示词模板
└── history/ # 操作记录文件
## 🚀 快速开始

```bash
git clone https://github.com/benjiesun/YanDao/YanDao-os.git
cd yandao-os
pip install -r requirements.txt
python main.py
``` 
然后输入：

我想列出当前目录下的所有文件

系统输出：

将执行命令: ls
是否继续执行？(y/n)

## 💭 设计哲学

“无为而无不为。”

言道 OS 的设计理念是：
让语言成为操作之道，让思维直接驱动机器。
不再拘泥于命令行语法，而是以自然语言通达计算之本。

📜 许可

MIT License © 2025 YanDao Project
