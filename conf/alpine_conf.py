from datetime import timedelta

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
)
from conf._conf import _Configurator


class AlpineConfigurator(_Configurator):
    to_datetime_changed = Signal(object)
    time_range_changed = Signal(timedelta)
    x_label_changed = Signal(str)
    y_label_changed = Signal(str)  # TODO mb remove all

    def __init__(self, sett):
        super().__init__(sett=sett)

    def _setup_ui(self):  # type: ignore
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.form = form

        # Интервал
        time_range_spin = QSpinBox()
        self.time_range_spin = time_range_spin
        time_range_spin.valueChanged.connect(self._on_time_range_changed)
        time_range_spin.setRange(1, 86400 * 365)
        time_range_spin.setValue(int(self.sett.time_range.total_seconds()))
        self.form.addRow("Интервал, сек:", time_range_spin)

        # Ось X
        x_label_edit = QLineEdit()
        self.x_label_edit = x_label_edit
        x_label_edit.textChanged.connect(self._on_x_label_changed)
        x_label_edit.setText(self.sett.x_axis_label)
        form.addRow("Ось X:", x_label_edit)
        self.x_label_edit = x_label_edit

        # Ось Y
        y_label_edit = QLineEdit()
        self.y_label_edit = y_label_edit
        y_label_edit.textChanged.connect(self._on_y_label_changed)
        y_label_edit.setText(self.sett.y_axis_label)
        form.addRow("Ось Y:", y_label_edit)
        self.y_label_edit = y_label_edit

        layout.addLayout(self.form)

    def _on_time_range_changed(self, seconds: int):
        td = timedelta(seconds=seconds)
        self.pending_settings.time_range = td
        self.time_range_changed.emit(td)

    def _on_x_label_changed(self, label: str):
        self.pending_settings.x_axis_label = label
        self.x_label_changed.emit(label)

    def _on_y_label_changed(self, label: str):
        self.pending_settings.y_axis_label = label
        self.y_label_changed.emit(label)
