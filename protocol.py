# protocol_server.py
import pickle
class Protocol:
    def __init__(self, socket):
        self.socket = socket

    def get_data(self):
        try:
            length = self.socket.recv(4).decode()
            data = self.socket.recv(int(length))
            return data
        except Exception as e:
            print(f"Receiving error: {e}")
            return None

    def send_data(self, data):
        try:
            length = str(len(data))
            zfill_length = length.zfill(4).encode()
            self.socket.sendall(zfill_length + data)
        except Exception as e:
            print(f"Sending error: {e}")

