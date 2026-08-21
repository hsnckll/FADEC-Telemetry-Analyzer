# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(480, 560)
        Dialog.setMinimumSize(QtCore.QSize(480, 560))

        # Ana Dikey Düzen
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.verticalLayout.setSpacing(14)
        self.verticalLayout.setObjectName("verticalLayout")

        # 1. Başlık Alanı
        self.layout_baslik = QtWidgets.QVBoxLayout()
        self.layout_baslik.setSpacing(4)
        self.lbl_baslik = QtWidgets.QLabel(Dialog)
        font_baslik = QtGui.QFont()
        font_baslik.setPointSize(13)
        font_baslik.setBold(True)
        self.lbl_baslik.setFont(font_baslik)
        self.lbl_baslik.setStyleSheet("color: #00ffcc;")
        self.lbl_baslik.setObjectName("lbl_baslik")
        self.layout_baslik.addWidget(self.lbl_baslik)

        self.lbl_aciklama = QtWidgets.QLabel(Dialog)
        font_alt = QtGui.QFont()
        font_alt.setPointSize(9)
        self.lbl_aciklama.setFont(font_alt)
        self.lbl_aciklama.setStyleSheet("color: #aaaaaa;")
        self.lbl_aciklama.setObjectName("lbl_aciklama")
        self.layout_baslik.addWidget(self.lbl_aciklama)
        self.verticalLayout.addLayout(self.layout_baslik)

        # Ayırıcı Çizgi
        self.cizgi = QtWidgets.QFrame(Dialog)
        self.cizgi.setFrameShape(QtWidgets.QFrame.HLine)
        self.cizgi.setStyleSheet("color: #333333;")
        self.verticalLayout.addWidget(self.cizgi)

        # 2. Sensör Listesi (Genişleyen Liste)
        self.limit_sensor_listesi = QtWidgets.QListWidget(Dialog)
        self.limit_sensor_listesi.setObjectName("limit_sensor_listesi")
        self.verticalLayout.addWidget(self.limit_sensor_listesi)

        # 3. Butonlar Düzeni (Uygula Daha Geniş, Kaldır Daha Dar)
        self.layout_butonlar = QtWidgets.QHBoxLayout()
        self.layout_butonlar.setSpacing(10)
        self.layout_butonlar.setObjectName("layout_butonlar")

        self.btn_limitUygula = QtWidgets.QPushButton(Dialog)
        self.btn_limitUygula.setMinimumSize(QtCore.QSize(0, 42))
        font_btn = QtGui.QFont()
        font_btn.setPointSize(11)
        font_btn.setBold(True)
        self.btn_limitUygula.setFont(font_btn)
        self.btn_limitUygula.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_limitUygula.setObjectName("btn_limitUygula")
        self.layout_butonlar.addWidget(self.btn_limitUygula, 2)

        self.btn_limitKaldir = QtWidgets.QPushButton(Dialog)
        self.btn_limitKaldir.setMinimumSize(QtCore.QSize(0, 42))
        self.btn_limitKaldir.setFont(font_btn)
        self.btn_limitKaldir.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_limitKaldir.setObjectName("btn_limitKaldir")
        self.layout_butonlar.addWidget(self.btn_limitKaldir, 1)

        self.verticalLayout.addLayout(self.layout_butonlar)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "FADEC - Limit Kontrolü İçin Sensör Seçimi"))
        self.lbl_baslik.setText(_translate("Dialog", "⚙️ Limit Aşımı Kontrolü"))
        self.lbl_aciklama.setText(_translate("Dialog", "Grafikte limit çizgilerini görmek istediğiniz sensörleri işaretleyiniz."))
        self.btn_limitUygula.setText(_translate("Dialog", "✅ Değişiklikleri Uygula"))
        self.btn_limitKaldir.setText(_translate("Dialog", "❌ Limitleri Kaldır"))

# Geriye dönük uyumluluk alias
Ui_MinMaxDialog = Ui_Dialog
