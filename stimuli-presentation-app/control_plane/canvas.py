from time import time

from pylsl import StreamInlet
from PyQt6 import QtGui, QtWidgets
from PyQt6.QtCore import Qt, QTimer


class Canvas(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.point_gaze = (0, 0)
        self.point_stimulus = (0, 0)

        # Start clock
        self.last_t = time()
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(int(1000 / 120))

        # create a inlets to read from the stream
        self.gaze_position_inlet: StreamInlet = None
        self.stimulus_inlet: StreamInlet = None

    def tick(self):
        if self.gaze_position_inlet:
            chunk, timestamps = self.gaze_position_inlet.pull_chunk()
            if timestamps:
                remote_resolution = (
                    self.gaze_position_inlet.info()
                    .desc()
                    .child("setup")
                    .child("display")
                    .child("resolution_primary")
                )
                remote_resolution_X = float(remote_resolution.child_value("X"))
                remote_resolution_Y = float(remote_resolution.child_value("Y"))

                gaze_x, gaze_y = chunk[-1]
                self.point_gaze = (
                    gaze_x * self.width() / remote_resolution_X,
                    gaze_y * self.height() / remote_resolution_Y,
                )

        if self.stimulus_inlet:
            chunk, timestamps = self.stimulus_inlet.pull_chunk()
            if timestamps:
                remote_resolution = (
                    self.stimulus_inlet.info()
                    .desc()
                    .child("setup")
                    .child("display")
                    .child("resolution_primary")
                )
                remote_resolution_X = float(remote_resolution.child_value("X"))
                remote_resolution_Y = float(remote_resolution.child_value("Y"))

                stimulus_x, stimulus_y = chunk[-1]
                self.point_stimulus = (
                    stimulus_x * self.width() / remote_resolution_X,
                    stimulus_y * self.height() / remote_resolution_Y,
                )

        self.last_t = time()
        self.update()

    def paintEvent(self, e):
        x_gaze, y_gaze = self.point_gaze
        x_stimulus, y_stimulus = self.point_stimulus

        ## Setup painter
        painter = QtGui.QPainter(self)

        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor("black"))
        pen.setWidth(1)
        painter.setPen(pen)

        # Draw boundary
        painter.drawRect(1, 1, self.width() - 2, self.height() - 2)

        # Draw stimulus position
        brush = QtGui.QBrush()
        brush.setColor(QtGui.QColor("#FFD141"))
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        painter.setBrush(brush)
        painter.drawEllipse(int(x_stimulus - 5), int(y_stimulus - 5), 11, 11)
        painter.drawEllipse(int(x_stimulus), int(y_stimulus), 1, 1)

        # Draw gaze cursor
        painter.setBrush(QtGui.QBrush())
        painter.drawEllipse(int(x_gaze - 5), int(y_gaze - 5), 11, 11)
        painter.drawEllipse(int(x_gaze), int(y_gaze), 1, 1)

        painter.end()
