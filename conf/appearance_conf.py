from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QDoubleSpinBox,
)

from conf._conf import _Configurator
from aux.gui.handy_enums import LineColor, LineShape


class AppearenceConfigurator(_Configurator):
    line_color_changed = Signal(str)
    line_width_changed = Signal(float)
    line_shape_changed = Signal(str)

    def __init__(self, sett):
        super().__init__(sett=sett)

    def _setup_ui(self):  # type: ignore
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.form = form
        layout.addLayout(form)

        # Цвет линии
        color_combo = QComboBox()
        self.color_combo = color_combo
        colors = [color.value for color in LineColor]
        color_combo.addItems(colors)
        color_combo.setCurrentText(self.sett.line_color.value)
        color_combo.currentTextChanged.connect(self._on_color_changed)
        form.addRow("Цвет линии:", color_combo)

        # Толщина линии
        width_spin = QDoubleSpinBox()
        self.width_spin = width_spin
        width_spin.setRange(0.5, 10.0)
        width_spin.setSingleStep(0.5)
        width_spin.setValue(self.sett.line_width)
        width_spin.valueChanged.connect(self._on_width_changed)
        form.addRow("Толщина линии:", width_spin)

        # Стиль линии (форма)
        shape_combo = QComboBox()
        self.shape_combo = shape_combo
        shapes = [shape.value for shape in LineShape]
        shape_combo.addItems(shapes)
        shape_combo.setCurrentText(self.sett.line_shape.value)
        shape_combo.currentTextChanged.connect(self._on_shape_changed)
        form.addRow("Стиль линии:", shape_combo)

    def _on_color_changed(self, color_str: str):
        # Преобразуем строку в enum
        new_color = LineColor(color_str)
        self.pending_settings.line_color = new_color
        self.line_color_changed.emit(color_str)

    def _on_width_changed(self, width: float):
        self.pending_settings.line_width = width
        self.line_width_changed.emit(width)

    def _on_shape_changed(self, shape_str: str):
        new_shape = LineShape(shape_str)
        self.pending_settings.line_shape = new_shape
        self.line_shape_changed.emit(shape_str)
