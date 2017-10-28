import msgpack
import socket
import time
import logging
import sys

BUFFER_SIZE = 1024

class Connection:
    def __init__(self, ip="127.0.0.1", port="1234", timeout=None):
        self.ip = ip
        self.port = port
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(timeout)
        self.conn = None
        
    def write(self, obj):
        self.conn.sendall(msgpack.packb(obj) + bytes("\n", "UTF-8"))
        
    def read(self):
        data = []
        while True:
            buf = self.conn.recv(BUFFER_SIZE)
            if not buf or buf == "":
                break
            if buf[-1:] == bytes("\n", "UTF-8"):
                data += buf[:-1]
                break
            else:
                data += buf
        return msgpack.unpackb(bytes(data))
    
class Client(Connection):
    def __enter__(self):
        logging.debug("Trying to connect to " + self.ip + ":" + str(self.port) + "...")
        while True:
            try:
                self.socket.connect((self.ip, self.port))
                break
            except socket.error:
                self.socket.close()
                time.sleep(1)
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        logging.debug("Connection established")
        self.conn = self.socket
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.socket.close()

class Server(Connection):
    def __enter__(self):
        self.socket.bind((self.ip, self.port))
        self.socket.listen(1)
        logging.debug("Waiting for connection on " + self.ip + ":" + str(self.port) + "...")
        self.conn, _ = self.socket.accept()
        logging.debug("Connection established")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.conn.close()
        except UnboundLocalError:
            pass
        self.socket.close()
