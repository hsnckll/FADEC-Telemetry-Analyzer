# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(620, 360)
        Dialog.setMinimumSize(QtCore.QSize(620, 360))
        Dialog.setMaximumSize(QtCore.QSize(620, 360))

        # Ana Dikey Düzen
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setContentsMargins(25, 25, 25, 25)
        self.verticalLayout.setSpacing(18)
        self.verticalLayout.setObjectName("verticalLayout")

        # 1. Başlık Alanı
        self.layout_baslik = QtWidgets.QVBoxLayout()
        self.layout_baslik.setSpacing(4)
        self.lbl_baslik = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        self.lbl_baslik.setFont(font)
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

        # 2. Form Alanı (Data ve Event Seçimi)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setHorizontalSpacing(12)
        self.gridLayout.setVerticalSpacing(14)
        self.gridLayout.setObjectName("gridLayout")

        # Data Record Satırı
        self.lbl_data = QtWidgets.QLabel(Dialog)
        font_label = QtGui.QFont()
        font_label.setPointSize(10)
        font_label.setBold(True)
        self.lbl_data.setFont(font_label)
        self.lbl_data.setObjectName("lbl_data")
        self.gridLayout.addWidget(self.lbl_data, 0, 0, 1, 1)

        self.txt_data_yolu = QtWidgets.QLineEdit(Dialog)
        self.txt_data_yolu.setMinimumSize(QtCore.QSize(0, 36))
        self.txt_data_yolu.setReadOnly(True)
        self.txt_data_yolu.setPlaceholderText("Data Record dosyası seçilmedi...")
        self.txt_data_yolu.setObjectName("txt_data_yolu")
        self.gridLayout.addWidget(self.txt_data_yolu, 0, 1, 1, 1)

        self.btn_data_sec = QtWidgets.QPushButton(Dialog)
        self.btn_data_sec.setMinimumSize(QtCore.QSize(110, 36))
        font_btn = QtGui.QFont()
        font_btn.setPointSize(10)
        font_btn.setBold(True)
        self.btn_data_sec.setFont(font_btn)
        self.btn_data_sec.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_data_sec.setObjectName("btn_data_sec")
        self.gridLayout.addWidget(self.btn_data_sec, 0, 2, 1, 1)

        # Event Record Satırı
        self.lbl_event = QtWidgets.QLabel(Dialog)
        self.lbl_event.setFont(font_label)
        self.lbl_event.setObjectName("lbl_event")
        self.gridLayout.addWidget(self.lbl_event, 1, 0, 1, 1)

        self.txt_event_yolu = QtWidgets.QLineEdit(Dialog)
        self.txt_event_yolu.setMinimumSize(QtCore.QSize(0, 36))
        self.txt_event_yolu.setReadOnly(True)
        self.txt_event_yolu.setPlaceholderText("Event Record dosyası seçilmedi...")
        self.txt_event_yolu.setObjectName("txt_event_yolu")
        self.gridLayout.addWidget(self.txt_event_yolu, 1, 1, 1, 1)

        self.btn_event_sec = QtWidgets.QPushButton(Dialog)
        self.btn_event_sec.setMinimumSize(QtCore.QSize(110, 36))
        self.btn_event_sec.setFont(font_btn)
        self.btn_event_sec.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_event_sec.setObjectName("btn_event_sec")
        self.gridLayout.addWidget(self.btn_event_sec, 1, 2, 1, 1)

        self.verticalLayout.addLayout(self.gridLayout)

        spacerItem = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        # 3. Alt Buton Alanı
        self.btn_yuklebirlestir = QtWidgets.QPushButton(Dialog)
        self.btn_yuklebirlestir.setMinimumSize(QtCore.QSize(0, 42))
        font_onay = QtGui.QFont()
        font_onay.setPointSize(11)
        font_onay.setBold(True)
        self.btn_yuklebirlestir.setFont(font_onay)
        self.btn_yuklebirlestir.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_yuklebirlestir.setObjectName("btn_yuklebirlestir")
        self.verticalLayout.addWidget(self.btn_yuklebirlestir)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "FADEC - Veri Dosyalarını Seç"))
        self.lbl_baslik.setText(_translate("Dialog", "📁 Telemetri ve Olay Kaydı Yükleme"))
        self.lbl_aciklama.setText(_translate("Dialog", "Analiz etmek istediğiniz Data Record (.csv/.xlsx) ve Event Record dosyalarını seçiniz."))
        self.lbl_data.setText(_translate("Dialog", "Data Record:"))
        self.btn_data_sec.setText(_translate("Dialog", "Gözat..."))
        self.lbl_event.setText(_translate("Dialog", "Event Record:"))
        self.btn_event_sec.setText(_translate("Dialog", "Gözat..."))
        self.btn_yuklebirlestir.setText(_translate("Dialog", "Verileri Yükle ve Birleştir"))

# Geriye dönük uyumluluk alias
Ui_DosyaSecimDialog = Ui_Dialog
