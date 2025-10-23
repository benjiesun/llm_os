import re
from llm_vllm import get_command_from_llm
from command_executor import execute_command

def extract_command_from_response(text: str) -> str:
    """
    尝试从模型返回文本中提取命令：
    1) 优先查找 '对应的命令是：' 或 '对应的命令：' 标签
    2) 否则回退到更严格的正则抽取单行看起来像命令的行
    """
    # 标记优先提取（支持多行）
    for marker in ["对应的命令是：", "对应的命令：", "Command:", "对应命令："]:
        if marker in text:
            # 取 marker 后面的部分，优先取下一行或同一行的剩余
            after = text.split(marker, 1)[1].strip()
            # 如果 after 多行，取第一非空行作为命令
            for line in after.splitlines():
                line = line.strip()
                if line:
                    return line
            # 如果没有明确下一行，直接返回 after
            return after.strip()

    # fallback：严格单行命令匹配（首 token 为字母，允许 - _ . /）
    cmd_pattern = r"(?m)^[ \t]*([a-zA-Z][a-zA-Z0-9_\-./]*(?:\s+[^`'\n]+)*)[ \t]*$"
    matches = re.findall(cmd_pattern, text.strip())
    if matches:
        # 取最后一个匹配（通常是模型生成的末尾）
        return matches[-1].strip()
    return ""

def main():
    print("🪶 言道 OS | 以言通道")
    print("输入自然语言指令（输入 exit 退出）\n")

    while True:
        user_input = input("🧠> ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("\n🍃 再会，道自无穷。")
            break

        # 调用模型
        response = get_command_from_llm(user_input)
        print("\n🤖 模型回答：")
        print(response)
        print("─" * 60)

        # 提取命令
        command = extract_command_from_response(response)
        if not command:
            print("❓ 未检测到可执行命令，请重试或更明确地要求模型给出“对应的命令是：”标签。")
            continue

        # 确认执行
        confirm = input(f"\n是否执行以下命令？\n👉 {command}\n(y/n): ").strip().lower()
        if confirm == "y":
            print("\n🪶 正在执行...\n")
            result = execute_command(command)
            print(result)
            print("─" * 60)
        else:
            print("🌀 已取消执行。")

if __name__ == "__main__":
    main()
