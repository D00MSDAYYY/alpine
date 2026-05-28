from PySide6.QtWidgets import QApplication, QDialog

from alpine import Alpine
from aux.gui.widgets.settings_picker import SettingsPicker


def main():
    app = QApplication()

    settings_picker = SettingsPicker()

    if settings_picker.exec() == QDialog.DialogCode.Accepted:
        alpine = Alpine(settings_picker.get_file_path())
        alpine.show()
    del settings_picker

    app.exec()


if __name__ == "__main__":
    main()
