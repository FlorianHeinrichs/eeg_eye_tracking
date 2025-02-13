import math
from time import time

from PyQt6 import QtGui
from PyQt6.QtCore import Qt, pyqtProperty

from .canvas_base import (
    GRID_BRUSH,
    GRID_PEN,
    HINT_BRUSH,
    HINT_PEN,
    POINT_BRUSH,
    POINT_PEN,
    BaseCanvas,
)


class SaccadesCanvas(BaseCanvas):

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
        grid_width,
        grid_height,
        positions,
        tps,
        **kwargs,
    ):
        super().__init__(tps)

        self.point = (self.cx, self.cy)
        self.point_hint = None
        self.scale = 1
        self.state = "stopped"
        self.step = 0
        self.positions = [
            tuple(map(float, position.split(","))) for position in positions.split(";")
        ]
        self.sum_dt = 0
        self.bounding_box_width = bounding_box_width
        self.bounding_box_height = bounding_box_height
        self.start_countdown = start_countdown
        self.grid_width = grid_width
        self.grid_height = grid_height

    def tick(self):
        current_t = time()
        dt = current_t - self.last_t
        dtick = dt * self.tps  # expected ticks since last tick

        if self.state == "stopped":
            self.point = (self.cx, self.cy)
        elif self.state == "starting":
            if self.n_ticks_to_event > 0:
                self.n_ticks_to_event -= dtick

                if self.sum_dt == 0:
                    x, y, row_dt = self.positions[self.step]

                    x = (x - self.grid_width / 2) * (
                        self.bounding_box_width_px / self.grid_width
                    ) + self.cx
                    y = (y - self.grid_height / 2) * (
                        self.bounding_box_height_px / self.grid_height
                    ) + self.cy

                    self.sum_dt += row_dt
                    self.point = (x, y)

                    x_hint, y_hint, _ = self.positions[self.step + 1]

                    x_hint = (x_hint - self.grid_width / 2) * (
                        self.bounding_box_width_px / self.grid_width
                    ) + self.cx
                    y_hint = (y_hint - self.grid_height / 2) * (
                        self.bounding_box_height_px / self.grid_height
                    ) + self.cy

                    self.point_hint = (x_hint, y_hint)
            else:
                self.start_t = current_t
                self.state = "moving"
        elif self.state == "moving":
            while (t_until_next_point := self.sum_dt - (current_t - self.start_t)) < 0:
                self.step += 1
                if self.step < len(self.positions):
                    x, y, row_dt = self.positions[self.step]

                    x = (x - self.grid_width / 2) * (
                        self.bounding_box_width_px / self.grid_width
                    ) + self.cx
                    y = (y - self.grid_height / 2) * (
                        self.bounding_box_height_px / self.grid_height
                    ) + self.cy

                    self.point = (x, y)

                    self.sum_dt += row_dt

                    if self.step + 1 < len(self.positions):
                        x_hint, y_hint, _ = self.positions[self.step + 1]

                        x_hint = (x_hint - self.grid_width / 2) * (
                            self.bounding_box_width_px / self.grid_width
                        ) + self.cx
                        y_hint = (y_hint - self.grid_height / 2) * (
                            self.bounding_box_height_px / self.grid_height
                        ) + self.cy

                        self.point_hint = (x_hint, y_hint)
                else:
                    self.stop()
                    break

            if self.step + 1 < len(self.positions):
                _, _, row_dt = self.positions[self.step]

                self.scale = t_until_next_point / row_dt
                # Discretize scale
                if 0.6 < self.scale:
                    self.scale = 1
                elif 0.3 < self.scale:
                    self.scale = 0.6
                else:
                    self.scale = 0.3
            else:
                self.scale = 1

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

        ## Draw grid points
        painter.setPen(GRID_PEN)
        painter.setBrush(GRID_BRUSH)

        for grid_x, grid_y, _ in set(self.positions):
            grid_x = (grid_x - self.grid_width / 2) * (
                self.bounding_box_width_px / self.grid_width
            ) + self.cx
            grid_y = (grid_y - self.grid_height / 2) * (
                self.bounding_box_height_px / self.grid_height
            ) + self.cy
            painter.drawEllipse(int(grid_x - 2), int(grid_y - 2), 5, 5)

        ## Display countdown when starting
        if self.state == "starting":
            painter.setPen(GRID_PEN)
            painter.drawText(
                int(x) - 2,
                int(y) - 20,
                str(math.ceil(self.n_ticks_to_event / self.tps)),
            )

        ## Draw hint
        if self.point_hint:
            x_hint, y_hint = self.point_hint

            painter.setPen(GRID_PEN)
            painter.drawLine(int(x), int(y), int(x_hint), int(y_hint))

        ## Draw point at new position
        painter.setPen(POINT_PEN)
        painter.setBrush(POINT_BRUSH)
        painter.drawEllipse(
            int(x) - int(10 * self.scale),
            int(y) - int(10 * self.scale),
            2 * int(10 * self.scale) + 1,
            2 * int(10 * self.scale) + 1,
        )
        painter.drawEllipse(int(x), int(y), 1, 1)

        painter.end()

    def start(self):
        self.step = 0
        self.point = (self.cx, self.cy)
        self.scale = 1
        self.point_hint = None
        self.n_ticks_to_event = self.start_countdown * self.tps
        self.start_t = None
        self.sum_dt = 0
        self.state = "starting"
        self.start_signal.emit()

    def stop(self):
        self.state = "stopped"
        self.stop_signal.emit()

        # Reset some fields for cleaner visuals
        # The "proper" reset is always done when start is called
        self.scale = 1
