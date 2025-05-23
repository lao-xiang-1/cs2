import cv2
import socket
import struct
import time
import mss
import numpy as np


class PPacket:
    def __init__(self, IP="0.0.0.0", Port=9888, PREFIX="ABAB", mode=0):
        self.MODE = mode # 0发送，1接受
        self.CHUNK_SIZE = 65000  # 每个数据包的最大字节大小
        self.IP = IP
        self.PORT = Port
        self.CHUNK_PREFIX = PREFIX  # ABAB是捕获截屏，AAAA是画框后的图片，BBBB是框，给到最后操作程序
        self.TEMP_PREFIX = PREFIX + "1"
        self.BUFFER_SIZE = 65536
        self.INDEX = 0  # 包序号
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if mode > 0:
            # self.socket.setblocking(0)
            self.socket.bind((IP, Port))
            print(f"Listening on {IP}:{Port}")
        self.image_buffers = [None]  # 用于存储不同 index 的数据包buffer[index][chunkID]=一个包的data
        self.chunk_counts = 0  # 记录每个 index 的总包数 count[index]=一个Index的包数

    def send(self, data, prefix=None):
        # 发送未编码的的np数据
        index = self.INDEX
        self.INDEX += 1
        self.INDEX = self.INDEX % 65535  # 超出重新计数，防止内存增长，因为python没有int限制
        self.CHUNK_PREFIX = self.CHUNK_PREFIX if prefix is None else prefix
        PRE = self.CHUNK_PREFIX
        server_ip = self.IP
        port = int(self.PORT)

        total_size = len(data)
        total_chunks = (total_size // self.CHUNK_SIZE) + 1
        print(f"Total size: {total_size} bytes, Total chunks: {total_chunks}")
        for i in range(total_chunks):
            start = i * self.CHUNK_SIZE
            end = start + self.CHUNK_SIZE
            chunk = data[start:end]

            # 包格式：PREFIX index:<序号>/<总包数>\n<数据>
            header = f"{PRE} {index}:{i}/{total_chunks}\n".encode()
            packet = header + chunk.tobytes()  # 这里的数据经过np的编码

            self.socket.sendto(packet, (server_ip, port))
            print(f"Sent chunk {i + 1}/{total_chunks}")


        print("Data sent successfully.")


    def recv(self, prefix=None):  # 外循环不能带入，不然所有业务都要在类里函数做，失去通用性，类函数功能要做到原子性
        # 返回接收到的数据（二进制流）， 需要np解码
        BUFFER_SIZE = self.BUFFER_SIZE
        self.CHUNK_PREFIX = self.CHUNK_PREFIX if prefix is None else prefix
        try:
            packet, addr = self.socket.recvfrom(BUFFER_SIZE)
        except Exception as e:
            # print(e)
            self.TEMP_PREFIX = "exception"
            return None
        self.TEMP_PREFIX = packet.split(b" ", 1)[0].decode()
        # 检查包头是否以 CHUNK_PREFIX 开头
        # if not packet.startswith(CHUNK_PREFIX.encode()):
        if self.CHUNK_PREFIX != self.TEMP_PREFIX:
            print("Invalid packet received, skipping.")
            return None

        # 解析 Header 信息
        header, chunk_data = packet.split(b" ", 1)[1].split(b"\n", 1)
        header_str = header.decode()
        index_str, chunk_info = header_str.split(":")
        index = int(index_str) % 65535 # 图片 ID
        chunk_idx, total_chunks = map(int, chunk_info.split("/"))

        print(f"Received chunk {chunk_idx + 1}/{total_chunks} for data {index} from {addr}")
        # if index not in image_buffers:  # 如果没有这个Key
        # self.image_buffers = [None] * total_chunks  # 用list替代dict，无法判断key是否存在，会直接清空已保存
        if self.image_buffers[0] is None or index != self.INDEX:
            # 当第一个是空的时候说明是新的包,或者丢包了，一直非空，但是序号变了，直接处理新包
            self.image_buffers = [None] * total_chunks
            self.INDEX = index
            self.chunk_counts = total_chunks

        # 保存数据块
        self.image_buffers[chunk_idx] = chunk_data
        # for part in self.image_buffers:
        #     print(part is not None)
        # 检查是否接收完整
        if all(part is not None for part in self.image_buffers):  # all:都为真则为真
            print(f"Image {index} fully received, reconstructing...")
            data = b"".join(self.image_buffers)
            self.image_buffers = [None]
            return data
        return None

    def get_prefix(self):
        return self.TEMP_PREFIX  # 注意奇怪包的情况

    def close(self):
        self.socket.close()