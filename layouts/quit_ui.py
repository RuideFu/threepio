# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'quit.ui'
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
        Dialog.resize(320, 110)
        Dialog.setModal(True)
        self.gridLayout_2 = QGridLayout(Dialog)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.sidereal_label = QLabel(Dialog)
        self.sidereal_label.setObjectName(u"sidereal_label")
        self.sidereal_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.sidereal_label.setWordWrap(True)

        self.gridLayout_2.addWidget(self.sidereal_label, 1, 1, 1, 1)

        self.button_frame = QFrame(Dialog)
        self.button_frame.setObjectName(u"button_frame")
        self.gridLayout = QGridLayout(self.button_frame)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 0, 0, 1, 1)

        self.ok_button = QPushButton(self.button_frame)
        self.ok_button.setObjectName(u"ok_button")

        self.gridLayout.addWidget(self.ok_button, 0, 3, 1, 1)

        self.cancel_button = QPushButton(self.button_frame)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 0, 2, 1, 1)


        self.gridLayout_2.addWidget(self.button_frame, 2, 1, 1, 1)

        QWidget.setTabOrder(self.cancel_button, self.ok_button)

        self.retranslateUi(Dialog)
        self.cancel_button.clicked.connect(Dialog.close)
        self.ok_button.clicked.connect(Dialog.accept)

        self.cancel_button.setDefault(True)


        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Exit?", None))
        self.sidereal_label.setText(QCoreApplication.translate("Dialog", u"Are you sure you want to exit? Incomplete observations may not be usable.", None))
        self.ok_button.setText(QCoreApplication.translate("Dialog", u"Yes, Exit", None))
        self.cancel_button.setText(QCoreApplication.translate("Dialog", u"No, go back", None))
    # retranslateUi

