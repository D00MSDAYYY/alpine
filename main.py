from threading import Timer

from pynput import mouse, keyboard
from PySide6.QtWidgets import QApplication, QDialog

from alpine import Alpine
from aux.gui.widgets.settings_picker import SettingsPicker
from aux.events import ClickEvent


def main():
    app = QApplication()

    settings_picker = SettingsPicker()

    if settings_picker.exec() == QDialog.DialogCode.Accepted:
        alpine = Alpine(settings_picker.get_file_path())
        alpine.show()
    del settings_picker

    def flip_input_flag():
        alpine.input_flag = not alpine.input_flag
        return alpine.input_flag

    def on_input():
        flip_input_flag()
        QApplication.postEvent(alpine, ClickEvent(), 1000)
        Timer(0.2, flip_input_flag).start()

    mouse_listener = mouse.Listener(on_click=lambda x, y, button, pressed: on_input()).start()
    keyboard_listener = keyboard.Listener(on_press=lambda key: on_input()).start()

    app.exec()


if __name__ == "__main__":
    main()
