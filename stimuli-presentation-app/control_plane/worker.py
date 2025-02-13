import socket

from PyQt6.QtCore import QObject, pyqtSignal


class Worker(QObject):
    received_connection = pyqtSignal(str)
    lost_connection = pyqtSignal()
    read = pyqtSignal(str)
    write = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.socket = None
        self.connection = None

        self.write.connect(self.handle_write)

    def open_socket(self):
        # Create a socket object
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to a specific IP and port
        self.socket.bind(("0.0.0.0", 49152))

        # Listen for incoming connections
        self.socket.listen(1)  # 1 is the maximum number of queued connections

        while self.socket.fileno() != -1:
            # Accept the connection when a client tries to connect
            try:
                c, addr = self.socket.accept()
                ip, port = addr
                print(f"Got connection from {ip}:{port}")

                self.connection = c
                self.received_connection.emit(ip)

                line = ""
                while True:
                    data = self.connection.recv(1024)
                    if not data:
                        break
                    print("Received", repr(data.decode()))
                    if b"\n" in data:
                        lines = (line + data.decode()).split("\n")
                        for line in lines[:-1]:
                            self.read.emit(line)
                        line = lines[-1]
                    else:
                        line += data.decode()
            except ConnectionResetError:
                # The client closed the connection
                self.lost_connection.emit()
            except ConnectionAbortedError:
                # The socket was closed and we tried to receive data
                break
            except OSError:
                # The socket was closed and we tried to accept a connection
                break

    def close_socket(self):
        if self.connection:
            self.connection.close()
        if self.socket:
            self.socket.close()

    def handle_write(self, data: str):
        # This method runs in the worker thread and handles the data
        try:
            if self.connection is None:
                raise ConnectionResetError
            # We add a newline character to the end of the message to signal the end of the message
            self.connection.sendall(f"{data}\n".encode())
            print("Sent", repr(f"{data}\n"))
        except ConnectionResetError:
            # The client closed the connection
            print("No Connection")
