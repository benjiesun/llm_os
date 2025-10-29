# frent_gui.py
import sys
import re
import os
import subprocess
import threading
from functools import partial

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject,QTimer,pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QRadioButton, QButtonGroup,
    QComboBox, QTextEdit, QPlainTextEdit, QMessageBox, QDialog,
    QFormLayout, QSpinBox, QCheckBox, QGroupBox
)

# ----- 尝试导入项目已有模块（按你项目结构来） -----
try:
    from llm_api import get_command_from_api
except Exception:
    get_command_from_api = None

try:
    from llm_vllm import get_command_from_llm
except Exception:
    get_command_from_llm = None

try:
    import ssh_executor
    connect_ssh_fn = getattr(ssh_executor, "connect_ssh", None)
    execute_remote_command_fn = getattr(ssh_executor, "execute_remote_command", None)
    close_ssh_fn = getattr(ssh_executor, "close_ssh", None)
except Exception:
    ssh_executor = None
    connect_ssh_fn = None
    execute_remote_command_fn = None
    close_ssh_fn = None

# ----------------- Worker（在后台调用 LLM / 执行命令） -----------------
class ModelWorker(QThread):
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, provider: str, user_input: str, system_type: str, provider_settings: dict):
        super().__init__()
        self.provider = provider
        self.user_input = user_input
        self.system_type = system_type
        self.settings = provider_settings or {}

    def run(self):
        try:
            if self.provider == "local":
                if get_command_from_llm is None:
                    raise RuntimeError("本地 llm_vllm 模块未找到或未实现 get_command_from_llm")
                # 尝试不同签名：优先传入 local_addr，如果实现不接受则回退
                try:
                    response = get_command_from_llm(self.user_input, self.system_type, self.settings.get("local_addr"))
                except TypeError:
                    # 回退到 2-arg 签名
                    response = get_command_from_llm(self.user_input, self.system_type)
            else:
                if get_command_from_api is None:
                    raise RuntimeError("远程 API 模块未找到或未实现 get_command_from_api")
                # 尝试以最完整签名调用： (user_input, system_type, api_base, api_key, api_model)
                try:
                    response = get_command_from_api(
                        self.user_input,
                        self.system_type,
                        self.settings.get("api_base"),
                        self.settings.get("api_key"),
                        self.settings.get("api_model")
                    )
                except TypeError:
                    # 回退 2-arg 调用 (user_input, system_type)
                    try:
                        response = get_command_from_api(self.user_input, self.system_type)
                    except TypeError:
                        # 最后尝试将 settings 当作关键字参数（如果实现支持）
                        try:
                            kwargs = {"system_type": self.system_type, **self.settings}
                            response = get_command_from_api(self.user_input, **kwargs)
                        except Exception as e:
                            raise RuntimeError(f"调用 get_command_from_api 时出错：{e}")
            if response is None:
                response = ""
            self.finished_signal.emit(response)
        except Exception as e:
            self.error_signal.emit(str(e))


class LocalExecWorker(QThread):
    line_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, command: str):
        super().__init__()
        self.command = command

    def run(self):
        try:
            proc = subprocess.Popen(
                self.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            output_accum = []
            if proc.stdout:
                for line in proc.stdout:
                    self.line_signal.emit(line.rstrip("\n"))
                    output_accum.append(line)
            proc.wait()
            final = "".join(output_accum)
            self.finished_signal.emit(final)
        except Exception as e:
            self.error_signal.emit(str(e))


class RemoteExecWorker(QThread):
    chunk_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, command: str, system_type: str, ssh_client=None):
        super().__init__()
        self.command = command
        self.system_type = system_type
        self.ssh_client = ssh_client

    def run(self):
        try:
            if execute_remote_command_fn is None:
                raise RuntimeError("未找到 ssh_executor.execute_remote_command 函数")
            res = execute_remote_command_fn(self.command, self.system_type)
            if isinstance(res, str):
                self.finished_signal.emit(res)
            else:
                self.finished_signal.emit(str(res))
        except Exception as e:
            self.error_signal.emit(str(e))

