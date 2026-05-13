# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'alert.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QGridLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(320, 100)
        Dialog.setModal(True)
        self.gridLayout = QGridLayout(Dialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.alert = QLabel(Dialog)
        self.alert.setObjectName(u"alert")
        font = QFont()
        font.setPointSize(24)
        self.alert.setFont(font)
        self.alert.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.alert, 0, 0, 1, 2)

        self.button_frame = QFrame(Dialog)
        self.button_frame.setObjectName(u"button_frame")
        self.gridLayout_2 = QGridLayout(self.button_frame)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.close_button = QPushButton(self.button_frame)
        self.close_button.setObjectName(u"close_button")

        self.gridLayout_2.addWidget(self.close_button, 0, 1, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer, 0, 0, 1, 1)


        self.gridLayout.addWidget(self.button_frame, 2, 0, 1, 2)


        self.retranslateUi(Dialog)
        self.close_button.clicked.connect(Dialog.accept)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Alert", None))
        self.alert.setText(QCoreApplication.translate("Dialog", u"!!!", None))
        self.close_button.setText(QCoreApplication.translate("Dialog", u"Close", None))
    # retranslateUi

