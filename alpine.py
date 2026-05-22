import gc
import json
import time
from typing import List
from datetime import datetime, timedelta

import pyqtgraph as pg
from pydantic import BaseModel, Field
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal, QThreadPool, QRunnable, QThread, QTimer, QEvent
from PySide6.QtWidgets import QToolBar, QMainWindow, QDialog, QSplitter


from conf.conf_dialog import ConfiguratorDialog
from conf.alpine_conf import AlpineConfigurator
from cnl.cnl import _ChannelSettings
from cnl.cnl_maker import ChannelMaker
from aux.events import ClickEvent
from aux.gui.widgets.time_axis import TimeAxisItem
from aux.gui.widgets.legend import LegendWidget
from aux.gui.widgets.opener_dialog import OpenerDialog
from aux.gui.widgets.searchable_list import SearchableListView
from aux.gui.polymorphic_field_handlers import polymorphic_list_field_handlers
from aux.gui.data_filter_with_binary_search import data_filter_with_binary_search
from aux.gui.settings_decorators import (
    with_settings_property,
    settings_with_signals,
    get_saving_trigger,
)

# TRY_USING_OPENGL = True
# if TRY_USING_OPENGL:
#     try:
#         import OpenGL.GL as gl  # pylint: disable=unused-import
#     except:  # pylint: disable=bare-except
#         print("OpenGL acceleration: Disabled")
#         print("To install: `conda install pyopengl` or `pip install pyopengl`")
#     else:
#         print("OpenGL acceleration: Enabled")
#         pg.setConfigOptions(useOpenGL=True)
#         pg.setConfigOptions(antialias=True)
#         pg.setConfigOptions(enableExperimental=True)


class _AlpineSettings(BaseModel):
    time_range: timedelta = Field(default=timedelta(seconds=30))
    x_axis_label: str = Field(default="X")
    y_axis_label: str = Field(default="Y")

    cnls_setts: List[_ChannelSettings] = Field(default_factory=list)
    _val_cnls_setts, _ser_cnls_setts = polymorphic_list_field_handlers(
        _ChannelSettings, "cnls_setts"
    )


AlpineSettings = settings_with_signals(_AlpineSettings)


class _FilterDataTask(QRunnable):
    def __init__(self, alpine, cnl, from_dt, to_dt, callback):
        super().__init__()
        self.alpine = alpine
        self.cnl = cnl
        self.from_dt = from_dt
        self.to_dt = to_dt
        self.callback = callback

    # @profile
    def run(self):
        current_thread = QThread.currentThread()
        current_thread.setPriority(QThread.Priority.LowestPriority)

        filtered_data = data_filter_with_binary_search(
            self.cnl.data, self.from_dt, self.to_dt
        )

        del self.cnl.data
        self.cnl.data = filtered_data

        x = [d["timestamp"] for d in filtered_data]
        y = [d["value"] for d in filtered_data]

        if self.alpine.input_flag:
            return
        self.callback(self.cnl, x, y)


