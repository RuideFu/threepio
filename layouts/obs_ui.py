# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'obs.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QDateTimeEdit, QDialog,
    QFrame, QGridLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QTimeEdit, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(264, 314)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setModal(True)
        self.gridLayout = QGridLayout(Dialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.button_frame = QFrame(Dialog)
        self.button_frame.setObjectName(u"button_frame")
        self.gridLayout_2 = QGridLayout(self.button_frame)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.accept_button = QPushButton(self.button_frame)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout_2.addWidget(self.accept_button, 0, 2, 1, 1)

        self.cancel_button = QPushButton(self.button_frame)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout_2.addWidget(self.cancel_button, 0, 1, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer, 0, 0, 1, 1)


        self.gridLayout.addWidget(self.button_frame, 9, 1, 1, 2)

        self.frame = QFrame(Dialog)
        self.frame.setObjectName(u"frame")
        self.gridLayout_3 = QGridLayout(self.frame)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.file_name_label = QLabel(self.frame)
        self.file_name_label.setObjectName(u"file_name_label")
        self.file_name_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.file_name_label, 0, 0, 1, 1)

        self.file_name_value = QLineEdit(self.frame)
        self.file_name_value.setObjectName(u"file_name_value")
        font = QFont()
        font.setFamilies([u"Iosevka Aile"])
        self.file_name_value.setFont(font)

        self.gridLayout_3.addWidget(self.file_name_value, 0, 2, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(20, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        self.gridLayout_3.addItem(self.horizontalSpacer_2, 0, 1, 1, 1)


        self.gridLayout.addWidget(self.frame, 8, 1, 1, 2)

        self.end_label = QLabel(Dialog)
        self.end_label.setObjectName(u"end_label")
        self.end_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.end_label, 1, 1, 1, 1)

        self.min_dec = QLineEdit(Dialog)
        self.min_dec.setObjectName(u"min_dec")
        self.min_dec.setFont(font)

        self.gridLayout.addWidget(self.min_dec, 2, 2, 1, 1)

        self.start_label = QLabel(Dialog)
        self.start_label.setObjectName(u"start_label")
        self.start_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.start_label, 0, 1, 1, 1)

        self.error_label = QLabel(Dialog)
        self.error_label.setObjectName(u"error_label")
        font1 = QFont()
        font1.setBold(True)
        self.error_label.setFont(font1)
        self.error_label.setStyleSheet(u"color: red")
        self.error_label.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.error_label, 10, 1, 1, 2)

        self.data_acquisition_rate_value = QSpinBox(Dialog)
        self.data_acquisition_rate_value.setObjectName(u"data_acquisition_rate_value")
        self.data_acquisition_rate_value.setFont(font)
        self.data_acquisition_rate_value.setMinimum(1)
        self.data_acquisition_rate_value.setMaximum(100)

        self.gridLayout.addWidget(self.data_acquisition_rate_value, 6, 2, 1, 1)

        self.end_dec_label = QLabel(Dialog)
        self.end_dec_label.setObjectName(u"end_dec_label")
        self.end_dec_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.end_dec_label, 4, 1, 1, 1)

        self.start_dec_label = QLabel(Dialog)
        self.start_dec_label.setObjectName(u"start_dec_label")
        self.start_dec_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.start_dec_label, 2, 1, 1, 1)

        self.line = QFrame(Dialog)
        self.line.setObjectName(u"line")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.line.sizePolicy().hasHeightForWidth())
        self.line.setSizePolicy(sizePolicy1)
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line, 7, 1, 1, 2)

        self.data_acquisition_rate_label = QLabel(Dialog)
        self.data_acquisition_rate_label.setObjectName(u"data_acquisition_rate_label")
        self.data_acquisition_rate_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.data_acquisition_rate_label, 6, 1, 1, 1)

        self.start_time = QTimeEdit(Dialog)
        self.start_time.setObjectName(u"start_time")
        self.start_time.setFont(font)
        self.start_time.setButtonSymbols(QAbstractSpinBox.NoButtons)

        self.gridLayout.addWidget(self.start_time, 0, 2, 1, 1)

        self.max_dec = QLineEdit(Dialog)
        self.max_dec.setObjectName(u"max_dec")
        self.max_dec.setFont(font)

        self.gridLayout.addWidget(self.max_dec, 4, 2, 1, 1)

        self.end_time = QDateTimeEdit(Dialog)
        self.end_time.setObjectName(u"end_time")
        self.end_time.setFont(font)
        self.end_time.setButtonSymbols(QAbstractSpinBox.NoButtons)

        self.gridLayout.addWidget(self.end_time, 1, 2, 1, 1)

        self.warning_label = QLabel(Dialog)
        self.warning_label.setObjectName(u"warning_label")
        self.warning_label.setFont(font1)
        self.warning_label.setStyleSheet(u"color: darkorange")
        self.warning_label.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.warning_label, 11, 1, 1, 2)

#if QT_CONFIG(shortcut)
        self.data_acquisition_rate_label.setBuddy(self.data_acquisition_rate_value)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.start_time, self.end_time)
        QWidget.setTabOrder(self.end_time, self.min_dec)
        QWidget.setTabOrder(self.min_dec, self.max_dec)
        QWidget.setTabOrder(self.max_dec, self.data_acquisition_rate_value)
        QWidget.setTabOrder(self.data_acquisition_rate_value, self.file_name_value)
        QWidget.setTabOrder(self.file_name_value, self.accept_button)
        QWidget.setTabOrder(self.accept_button, self.cancel_button)

        self.retranslateUi(Dialog)
        self.cancel_button.clicked.connect(Dialog.reject)
        self.accept_button.clicked.connect(Dialog.accept)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"New Observation", None))
        self.accept_button.setText(QCoreApplication.translate("Dialog", u"Next", None))
        self.cancel_button.setText(QCoreApplication.translate("Dialog", u"Cancel", None))
        self.file_name_label.setText(QCoreApplication.translate("Dialog", u"File name", None))
        self.end_label.setText(QCoreApplication.translate("Dialog", u"Ending RA", None))
        self.start_label.setText(QCoreApplication.translate("Dialog", u"Starting RA", None))
        self.error_label.setText(QCoreApplication.translate("Dialog", u"Error creating observation", None))
        self.end_dec_label.setText(QCoreApplication.translate("Dialog", u"Maximum Declination", None))
        self.start_dec_label.setText(QCoreApplication.translate("Dialog", u"Minimum Declination", None))
        self.data_acquisition_rate_label.setText(QCoreApplication.translate("Dialog", u"Data Acquisition Rate", None))
        self.start_time.setDisplayFormat(QCoreApplication.translate("Dialog", u"HH:mm:ss", None))
        self.end_time.setDisplayFormat(QCoreApplication.translate("Dialog", u"HH:mm:ss", None))
        self.warning_label.setText(QCoreApplication.translate("Dialog", u"Warning about observation", None))
    # retranslateUi

