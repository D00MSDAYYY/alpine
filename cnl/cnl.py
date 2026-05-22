from typing import Literal

from pydantic import Field, BaseModel
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QLabel, QDialog, QHBoxLayout, QPushButton

from aux.gui.handy_enums import *
from aux.gui.polymorphic_field_handlers import PolymorphicBase
from aux.gui.settings_decorators import with_settings_property, settings_with_signals

from conf.conf_dialog import ConfiguratorDialog
from conf.appearance_conf import AppearenceConfigurator


class _Appearence(BaseModel):
    line_width: float = Field(default=1.0)
    line_color: LineColor = Field(default_factory=random_line_color)
    line_shape: LineShape = Field(default=LineShape.SolidLine)


Appearence = settings_with_signals(_Appearence)


class _ChannelSettings(PolymorphicBase):
    type: Literal["ChannelSettings"] = "ChannelSettings"
    name: str = Field(default="безымянный_канал")
    units: str | None = Field(default=None)

    appearence: _Appearence = Field(default_factory=_Appearence)


ChannelSettings = settings_with_signals(_ChannelSettings)


@with_settings_property()
class _Channel(QWidget):
    updated = Signal(object)
    close_requested = Signal(object)
    stopped = Signal()

    def __init__(self, settings):
        super().__init__()

        self.settings = settings
        self.new_data = None
        self.data = []

        self._setup_ui()
        self._connect_signals()

    def start(self):
        raise

    def stop(self):
        raise

    def __del__(self):
        self.stop()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)

        color_wgt = QWidget()
        self.color_wgt = color_wgt
        color_wgt.setFixedSize(20, 20)
        self._update_color_indicator()

        self.name_label = QLabel("")

        self.name_label.setText(self.settings.name)
        self.settings.name_changed.connect(self.name_label.setText)

        sq_side = 30
        fixed_w = sq_side
        fixed_h = sq_side

        palette_btn = QPushButton("🎨")
        self.palette_btn = palette_btn
        palette_btn.setFixedSize(fixed_w, fixed_h)

        close_btn = QPushButton("❌")
        self.close_btn = close_btn
        close_btn.setFixedSize(fixed_w, fixed_h)

        main_layout.addWidget(color_wgt)
        main_layout.addWidget(self.name_label)
        main_layout.addStretch()
        main_layout.addWidget(palette_btn)
        main_layout.addWidget(close_btn)

    def _update_color_indicator(self):
        color_name = self.settings.appearence.line_color.name.lower()
        self.color_wgt.setStyleSheet(f"background-color: {color_name};")

    def _connect_signals(self):
        self.close_btn.clicked.connect(lambda flag: self._btn_close_clicked())

        self.palette_btn.clicked.connect(self._btn_palette_clicked)
        self.settings.appearence.line_color_changed.connect(
            self._update_color_indicator
        )

    def _btn_palette_clicked(self):
        conf = AppearenceConfigurator(sett=self.settings.appearence)
        conf_dialog = ConfiguratorDialog(configurators={"Общее": conf})
        if conf_dialog.exec() == QDialog.DialogCode.Accepted:
            pass  #  done

    def _btn_close_clicked(self):
        self.close_requested.emit(self)
