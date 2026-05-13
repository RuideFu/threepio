# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dec_cal.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(554, 369)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.cal_display_widget = QWidget(Dialog)
        self.cal_display_widget.setObjectName(u"cal_display_widget")
        self.gridLayout = QGridLayout(self.cal_display_widget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.degree_values_label = QLabel(self.cal_display_widget)
        self.degree_values_label.setObjectName(u"degree_values_label")
        font = QFont()
        font.setFamilies([u"Iosevka Aile"])
        font.setBold(True)
        self.degree_values_label.setFont(font)
        self.degree_values_label.setAlignment(Qt.AlignRight|Qt.AlignTop|Qt.AlignTrailing)

        self.gridLayout.addWidget(self.degree_values_label, 0, 2, 1, 1)

        self.input_data_label = QLabel(self.cal_display_widget)
        self.input_data_label.setObjectName(u"input_data_label")
        font1 = QFont()
        font1.setFamilies([u"Iosevka Aile"])
        self.input_data_label.setFont(font1)
        self.input_data_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.gridLayout.addWidget(self.input_data_label, 0, 3, 1, 1)


        self.verticalLayout.addWidget(self.cal_display_widget)

        self.set_dec_widget = QWidget(Dialog)
        self.set_dec_widget.setObjectName(u"set_dec_widget")
        self.horizontalLayout = QHBoxLayout(self.set_dec_widget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, 0)
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.set_dec_label = QLabel(self.set_dec_widget)
        self.set_dec_label.setObjectName(u"set_dec_label")

        self.horizontalLayout.addWidget(self.set_dec_label)

        self.set_dec_value = QLabel(self.set_dec_widget)
        self.set_dec_value.setObjectName(u"set_dec_value")
        font2 = QFont()
        font2.setFamilies([u"Iosevka Aile"])
        font2.setPointSize(20)
        self.set_dec_value.setFont(font2)
        self.set_dec_value.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout.addWidget(self.set_dec_value)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)


        self.verticalLayout.addWidget(self.set_dec_widget)

        self.warning_label = QLabel(Dialog)
        self.warning_label.setObjectName(u"warning_label")
        self.warning_label.setEnabled(True)
        font3 = QFont()
        font3.setBold(True)
        self.warning_label.setFont(font3)
        self.warning_label.setStyleSheet(u"color: darkorange")
        self.warning_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.warning_label)

        self.button_frame = QFrame(Dialog)
        self.button_frame.setObjectName(u"button_frame")
        self.horizontalLayout_3 = QHBoxLayout(self.button_frame)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.north_south_combo_box = QComboBox(self.button_frame)
        self.north_south_combo_box.addItem("")
        self.north_south_combo_box.addItem("")
        self.north_south_combo_box.setObjectName(u"north_south_combo_box")

        self.horizontalLayout_3.addWidget(self.north_south_combo_box)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.discard_cal_button = QPushButton(self.button_frame)
        self.discard_cal_button.setObjectName(u"discard_cal_button")

        self.horizontalLayout_3.addWidget(self.discard_cal_button)

        self.previous_button = QPushButton(self.button_frame)
        self.previous_button.setObjectName(u"previous_button")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.previous_button.sizePolicy().hasHeightForWidth())
        self.previous_button.setSizePolicy(sizePolicy)

        self.horizontalLayout_3.addWidget(self.previous_button)

        self.next_button = QPushButton(self.button_frame)
        self.next_button.setObjectName(u"next_button")

        self.horizontalLayout_3.addWidget(self.next_button)

        self.record_button = QPushButton(self.button_frame)
        self.record_button.setObjectName(u"record_button")
        self.record_button.setCheckable(False)

        self.horizontalLayout_3.addWidget(self.record_button)

        self.save_button = QPushButton(self.button_frame)
        self.save_button.setObjectName(u"save_button")
        self.save_button.setEnabled(False)

        self.horizontalLayout_3.addWidget(self.save_button)


        self.verticalLayout.addWidget(self.button_frame)

        QWidget.setTabOrder(self.north_south_combo_box, self.record_button)
        QWidget.setTabOrder(self.record_button, self.next_button)
        QWidget.setTabOrder(self.next_button, self.previous_button)
        QWidget.setTabOrder(self.previous_button, self.discard_cal_button)
        QWidget.setTabOrder(self.discard_cal_button, self.save_button)

        self.retranslateUi(Dialog)
        self.discard_cal_button.clicked.connect(Dialog.close)

        self.record_button.setDefault(True)


        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Declination Calibration", None))
        self.degree_values_label.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p>-25<br/>-15<br/>-5<br/>5<br/>15<br/>25<br/>35<br/>45<br/>55<br/>65<br/>75<br/>85<br/>95</p></body></html>", None))
        self.input_data_label.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p>-25<br/>-15<br/>-5<br/>5<br/>15<br/>25<br/>35<br/>45<br/>55<br/>65<br/>75<br/>85<br/>95</p></body></html>", None))
        self.set_dec_label.setText(QCoreApplication.translate("Dialog", u"Currently calibrating", None))
        self.set_dec_value.setText(QCoreApplication.translate("Dialog", u"N\u00b0", None))
        self.warning_label.setText(QCoreApplication.translate("Dialog", u"Warning about data", None))
        self.north_south_combo_box.setItemText(0, QCoreApplication.translate("Dialog", u"S \u2192 N", None))
        self.north_south_combo_box.setItemText(1, QCoreApplication.translate("Dialog", u"N \u2192 S", None))

        self.discard_cal_button.setText(QCoreApplication.translate("Dialog", u"Discard All", None))
        self.previous_button.setText(QCoreApplication.translate("Dialog", u"<", None))
        self.next_button.setText(QCoreApplication.translate("Dialog", u">", None))
        self.record_button.setText(QCoreApplication.translate("Dialog", u"Record", None))
        self.save_button.setText(QCoreApplication.translate("Dialog", u"Save", None))
    # retranslateUi

