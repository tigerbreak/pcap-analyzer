import requests
import json
from typing import List, Dict, Callable
import time
import threading

class DeepSeekClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.siliconflow.cn/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"  # 添加SSE支持
        }
        self.conversation_history: List[Dict] = []
        self.system_prompt = """你是这个抓包分析工具的AI助手，专注于帮助用户使用和理解本工具的功能。

你的主要职责是：
1. 解释工具的抓包分析功能：
   - 数据包统计（总包数、总流量）
   - 协议分布分析（TCP/UDP）
   - IP地址统计（源IP、目的IP）
   - 端口使用情况

2. 引导用户正确使用工具：
   - 帮助用户理解分析结果
   - 解释各项统计数据的含义
   - 说明特定协议或端口的作用

3. 回答用户关于分析结果的问题：
   - 基于上下文解释具体的分析数据
   - 帮助理解流量模式
   - 解释异常情况

注意：
- 只回答与本工具功能相关的问题
- 如果用户询问工具功能范围之外的问题，请引导用户关注工具现有功能
- 保持回答简洁、专业、实用"""

    def process_stream(self, response, message_id: str, full_message: str, callback: Callable[[str, bool, str], None]):
        """处理流式响应"""
        buffer = ""
        full_response = ""
        
        print(f"\n=== 开始处理流式响应 [message_id={message_id}] ===")
        try:
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                    
                try:
                    chunk_str = chunk.decode('utf-8', errors='replace')
                    print(f"接收到数据块: {len(chunk)} 字节")
                    
                    buffer += chunk_str
                    
                    if '\n' in buffer:
                        lines = buffer.split('\n')
                        buffer = lines[-1]  # 保留最后一个不完整的行
                        
                        for line in lines[:-1]:  # 处理完整的行
                            line = line.strip()
                            if not line:
                                continue
                                
                            if line.startswith('data: '):
                                data = line[6:]  # 去掉 'data: ' 前缀
                                
                                if data == '[DONE]':
                                    print(f"收到结束标记 [DONE] [message_id={message_id}]")
                                    # 更新对话历史
                                    self.conversation_history.append({
                                        "role": "user",
                                        "content": full_message
                                    })
                                    self.conversation_history.append({
                                        "role": "assistant",
                                        "content": full_response
                                    })
                                    # 发送完成信号
                                    if callback:
                                        callback("", True, message_id)
                                    print(f"=== 流式响应处理完成 [message_id={message_id}] ===\n")
                                    return
                                    
                                try:
                                    json_data = json.loads(data)
                                    print(f"解析的JSON数据: {json.dumps(json_data, ensure_ascii=False)[:100]}...")
                                    
                                    if "choices" in json_data and json_data["choices"]:
                                        delta = json_data["choices"][0].get("delta", {})
                                        content = delta.get("content", "")
                                        print(f"提取的content: {content}")
                                        
                                        if content:
                                            full_response += content
                                            if callback:
                                                print(f"调用callback，发送内容: {content[:50]}... [message_id={message_id}]")
                                                callback(content, False, message_id)
                                            else:
                                                print("警告: callback函数为None")
                                        else:
                                            print("警告: 没有提取到content内容")
                                    else:
                                        print(f"警告: JSON数据格式不符合预期: {json_data}")
                                        
                                except json.JSONDecodeError as je:
                                    print(f"JSON解析错误: {str(je)}")
                                    print(f"问题数据: {data}")
                                    continue
                                except Exception as e:
                                    print(f"处理JSON数据时出错: {str(e)}")
                                    print(f"问题数据: {data}")
                                    continue
                                    
                except UnicodeDecodeError as ude:
                    print(f"解码错误: {str(ude)}")
                    print(f"问题数据块: {chunk[:20]}")
                    continue
                    
        except Exception as e:
            error_msg = f"处理流时出错: {str(e)}"
            print(error_msg)
            if callback:
                callback(error_msg, True, message_id)
            
        if not full_response:
            print(f"警告: 整个处理过程没有生成任何响应内容 [message_id={message_id}]")
            
        print(f"=== 流式响应处理结束 [message_id={message_id}] ===\n")

    def chat(self, message: str, context: str = None, callback: Callable[[str, bool, str], None] = None, message_id: str = None) -> None:
        """
        与DeepSeek模型进行异步对话，支持流式输出
        
        Args:
            message: 用户输入的消息
            context: 额外的上下文信息（如分析结果）
            callback: 回调函数，用于接收AI的回复、完成状态和消息ID（字符串类型）
            message_id: 消息ID，如果不提供则自动生成
        """
        def chat_thread():
            try:
                # 构建完整的提示信息
                if context:
                    full_message = f"上下文信息：\n{context}\n\n用户问题：\n{message}"
                else:
                    full_message = message
                    
                # 构建对话历史
                messages = [
                    {"role": "system", "content": self.system_prompt}
                ]
                
                # 添加历史对话
                messages.extend(self.conversation_history)
                
                # 添加当前消息
                messages.append({"role": "user", "content": full_message})
                
                # 使用传入的消息ID或生成新的
                msg_id = message_id if message_id else str(id(full_message))
                print(f"DeepSeekClient - 使用消息ID: {msg_id}")
                
                # 准备请求数据
                request_data = {
                    "model": "deepseek-ai/DeepSeek-V3",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "stream": True
                }
                
                # 使用流式API调用
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=request_data,
                    stream=True
                )
                
                if response.status_code == 200:
                    # 处理流式响应
                    self.process_stream(response, msg_id, full_message, callback)
                else:
                    error_msg = f"API调用失败: {response.status_code} - {response.text}"
                    print(error_msg)
                    if callback:
                        callback(error_msg, True, msg_id)
                    
            except Exception as e:
                error_msg = f"错误: {str(e)}"
                print(error_msg)
                if callback:
                    callback(error_msg, True, msg_id if 'msg_id' in locals() else str(id(error_msg)))
        
        # 启动新线程处理API调用
        thread = threading.Thread(target=chat_thread)
        thread.daemon = True
        thread.start()
            
    def clear_history(self):
        """清除对话历史"""
        self.conversation_history = [] 