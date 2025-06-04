import pickle
import socket
import threading
import protocol


class GameServer:
    def __init__(self, host="0.0.0.0", port=5555):
        self.host_ip = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host_ip, self.port))
        self.server_socket.listen(2)
        print(f"Server started on {self.host_ip}:{self.port}. Waiting for players...")

        self.players_data = [{}, {}]
        self.connected_event = threading.Event()
        self.connected_clients = [None, None]
        self.player_count = 0

    def handle_client(self, client_socket, player_id):
        print(f"Player {player_id} connected.")

        pro = protocol.Protocol(client_socket)
        pro.send_data(str(player_id).encode())

        self.connected_clients[player_id] = client_socket
        if all(self.connected_clients):
            self.connected_event.set()

        self.connected_event.wait()

        try:
            pro.send_data("start".encode())
        except Exception as e:
            print(f"Failed to send start to player {player_id}: {e}")
            return

        try:
            while True:
                raw_data = pro.get_data()

                if not raw_data:
                    print(f"Player {player_id} disconnected.")
                    break

                # Handle quit signal
                if raw_data == b"quit":
                    print(f"Player {player_id} quit the game.")
                    other_socket = self.connected_clients[1 - player_id]
                    if other_socket:
                        try:
                            other_socket.sendall(b"quit")
                        except:
                            pass
                    break

                try:
                    data = pickle.loads(raw_data)
                    self.players_data[player_id] = data
                    enemy_data = self.players_data[1 - player_id]
                    pro.send_data(pickle.dumps(enemy_data))
                except Exception as e:
                    print(f"Error processing data from player {player_id}: {e}")
                    break

        except Exception as e:
            print(f"Player {player_id} caused error: {e}")

        self.players_data[player_id] = {}
        client_socket.close()

    def start(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connected to {addr}")

            if self.player_count < 2:
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, self.player_count),
                    daemon=True
                )
                thread.start()
                self.player_count += 1
            else:
                print("Server full. Rejecting new connection.")
                client_socket.send(b"Server full")
                client_socket.close()


if __name__ == "__main__":
    server = GameServer()
    server.start()