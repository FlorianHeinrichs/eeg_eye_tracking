from .canvas_base import BaseCanvas


class EmptyCanvas(BaseCanvas):

    def __init__(self):
        super().__init__(1)

    def tick(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass
