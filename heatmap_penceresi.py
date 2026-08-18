# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(920, 720)
        Dialog.setMinimumSize(QtCore.QSize(920, 720))

        # Ana Dikey Düzen
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setContentsMargins(15, 15, 15, 15)
        self.verticalLayout.setSpacing(12)
        self.verticalLayout.setObjectName("verticalLayout")

        # 1. Üst Toolbar
        self.layout_toolbar = QtWidgets.QHBoxLayout()
        self.layout_toolbar.setSpacing(10)
        self.layout_toolbar.setObjectName("layout_toolbar")

        # Kolon Seçim ComboBox
        self.combobx_kolon = QtWidgets.QComboBox(Dialog)
        self.combobx_kolon.setMinimumSize(QtCore.QSize(240, 38))
        self.combobx_kolon.setMaximumSize(QtCore.QSize(280, 38))
        font_combo = QtGui.QFont()
        font_combo.setPointSize(10)
        font_combo.setBold(True)
        self.combobx_kolon.setFont(font_combo)
        self.combobx_kolon.setObjectName("combobx_kolon")
        self.layout_toolbar.addWidget(self.combobx_kolon)

        # Uygula / Çiz Butonu
        self.btn_uygula = QtWidgets.QPushButton(Dialog)
        self.btn_uygula.setMinimumSize(QtCore.QSize(100, 38))
        font_btn = QtGui.QFont()
        font_btn.setPointSize(10)
        font_btn.setBold(True)
        self.btn_uygula.setFont(font_btn)
        self.btn_uygula.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_uygula.setObjectName("btn_uygula")
        self.layout_toolbar.addWidget(self.btn_uygula)

        # Tümünü Göster Butonu
        self.btn_tumunuGoster = QtWidgets.QPushButton(Dialog)
        self.btn_tumunuGoster.setMinimumSize(QtCore.QSize(130, 38))
        self.btn_tumunuGoster.setFont(font_btn)
        self.btn_tumunuGoster.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_tumunuGoster.setObjectName("btn_tumunuGoster")
        self.layout_toolbar.addWidget(self.btn_tumunuGoster)

        # Tümünü Sil Butonu
        self.btn_silme = QtWidgets.QPushButton(Dialog)
        self.btn_silme.setMinimumSize(QtCore.QSize(110, 38))
        self.btn_silme.setFont(font_btn)
        self.btn_silme.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_silme.setObjectName("btn_silme")
        self.layout_toolbar.addWidget(self.btn_silme)

        # Araya Esnek Boşluk (PNG Kaydet sağa yaslansın)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.layout_toolbar.addItem(spacerItem)

        # PNG Kaydet Butonu
        self.btn_pngKaydet = QtWidgets.QPushButton(Dialog)
        self.btn_pngKaydet.setMinimumSize(QtCore.QSize(130, 38))
        self.btn_pngKaydet.setFont(font_btn)
        self.btn_pngKaydet.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_pngKaydet.setObjectName("btn_pngKaydet")
        self.layout_toolbar.addWidget(self.btn_pngKaydet)

        self.verticalLayout.addLayout(self.layout_toolbar)

        # 2. Grafik Alanı (Heatmap Container)
        self.widget_HeatMap = QtWidgets.QWidget(Dialog)
        self.widget_HeatMap.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.widget_HeatMap.setObjectName("widget_HeatMap")
        self.verticalLayout.addWidget(self.widget_HeatMap)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Sensörler Arası Korelasyon Analizi (HeatMap)"))
        self.btn_uygula.setText(_translate("Dialog", "Uygula"))
        self.btn_tumunuGoster.setText(_translate("Dialog", "Tümünü Göster"))
        self.btn_silme.setText(_translate("Dialog", "Tümünü Sil"))
        self.btn_pngKaydet.setText(_translate("Dialog", "📷 PNG Kaydet"))

# Geriye dönük uyumluluk alias
Ui_HeatmapDialog = Ui_Dialog
