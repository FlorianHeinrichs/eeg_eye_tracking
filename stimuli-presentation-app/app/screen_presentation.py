import time

from pylsl import StreamInfo, StreamOutlet
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal

from .canvas_empty import EmptyCanvas
from .canvas_saccades import SaccadesCanvas
from .canvas_smooth import SmoothCanvas


class PresentationScreenWidget(QtWidgets.QWidget):
    stimulus_started = pyqtSignal()
    stimulus_stopped = pyqtSignal()
    step_changed = pyqtSignal(int)
    streams_started = pyqtSignal()
    streams_stopped = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.stimulus = None

        self.stimulus_outlet = None
        self.markers_outlet = None

        self.layout = QtWidgets.QStackedLayout()
        self.layout.setStackingMode(QtWidgets.QStackedLayout.StackingMode.StackAll)
        self.setLayout(self.layout)

        self.canvas = EmptyCanvas()
        self.info_label = QtWidgets.QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )

        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.info_label)

    def change_stimulus(self, stimulus, settings={}):
        # Remove the old canvas from the layout
        self.layout.removeWidget(self.canvas)
        self.canvas.deleteLater()

        if stimulus == "level-1-smooth":
            self.canvas = SmoothCanvas(**settings)
        elif stimulus == "level-1-saccades":
            self.canvas = SaccadesCanvas(**settings)
        elif stimulus == "level-2-smooth":
            self.canvas = SmoothCanvas(**settings)
        elif stimulus == "level-2-saccades":
            self.canvas = SaccadesCanvas(**settings)
        else:
            self.canvas = EmptyCanvas()

        # Update the info label
        self.info_label.setText(f"{stimulus}")

        # Add the new canvas to the layout
        self.canvas.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.canvas.point_changed_signal.connect(self.push_to_stimulus_outlet)
        self.canvas.state_changed_signal.connect(self.push_to_markers_outlet)
        self.canvas.start_signal.connect(self.stimulus_started.emit)
        self.canvas.start_signal.connect(self.info_label.hide)
        self.canvas.stop_signal.connect(self.stimulus_stopped.emit)
        self.canvas.stop_signal.connect(self.info_label.show)
        self.canvas.step_changed_signal.connect(
            lambda step: self.step_changed.emit(step)
        )
        self.layout.addWidget(self.canvas)

        self.stimulus = stimulus
        self.settings = settings

        print(f"Changed to {stimulus} with settings: {settings}")

    def clear_canvas(self):
        # Remove the old canvas from the layout
        self.layout.removeWidget(self.canvas)
        self.canvas.deleteLater()
        self.canvas = EmptyCanvas()

        self.info_label.setText("")

        self.stimulus = None
        self.settings = {}

    def start_stimulus(self):
        self.canvas.start()

    def stop_stimulus(self):
        self.canvas.stop()

    def stop_streams(self):
        if self.stimulus_outlet:
            del self.stimulus_outlet
            self.stimulus_outlet = None
        if self.markers_outlet:
            del self.markers_outlet
            self.markers_outlet = None

        self.streams_stopped.emit()

    def start_streams(self):
        if self.stimulus is None:
            return

        # Open two lsl streams
        # One for the stimulus data and one for the current state
        # of the stimuli presentation, i.e. "stopped", "waiting", "moving"

        uuid = time.time()

        ## Stimulus Stream
        stimulus_stream_info = StreamInfo(
            f"{self.stimulus}-stimulus",  # stream name
            "Stimulus",  # content-type
            2,  # number of channels
            0,  # sampling rate, 0 means: irregular sampling rate
            # TPS might seem like the right sampling rate
            # but this is only correct if the CPU is fast enough to refresh at the selected TPS
            "float32",  # channel format
            f"{self.stimulus}-stimulus-{uuid}",  # unique stream id
        )

        # We add stimulus metadata following the XDF Specification
        # See https://github.com/sccn/xdf/wiki/Specifications

        channels = stimulus_stream_info.desc().append_child("channels")
        for c in ["x", "y"]:
            channels.append_child("channel").append_child_value(
                "label", c
            ).append_child_value("eye", "both").append_child_value(
                "type", f"Screen{c.upper()}"
            ).append_child_value(
                "unit", "pixels"
            ).append_child_value(
                "coordinate_system", "image-space"
            )

        # We also add metadata of the display
        # (similar to: https://github.com/sccn/xdf/wiki/Video-Raw-Meta-Data
        # but with resolution information like: https://github.com/labstreaminglayer/App-Input/blob/master/win_mouse.cpp)

        app: QtWidgets.QApplication = QtWidgets.QApplication.instance()

        setup = stimulus_stream_info.desc().append_child("setup")
        display = setup.append_child("display")
        display.append_child_value("monitors", str(len(app.screens())))
        resolution_primary = display.append_child("resolution_primary")
        resolution_primary.append_child_value(
            "X", str(app.primaryScreen().geometry().width())
        )
        resolution_primary.append_child_value(
            "Y", str(app.primaryScreen().geometry().height())
        )
        # The following values are calculated based on the width()/height() and widthMM()/heightMM() methods
        # Those turned out to be much more precise than the logicalDpiX() or physicalDpiX() methods
        # Note: 1 inch = 25.4 mm (exactly)
        resolution_primary.append_child_value(
            "pixel_aspect", str(self.canvas.px_x_mm / self.canvas.px_y_mm)
        )
        resolution_primary.append_child_value(
            "x_dpi", str(self.canvas.width() * 25.4 / self.canvas.widthMM())
        )
        resolution_primary.append_child_value(
            "y_dpi", str(self.canvas.height() * 25.4 / self.canvas.heightMM())
        )
        resolution_virtual = display.append_child("resolution_virtual")
        resolution_virtual.append_child_value(
            "X", str(app.primaryScreen().virtualGeometry().width())
        )
        resolution_virtual.append_child_value(
            "Y", str(app.primaryScreen().virtualGeometry().height())
        )
        display.append_child_value(
            "refresh_rate", str(app.primaryScreen().refreshRate())
        )
        display.append_child_value("origin", "top-left")
        canvas_x, canvas_y, canvas_width, canvas_height = (
            self.canvas.geometry().getRect()
        )
        canvas = display.append_child("canvas")
        canvas.append_child_value("x", str(canvas_x))
        canvas.append_child_value("y", str(canvas_y))
        canvas.append_child_value("width", str(canvas_width))
        canvas.append_child_value("height", str(canvas_height))

        # We also add custom metadata

        self._add_settings_to_stream(stimulus_stream_info, self.settings)

        self.stimulus_outlet = StreamOutlet(stimulus_stream_info)

        ## Marker Stream

        markers_stream_info = StreamInfo(
            f"{self.stimulus}-markers",  # stream name
            "Markers",  # content-type
            1,  # number of channels
            0,  # sampling rage, 0 means: irregular sampling rate
            "string",  # channel format
            f"{self.stimulus}-markers-{uuid}",  # unique stream id
        )

        channels = markers_stream_info.desc().append_child("channels")
        channels.append_child("channel").append_child_value("label", "state")

        self._add_settings_to_stream(markers_stream_info, self.settings)

        self.markers_outlet = StreamOutlet(markers_stream_info)

        self.streams_started.emit()

    def _add_settings_to_stream(self, stream_info: StreamInfo, settings_dict={}):
        experiment = stream_info.desc().append_child("experiment")
        settings = experiment.append_child("settings")
        for key, value in settings_dict.items():
            settings.append_child_value(key, str(value))

    def push_to_stimulus_outlet(self, data):
        if self.stimulus_outlet:
            self.stimulus_outlet.push_sample(list(data))

    def push_to_markers_outlet(self, data):
        if self.markers_outlet:
            self.markers_outlet.push_sample([data])
