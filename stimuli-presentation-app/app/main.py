# Only needed for access to command line arguments
import sys

from PyQt6 import QtWidgets

from .window_main import MainWindow

app = QtWidgets.QApplication(sys.argv)

window = MainWindow()
window.show()

# Start the event loop.
app.exec()