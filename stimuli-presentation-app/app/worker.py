import socket

from PyQt6.QtCore import QObject, pyqtSignal


class Worker(QObject):
    established_connection = pyqtSignal()
    lost_connection = pyqtSignal()
    read = pyqtSignal(str)
    write = pyqtSignal(str)

    def __init__(self, ip):
        super().__init__()

        self.ip = ip
        self.socket = None

        self.write.connect(self.handle_write)

    def open_socket(self):
        # Create a socket object
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the server's IP and port
        try:
            self.socket.connect((self.ip, 49152))
            print("Connected to the server")
            self.established_connection.emit()
        except ConnectionRefusedError:
            print("Connection refused")
            return
        except Exception as e:
            # Probably an invalid IP address
            print(e)
            return

        # Receive data from the server
        line = ""
        while True:
            try:
                data = self.socket.recv(1024)
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
                # The server closed the connection
                self.lost_connection.emit()
                break
            except ConnectionAbortedError:
                # The socket was closed and we tried to receive data
                break

        # Close the connection
        self.socket.close()

    def close_socket(self):
        if self.socket:
            self.socket.close()

    def handle_write(self, data: str):
        # This method runs in the worker thread and handles the data
        try:
            if self.socket is None:
                raise ConnectionResetError
            # We add a newline character to the end of the message to signal the end of the message
            self.socket.sendall(f"{data}\n".encode())
            print("Sent", repr(f"{data}\n"))
        except ConnectionResetError:
            # The server closed the connection
            print("No Connection")
        except ConnectionAbortedError:
            # The socket was closed and we tried to send data
            pass
        except OSError:
            # The socket was closed and we tried to send data
            pass
