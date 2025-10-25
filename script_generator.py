#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
script_generator.py
用于解析模型输出中的 SCRIPT: 块，生成并可选执行脚本文件。
"""

import os
import re
from command_executor import execute_command

def handle_script_response(response: str):
    script_block = response.split("SCRIPT:")[1].strip().splitlines()
    filename = script_block[0].strip() if len(script_block) > 0 else "script.py"
    
    raw_location = script_block[1].strip() if len(script_block) > 1 else ""
    # 映射模型可能生成的自然语言路径
    if raw_location in ["当前路径", "当前目录", "当前文件夹", "."]:
        location = os.getcwd()
    elif raw_location:
        location = raw_location if os.path.isabs(raw_location) else os.path.join(os.getcwd(), raw_location)
    else:
        location = os.getcwd()

    description = script_block[2].strip() if len(script_block) > 2 else "无描述"

    # 提取脚本内容（优先识别代码块）
    match = re.search(r"```(?:python|bash)?\n([\s\S]*?)```", response)
    if match:
        script_content = match.group(1).strip()
    else:
        script_content = "\n".join(script_block[3:])

    # 清理脚本内容中多余标签
    script_content = re.sub(r"<\/?script>|```", "", script_content).strip()

    # 自动补全扩展名
    if not re.search(r"\.\w+$", filename):
        filename += ".py"

    print(f"\n🤖 即将生成脚本文件：{filename}")
    print(f"📁 生成位置：{location}")
    print(f"脚本说明：{description}")
    print("内容预览：\n" + "─" * 40)
    print(script_content)
    print("─" * 40)

    confirm = input("是否生成该脚本文件？(y/n): ").lower()
    if confirm == "y":
        filepath = os.path.join(location, filename)
        os.makedirs(location, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(script_content)
        print(f"✅ 已生成脚本文件: {filepath}")

        run = input("是否立即执行？(y/n): ").lower()
        if run == "y":
            cmd = f"python3 {filepath}" if filename.endswith(".py") else f"bash {filepath}"
            result = execute_command(cmd)
            print("📤 脚本输出：\n", result)
        else:
            print("✅ 已保存脚本，未执行。")
    else:
        print("❎ 已取消脚本生成。")