# ----------------- SSH 参数输入对话框 -----------------
class SSHDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SSH 连接设置")
        self.setModal(True)
        form = QFormLayout()

        self.host_input = QLineEdit()
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(22)
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)

        self.os_combo = QComboBox()
        self.os_combo.addItems(["Linux", "Windows", "Unix"])
        print(f"test1: {self.os_combo.currentText()}")
        form.addRow("主机 (host):", self.host_input)
        form.addRow("端口 (port):", self.port_input)
        form.addRow("用户名:", self.user_input)
        form.addRow("密码:", self.pass_input)
        form.addRow("远程系统类型:", self.os_combo)

        btn_box = QHBoxLayout()
        self.btn_ok = QPushButton("连接并保存")
        self.btn_cancel = QPushButton("取消")
        btn_box.addWidget(self.btn_ok)
        btn_box.addWidget(self.btn_cancel)

        vbox = QVBoxLayout()
        vbox.addLayout(form)
        vbox.addLayout(btn_box)
        self.setLayout(vbox)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def get_values(self):
        return {
            "host": self.host_input.text().strip(),
            "port": int(self.port_input.value()),
            "username": self.user_input.text().strip(),
            "password": self.pass_input.text(),
            "system_type": self.os_combo.currentText()
        }

# ----------------- 主窗口 -----------------
class MainWindow(QMainWindow):

    voice_text_signal = pyqtSignal(str)
    voice_done_signal = pyqtSignal()


    def __init__(self):
        super().__init__()
        self.setWindowTitle("言道 OS 前端 — PyQt5")
        self.resize(1000, 720)

        self.ssh_client = None
        self.remote_system_type = None
        self.is_recording = False

        # 顶部设置区
        top_widget = QWidget()
        top_layout = QHBoxLayout()
        top_widget.setLayout(top_layout)

        # 运行模式选择
        mode_groupbox = QGroupBox("执行模式")
        mg_layout = QVBoxLayout()
        self.rb_local = QRadioButton("在本机运行")
        self.rb_ssh = QRadioButton("通过 SSH 在远端运行")
        self.rb_local.setChecked(True)
        mg_layout.addWidget(self.rb_local)
        mg_layout.addWidget(self.rb_ssh)
        mode_groupbox.setLayout(mg_layout)
        top_layout.addWidget(mode_groupbox)

        # 模型类型 & 配置面板
        provider_groupbox = QGroupBox("模型提供者 & 配置")
        pg_layout = QVBoxLayout()

        provider_row = QHBoxLayout()
        provider_row.addWidget(QLabel("Provider:"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["api", "local"])
        provider_row.addWidget(self.provider_combo)
        provider_row.addStretch()
        pg_layout.addLayout(provider_row)

        # API 配置区（只在 provider == api 时可见）
        self.api_cfg_widget = QWidget()
        api_layout = QFormLayout()
        self.api_base_input = QLineEdit()
        self.api_base_input.setPlaceholderText("https://api.deepseek.com/v1")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_model_input = QLineEdit()
        self.api_model_input.setPlaceholderText("deepseek-chat")
        api_layout.addRow("API_BASE:", self.api_base_input)
        api_layout.addRow("API_KEY:", self.api_key_input)
        api_layout.addRow("API_MODEL:", self.api_model_input)
        self.api_cfg_widget.setLayout(api_layout)
        pg_layout.addWidget(self.api_cfg_widget)

        # Local 模型配置区（只在 provider == local 时可见）
        self.local_cfg_widget = QWidget()
        local_layout = QFormLayout()
        self.local_addr_input = QLineEdit()
        self.local_addr_input.setPlaceholderText("例如：http://127.0.0.1:8000 或 unix:///path/to/socket")
        local_layout.addRow("本地模型地址:", self.local_addr_input)
        self.local_cfg_widget.setLayout(local_layout)
        pg_layout.addWidget(self.local_cfg_widget)

        provider_groupbox.setLayout(pg_layout)
        top_layout.addWidget(provider_groupbox)

        # 远程连接按钮 & 当前状态
        conn_layout = QVBoxLayout()
        self.btn_ssh_cfg = QPushButton("SSH 设置 / 连接")
        self.lbl_ssh_status = QLabel("SSH: 未连接")
        conn_layout.addWidget(self.btn_ssh_cfg)
        conn_layout.addWidget(self.lbl_ssh_status)
        top_layout.addLayout(conn_layout)

        # 系统类型（可手动覆盖）
        sys_layout = QVBoxLayout()
        sys_layout.addWidget(QLabel("本机 / 指定系统类型（覆盖）:"))
        self.sys_combo = QComboBox()
        self.sys_combo.addItems(["Auto (detect)", "Linux", "Windows", "Unix"])
        print(f"test2: {self.sys_combo.currentText()}")
        sys_layout.addWidget(self.sys_combo)
        top_layout.addLayout(sys_layout)

        # 中央：指令输入与输出
        central = QWidget()
        central_layout = QVBoxLayout()
        central.setLayout(central_layout)

        input_box = QGroupBox("自然语言指令")
        inp_layout = QVBoxLayout()
        self.input_text = QLineEdit()
        self.input_text.setPlaceholderText("在此输入自然语言，例如：'帮我查看 /var/log/syslog 最近 50 行'，回车发送或点击“发送”")
        self.btn_send = QPushButton("发送到模型")
        self.btn_voice = QPushButton("语音输入")
        send_row = QHBoxLayout()
        send_row.addWidget(self.input_text)
        send_row.addWidget(self.btn_send)
        send_row.addWidget(self.btn_voice)
        inp_layout.addLayout(send_row)
        input_box.setLayout(inp_layout)

        output_box = QGroupBox("模型回应 / 终端输出")
        out_layout = QVBoxLayout()
        self.model_resp = QPlainTextEdit()
        self.model_resp.setReadOnly(True)
        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setPlaceholderText("命令执行输出会在此处滚动显示...")
        out_layout.addWidget(QLabel("模型回答："))
        out_layout.addWidget(self.model_resp, stretch=1)
        out_layout.addWidget(QLabel("执行输出："))
        out_layout.addWidget(self.terminal, stretch=2)
        output_box.setLayout(out_layout)

        # 底部快捷按钮
        bottom_row = QHBoxLayout()
        self.btn_clear = QPushButton("清空终端")
        self.btn_disconnect = QPushButton("断开 SSH（若已连接）")
        bottom_row.addWidget(self.btn_clear)
        bottom_row.addStretch()
        bottom_row.addWidget(self.btn_disconnect)

        central_layout.addWidget(input_box)
        central_layout.addWidget(output_box)
        central_layout.addLayout(bottom_row)

        # 总体布局
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        main_layout.addWidget(top_widget)
        main_layout.addWidget(central)
        self.setCentralWidget(main_widget)

        # 信号连接
        self.provider_combo.currentIndexChanged.connect(self.on_provider_changed)
        self.btn_ssh_cfg.clicked.connect(self.open_ssh_dialog)
        self.btn_send.clicked.connect(self.on_send_clicked)
        self.btn_voice.clicked.connect(self.on_voice_clicked)
        self.input_text.returnPressed.connect(self.on_send_clicked)
        self.btn_clear.clicked.connect(self.terminal.clear)
        self.btn_disconnect.clicked.connect(self.disconnect_ssh)
        self.voice_text_signal.connect(self._apply_voice_text)
        self.voice_done_signal.connect(self._reset_voice_ui)

        # 初始化可见性
        self.on_provider_changed()

    # ---------- Provider 面板可见性 ----------
    def on_provider_changed(self):
        provider = self.provider_combo.currentText()
        if provider == "api":
            self.api_cfg_widget.setVisible(True)
            self.local_cfg_widget.setVisible(False)
        else:
            self.api_cfg_widget.setVisible(False)
            self.local_cfg_widget.setVisible(True)

    # ---------- SSH 处理 ----------
    def open_ssh_dialog(self):
        dlg = SSHDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            host = vals["host"]; port = vals["port"]
            username = vals["username"]; password = vals["password"]
            print(f"SSH: 连接中 -> {host}:{port} ...")
            system_type = vals["system_type"]
            self.remote_system_type = system_type
            self.lbl_ssh_status.setText(f"SSH: 连接中 -> {host}:{port} ...")
            QApplication.processEvents()
            try:
                if connect_ssh_fn is None:
                    raise RuntimeError("未找到 ssh_executor.connect_ssh")
                try:
                    ssh_client = connect_ssh_fn(host, port, username, password)
                except TypeError:
                    ssh_client = connect_ssh_fn()
                self.ssh_client = ssh_client
                self.lbl_ssh_status.setText(f"SSH: 已连接到 {host}:{port}")
            except Exception as e:
                self.ssh_client = None
                self.lbl_ssh_status.setText(f"SSH: 连接失败 — {e}")
                QMessageBox.warning(self, "SSH 连接失败", f"无法连接到远程主机：\n{e}")

    def disconnect_ssh(self):
        if self.ssh_client and close_ssh_fn:
            try:
                close_ssh_fn(self.ssh_client)
            except Exception:
                pass
        self.ssh_client = None
        self.lbl_ssh_status.setText("SSH: 未连接")

    # ---------- 发送到模型 ----------
    def on_send_clicked(self):
        user_text = self.input_text.text().strip()
        if not user_text:
            return
        provider = self.provider_combo.currentText()
        # 决定 system_type：优先远程已选，或手动下拉选择，或自动平台检测
        if self.rb_ssh.isChecked():
            if not self.ssh_client:
                QMessageBox.warning(self, "未连接 SSH", "你选择了 SSH 模式，但尚未连接远程主机，请先点击“SSH 设置 / 连接”。")
                return
            system_type = self.remote_system_type or "Linux"
        else:
            sys_choice = self.sys_combo.currentText()
            if sys_choice == "Auto (detect)":
                import platform
                system_type = platform.system()
            else:
                system_type = sys_choice

        # 构建 provider_settings
        provider_settings = {}
        if provider == "api":
            provider_settings["api_base"] = self.api_base_input.text().strip() or None
            provider_settings["api_key"] = self.api_key_input.text().strip() or None
            provider_settings["api_model"] = self.api_model_input.text().strip() or None
        else:
            provider_settings["local_addr"] = self.local_addr_input.text().strip() or None

        # 清理旧输出
        self.model_resp.clear()
        self.terminal.appendPlainText(f">>> 发送请求到模型（{provider}），系统类型：{system_type}\n")

        # 调用后台模型线程（传入 provider_settings）
        self.model_worker = ModelWorker(provider, user_text, system_type, provider_settings)
        self.model_worker.finished_signal.connect(self.on_model_response)
        self.model_worker.error_signal.connect(lambda e: self.append_model_error(e))
        self.model_worker.start()
        self.btn_send.setEnabled(False)

        self.input_text.clear()

    def append_model_error(self, e):
        self.btn_send.setEnabled(True)
        self.model_resp.appendPlainText(f"[模型调用错误] {e}")

    
    def on_model_response(self, response: str):
        self.btn_send.setEnabled(True)

        # ========== 执行命令 ==========
        if "EXECUTE:" in response:
            cmd = response.split("EXECUTE:")[1].strip()
            lines = cmd.splitlines()
            desc = lines[0] if lines else "执行命令"
            self.model_resp.appendPlainText(f"言道将为您做：{desc}\n")

            command = "\n".join(lines[1:]) if len(lines) > 1 else ""
            r = QMessageBox.question(
                self, "确认执行",
                f"是否执行以下命令？\n\n{command}\n\n（在 SSH 模式下，命令将在远程执行）",
                QMessageBox.Yes | QMessageBox.No
            )
            if r != QMessageBox.Yes:
                self.terminal.appendPlainText("🌀 已取消执行命令。\n")
                return

            self.terminal.appendPlainText(f"🪶 正在执行: {command}\n")

            if self.rb_ssh.isChecked():
                self.remote_exec_worker = RemoteExecWorker(command, self.remote_system_type or "Linux", ssh_client=self.ssh_client)
                self.remote_exec_worker.chunk_signal.connect(lambda s: self.terminal.appendPlainText(s))
                self.remote_exec_worker.finished_signal.connect(lambda _: self.terminal.appendPlainText("\n[远程执行结束]\n"))
                self.remote_exec_worker.error_signal.connect(lambda e: self.terminal.appendPlainText(f"[远程执行错误] {e}"))
                self.remote_exec_worker.start()
            else:
                self.local_exec_worker = LocalExecWorker(command)
                self.local_exec_worker.line_signal.connect(lambda ln: self.terminal.appendPlainText(ln))
                self.local_exec_worker.finished_signal.connect(lambda _: self.terminal.appendPlainText("\n[本地执行结束]\n"))
                self.local_exec_worker.error_signal.connect(lambda e: self.terminal.appendPlainText(f"[本地执行错误] {e}"))
                self.local_exec_worker.start()

        # ========== 生成脚本 ==========
        elif "SCRIPT:" in response:
            # --- 提取脚本块 ---
            script_block = response.split("SCRIPT:")[1].strip().splitlines()
            filename = script_block[0].strip() if len(script_block) > 0 else "script.py"
            raw_location = script_block[1].strip() if len(script_block) > 1 else ""
            description = script_block[2].strip() if len(script_block) > 2 else "无描述"

            # --- 自动路径识别 ---
            if raw_location in ["当前路径", "当前目录", "当前文件夹", "."]:
                location = os.getcwd()
            elif raw_location:
                location = raw_location if os.path.isabs(raw_location) else os.path.join(os.getcwd(), raw_location)
            else:
                location = os.getcwd()

            # --- 提取代码内容 ---
            match = re.search(r"```(?:python|bash)?\n([\s\S]*?)```", response)
            if match:
                script_content = match.group(1).strip()
            else:
                # 清理 <script> 标签
                script_content = "\n".join(script_block[3:])
                script_content = re.sub(r"</?script>", "", script_content).strip()

            # --- 展示信息 ---
            self.model_resp.appendPlainText(f"即将生成脚本文件：{filename}")
            self.model_resp.appendPlainText(f"生成位置：{location}")
            self.model_resp.appendPlainText(f"脚本说明：{description}")
            self.model_resp.appendPlainText("内容预览：\n" + "─" * 40 + f"\n{script_content}\n" + "─" * 40 + "\n")

            # --- 确认保存 ---
            r = QMessageBox.question(self, "保存脚本", f"是否保存脚本文件 '{filename}'？", QMessageBox.Yes | QMessageBox.No)
            if r != QMessageBox.Yes:
                self.terminal.appendPlainText("❎ 已取消脚本生成。\n")
                return

            os.makedirs(location, exist_ok=True)
            if not re.search(r"\.\w+$", filename):
                filename += ".py"
            save_path = os.path.join(location, filename)

            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(script_content)
                self.terminal.appendPlainText(f"✅ 已生成脚本文件: {save_path}\n")
            except Exception as e:
                self.terminal.appendPlainText(f"❌ 保存失败: {e}\n")
                return

            # --- 执行脚本 ---
            run_now = QMessageBox.question(self, "执行脚本", "是否立即执行该脚本？", QMessageBox.Yes | QMessageBox.No)
            if run_now == QMessageBox.Yes:
                if filename.endswith(".py"):
                    command = f"python3 {save_path}"
                elif filename.endswith(".sh"):
                    command = f"bash {save_path}"
                else:
                    command = f"./{save_path}"

                self.terminal.appendPlainText(f"🪶 正在执行脚本: {command}\n")
                if self.rb_ssh.isChecked():
                    self.remote_exec_worker = RemoteExecWorker(command, self.remote_system_type or "Linux", ssh_client=self.ssh_client)
                    self.remote_exec_worker.chunk_signal.connect(lambda s: self.terminal.appendPlainText(s))
                    self.remote_exec_worker.finished_signal.connect(lambda _: self.terminal.appendPlainText("\n[远程脚本执行结束]\n"))
                    self.remote_exec_worker.error_signal.connect(lambda e: self.terminal.appendPlainText(f"[远程脚本执行错误] {e}"))
                    self.remote_exec_worker.start()
                else:
                    self.local_exec_worker = LocalExecWorker(command)
                    self.local_exec_worker.line_signal.connect(lambda ln: self.terminal.appendPlainText(ln))
                    self.local_exec_worker.finished_signal.connect(lambda _: self.terminal.appendPlainText("\n[脚本执行结束]\n"))
                    self.local_exec_worker.start()

            else:
                self.terminal.appendPlainText("✅ 已保存脚本，但未执行。\n")

        # ========== 普通回复 ==========
        elif "REPLY:" in response:
            reply_content = response.split("REPLY:")[1].strip()
            self.model_resp.appendPlainText(reply_content)

        # ========== 其他情况 ==========
        else:
            self.model_resp.appendPlainText(f"❌ 未检测到可识别内容，请重试。\n")
            print("=== RAW RESPONSE START ===")
            print(response)
            print("=== RAW RESPONSE END ===")


    def _apply_voice_text(self, text: str):
        if text:
            cur = self.input_text.text()
            self.input_text.setText((cur + " " + text).strip())
            self.model_resp.appendPlainText(f"💬 语音识别: {text}\n")
        else:
            self.model_resp.appendPlainText("😕 语音识别失败\n")

    def _reset_voice_ui(self):
        self.is_recording = False
        self.btn_voice.setText("语音输入")
        self.btn_voice.setEnabled(True)

    def on_voice_clicked(self):
        if self.is_recording:
            return
        self.is_recording = True
        self.btn_voice.setText("录音中...")
        self.btn_voice.setEnabled(False)
        self.model_resp.appendPlainText("🎧 正在录音，请说话...\n")

        def worker():
            try:
                from voice_input import record_once
                text = record_once()  # 阻塞的外部录音/识别
                # 通过信号将结果发送回主线程（比 QTimer.singleShot 更可靠）
                try:
                    self.voice_text_signal.emit(text or "")
                except Exception:
                    # 如果信号发射失败，仍尝试在 model_resp 打印错误
                    pass
            except Exception as e:
                try:
                    self.voice_text_signal.emit("")  # 通知识别失败
                    self.model_resp.appendPlainText(f"❌ 语音输入错误: {e}\n")
                except Exception:
                    pass
            finally:
                try:
                    self.voice_done_signal.emit()
                except Exception:
                    pass

        threading.Thread(target=worker, daemon=True).start()
def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
