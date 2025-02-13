from abc import ABCMeta, abstractmethod
from time import time

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import QPoint, QTimer, pyqtProperty, pyqtSignal, Qt

## Constants
# Colors
BACKGROUND_COLOR = QtGui.QColor(180, 180, 180)
POINT_COLOR = QtGui.QColor("#FFD141")
HINT_COLOR = QtGui.QColor(200, 200, 200)
GRID_COLOR = QtGui.QColor("black")

# Pens and brushes
POINT_PEN = QtGui.QPen()
POINT_PEN.setColor(QtGui.QColor("black"))
POINT_PEN.setWidth(1)
POINT_BRUSH = QtGui.QBrush(POINT_COLOR)
POINT_BRUSH.setStyle(Qt.BrushStyle.SolidPattern)

HINT_PEN = QtGui.QPen()
HINT_PEN.setColor(QtGui.QColor(128, 128, 128))
HINT_PEN.setWidth(1)
HINT_BRUSH = QtGui.QBrush(HINT_COLOR)
HINT_BRUSH.setStyle(Qt.BrushStyle.SolidPattern)

GRID_PEN = QtGui.QPen()
GRID_PEN.setColor(QtGui.QColor("black"))
GRID_PEN.setWidth(1)
GRID_BRUSH = QtGui.QBrush(GRID_COLOR)
GRID_BRUSH.setStyle(Qt.BrushStyle.SolidPattern)


class ABCQWidgetMeta(type(QtWidgets.QWidget), ABCMeta):
    pass


class BaseCanvas(QtWidgets.QWidget, metaclass=ABCQWidgetMeta):

    ## Signals
    start_signal = pyqtSignal()
    stop_signal = pyqtSignal()

    point_changed_signal = pyqtSignal(tuple)
    state_changed_signal = pyqtSignal(str)
    step_changed_signal = pyqtSignal(int)

    ## Properties
    # point
    def get_point(self):
        return self._point

    def set_point(self, value):
        self._point = value

        global_point = self.mapToGlobal(QPoint(int(value[0]), int(value[1])))
        self.point_changed_signal.emit((global_point.x(), global_point.y()))

    point = pyqtProperty(float, get_point, set_point)

    # state
    def get_state(self):
        return self._state

    def set_state(self, value):
        self._state = value
        self.state_changed_signal.emit(value)

    state = pyqtProperty(str, get_state, set_state)

    # step
    def get_step(self):
        return self._step

    def set_step(self, value):
        self._step = value
        self.step_changed_signal.emit(value)

    step = pyqtProperty(int, get_step, set_step)

    def __init__(
        self,
        tps,
    ):
        super().__init__()

        self.setAutoFillBackground(True)
        pallet = self.palette()
        pallet.setColor(self.backgroundRole(), BACKGROUND_COLOR)
        self.setPalette(pallet)

        # Ticks per second
        self.tps = tps

        # Start clock
        self.last_t = time()
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(int(1000 / self.tps))

    def mm_to_px_x(self, value):
        return value / self.px_x_mm

    def mm_to_px_y(self, value):
        return value / self.px_y_mm

    def px_to_mm_x(self, value):
        return value * self.px_x_mm

    def px_to_mm_y(self, value):
        return value * self.px_y_mm

    @property
    def px_x_mm(self):  # horizontal length of one logical px in mm
        return self.widthMM() / self.width()

    @property
    def px_y_mm(self):  # vertical length of one logical px in mm
        return self.heightMM() / self.height()

    @property
    def cx(self):  # center x
        return self.width() / 2

    @property
    def cy(self):  # center y
        return self.height() / 2

    @abstractmethod
    def tick(self):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass
