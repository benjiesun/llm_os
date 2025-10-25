#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gui_main.py
YanDao-OS 图形化界面版本
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import platform
import re
import queue
from datetime import datetime

# 导入现有模块
from command_executor import execute_command
from ssh_executor import connect_ssh, execute_remote_command, close_ssh


class YanDaoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("言道 OS")
        self.root.geometry("1000x700")
        self.root.configure(bg='#2b2b2b')

        # 状态变量
        self.provider = "api"  # api 或 local
        self.use_ssh = False
        self.ssh_session = None
        self.system_type = platform.system()
        self.is_recording = False

        # 线程安全的消息队列
        self.message_queue = queue.Queue()

        self.setup_ui()
        self.setup_styles()

        # 启动消息处理循环
        self.process_messages()

    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')

        # 自定义样式
        style.configure('Title.TLabel',
                        font=('Arial', 16, 'bold'),
                        background='#2b2b2b',
                        foreground='#ffffff')

        style.configure('Status.TLabel',
                        font=('Arial', 10),
                        background='#2b2b2b',
                        foreground='#00ff00')

        style.configure('Accent.TButton',
                        font=('Arial', 10, 'bold'))

    def setup_ui(self):
        """构建用户界面"""
        # 主标题
        title_frame = tk.Frame(self.root, bg='#2b2b2b')
        title_frame.pack(fill='x', padx=10, pady=5)

        title_label = ttk.Label(title_frame,
                                text="言道 OS | “言有尽，而道无穷。” —— 《道德经》",
                                style='Title.TLabel')
        title_label.pack(side='left')

        # 状态显示
        self.status_label = ttk.Label(title_frame,
                                      text=self.get_status_text(),
                                      style='Status.TLabel')
        self.status_label.pack(side='right')

        # 控制面板
        self.setup_control_panel()

        # 聊天显示区域
        self.setup_chat_area()

        # 输入区域
        self.setup_input_area()

        # 功能按钮区域
        self.setup_button_area()

    def setup_control_panel(self):
        """设置控制面板"""
        control_frame = tk.Frame(self.root, bg='#2b2b2b')
        control_frame.pack(fill='x', padx=10, pady=5)

        # 模型选择
        ttk.Label(control_frame, text="模型:", background='#2b2b2b', foreground='white').pack(side='left')

        self.provider_var = tk.StringVar(value=self.provider)
        provider_combo = ttk.Combobox(control_frame, textvariable=self.provider_var,
                                      values=['api', 'local'], width=8, state='readonly')
        provider_combo.pack(side='left', padx=(5, 15))
        provider_combo.bind('<<ComboboxSelected>>', self.on_provider_change)

        # SSH开关
        self.ssh_var = tk.BooleanVar(value=self.use_ssh)
        ssh_check = ttk.Checkbutton(control_frame, text="SSH远程模式",
                                    variable=self.ssh_var,
                                    command=self.on_ssh_toggle)
        ssh_check.pack(side='left', padx=(0, 15))

        # 清除历史按钮
        clear_btn = ttk.Button(control_frame, text="清除历史",
                               command=self.clear_history)
        clear_btn.pack(side='right')

    def setup_chat_area(self):
        """设置聊天显示区域"""
        chat_frame = tk.Frame(self.root)
        chat_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='white',
            state='disabled'
        )
        self.chat_display.pack(fill='both', expand=True)

        # 配置文本标签样式
        self.chat_display.tag_configure('user', foreground='#00bfff', font=('Consolas', 10, 'bold'))
        self.chat_display.tag_configure('assistant', foreground='#90ee90')
        self.chat_display.tag_configure('command', foreground='#ffa500', font=('Consolas', 10, 'bold'))
        self.chat_display.tag_configure('result', foreground='#ffff00')
        self.chat_display.tag_configure('error', foreground='#ff6b6b')

    def setup_input_area(self):
        """设置输入区域"""
        input_frame = tk.Frame(self.root)
        input_frame.pack(fill='x', padx=10, pady=5)

        # 输入框
        self.input_text = tk.Text(input_frame, height=3,
                                  font=('Arial', 11),
                                  bg='#3c3c3c', fg='white',
                                  insertbackground='white')
        self.input_text.pack(fill='x', pady=(0, 5))

        # 绑定快捷键
        self.input_text.bind('<Control-Return>', self.on_send_message)

    def setup_button_area(self):
        """设置功能按钮区域"""
        button_frame = tk.Frame(self.root, bg='#2b2b2b')
        button_frame.pack(fill='x', padx=10, pady=5)

        # 发送按钮
        send_btn = ttk.Button(button_frame, text="发送 (Ctrl+Enter)",
                              command=self.on_send_message,
                              style='Accent.TButton')
        send_btn.pack(side='left', padx=(0, 10))

        # 语音输入按钮
        self.voice_btn = ttk.Button(button_frame, text="🎤 语音输入",
                                    command=self.on_voice_input)
        self.voice_btn.pack(side='left', padx=(0, 10))

        # SSH连接按钮
        self.ssh_btn = ttk.Button(button_frame, text="🔗 SSH连接",
                                  command=self.on_ssh_connect)
        self.ssh_btn.pack(side='left', padx=(0, 10))

        # 保存对话按钮
        save_btn = ttk.Button(button_frame, text="💾 保存对话",
                              command=self.save_conversation)
        save_btn.pack(side='right')

    def get_status_text(self):
        """获取状态文本"""
        provider_text = "远程API🌐" if self.provider == "api" else "本地模型💾"
        exec_text = "SSH远程🔗" if self.use_ssh else "本地终端💻"
        return f"{provider_text} | {exec_text}"

    def update_status(self):
        """更新状态显示"""
        self.status_label.config(text=self.get_status_text())

    def append_to_chat(self, text, tag=None):
        """线程安全地添加消息到聊天区域"""
        self.message_queue.put(('append', text, tag))

    def process_messages(self):
        """处理消息队列中的消息"""
        try:
            while True:
                action, text, tag = self.message_queue.get_nowait()
                if action == 'append':
                    self.chat_display.config(state='normal')
                    if tag:
                        self.chat_display.insert(tk.END, text, tag)
                    else:
                        self.chat_display.insert(tk.END, text)
                    self.chat_display.see(tk.END)
                    self.chat_display.config(state='disabled')
        except queue.Empty:
            pass

        # 继续处理消息
        self.root.after(100, self.process_messages)

    def on_provider_change(self, event):
        """模型提供商更改"""
        self.provider = self.provider_var.get()
        self.update_status()
        self.append_to_chat(f"\n📝 已切换到: {self.get_status_text()}\n", 'assistant')

    def on_ssh_toggle(self):
        """SSH模式切换"""
        self.use_ssh = self.ssh_var.get()
        self.update_status()
        if not self.use_ssh and self.ssh_session:
            close_ssh()
            self.ssh_session = None
            self.append_to_chat("\n🔌 SSH连接已断开\n", 'assistant')

    def on_ssh_connect(self):
        """SSH连接按钮点击"""
        if self.use_ssh and not self.ssh_session:
            def connect_thread():
                try:
                    self.append_to_chat("\n🔗 正在连接SSH...\n", 'assistant')
                    self.ssh_session, self.system_type = connect_ssh()
                    if self.ssh_session:
                        self.append_to_chat("✅ SSH连接成功!\n", 'assistant')
                    else:
                        self.append_to_chat("❌ SSH连接失败\n", 'error')
                except Exception as e:
                    self.append_to_chat(f"❌ SSH连接错误: {str(e)}\n", 'error')

            threading.Thread(target=connect_thread, daemon=True).start()
        else:
            messagebox.showinfo("提示", "请先启用SSH模式或检查连接状态")

    def on_voice_input(self):
        """语音输入按钮点击"""
        if self.is_recording:
            return

        def record_thread():
            try:
                self.is_recording = True
                self.voice_btn.config(text="🎙️ 录音中...", state='disabled')

                from voice_input import record_once
                self.append_to_chat("\n🎧 正在录音，请说话...\n", 'assistant')

                text = record_once()
                if text:
                    self.root.after(0, lambda: self.input_text.insert(tk.END, text))
                    self.append_to_chat(f"💬 语音识别: {text}\n", 'user')
                else:
                    self.append_to_chat("😕 语音识别失败\n", 'error')

            except Exception as e:
                self.append_to_chat(f"❌ 语音输入错误: {str(e)}\n", 'error')
            finally:
                self.is_recording = False
                self.root.after(0, lambda: self.voice_btn.config(text="🎤 语音输入", state='normal'))

        threading.Thread(target=record_thread, daemon=True).start()

    def extract_command_from_response(self, text):
        """从模型响应中提取命令（复用原逻辑）"""
        # 标记优先提取
        for marker in ["对应的命令是：", "对应的命令：", "Command:", "对应命令："]:
            if marker in text:
                after = text.split(marker, 1)[1].strip()
                for line in after.splitlines():
                    line = line.strip()
                    if line:
                        return line
                return after.strip()

        # fallback：严格单行命令匹配
        cmd_pattern = r"(?m)^[ \t]*([a-zA-Z][a-zA-Z0-9_\-./]*(?:\s+[^`'\n]+)*)[ \t]*$"
        matches = re.findall(cmd_pattern, text.strip())
        if matches:
            return matches[-1].strip()
        return ""

    def on_send_message(self, event=None):
        """发送消息"""
        user_input = self.input_text.get("1.0", tk.END).strip()
        if not user_input:
            return

        # 清空输入框
        self.input_text.delete("1.0", tk.END)

        # 显示用户输入
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.append_to_chat(f"\n[{timestamp}] 🧠 您: {user_input}\n", 'user')

        def process_thread():
            try:
                # 调用模型
                self.append_to_chat("🤖 正在思考...\n", 'assistant')

                if self.provider == "local":
                    from llm_vllm import get_command_from_llm
                    response = get_command_from_llm(user_input, self.system_type)
                elif self.provider == "api":
                    from llm_api import get_command_from_api
                    response = get_command_from_api(user_input, self.system_type)
                else:
                    self.append_to_chat("❌ 未知的模型提供商\n", 'error')
                    return

                # 显示模型回答
                self.append_to_chat(f"🤖 模型回答:\n{response}\n", 'assistant')
                self.append_to_chat("─" * 60 + "\n", 'assistant')

                # 提取命令
                command = self.extract_command_from_response(response)
                if not command:
                    self.append_to_chat("❓ 未检测到可执行命令\n", 'error')
                    return

                # 在主线程中显示确认对话框
                self.root.after(0, lambda: self.confirm_and_execute(command))

            except Exception as e:
                self.append_to_chat(f"❌ 处理错误: {str(e)}\n", 'error')

        threading.Thread(target=process_thread, daemon=True).start()

    def confirm_and_execute(self, command):
        """确认并执行命令"""
        self.append_to_chat(f"💡 检测到命令: {command}\n", 'command')

        result = messagebox.askyesno("确认执行",
                                     f"是否执行以下命令？\n\n👉 {command}")
        if not result:
            self.append_to_chat("🌀 已取消执行\n", 'assistant')
            return

        def execute_thread():
            try:
                self.append_to_chat("🪶 正在执行...\n", 'assistant')

                if self.use_ssh and self.ssh_session:
                    result = execute_remote_command(command, self.system_type)
                else:
                    result = execute_command(command)

                self.append_to_chat(f"📋 执行结果:\n{result}\n", 'result')
                self.append_to_chat("─" * 60 + "\n", 'assistant')

            except Exception as e:
                self.append_to_chat(f"❌ 执行错误: {str(e)}\n", 'error')

        threading.Thread(target=execute_thread, daemon=True).start()

    def clear_history(self):
        """清除聊天历史"""
        self.chat_display.config(state='normal')
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state='disabled')
        self.append_to_chat("🧹 聊天历史已清除\n", 'assistant')

    def save_conversation(self):
        """保存对话到文件"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="保存对话"
            )
            if filename:
                content = self.chat_display.get("1.0", tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("成功", f"对话已保存到: {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")


def main():
    """主函数"""
    root = tk.Tk()
    app = YanDaoGUI(root)

    # 处理窗口关闭事件
    def on_closing():
        if app.ssh_session:
            close_ssh()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # 显示欢迎消息
    app.append_to_chat("🪶 欢迎使用言道OS图形界面版！\n", 'assistant')
    app.append_to_chat("💡 输入自然语言指令，AI将为您生成并执行命令\n", 'assistant')
    app.append_to_chat("🎯 功能: API/本地模型切换 | 语音输入 | SSH远程执行\n", 'assistant')
    app.append_to_chat("─" * 60 + "\n", 'assistant')

    root.mainloop()


if __name__ == "__main__":
    main()