import re
import subprocess
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# ========== 模型配置 ==========
MODEL_PATH = "/home/Users/SharedFile/Models/Qwen/Qwen3-8B/"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
).to(DEVICE).eval()

# ========== 系统提示 ==========
SYSTEM_PROMPT = """
你是一个智能Shell代理(LLM Agent Shell)。
你具备以下能力：
1. 理解用户自然语言请求；   
2. 判断是否需要执行Linux命令；
3. 当需要执行时，直接输出命令；
4. 当用户只是提问时，直接回答；
5. 避免执行危险命令（如 rm, reboot, shutdown, :(){ 等）；
6. 当用户执行命令后，你能根据命令输出进行总结或解释。

输出格式规则：
- 如果决定执行命令，请输出：
EXECUTE:
<命令>
- 如果不需要执行命令，请输出自然语言回答。
不要输出任何解释性内容或思考过程。
"""

messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# ========== 执行Shell命令 ==========
def execute_shell_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"❌ 错误：{result.stderr.strip()}"
    except Exception as e:
        return f"⚠️ 执行异常：{str(e)}"

# ========== 与模型交互 ==========
def agent_chat(user_input):
    messages.append({"role": "user", "content": user_input})
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    inputs = tokenizer(text, return_tensors="pt").to(DEVICE)
    outputs = model.generate(
        **inputs,
        max_new_tokens=700,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )
    reply = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if "assistant" in reply:
        reply = reply.split("assistant")[-1]
    reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL).strip()
    messages.append({"role": "assistant", "content": reply})
    return reply

# ========== 解释命令输出 ==========
def explain_output(cmd, output):
    prompt = f"命令: {cmd}\n输出:\n{output}\n请用简洁自然语言解释这个输出。"
    messages.append({"role": "user", "content": prompt})

    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    inputs = tokenizer(text, return_tensors="pt").to(DEVICE)
    outputs = model.generate(
        **inputs,
        max_new_tokens=500,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )
    reply = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if "assistant" in reply:
        reply = reply.split("assistant")[-1]
    reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL).strip()
    messages.append({"role": "assistant", "content": reply})
    return reply

# ========== 主交互 ==========
def main():
    print("🤖 欢迎使用 LLM Agent Shell！输入 exit 退出。\n")

    while True:
        user_input = input("🧑 你：")
        if user_input.lower() in ["exit", "quit"]:
            print("🤖：再见👋")
            break

        reply = agent_chat(user_input)

        if "EXECUTE:" in reply:
            cmd = reply.split("EXECUTE:")[1].strip()

            # 危险命令检测
            if any(danger in cmd for danger in ["rm", "shutdown", "reboot", ":(){", "mkfs", "dd", "kill", ">:"]):
                print("⚠️ 检测到危险命令，已拒绝执行。")
                continue

            print(f"🤖 建议执行命令: {cmd}")
            confirm = input("是否执行？(y/n): ")
            if confirm.lower() == "y":
                result = execute_shell_command(cmd)
                print("命令输出：\n", result)
                explanation = explain_output(cmd, result)
                print(f"🤖 输出内容解释：{explanation}")
            else:
                print("✅ 已取消执行。")
        else:
            print(f"🤖：{reply}")

if __name__ == "__main__":
    main()
