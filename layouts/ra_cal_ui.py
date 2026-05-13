# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ra_cal.ui'
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
    QTimeEdit, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(320, 100)
        Dialog.setModal(True)
        self.gridLayout = QGridLayout(Dialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.sidereal_label = QLabel(Dialog)
        self.sidereal_label.setObjectName(u"sidereal_label")
        font = QFont()
        font.setPointSize(13)
        self.sidereal_label.setFont(font)
        self.sidereal_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.sidereal_label, 2, 2, 1, 1)

        self.sidereal_value = QTimeEdit(Dialog)
        self.sidereal_value.setObjectName(u"sidereal_value")
        font1 = QFont()
        font1.setFamilies([u"Iosevka Aile"])
        self.sidereal_value.setFont(font1)

        self.gridLayout.addWidget(self.sidereal_value, 2, 3, 1, 1)

        self.button_frame = QFrame(Dialog)
        self.button_frame.setObjectName(u"button_frame")
        self.gridLayout_2 = QGridLayout(self.button_frame)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.cancel_button = QPushButton(self.button_frame)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout_2.addWidget(self.cancel_button, 1, 1, 1, 1)

        self.ok_button = QPushButton(self.button_frame)
        self.ok_button.setObjectName(u"ok_button")

        self.gridLayout_2.addWidget(self.ok_button, 1, 2, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer, 1, 0, 1, 1)


        self.gridLayout.addWidget(self.button_frame, 3, 2, 1, 2)

        QWidget.setTabOrder(self.sidereal_value, self.ok_button)
        QWidget.setTabOrder(self.ok_button, self.cancel_button)

        self.retranslateUi(Dialog)
        self.cancel_button.clicked.connect(Dialog.reject)
        self.ok_button.clicked.connect(Dialog.accept)

        self.ok_button.setDefault(True)


        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"RA Calibration", None))
        self.sidereal_label.setText(QCoreApplication.translate("Dialog", u"Current Sidereal Time", None))
        self.sidereal_value.setDisplayFormat(QCoreApplication.translate("Dialog", u"HH:mm:ss", None))
        self.cancel_button.setText(QCoreApplication.translate("Dialog", u"Cancel", None))
        self.ok_button.setText(QCoreApplication.translate("Dialog", u"Set RA", None))
    # retranslateUi

