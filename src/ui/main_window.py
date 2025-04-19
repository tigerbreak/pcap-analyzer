from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QFileDialog, 
                               QTextEdit, QLabel, QSplitter)
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from ..analyzer.packet_analyzer import PacketAnalyzer
from ..ai.deepseek_client import DeepSeekClient
from .chat_area import ChatArea

class SignalBridge(QObject):
    """用于在线程间传递信号的桥接类"""
    message_received = pyqtSignal(str, bool, str)  # 修改消息ID为字符串类型

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.packet_analyzer = PacketAnalyzer()
        self.ai_client = DeepSeekClient("sk-fizngoapnujlutpxoeugxlvitqwtupudnfeupudlvqjoqiyw")
        self.signal_bridge = SignalBridge()
        self.signal_bridge.message_received.connect(self.on_ai_message_received)
        self.active_messages = {}  # 存储活跃的消息气泡
        self.completed_messages = set()  # 存储已完成的消息ID
        self.message_counter = 0  # 用于生成唯一的消息ID
        self.init_ui()
        self.show_welcome_message()
        
    def init_ui(self):
        self.setWindowTitle('Pcap分析器与AI助手')
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建左侧面板（文件上传和分析结果）
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 文件上传按钮
        upload_button = QPushButton('选择PCAP文件')
        upload_button.clicked.connect(self.upload_file)
        left_layout.addWidget(upload_button)
        
        # 分析结果显示区域
        self.analysis_result = QTextEdit()
        self.analysis_result.setReadOnly(True)
        left_layout.addWidget(QLabel('分析结果：'))
        left_layout.addWidget(self.analysis_result)
        
        # 创建右侧面板（AI对话）
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 对话历史显示区域
        self.chat_area = ChatArea()
        right_layout.addWidget(QLabel('对话历史：'))
        right_layout.addWidget(self.chat_area)
        
        # 用户输入区域
        self.user_input = QTextEdit()
        self.user_input.setMaximumHeight(100)
        right_layout.addWidget(QLabel('输入问题：'))
        right_layout.addWidget(self.user_input)
        
        # 按钮面板
        button_panel = QHBoxLayout()
        
        # 发送按钮
        self.send_button = QPushButton('发送')
        self.send_button.clicked.connect(self.send_message)
        button_panel.addWidget(self.send_button)
        
        # 清除历史按钮
        clear_button = QPushButton('清除历史')
        clear_button.clicked.connect(self.clear_chat_history)
        button_panel.addWidget(clear_button)
        
        # 添加按钮面板到右侧布局
        button_widget = QWidget()
        button_widget.setLayout(button_panel)
        right_layout.addWidget(button_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # 设置分割器的初始大小
        splitter.setSizes([600, 600])
        
        main_layout.addWidget(splitter)
        
    def show_welcome_message(self):
        """显示欢迎信息和功能指南"""
        welcome_message = """欢迎使用Pcap分析器！

我是您的网络抓包分析助手，可以帮助您分析网络数据包。本工具支持以下分析功能：

1. 协议分析
   - TCP/UDP协议识别
   - 协议分布统计
   - 端口使用情况

2. 流量分析
   - 数据包大小统计
   - 总流量计算
   - 时间分布分析

3. IP分析
   - 源/目的IP统计
   - 最活跃IP识别
   - 端口使用统计

使用方法：
1. 点击"选择PCAP文件"按钮上传您的抓包文件
2. 系统会自动分析并显示：
   - 总数据包数
   - 协议分布
   - 活跃IP和端口
   - 流量统计

您可以问我：
- 如何获取PCAP文件？
- 这个分析结果中的协议分布是什么意思？
- 如何理解这些IP和端口统计？
- 某个特定的数据包代表什么含义？

请上传您的PCAP文件开始分析吧！"""
        self.chat_area.add_message(welcome_message, False)
        
    def upload_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "选择PCAP文件",
            "",
            "PCAP Files (*.pcap *.pcapng);;All Files (*)"
        )
        if file_name:
            # 显示正在分析的消息
            analyzing_bubble = self.chat_area.add_message("正在分析文件，请稍候...", False)
            
            if self.packet_analyzer.load_pcap(file_name):
                analysis_result = self.packet_analyzer.analyze()
                self.analysis_result.setText(analysis_result)
                
                # 显示分析完成的消息
                complete_message = """文件分析完成！分析结果已显示在左侧面板。

您可以：
1. 查看左侧的分析结果
2. 向我询问任何关于分析结果的问题
3. 让我解释特定的网络协议或流量模式

需要我为您解释什么吗？"""
                
                # 创建新的消息气泡
                complete_bubble = self.chat_area.add_message(complete_message, False)
                
            else:
                self.analysis_result.setText("文件加载失败，请检查文件格式是否正确。")
                error_bubble = self.chat_area.add_message("抱歉，文件加载失败。请确保您选择的是有效的PCAP文件。", False)
            
    def send_message(self):
        message = self.user_input.toPlainText().strip()
        if message:
            # 显示用户消息
            self.chat_area.add_message(message, True)
            self.user_input.clear()
            
            # 获取分析结果作为上下文
            context = self.analysis_result.toPlainText()
            
            # 生成唯一的消息ID
            self.message_counter += 1
            message_id = str(self.message_counter)
            print(f"生成新的消息ID: {message_id}")
            
            # 创建AI消息气泡并存储
            ai_bubble = self.chat_area.add_message("", False)
            
            # 存储消息气泡
            self.active_messages[message_id] = ai_bubble
            
            # 创建一个闭包来保持消息ID的值
            def callback(response: str, is_done: bool, msg_id: str = message_id):
                """创建一个闭包来保持消息ID的值"""
                print(f"回调函数被调用: msg_id={msg_id}, response={response[:50]}...")
                self.handle_ai_response(response, is_done, msg_id)
            
            # 异步调用AI获取回复
            self.ai_client.chat(message, context, callback, message_id)
            
    def handle_ai_response(self, response: str, is_done: bool, message_id: str):
        """处理AI响应的回调函数"""
        print(f"发送信号: message_id={message_id}, is_done={is_done}, response={response[:50]}...")
        # 使用信号发送消息到主线程
        self.signal_bridge.message_received.emit(response, is_done, message_id)
            
    def on_ai_message_received(self, message: str, is_done: bool, message_id: str):
        """在主线程中处理AI消息"""
        print(f"处理AI消息: message_id={message_id}, is_done={is_done}, message={message[:50]}...")
        print(f"当前活跃消息列表: {list(self.active_messages.keys())}")
        
        if message_id in self.active_messages:
            print(f"找到消息气泡: message_id={message_id}")
            ai_bubble = self.active_messages[message_id]
            
            if message:  # 如果有新内容
                print(f"追加文本到气泡: {message[:50]}...")
                ai_bubble.append_text(message)
            
            if is_done:  # 如果消息完成
                print(f"消息完成: message_id={message_id}")
                # 将消息ID添加到已完成集合
                self.completed_messages.add(message_id)
                # 从活跃消息中移除
                del self.active_messages[message_id]
        else:
            print(f"警告: 未找到消息气泡 message_id={message_id}")
            print(f"当前活跃消息: {list(self.active_messages.keys())}")
            
    def clear_chat_history(self):
        """清除对话历史"""
        # 清除聊天区域的所有消息
        self.chat_area.clear()
        # 清除活跃消息记录
        self.active_messages.clear()
        # 清除已完成消息记录
        self.completed_messages.clear()
        # 清除AI对话历史
        self.ai_client.clear_history()
        # 重新显示欢迎信息
        self.show_welcome_message() 