@with_settings_property()
class Alpine(QMainWindow):
    cnl_created_with_sett = Signal(object)
    cnl_closed_with_sett = Signal(object)
    cnl_deleted_with_sett = Signal(object)

    settings_created = Signal(object)
    _filtered_data_ready = Signal(object, list, list)  # cnl, [x], [y]

    def __init__(self, sett_path):
        super().__init__()
        self._setup_settings(sett_path)
        self._setup_ui()
        self._setup_stats_timer()
        self._setup_gc_timer()

        self.time_range = self.settings.time_range

        self.stop_flag = False
        self.input_flag = False

        # TODO this violates DI principles but ok for now
        self.cnl_maker = ChannelMaker(self)
        self.cnl_to_curve = {}

        self._threadpool = QThreadPool.globalInstance()

        self._filtered_data_ready.connect(
            self._redraw_plot, Qt.ConnectionType.QueuedConnection
        )

    ###################
    #                 #
    #    interface    #
    #                 #
    ###################
    def add_cnl(self, cnl):
        self.legend.add_cnl(cnl)

        curve = self.plot_widget.plot(
            [],
            [],
            pen=pg.mkPen(
                color=cnl.settings.appearence.line_color.name.lower(),
                width=cnl.settings.appearence.line_width,
                # symbol="o",
                # symbolSize=5,
                # symbolBrush="w",
            ),
            name=cnl.settings.name,
        )
        self.cnl_to_curve[cnl] = curve

        cnl.close_requested.connect(self.remove_cnl)
        cnl.updated.connect(self._on_cnl_updated)

        cnl.settings.appearence.line_color_changed.connect(
            lambda color, cnl=cnl: self._update_curve_style(cnl),
            self.Qt_DirConn,
        )
        cnl.settings.appearence.line_width_changed.connect(
            lambda width, cnl=cnl: self._update_curve_style(cnl),
            self.Qt_DirConn,
        )
        cnl.settings.appearence.line_shape_changed.connect(
            lambda shape, cnl=cnl: self._update_curve_style(cnl),
            self.Qt_DirConn,
        )
        try:
            cnl.start()
        except Exception as e:
            print(str(e))
            self.remove_cnl(cnl)

    def remove_cnl(self, cnl):
        if curve := self.cnl_to_curve.pop(cnl, None):
            self.plot_widget.removeItem(curve)
        self.legend.remove_cnl(cnl)
        cnl.stop()
        cnl.deleteLater()

    ###########################
    #                         #
    #    actions callbacks    #
    #                         #
    ###########################
    def _action_add_triggered(self):
        crts_list_view = SearchableListView(
            items=self.settings.cnls_setts,
            item_maker=lambda cnl_sett: f"{cnl_sett.name}",
            multi_select=True,
        )
        dialog = OpenerDialog(crts_list_view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            for sett in crts_list_view.get_selected_data():
                all_channels = self.legend.get_channels()
                if sett.name in [cnl.settings.name for cnl in all_channels]:
                    continue
                cnl = self.cnl_maker.create_cnl(sett)
                self.add_cnl(cnl)

    def _action_palette_triggered(self):
        conf = AlpineConfigurator(sett=self.settings)
        conf_dialog = ConfiguratorDialog(configurators={"Общее": conf})
        if conf_dialog.exec() == QDialog.DialogCode.Accepted:
            pass

    def _action_pause_triggered(self):
        self.stop_flag = not self.stop_flag
        self.pause_action.setText("▶" if self.stop_flag else "⏸")

    ########################
    #                      #
    #    setup funtions    #
    #                      #
    ########################
    def _setup_settings(self, sett_path):
        self.settings_path = sett_path
        try:
            with open(self.settings_path, "r") as f:
                obj = json.load(f)
            self.settings: _AlpineSettings = AlpineSettings(**obj)  # type: ignore

            get_saving_trigger().triggered.connect(
                self._save_all_settings, self.Qt_DirConn
            )
            self.settings.x_axis_label_changed.connect(self._update_axis_labels, self.Qt_DirConn)  # type: ignore
            self.settings.y_axis_label_changed.connect(self._update_axis_labels, self.Qt_DirConn)  # type: ignore
            self.settings.time_range_changed.connect(self._on_time_range_changed, self.Qt_DirConn)  # type: ignore

            self.settings_created.emit(self.settings)
        except Exception as e:
            print("exception in settings")
            raise

    def _setup_ui(self):
        self.setFont(QFont("Arial", 18))
        self._setup_toolbar()

        splitter = QSplitter(Qt.Orientation.Horizontal)

        plot_widget = pg.PlotWidget(axisItems={"bottom": TimeAxisItem()})
        # plot_widget = pg.PlotWidget()
        self.plot_widget = plot_widget
        plot_widget.showGrid(x=True, y=True, alpha=0.3)
        plot_widget.setLabel("left", self.settings.y_axis_label)
        plot_widget.setLabel("bottom", self.settings.x_axis_label)

        self.legend = LegendWidget()

        splitter.addWidget(self.plot_widget)
        splitter.addWidget(self.legend)
        splitter.setSizes([int(self.width() * 0.75), int(self.width() * 0.25)])

        self.setCentralWidget(splitter)

    def _setup_toolbar(self):
        toolbar = QToolBar(self)
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        self.add_action = toolbar.addAction("➕")
        self.add_action.setToolTip("Добавить канал")
        self.add_action.triggered.connect(self._action_add_triggered, self.Qt_DirConn)

        self.palette_action = toolbar.addAction("🎨")
        self.palette_action.setToolTip("Настройки внешнего вида")
        self.palette_action.triggered.connect(
            self._action_palette_triggered, self.Qt_DirConn
        )

        self.pause_action = toolbar.addAction("⏸")
        self.pause_action.setToolTip("Пауза обновления графика")
        self.pause_action.triggered.connect(
            self._action_pause_triggered, self.Qt_DirConn
        )

    def _setup_stats_timer(self):
        self._redraw_plot_count = 0
        self._redraw_plot_hz = 0.0
        self._stats_timer = QTimer()
        self._stats_timer.setInterval(1000)  # раз в секунду
        self._stats_timer.timeout.connect(self._on_stats_timer)
        self._stats_timer.start()

    def _setup_gc_timer(self):
        self._gc_timer = QTimer()
        self._gc_timer.setInterval(30000)  # 30 секунд
        self._gc_timer.timeout.connect(self._on_gc_timer)
        self._gc_timer.start()

    ############################
    #                          #
    #    settings callbacks    #
    #                          #
    ############################
    def _update_curve_style(self, cnl):
        if curve := self.cnl_to_curve.get(cnl):
            color = cnl.settings.appearence.line_color.name.lower()
            width = cnl.settings.appearence.line_width
            style = getattr(Qt.PenStyle, cnl.settings.appearence.line_shape.value)
            curve.setPen(pg.mkPen(color=color, width=width, style=style))

    def _update_axis_labels(self):
        self.plot_widget.setLabel("bottom", self.settings.x_axis_label)
        self.plot_widget.setLabel("left", self.settings.y_axis_label)

    def _on_time_range_changed(self, value):
        self.time_range = value

    def _save_all_settings(self):
        with open(self.settings_path, "w") as f:
            f.write(self.settings.model_dump_json(indent=2))

    ##########################
    #                        #
    #    timers callbacks    #
    #                        #
    ##########################

    def _on_stats_timer(self):
        if self._redraw_plot_count > 0:
            self._redraw_plot_hz = self._redraw_plot_count / 1.0  # за секунду
            print(f"📊 Герцовка отрисовки графика: {self._redraw_plot_hz:.1f} FPS")
        else:
            self._redraw_plot_hz = 0.0
        self._redraw_plot_count = 0  # сброс счётчика

    def _on_gc_timer(self):
        collected = gc.collect()
        print(f"🧹 Сборщик мусора вызван (каждые 30 с), удалено объектов: {collected}")

    ###############################################
    #                                             #
    #    misc (but most intensitive) callbacks    #
    #                                             #
    ###############################################
    def _on_data_filtered(self, cnl, x, y):
        if self.input_flag:
            return
        self._filtered_data_ready.emit(cnl, x, y)

    def _on_cnl_updated(self, cnl):
        to_dt = datetime.now()
        from_dt = to_dt - self.time_range

        task = _FilterDataTask(self, cnl, from_dt, to_dt, self._on_data_filtered)
        self._threadpool.start(task, priority=0)

    def _redraw_plot(self, cnl, x, y):
        if self.stop_flag or self.input_flag:
            return
        if curve := self.cnl_to_curve.get(cnl):
            curve.setData(x, y)
            self.plot_widget.autoRange()
            self._redraw_plot_count += 1

    # def event(self, event):
    #     if event.type() == QEvent.Type.MouseButtonPress:
    #         print("click2")
    #         if event.button() == Qt.MouseButton.LeftButton:
    #             # self.stop_flag = not self.stop_flag
    #             return True
    #     return super().event(event)

    Qt_DirConn = Qt.ConnectionType.DirectConnection
