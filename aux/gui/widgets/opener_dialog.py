from PySide6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox


class OpenerDialog(QDialog):
    def __init__(self, widget, parent=None):
        super().__init__(parent)
        self.widget = widget
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(self.widget)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(self.button_box)

    def _connect_signals(self):
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
