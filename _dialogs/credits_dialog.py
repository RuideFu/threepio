from PySide6.QtWidgets import QDialog
from PySide6.QtGui import QPixmap
from layouts import credits_ui


class CreditsDialog(QDialog):
    """Credits dialog window"""

    def __init__(self):
        super().__init__()

        self.ui = credits_ui.Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.label.setPixmap(QPixmap("assets/c3po.png"))
