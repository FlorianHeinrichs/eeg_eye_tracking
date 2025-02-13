import math
from time import time

from PyQt6 import QtGui
from PyQt6.QtCore import Qt, pyqtProperty

from .canvas_base import (
    BACKGROUND_COLOR,
    GRID_PEN,
    HINT_BRUSH,
    HINT_PEN,
    POINT_BRUSH,
    POINT_PEN,
    BaseCanvas,
)


class SmoothCanvas(BaseCanvas):

    ## Properties
    # bounding box width
    def set_bounding_box_width(self, value):
        self._bounding_box_width = value
        self.bounding_box_width_px = self.mm_to_px_x(value)

    def get_bounding_box_width(self):
        return self._bounding_box_width

    bounding_box_width = pyqtProperty(
        float, get_bounding_box_width, set_bounding_box_width
    )

    # bounding box height
    def set_bounding_box_height(self, value):
        self._bounding_box_height = value
        self.bounding_box_height_px = self.mm_to_px_y(value)

    def get_bounding_box_height(self):
        return self._bounding_box_height

    bounding_box_height = pyqtProperty(
        float, get_bounding_box_height, set_bounding_box_height
    )

    def __init__(
        self,
        bounding_box_width,
        bounding_box_height,
        start_countdown,
        pre_move_seconds,
        pre_move_countdown,
        hint_past_seconds,
        hint_future_seconds,
        curves,
        tps,
        **kwargs,
    ):
        super().__init__(tps)

        self.point = (self.cx, self.cy)
        self.points = [(self.cx, self.cy)]
        self.point_hint = None
        self.state = "stopped"
        self.step = 0
        self.curves = [
            tuple(map(float, curve.split(","))) for curve in curves.split(";")
        ]
        self.bounding_box_width = bounding_box_width
        self.bounding_box_height = bounding_box_height
        self.start_countdown = start_countdown
        self.pre_move_seconds = pre_move_seconds
        self.pre_move_countdown = pre_move_countdown
        self.hint_past_seconds = hint_past_seconds
        self.hint_future_seconds = hint_future_seconds

    def tick(self):
        current_t = time()
        dt = current_t - self.last_t
        dtick = dt * self.tps  # expected ticks since last tick

        if self.state == "stopped":
            self.point = (self.cx, self.cy)
        elif self.state == "starting" or self.state == "pre_moving":
            a, b, c, d, e, f, T = self.curves[self.step]

            if self.points == []:
                for k in range(
                    -int(self.tps * self.hint_past_seconds),
                    int(self.tps * self.hint_future_seconds),
                ):
                    t = k / (T * self.tps)
                    x = (
                        math.cos(t * a) * math.sin(t * b) + e * t
                    ) * self.bounding_box_width_px / 2 + self.cx
                    y = (
                        -(math.cos(t * c) * math.sin(t * d) + f * t)
                        * self.bounding_box_height_px
                        / 2
                        + self.cy
                    )
                    self.points.append((x, y))

                    if k == 0:
                        self.point = (x, y)

            if self.n_ticks <= self.tps * self.pre_move_seconds:
                t = -self.n_ticks / (T * self.tps)
                x = (
                    math.cos(t * a) * math.sin(t * b) + e * t
                ) * self.bounding_box_width_px / 2 + self.cx
                y = (
                    -(math.cos(t * c) * math.sin(t * d) + f * t)
                    * self.bounding_box_height_px
                    / 2
                    + self.cy
                )
                self.point_hint = (x, y)
            else:
                self.point_hint = None

            if self.n_ticks > 0:
                self.n_ticks -= dtick
            else:
                self.point_hint = None
                self.state = "moving"
        elif self.state == "moving":
            a, b, c, d, e, f, T = self.curves[self.step]

            if self.n_ticks < T * self.tps:
                self.points = []
                for k in range(
                    -int(self.tps * self.hint_past_seconds),
                    int(self.tps * self.hint_future_seconds),
                ):
                    t = (self.n_ticks + k) / (T * self.tps)
                    x = (
                        math.cos(t * a) * math.sin(t * b) + e * t
                    ) * self.bounding_box_width_px / 2 + self.cx
                    y = (
                        -(math.cos(t * c) * math.sin(t * d) + f * t)
                        * self.bounding_box_height_px
                        / 2
                        + self.cy
                    )
                    self.points.append((x, y))

                    if k == 0:
                        self.point = (x, y)

                self.n_ticks += dtick
            else:
                self.step += 1

                if self.step == len(self.curves):
                    self.stop()
                else:
                    self.points = []
                    self.n_ticks = self.pre_move_countdown * self.tps
                    self.state = "pre_moving"

        self.last_t = time()
        self.update()

    def paintEvent(self, e):
        x, y = self.point

        ## Setup painter
        painter = QtGui.QPainter(self)

        ## Draw bounding box
        if self.state == "stopped":
            painter.setPen(GRID_PEN)

            for scale in [1, 0.5, 0.25]:
                painter.drawRect(
                    int(self.cx - scale * self.bounding_box_width_px / 2),
                    int(self.cy - scale * self.bounding_box_height_px / 2),
                    int(scale * self.bounding_box_width_px),
                    int(scale * self.bounding_box_height_px),
                )

                # Draw horizontal text
                painter.drawText(
                    int(self.cx - scale * self.bounding_box_width_px / 2),
                    int(self.cy - scale * self.bounding_box_height_px / 2),
                    str(int(self.bounding_box_width * scale)),
                )

                # Draw vertical text
                painter.save()
                painter.translate(
                    int(self.cx - scale * self.bounding_box_width_px / 2),
                    int(self.cy + scale * self.bounding_box_height_px / 2),
                )
                painter.rotate(-90)  # Rotate the coordinate system by 90 degrees
                # Draw rotated text (it will be rotated)
                painter.drawText(
                    0,
                    0,
                    str(int(self.bounding_box_height * scale)),
                )
                # Restore the painter to its previously saved state
                painter.restore()

        ## Display countdown when starting
        if self.state == "starting":
            painter.setPen(GRID_PEN)
            painter.drawText(
                int(x) - 2,
                int(y) - 20,
                str(math.ceil(self.n_ticks / self.tps)),
            )

        ## Hint at part of the curve
        pen = QtGui.QPen()
        color = QtGui.QColor(BACKGROUND_COLOR)
        pen.setColor(color)
        painter.setPen(pen)

        for i in range(1, len(self.points)):
            x1, y1 = self.points[i - 1]
            x2, y2 = self.points[i]

            # Decrease lightness by a certain percentage
            color = color.darker(101)  # 101% darker each time

            # Create a pen with the color and set it to the painter
            pen = QtGui.QPen(color)
            painter.setPen(pen)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        ## Draw hint point
        if self.point_hint:
            x_hint, y_hint = self.point_hint

            painter.setPen(HINT_PEN)
            painter.setBrush(HINT_BRUSH)
            painter.drawEllipse(int(x_hint - 10), int(y_hint - 10), 21, 21)

        ## Draw point at new position
        painter.setPen(POINT_PEN)
        painter.setBrush(POINT_BRUSH)
        painter.drawEllipse(int(x - 10), int(y - 10), 21, 21)
        painter.drawEllipse(int(x), int(y), 1, 1)

        painter.end()

    def start(self):
        self.point = (self.cx, self.cy)
        self.points = []
        self.point_hint = None
        self.n_ticks = self.start_countdown * self.tps
        self.step = 0
        self.state = "starting"
        self.start_signal.emit()

    def stop(self):
        self.state = "stopped"
        self.stop_signal.emit()

        # Reset some fields for cleaner visuals
        # The "proper" reset is always done when start is called
        self.points = []
        self.point_hint = None
