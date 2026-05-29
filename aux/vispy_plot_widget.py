import numpy as np
from vispy import scene
from vispy.visuals.axis import Ticker
from datetime import datetime
from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QVBoxLayout, QWidget


class FormattedTicker(Ticker):
    def __init__(self, axis, formatter, anchors=None, min_label_spacing=75):
        super().__init__(axis, anchors=anchors)
        self._formatter = formatter
        self._min_label_spacing = min_label_spacing

    def _get_tick_frac_labels(self):
        major_frac, minor_frac, _ = super()._get_tick_frac_labels()
        major_frac = self._thin_major_ticks(major_frac)
        domain_start, domain_end = self.axis.domain
        values = domain_start + major_frac * (domain_end - domain_start)
        labels = [self._formatter(value) for value in values]
        return major_frac, minor_frac, labels

    def _thin_major_ticks(self, major_frac):
        if len(major_frac) < 2 or self.axis.pos is None:
            return major_frac

        axis_length = np.linalg.norm(self.axis.pos[1] - self.axis.pos[0])
        if axis_length <= 0:
            return major_frac

        step = 1
        while len(major_frac[::step]) > 1:
            label_spacing = axis_length / (len(major_frac[::step]) - 1)
            if label_spacing >= self._min_label_spacing:
                break
            step += 1

        return major_frac[::step]


class TimeAxisWidget(scene.AxisWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unfreeze()
        self.time_offset = 0.0
        self.freeze()

    def _view_changed(self, event=None):
        tr = self.node_transform(self._linked_view.scene)
        p1, p2 = tr.map(self._axis_ends())
        if self.orientation in ("left", "right"):
            self.axis.domain = (p1[1], p2[1])
        else:
            self.axis.domain = (p1[0] + self.time_offset, p2[0] + self.time_offset)


class VispyPlot(QWidget):
    class Pen:
        def __init__(self, color, width=1.0):
            self.color = color
            self.width = width

    class Curve:
        def __init__(self, vispy_line, parent_plot):
            self._line = vispy_line
            self._parent_plot = parent_plot

        def setData(self, data):
            self._line.set_data(data)

        def setColor(self, color):
            self._line.set_data(color=color)

        def setWidth(self, width):
            self._line.set_data(width=width)

    def __init__(self):
        super().__init__()
        canvas = scene.SceneCanvas(keys="interactive", show=True)
        grid = canvas.central_widget.add_grid(spacing=0, margin=0)

        viewbox = grid.add_view(row=0, col=1, camera="panzoom")

        x_axis = TimeAxisWidget(orientation="bottom")
        x_axis.axis.ticker = FormattedTicker(x_axis.axis, self._format_x_tick_as_time)
        grid.add_widget(x_axis, row=1, col=1)
        x_axis.link_view(viewbox)

        y_axis = scene.AxisWidget(orientation="left")
        grid.add_widget(y_axis, row=0, col=0)
        y_axis.link_view(viewbox)

        y_axis.width_min = 80
        y_axis.width_max = 80
        x_axis.height_min = 60
        x_axis.height_max = 60

        self.canvas = canvas
        self.grid = grid
        self.viewbox = viewbox
        self.x_axis = x_axis
        self.y_axis = y_axis

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas.native)

        self.curves = set()

    def set_x_axis_time_reference(self, value):
        if isinstance(value, datetime):
            value = value.timestamp()
        self.x_axis.time_offset = float(value)
        self.x_axis._view_changed()
        self.x_axis.axis._need_update = True
        self.x_axis.axis.update()

    def set_x_axis_label(self, label):
        self.x_axis.axis.axis_label = label
        self.x_axis.axis.update()

    def set_y_axis_label(self, label):
        self.y_axis.axis.axis_label = label
        self.y_axis.axis.update()

    def set_axis_labels(self, x_label, y_label):
        self.set_x_axis_label(x_label)
        self.set_y_axis_label(y_label)

    def plotCurve(self, dots_coords, pen):
        line = scene.Line(
            pos=dots_coords,
            color=pen.color,
            width=pen.width,
            parent=self.viewbox.scene,
        )  # type: ignore
        curve = self.Curve(line, self)
        self.curves.add(curve)
        return curve

    def removeCurve(self, curve):
        self.curves.discard(curve)
        curve._line.parent = None

        del curve

    def autoRange(self, margin=0.00000001):
        has_data, x_min, x_max, y_min, y_max = self._get_data_bounds()
        if not has_data:
            self.viewbox.camera.set_range(x=(0, 1), y=(0, 1))
            return

        # Обработка X
        if np.isfinite(x_min) and np.isfinite(x_max):
            x_range = x_max - x_min
            if x_range == 0:
                x_min -= 1.0
                x_max += 1.0
            x_margin = (x_max - x_min) * margin
            x_left = x_min - x_margin
            x_right = x_max + x_margin
        else:
            # Если нет корректных X, оставляем текущие
            rect = self.viewbox.camera.rect
            x_left, x_right = rect.left, rect.left + rect.width

        # Обработка Y
        if np.isfinite(y_min) and np.isfinite(y_max):
            y_range = y_max - y_min
            if y_range == 0:
                y_min -= 1.0
                y_max += 1.0
            y_margin = (y_max - y_min) * margin
            y_bottom = y_min - y_margin
            y_top = y_max + y_margin
        else:
            rect = self.viewbox.camera.rect
            y_bottom, y_top = rect.bottom, rect.bottom + rect.height

        self.viewbox.camera.set_range(x=(x_left, x_right), y=(y_bottom, y_top))

    def _get_data_bounds(self):
        x_min, x_max = np.inf, -np.inf
        y_min, y_max = np.inf, -np.inf
        has_data = False
        for curve in self.curves:
            pos = curve._line.pos
            if pos is None or len(pos) == 0:
                continue
            has_data = True
            cur_x_min = np.nanmin(pos[:, 0])
            cur_x_max = np.nanmax(pos[:, 0])
            cur_y_min = np.nanmin(pos[:, 1])
            cur_y_max = np.nanmax(pos[:, 1])
            x_min = min(x_min, cur_x_min)
            x_max = max(x_max, cur_x_max)
            y_min = min(y_min, cur_y_min)
            y_max = max(y_max, cur_y_max)
        return has_data, x_min, x_max, y_min, y_max

    def _format_x_tick_as_time(self, value):
        return datetime.fromtimestamp(float(value)).strftime("%H:%M:%S")
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.canvas.size = event.size().width(), event.size().height()
        self.canvas.update()
