from scapy.all import rdpcap, IP, TCP, UDP
import pandas as pd
from datetime import datetime

class PacketAnalyzer:
    def __init__(self):
        self.packets = None
        self.df = None
        
    def load_pcap(self, file_path):
        """加载PCAP文件"""
        try:
            self.packets = rdpcap(file_path)
            return True
        except Exception as e:
            print(f"Error loading pcap file: {e}")
            return False
            
    def analyze(self):
        """分析数据包"""
        if not self.packets:
            return "请先加载PCAP文件"
            
        data = []
        for packet in self.packets:
            packet_info = self._analyze_packet(packet)
            if packet_info:
                data.append(packet_info)
                
        # 转换为DataFrame以便于分析
        self.df = pd.DataFrame(data)
        
        # 生成分析报告
        return self._generate_report()
        
    def _analyze_packet(self, packet):
        """分析单个数据包"""
        packet_info = {
            'time': datetime.fromtimestamp(packet.time).strftime('%Y-%m-%d %H:%M:%S'),
            'size': len(packet),
            'protocol': 'Unknown'
        }
        
        if IP in packet:
            packet_info.update({
                'src_ip': packet[IP].src,
                'dst_ip': packet[IP].dst,
                'protocol': packet[IP].proto
            })
            
            if TCP in packet:
                packet_info.update({
                    'protocol': 'TCP',
                    'src_port': packet[TCP].sport,
                    'dst_port': packet[TCP].dport
                })
            elif UDP in packet:
                packet_info.update({
                    'protocol': 'UDP',
                    'src_port': packet[UDP].sport,
                    'dst_port': packet[UDP].dport
                })
                
        return packet_info
        
    def _generate_report(self):
        """生成分析报告"""
        if self.df is None or len(self.df) == 0:
            return "没有找到可分析的数据包"
            
        report = []
        
        # 基本统计
        report.append(f"总数据包数: {len(self.df)}")
        report.append(f"总流量: {self.df['size'].sum() / 1024:.2f} KB")
        
        # 协议分布
        protocol_stats = self.df['protocol'].value_counts()
        report.append("\n协议分布:")
        for protocol, count in protocol_stats.items():
            report.append(f"{protocol}: {count} 个数据包")
            
        # IP统计
        if 'src_ip' in self.df.columns:
            top_src_ips = self.df['src_ip'].value_counts().head(5)
            report.append("\n最活跃的源IP:")
            for ip, count in top_src_ips.items():
                report.append(f"{ip}: {count} 个数据包")
                
        # 端口统计
        if 'src_port' in self.df.columns:
            top_ports = self.df['src_port'].value_counts().head(5)
            report.append("\n最常用的源端口:")
            for port, count in top_ports.items():
                report.append(f"端口 {port}: {count} 次使用")
                
        return "\n".join(report) 