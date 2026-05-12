"""Dialogue box for alerting the user about something"""

from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Qt
from layouts import alert_ui  # compiled PyQt dialogue ui


class AlertDialog(QDialog):
    """Alert dialogue window"""

    def __init__(self, alert: str, button_text: str):
        super().__init__()
        self.ui = alert_ui.Ui_Dialog()
        # self.setModal(False)
        self.ui.setupUi(self)

        # Hide the close/minimize/fullscreen buttons and make window always on top
        # noinspection PyTypeChecker
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.ui.alert.setText(alert)
        self.ui.close_button.setText(button_text)
