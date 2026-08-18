# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(950, 750)
        Dialog.setMinimumSize(QtCore.QSize(950, 750))

        # Ana Dikey Düzen
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setContentsMargins(18, 18, 18, 18)
        self.verticalLayout.setSpacing(14)
        self.verticalLayout.setObjectName("verticalLayout")

        # 1. Üst Başlık ve Bilgi Kartı Alanı
        self.layout_ust = QtWidgets.QHBoxLayout()
        self.layout_ust.setSpacing(12)
        self.layout_ust.setObjectName("layout_ust")

        # Hata Aralığı Bilgi Kartı (Container)
        self.card_info = QtWidgets.QFrame(Dialog)
        self.card_info.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 6px;
                padding: 4px 12px;
            }
        """)
        self.layout_card = QtWidgets.QVBoxLayout(self.card_info)
        self.layout_card.setContentsMargins(8, 6, 8, 6)
        self.layout_card.setSpacing(2)

        self.lbl_baslik_kucuk = QtWidgets.QLabel("🏷️ İNCELENEN HATA BLOĞU & ZAMAN ARALIĞI", self.card_info)
        font_kucuk = QtGui.QFont()
        font_kucuk.setPointSize(8)
        font_kucuk.setBold(True)
        self.lbl_baslik_kucuk.setFont(font_kucuk)
        self.lbl_baslik_kucuk.setStyleSheet("color: #00ffcc; border: none; background: transparent;")
        self.layout_card.addWidget(self.lbl_baslik_kucuk)

        self.lbl_HataAraligi = QtWidgets.QLabel(self.card_info)
        font_hata = QtGui.QFont()
        font_hata.setPointSize(10)
        font_hata.setBold(True)
        self.lbl_HataAraligi.setFont(font_hata)
        self.lbl_HataAraligi.setStyleSheet("color: #ffffff; border: none; background: transparent;")
        self.lbl_HataAraligi.setObjectName("lbl_HataAraligi")
        self.layout_card.addWidget(self.lbl_HataAraligi)

        self.layout_ust.addWidget(self.card_info)

        # PNG Kaydet Butonu (Sağa Hizalı)
        self.btn_pngKaydetRadar = QtWidgets.QPushButton(Dialog)
        self.btn_pngKaydetRadar.setMinimumSize(QtCore.QSize(130, 42))
        font_btn = QtGui.QFont()
        font_btn.setPointSize(10)
        font_btn.setBold(True)
        self.btn_pngKaydetRadar.setFont(font_btn)
        self.btn_pngKaydetRadar.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_pngKaydetRadar.setObjectName("btn_pngKaydetRadar")
        self.layout_ust.addWidget(self.btn_pngKaydetRadar)

        self.verticalLayout.addLayout(self.layout_ust)

        # 2. Grafik Alanı (Radar Container)
        self.widget_Radar = QtWidgets.QWidget(Dialog)
        self.widget_Radar.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.widget_Radar.setObjectName("widget_Radar")
        self.verticalLayout.addWidget(self.widget_Radar)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Kök Neden ve Sensör Sapma Analizi (Radar - Z-Score)"))
        self.lbl_HataAraligi.setText(_translate("Dialog", "Hata Aralığı Yükleniyor..."))
        self.btn_pngKaydetRadar.setText(_translate("Dialog", "📷 PNG Kaydet"))

# Geriye dönük uyumluluk alias
Ui_RadarDialog = Ui_Dialog
