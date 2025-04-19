from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, 
                               QScrollArea, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QColor, QPalette

class MessageBubble(QFrame):
    """消息气泡组件"""
    def __init__(self, is_user: bool, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.init_ui()
        
    def init_ui(self):
        # 设置气泡样式
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(0)
        
        # 创建文本编辑框
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFrameShape(QFrame.NoFrame)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.text_edit.setMinimumWidth(200)  # 设置最小宽度
        self.text_edit.setMaximumWidth(800)  # 设置最大宽度
        
        # 设置文本编辑框样式
        text_style = """
            QTextEdit {
                background-color: transparent;
                border: none;
                color: %s;
                font-size: 12pt;
                padding: 5px;
            }
        """ % ("white" if self.is_user else "black")
        self.text_edit.setStyleSheet(text_style)
        
        # 设置气泡样式
        if self.is_user:
            self.setStyleSheet("""
                QFrame {
                    background-color: #007AFF;
                    border-radius: 15px;
                    margin-left: 50px;
                    margin-right: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #E9E9EB;
                    border-radius: 15px;
                    margin-left: 10px;
                    margin-right: 50px;
                }
            """)
        
        layout.addWidget(self.text_edit)
        
    def set_text(self, text: str):
        """设置消息文本"""
        self.text_edit.setPlainText(text)
        self.adjust_size()
        
    def append_text(self, text: str):
        """追加消息文本"""
        print(f"MessageBubble.append_text: 追加文本: {text[:50]}...")
        current_text = self.text_edit.toPlainText()
        if current_text:
            self.text_edit.setPlainText(current_text + text)
        else:
            self.text_edit.setPlainText(text)
        self.text_edit.moveCursor(self.text_edit.textCursor().End)
        self.adjust_size()
        
    def adjust_size(self):
        """调整气泡大小"""
        # 获取文本大小
        doc = self.text_edit.document()
        doc.setTextWidth(self.text_edit.viewport().width())
        height = doc.size().height()
        
        # 设置文本编辑框的固定高度
        self.text_edit.setFixedHeight(int(height + 20))  # 添加一些padding
        
        # 更新气泡大小
        self.updateGeometry()

class ChatArea(QScrollArea):
    """聊天区域组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        # 设置滚动区域属性
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 设置滚动区域样式
        self.setStyleSheet("""
            QScrollArea {
                background-color: white;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #F0F0F0;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #CCCCCC;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical {
                height: 0px;
            }
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # 创建内容部件
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: white;")
        self.setWidget(self.content_widget)
        
        # 创建垂直布局
        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(15)  # 增加消息之间的间距
        
        # 添加弹性空间，使消息从顶部开始显示
        self.layout.addStretch()
        
    def add_message(self, text: str, is_user: bool) -> MessageBubble:
        """添加新消息"""
        # 创建消息气泡
        bubble = MessageBubble(is_user)
        bubble.set_text(text)
        
        # 添加到布局
        self.layout.insertWidget(self.layout.count() - 1, bubble)
        
        # 使用QTimer延迟滚动到底部，确保布局更新完成
        QTimer.singleShot(10, self.scroll_to_bottom)
        
        return bubble
        
    def scroll_to_bottom(self):
        """滚动到底部"""
        self.verticalScrollBar().setValue(
            self.verticalScrollBar().maximum()
        )
        
    def clear(self):
        """清除所有消息"""
        # 移除所有消息气泡
        while self.layout.count() > 1:  # 保留最后的弹性空间
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater() 