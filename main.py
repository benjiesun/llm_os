import platform
import re
from command_executor import execute_command
from script_generator import handle_script_response

from ssh_executor import connect_ssh, execute_remote_command, close_ssh
# ========== 选择使用模式 ==========
# 可选："local"（本地模型）或 "api"（远程模型）
PROVIDER = "local"     # local / api
USE_VOICE = False     # 🎤 是否启用语音输入
USE_SSH = False        # 🌐 是否通过 SSH 在远程执行命令


def main():
    exec_mode = "远程 SSH 模式 🔗" if USE_SSH else "本地终端模式 💻"
    provider_mode = "远程 API 模型 🌐" if PROVIDER == "api" else "本地模型 💾"

    if USE_SSH:
        ssh, system_type = connect_ssh()
    else:
        system_type = platform.system()
        
    if PROVIDER == "local":
        from llm_vllm import init_vllm_prompt
        init_vllm_prompt(system_type)
    elif PROVIDER == "api":
        from llm_api import init_api_prompt
        init_api_prompt(system_type)
    else:
        print("❌ 未知的 PROVIDER，请设置为 'local' 或 'api'")
        exit()

    print(f"🪶 言道 OS | 以言通道 —— 当前模式：{provider_mode} | {exec_mode}")

    
    print("输入自然语言指令（输入 exit 退出）")

    while True:
        if USE_VOICE:
            from voice_input import record_once
            print("\n🎧 按 Enter 开始录音，或输入文字指令：")
            choice = input("> ").strip()
            if choice.lower() in ["exit", "quit"]:
                print("\n🍃 再会，道自无穷。")
                break

            if choice == "":
                user_input = record_once()
                if not user_input:
                    continue
            else:
                user_input = choice
        else:
            user_input = input("🧠 你> ").strip()
            if user_input.lower() in ["exit", "quit"]:
                print("\n🍃 再会，道自无穷。")
                break


        # 调用模型
        if PROVIDER == "local":
            from llm_vllm import get_command_from_llm
            response = get_command_from_llm(user_input, system_type)
        elif PROVIDER == "api":
            from llm_api import get_command_from_api
            response = get_command_from_api(user_input, system_type)
        else:
            print("❌ 未知的 PROVIDER，请设置为 'local' 或 'api'")
            continue


        if "EXECUTE:" in response:
            # 提取命令部分
            cmd = response.split("EXECUTE:")[1].strip()
            lines = cmd.splitlines()
            desc = lines[0] if lines else "执行命令"
            command = "\n".join(lines[1:]) if len(lines) > 1 else ""

            print(f"\n🤖 言道将为您做：{desc}")
            print(f"建议执行命令：{command}")

            confirm = input("是否内您执行？(y/n): ").lower()
            if confirm == "y":
                print("\n🪶 正在执行...\n")

                #执行命令（本地 / 远程）
                if USE_SSH:
                    from ssh_executor import execute_remote_command
                    result = execute_shell_command(command,system_type)
                else:
                    result = execute_command(command)

                print("命令输出：\n", result)
                # explanation = explain_output(command_lines, result)
                # print(f"🤖 输出解释：{explanation}")
            else:
                print("🌀 已取消执行。")

        elif "SCRIPT:" in response:
            handle_script_response(response)

        elif "REPLY:" in response:
            reply_content = response.split("REPLY:")[1].strip()
            print("\n🤖 言道：")
            print(reply_content)
            print("─" * 60)

        else:
            print(f"\n🤖 言道：❌生成失败，请重试。")
            print("─" * 60)


if __name__ == "__main__":
    main()
