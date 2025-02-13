from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal


class ConnectScreenWidget(QtWidgets.QWidget):
    clicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.layout)

        # Add QLineEdit for text input
        self.ip_input = QtWidgets.QLineEdit()
        self.ip_input.setFixedWidth(200)
        self.layout.addWidget(self.ip_input)

        # Add QPushButton for connecting to the server
        self.connect_button = QtWidgets.QPushButton("Connect")
        self.connect_button.setFixedWidth(200)
        self.connect_button.clicked.connect(
            lambda: self.clicked.emit(self.ip_input.text())
        )
        self.layout.addWidget(self.connect_button)
