import numpy as np
from vispy import scene
from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QVBoxLayout, QWidget



class VispyPlot(QWidget):
    class Pen:
        def __init__(self, color):
            self.color = color

    class Curve:
        def __init__(self, vispy_line, parent_plot):
            self._line = vispy_line
            self._parent_plot = parent_plot

        def setData(self, data):
            self._line.set_data(data)

        def setColor(self, color):
            self._line.set_data(color=color)

    def __init__(self):
        super().__init__()
        canvas = scene.SceneCanvas(keys="interactive", show=True)
        grid = canvas.central_widget.add_grid(spacing=0, margin=0)

        viewbox = grid.add_view(row=0, col=1, camera="panzoom")

        x_axis = scene.AxisWidget(orientation="bottom")
        grid.add_widget(x_axis, row=1, col=1)
        x_axis.link_view(viewbox)

        y_axis = scene.AxisWidget(orientation="left")
        grid.add_widget(y_axis, row=0, col=0)
        y_axis.link_view(viewbox)

        y_axis.width_max = 40
        x_axis.height_max = 40

        self.canvas = canvas
        self.grid = grid
        self.viewbox = viewbox
        self.x_axis = x_axis
        self.y_axis = y_axis

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas.native)

        self.curves = set()

    def plotCurve(self, dots_coords, pen):
        line = scene.Line(pos=dots_coords, color=pen.color, parent=self.viewbox.scene)  # type: ignore
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
