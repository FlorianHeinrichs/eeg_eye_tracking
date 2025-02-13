import json

from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, QThread

from .screen_connect import ConnectScreenWidget
from .screen_presentation import PresentationScreenWidget
from .worker import Worker


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.worker = None
        self.socket_thread = None

        # Layout
        self.setWindowTitle("Stimuli Presentation")
        self.showFullScreen()

        self.stacked_widget = QtWidgets.QStackedWidget()

        self.connect_screen_widget = ConnectScreenWidget()
        self.connect_screen_widget.clicked.connect(self.connect_to_server)
        self.stacked_widget.addWidget(self.connect_screen_widget)

        self.presentation_screen_widget = PresentationScreenWidget()
        self.presentation_screen_widget.stimulus_started.connect(
            lambda: self.worker.write.emit("stimulus-started")
        )
        self.presentation_screen_widget.stimulus_stopped.connect(
            lambda: self.worker.write.emit("stimulus-stopped")
        )
        self.presentation_screen_widget.streams_started.connect(
            lambda: self.worker.write.emit("streams-started")
        )
        self.presentation_screen_widget.streams_stopped.connect(
            lambda: self.worker.write.emit("streams-stopped")
        )
        self.presentation_screen_widget.step_changed.connect(
            lambda state: self.worker.write.emit(f"step:{state}")
        )
        self.stacked_widget.addWidget(self.presentation_screen_widget)

        self.setCentralWidget(self.stacked_widget)

    def closeEvent(self, event):
        if self.worker:
            self.worker.write.emit("stimulus-stopped")
            self.worker.write.emit("streams-stopped")
            self.worker.close_socket()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_R:
                self.connect_to_server(self.connect_screen_widget.ip_input.text())

    def connect_to_server(self, ip):
        print("Connecting to", ip)

        # Stop the current thread if it's running
        if self.socket_thread is not None and self.socket_thread.isRunning():
            self.worker.write.emit("stimulus-stopped")
            self.worker.write.emit("streams-stopped")
            self.worker.close_socket()
            self.socket_thread.quit()
            self.socket_thread.wait()

            self.worker.deleteLater()

        # Start the socket in a new thread
        self.worker = Worker(ip)
        self.worker.established_connection.connect(self.switch_to_presentation_screen)
        self.worker.lost_connection.connect(self.switch_to_connect_screen)
        self.worker.read.connect(self.handle_socket)

        self.socket_thread = QThread()
        self.worker.moveToThread(self.socket_thread)
        self.socket_thread.started.connect(self.worker.open_socket)
        self.socket_thread.start()

    def handle_socket(self, data: str):
        if data == "start-stimulus":
            self.presentation_screen_widget.start_stimulus()
        elif data == "stop-stimulus":
            self.presentation_screen_widget.stop_stimulus()
        elif data == "start-streams":
            self.presentation_screen_widget.start_streams()
        elif data == "stop-streams":
            self.presentation_screen_widget.stop_streams()
        elif (stimulus := data.split(":")[0]) in [
            "level-1-smooth",
            "level-1-saccades",
            "level-2-smooth",
            "level-2-saccades",
        ]:
            settings = data[len(stimulus) + 1 :]
            self.presentation_screen_widget.change_stimulus(
                stimulus, json.loads(settings)
            )

    def switch_to_connect_screen(self):
        self.stacked_widget.setCurrentIndex(0)
        self.presentation_screen_widget.clear_canvas()

    def switch_to_presentation_screen(self):
        self.stacked_widget.setCurrentIndex(1)
