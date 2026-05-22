from types import SimpleNamespace

from PySide6.QtWidgets import QWidget


class _Configurator(QWidget):
    def __init__(self, sett):
        super().__init__()

        self.sett = sett
        self.pending_settings = SimpleNamespace()

        self._setup_ui()

    def _setup_ui(self):
        raise

    def _on_accept(self):
        for name, value in vars(self.pending_settings).items():
            setattr(self.sett, name, value)
