import json
import socket

from pylsl import StreamInlet, resolve_streams
from PyQt6 import QtWidgets
from PyQt6.QtCore import QThread, Qt

from .canvas import Canvas
from .window_options import OptionsWindow
from .worker import Worker


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        ip = socket.gethostbyname(socket.gethostname())

        self.setWindowTitle(f"Control Plane ({ip})")

        # Add options screen
        self.options_window = OptionsWindow()
        self.options_window.options_changed.connect(self.update_options)

        self.update_options()

        # Layout

        layout = QtWidgets.QHBoxLayout()

        layout2 = QtWidgets.QVBoxLayout()

        self.step = 0
        self.total_steps = 0
        self.step_label = QtWidgets.QLabel(f"{self.step}/{self.total_steps}")
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout2.addWidget(self.step_label)

        self.canvas = Canvas()
        self.canvas.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        layout2.addWidget(self.canvas)

        layout.addLayout(layout2)

        ### Button Panel

        layout3 = QtWidgets.QVBoxLayout()

        # Connection status label
        connection_status_label = QtWidgets.QLabel(
            "<span style='color: red;'>●</span>  Not connected"
        )
        connection_status_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Maximum,
        )
        self.connection_status_label = connection_status_label
        layout3.addWidget(self.connection_status_label)

        # Disconnect button
        disconnect_button = QtWidgets.QPushButton("Disconnect")
        disconnect_button.clicked.connect(self.start_socket)
        layout3.addWidget(disconnect_button)

        layout3.addSpacing(20)

        # A level-1-smooth button
        level_1_smooth_button = QtWidgets.QPushButton("Level 1 Smooth")
        level_1_smooth_button.clicked.connect(self.change_to_level_1_smooth)
        layout3.addWidget(level_1_smooth_button)

        # A level-1-saccades button
        level_1_saccades_button = QtWidgets.QPushButton("Level 1 Saccades")
        level_1_saccades_button.clicked.connect(self.change_to_level_1_saccades)
        layout3.addWidget(level_1_saccades_button)

        # A level-2-smooth button
        level_2_smooth_button = QtWidgets.QPushButton("Level 2 Smooth")
        level_2_smooth_button.clicked.connect(self.change_to_level_2_smooth)
        layout3.addWidget(level_2_smooth_button)

        # A level-2-saccades button
        level_2_saccades_button = QtWidgets.QPushButton("Level 2 Saccades")
        level_2_saccades_button.clicked.connect(self.change_to_level_2_saccades)
        layout3.addWidget(level_2_saccades_button)

        layout3.addSpacing(20)

        # Streams status Label
        self.stream_label = QtWidgets.QLabel(
            "Stream: <span style='color: red;'>Stopped</span>"
        )
        self.stream_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Maximum,
        )
        layout3.addWidget(self.stream_label)

        # Start and stop buttons for the streams
        self.start_streams_button = QtWidgets.QPushButton("Start")
        self.start_streams_button.clicked.connect(self.start_streams)
        layout3.addWidget(self.start_streams_button)

        self.stop_streams_button = QtWidgets.QPushButton("Stop")
        self.stop_streams_button.setDisabled(True)
        self.stop_streams_button.clicked.connect(self.stop_streams)
        layout3.addWidget(self.stop_streams_button)

        layout3.addSpacing(20)

        # A "search for streams" button
        search_button = QtWidgets.QPushButton("Search for streams")
        search_button.clicked.connect(self.search_for_streams)
        layout3.addWidget(search_button)

        # A list of checkboxes for each stream
        self.stream_checkboxes = StreamCheckboxes(self.canvas)
        self.stream_checkboxes.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        layout3.addWidget(self.stream_checkboxes)

        layout3.addSpacing(20)

        # Stimulus status label
        self.stimulus_label = QtWidgets.QLabel(
            "Stimulus: <span style='color: red;'>Stopped</span>"
        )
        self.stimulus_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Maximum,
        )
        layout3.addWidget(self.stimulus_label)

        # Start and stop buttons for the stimulus
        self.start_stimulus_button = QtWidgets.QPushButton("Start")
        self.start_stimulus_button.clicked.connect(self.start_stimulus)
        layout3.addWidget(self.start_stimulus_button)

        self.stop_stimulus_button = QtWidgets.QPushButton("Stop")
        self.stop_stimulus_button.setDisabled(True)
        self.stop_stimulus_button.clicked.connect(self.stop_stimulus)
        layout3.addWidget(self.stop_stimulus_button)

        layout3.addSpacing(20)

        # Add options button

        options_button = QtWidgets.QPushButton("Settings")
        options_button.clicked.connect(self.options_window.show)
        layout3.addWidget(options_button)

        # will fill in the remaining vertical space of the button panel
        layout3.addWidget(QtWidgets.QWidget())

        layout.addLayout(layout3)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)

        # Start the socket in a new thread
        self.socket_thread = None
        self.start_socket()

    def closeEvent(self, event):
        if self.worker:
            self.worker.write.emit("stop-stimulus")
            self.worker.write.emit("stop-streams")
            self.worker.close_socket()
        event.accept()

    def start_socket(self):
        # Stop the socket if it is already running
        if self.socket_thread is not None and self.socket_thread.isRunning():
            self.worker.write.emit("stop-stimulus")
            self.worker.write.emit("stop-streams")
            self.worker.close_socket()
            self.socket_thread.quit()
            self.socket_thread.wait()

            self.worker.deleteLater()

        self.lost_connection()

        # Start the socket in a new thread
        self.worker = Worker()
        self.worker.received_connection.connect(self.received_connection)
        self.worker.lost_connection.connect(self.lost_connection)
        self.worker.read.connect(self.handle_socket)

        self.socket_thread = QThread()
        self.worker.moveToThread(self.socket_thread)
        self.socket_thread.started.connect(self.worker.open_socket)
        self.socket_thread.start()

    def handle_socket(self, data: str):
        if data == "stimulus-started":
            self.start_stimulus_button.setDisabled(True)
            self.stop_stimulus_button.setDisabled(False)
            self.stimulus_label.setText(
                "Stimulus: <span style='color: green;'>Running</span>"
            )
        elif data == "stimulus-stopped":
            self.start_stimulus_button.setDisabled(False)
            self.stop_stimulus_button.setDisabled(True)
            self.stimulus_label.setText(
                "Stimulus: <span style='color: red;'>Stopped</span>"
            )
        elif data == "streams-started":
            self.start_streams_button.setDisabled(True)
            self.stop_streams_button.setDisabled(False)
            self.stream_label.setText(
                "Stream: <span style='color: green;'>Running</span>"
            )
        elif data == "streams-stopped":
            self.start_streams_button.setDisabled(False)
            self.stop_streams_button.setDisabled(True)
            self.stream_label.setText(
                "Stream: <span style='color: red;'>Stopped</span>"
            )
        elif data.startswith("step:"):
            self.step = data[5:]
            self.step_label.setText(f"{self.step}/{self.total_steps}")

    def received_connection(self, ip):
        self.connection_status_label.setText(
            f"<span style='color: green;'>●</span>  {ip}"
        )

    def lost_connection(self):
        self.connection_status_label.setText(
            "<span style='color: red;'>●</span>  Not connected"
        )

    def start_stimulus(self):
        self.worker.write.emit("start-stimulus")

    def stop_stimulus(self):
        self.worker.write.emit("stop-stimulus")

    def start_streams(self):
        self.worker.write.emit("start-streams")
        self.search_for_streams()

    def stop_streams(self):
        if self.canvas.gaze_position_inlet:
            del self.canvas.gaze_position_inlet
            self.canvas.gaze_position_inlet = None
        if self.canvas.stimulus_inlet:
            del self.canvas.stimulus_inlet
            self.canvas.stimulus_inlet = None
        self.worker.write.emit("stop-streams")

    def search_for_streams(self):
        streams = resolve_streams()
        self.stream_checkboxes.update_streams(streams)

    def change_to_level_1_smooth(self):
        self.stop_stimulus()
        self.stop_streams()

        options = {
            "curves": ";".join([",".join(map(str, curve)) for curve in self.curves_1]),
            **self.settings,
        }
        self.worker.write.emit(f"level-1-smooth:{json.dumps(options)}")

        self.total_steps = len(self.curves_1)
        self.step_label.setText(f"{self.step}/{self.total_steps}")

    def change_to_level_1_saccades(self):
        self.stop_stimulus()
        self.stop_streams()

        options = {
            "positions": ";".join(
                [",".join(map(str, position)) for position in self.positions_1]
            ),
            **self.settings,
        }
        self.worker.write.emit(f"level-1-saccades:{json.dumps(options)}")

        self.total_steps = len(self.positions_1)
        self.step_label.setText(f"{self.step}/{self.total_steps}")

    def change_to_level_2_smooth(self):
        self.stop_stimulus()
        self.stop_streams()

        options = {
            "curves": ";".join([",".join(map(str, curve)) for curve in self.curves_2]),
            **self.settings,
        }
        self.worker.write.emit(f"level-2-smooth:{json.dumps(options)}")

        self.total_steps = len(self.curves_2)
        self.step_label.setText(f"{self.step}/{self.total_steps}")

    def change_to_level_2_saccades(self):
        self.stop_stimulus()
        self.stop_streams()

        options = {
            "positions": ";".join(
                [",".join(map(str, position)) for position in self.positions_2]
            ),
            **self.settings,
        }
        self.worker.write.emit(f"level-2-saccades:{json.dumps(options)}")

        self.total_steps = len(self.positions_2)
        self.step_label.setText(f"{self.step}/{self.total_steps}")

    def update_options(self):
        self.settings = self.options_window.settings
        self.positions_1 = self.options_window.positions_1
        self.positions_2 = self.options_window.positions_2
        self.curves_1 = self.options_window.curves_1
        self.curves_2 = self.options_window.curves_2


class StreamCheckboxes(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()

        self.canvas = canvas

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

    def update_streams(self, streams):
        # Clear the layout
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add new checkboxes
        for stream in streams:
            checkbox = QtWidgets.QCheckBox(stream.name())
            checkbox.setDisabled(True)
            checkbox.setChecked(True)
            self.layout.addWidget(checkbox)

            if stream.name() in ["webcam", "cursor", "MousePosition"]:
                self.canvas.gaze_position_inlet = StreamInlet(stream)
            elif stream.name() in [
                "level-1-saccades-stimulus",
                "level-1-smooth-stimulus",
                "level-2-saccades-stimulus",
                "level-2-smooth-stimulus",
            ]:
                self.canvas.stimulus_inlet = StreamInlet(stream)
            else:
                checkbox.setChecked(False)
