import csv
from pathlib import Path

import yaml
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal


class OptionsWindow(QtWidgets.QWidget):
    options_changed = pyqtSignal()

    options_dir = Path(__file__).parent.parent / "options"
    settings_path = options_dir / "settings.yaml"
    positions_1_path = options_dir / "level-1_positions.csv"
    positions_2_path = options_dir / "level-2_positions.csv"
    curves_1_path = options_dir / "level-1_curves.csv"
    curves_2_path = options_dir / "level-2_curves.csv"

    settings = {}
    positions_1 = []
    positions_2 = []
    curves_1 = []
    curves_2 = []

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.setLayout(self.layout)

        self.settings_button_with_label = ButtonWithLabel(
            "", "Select", self.open_settings_file_picker
        )
        self.layout.addWidget(self.settings_button_with_label)

        self.positions_1_button_with_label = ButtonWithLabel(
            "", "Select", self.open_positions_1_file_picker
        )
        self.layout.addWidget(self.positions_1_button_with_label)

        self.positions_2_button_with_label = ButtonWithLabel(
            "", "Select", self.open_positions_2_file_picker
        )
        self.layout.addWidget(self.positions_2_button_with_label)

        self.curves_1_button_with_label = ButtonWithLabel(
            "", "Select", self.open_curves_1_file_picker
        )
        self.layout.addWidget(self.curves_1_button_with_label)

        self.curves_2_button_with_label = ButtonWithLabel(
            "", "Select", self.open_curves_2_file_picker
        )
        self.layout.addWidget(self.curves_2_button_with_label)

        self.update_button = QtWidgets.QPushButton("Update")
        self.update_button.clicked.connect(self.update_options)
        self.layout.addWidget(self.update_button)

        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save_options)
        self.layout.addWidget(self.save_button)

        # Load the default options
        self.load_settings(self.settings_path)
        self.load_positions_1(self.positions_1_path)
        self.load_positions_2(self.positions_2_path)
        self.load_curves_1(self.curves_1_path)
        self.load_curves_2(self.curves_2_path)

    def load_settings(self, file_name: Path):
        with open(file_name, "r") as f:
            self.settings = yaml.safe_load(f)

        self.settings_path = file_name
        self.settings_button_with_label.label.setText(file_name.name)

    def load_positions(self, file_name: Path):
        positions = []
        with open(file_name, "r") as f:
            reader = csv.reader(f)
            next(reader)  # Skipp the csv header
            positions = [(float(x), float(y), float(dt)) for dt, x, y in reader]

        return positions

    def load_positions_1(self, file_name: Path):
        self.positions_1 = self.load_positions(file_name)
        self.positions_1_path = file_name
        self.positions_1_button_with_label.label.setText(file_name.name)

    def load_positions_2(self, file_name: Path):
        self.positions_2 = self.load_positions(file_name)
        self.positions_2_path = file_name
        self.positions_2_button_with_label.label.setText(file_name.name)

    def load_curves(self, file_name: Path):
        curves = []
        with open(file_name, "r") as f:
            reader = csv.reader(f)
            next(reader)  # Skipp the csv header
            curves = [
                (float(a), float(b), float(c), float(d), float(e), float(f), float(T))
                for T, a, b, c, d, e, f in reader
            ]

        return curves

    def load_curves_1(self, file_name: Path):
        self.curves_1 = self.load_curves(file_name)
        self.curves_1_path = file_name
        self.curves_1_button_with_label.label.setText(file_name.name)

    def load_curves_2(self, file_name: Path):
        self.curves_2 = self.load_curves(file_name)
        self.curves_2_path = file_name
        self.curves_2_button_with_label.label.setText(file_name.name)

    def open_file_picker(self, name_filter, callback):
        dialog = QtWidgets.QFileDialog()
        dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter(name_filter)
        dialog.setViewMode(QtWidgets.QFileDialog.ViewMode.List)
        dialog.setOption(QtWidgets.QFileDialog.Option.ReadOnly)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptOpen)
        dialog.setDirectory(self.options_dir.absolute().as_posix())

        file_names = None
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            file_names = dialog.selectedFiles()

        if file_names:
            callback(Path(file_names[0]))

    def open_settings_file_picker(self):
        self.open_file_picker("YAML files (*.yaml)", self.load_settings)

    def open_positions_1_file_picker(self):
        self.open_file_picker("CSV files (*.csv)", self.load_positions_1)

    def open_positions_2_file_picker(self):
        self.open_file_picker("CSV files (*.csv)", self.load_positions_2)

    def open_curves_1_file_picker(self):
        self.open_file_picker("CSV files (*.csv)", self.load_curves_1)

    def open_curves_2_file_picker(self):
        self.open_file_picker("CSV files (*.csv)", self.load_curves_2)

    def save_options(self):
        self.options_changed.emit()
        self.hide()

    def update_options(self):
        self.load_settings(self.settings_path)
        self.load_positions_1(self.positions_1_path)
        self.load_positions_2(self.positions_2_path)
        self.load_curves_1(self.curves_1_path)
        self.load_curves_2(self.curves_2_path)


class ButtonWithLabel(QtWidgets.QWidget):
    def __init__(self, label, button_text, on_click):
        super().__init__()

        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        self.label = QtWidgets.QLabel(label)
        self.layout.addWidget(self.label)

        self.button = QtWidgets.QPushButton(button_text)
        self.button.clicked.connect(on_click)
        self.layout.addWidget(self.button)
