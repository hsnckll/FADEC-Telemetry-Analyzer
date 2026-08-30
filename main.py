# -*- coding: utf-8 -*-
"""
@file main.py
@brief FADEC Veri Görselleştirme ve Teşhis Analiz Platformu Ana Modülü.
@details Havacılık gaz türbinli motor sensör verilerini gerçek zamanlı ve yüksek
         başarımla görselleştiren, LTTB ve Sanal Model (Virtual Table)
         mimarisiyle büyük veri (3+ Milyon satır) üzerinde kriz anlarını, korelasyonları
         ve kök neden sapmalarını (Z-Score) analiz eden masaüstü uygulaması.

@author FADEC Geliştirme Ekibi
@date 2026
@version 2.0
"""

# ==============================================================================
# 1. STANDART KÜTÜPHANELER
# ==============================================================================
import os
import sys
import time
import random
import ctypes
import datetime
from collections import deque

# ==============================================================================
# 2. ÜÇÜNCÜ PARTİ BİLİMSEL VE GRAFİK KÜTÜPHANELERİ
# ==============================================================================
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from mpl_toolkits.axes_grid1 import make_axes_locatable

import pyqtgraph as pg
from pyqtgraph import mkPen
from grafik_class import SensorGrafikKarti,  kareli_izgara_deseni_olustur, DashboardTuval

pg.setConfigOptions(useOpenGL=True, enableExperimental=False, antialias=False)
# ==============================================================================
# 3. PYQT5 ARAYÜZ BİLEŞENLERİ
# ==============================================================================
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDialog, QFileDialog, QMessageBox,
    QTableWidgetItem, QListWidgetItem, QSplashScreen, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap, QBrush, QColor, QFont
from pyqtgraph.exporters import ImageExporter
# ==============================================================================
# 4. KULLANICI ARAYÜZÜ (UI) MODÜLLERİ
# ==============================================================================
from arayuz_python import Ui_MainWindow
from limit_ayarlari_python import Ui_Dialog as Ui_LimitDialog
from minmax_python import Ui_Dialog as Ui_MinMaxDialog
from dosya_secim_python import Ui_Dialog as Ui_DosyaSecimDialog
from radar_penceresi import Ui_Dialog as Ui_RadarDialog
from heatmap_penceresi import Ui_Dialog as Ui_HeatmapDialog
from ai import AIPromptBuilder
from generate_pdf import PDFRaporMotoru


# ==============================================================================
# 5. MODERN KOYU TEMA (DARK THEME QSS)
# ==============================================================================
KOYU_TEMA_QSS = """
QSplitter::handle { background-color: #2b2b2b; }
QSplitter::handle:horizontal { background-color: #2b2b2b; width: 4px; }
QSplitter::handle:vertical { background-color: #2b2b2b; height: 4px; }
QSplitter::handle:hover { background-color: #00ffcc; }

QTableView, QTableWidget {
    background-color: #181818;
    alternate-background-color: #1e1e1e;
    color: #e0e0e0;
    gridline-color: #2a2a2a;
    border: 1px solid #333333;
}

QHeaderView::section {
    background-color: #252526;
    color: #00ffcc;
    padding: 6px;
    border: 1px solid #333333;
    font-weight: bold;
}

QTableCornerButton::section {
    background-color: #252526;
    border: 1px solid #333333;
}

QListWidget {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: 1px solid #333;
    border-radius: 6px;
    font-family: 'Segoe UI', Arial;
    font-size: 14px;
    outline: none;
}

QListWidget::item {
    padding: 12px;
    border-bottom: 1px solid #2a2a2a;
    font-weight: bold;
    font-size: 15px;
}

QListWidget::item:hover { background-color: #2d2d30; }
QListWidget::item:selected {
    background-color: #264f78;
    color: white;
    border-left: 5px solid #00ffcc;
}

QLineEdit {
    background-color: #333333;
    color: #ffffff;
    border: 1px solid #555555;
    padding: 5px;
    border-radius: 4px;
}

QMainWindow, QDialog { background-color: #1e1e1e; }
QWidget { color: #ffffff; font-family: "Segoe UI", Arial, sans-serif; font-size: 10pt; }

QPushButton {
    background-color: #3a3a3a;
    border: 2px solid #555555;
    border-radius: 6px;
    padding: 4px 8px;
    font-weight: bold;
    font-size: 11pt;
    color: #ffffff;
}
QPushButton:hover {
    background-color: #00ffcc;
    color: #000000;
    border: 2px solid #00ffcc;
}
QPushButton:pressed { background-color: #00ccaa; }

QComboBox {
    background-color: #2b2b2b;
    border: 1px solid #444444;
    padding: 4px 10px;
    border-radius: 6px;
    color: #ffffff;
    font-size: 11pt;
    font-weight: bold;
    min-height: 28px;
}
QComboBox:hover { border: 1px solid #00ffcc; background-color: #333333; }



QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid #444444;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    background-color: #242424;
}
QComboBox::drop-down:hover {
    background-color: #333333;
}
QComboBox::down-arrow {
    image: url(asagi_ok.png);
    width: 12px;
    height: 12px;
}


QComboBox QAbstractItemView {
    background-color: #1e1e1e;
    color: #ffffff;
    selection-background-color: #00ffcc;
    selection-color: #000000;
    border: 1px solid #444444;
    outline: none;
    padding: 4px;
}
QComboBox QAbstractItemView::item {
    min-height: 26px;
    padding: 4px 8px;
    color: #ffffff;
    background-color: #1e1e1e;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #2d2d30;
    color: #00ffcc;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #00ffcc;
    color: #000000;
    font-weight: bold;
}

QCheckBox {
    color: #ffffff;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555555;
    background-color: #252526;
    border-radius: 3px;
}
QCheckBox::indicator:hover {
    border: 1px solid #00ffcc;
}
QCheckBox::indicator:checked {
    background-color: #00ffcc;
    border: 1px solid #00ffcc;
}

QTabWidget::pane { border: 1px solid #333333; background: #181818; }
QTabBar::tab {
    background: #252526;
    color: #a0a0a0;
    font-size: 11pt;
    font-weight: bold;
    min-height: 32px;
    min-width: 190px;
    padding: 4px 10px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border: 1px solid #333333;
    border-bottom: none;
}
QTabBar::tab:hover { background: #2d2d30; color: #ffffff; }
QTabBar::tab:selected {
    background: #181818;
    color: #00ffcc;
    font-weight: bold;
    border-top: 3px solid #00ffcc;
    border-bottom: 1px solid #181818;
}

QScrollBar:horizontal, QScrollBar:vertical {
    background-color: #1e1e1e;
    border: none;
    width: 14px;
    height: 14px;
}
QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
    background-color: #555555;
    border-radius: 6px;
    min-height: 20px;
    min-width: 20px;
}
QScrollBar::handle:hover { background-color: #777777; }

QMdiArea, #tab_4 {
    background-color: #181818;
    border: none;
}
QMdiSubWindow {
    background-color: #1a1a1a;
    border: 1px solid #383838;
    border-radius: 4px;
}
QMdiSubWindow:active {
    border: 1px solid #00ffcc;
}
QMdiSubWindow QLabel, QMdiSubWindow > QWidget {
    background-color: transparent;
    background: transparent;
}
"""

# ==============================================================================
# 5.1 MODERN AÇIK TEMA (LIGHT THEME QSS - PREMIUM AEROSPACE EDITION)
# ==============================================================================
ACIK_TEMA_QSS = """
QSplitter::handle { background-color: #e2e8f0; }
QSplitter::handle:horizontal { background-color: #e2e8f0; width: 4px; }
QSplitter::handle:vertical { background-color: #e2e8f0; height: 4px; }
QSplitter::handle:hover { background-color: #0284c7; }

QTableView, QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f8fafc;
    color: #0f172a;
    gridline-color: #e2e8f0;
    border: 1px solid #cbd5e1;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #f1f5f9;
    color: #0369a1;
    padding: 6px;
    border: 1px solid #cbd5e1;
    font-weight: bold;
}

QTableCornerButton::section {
    background-color: #f1f5f9;
    border: 1px solid #cbd5e1;
}

QListWidget {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    font-family: 'Segoe UI', Arial;
    font-size: 14px;
    outline: none;
}

QListWidget::item {
    padding: 12px;
    border-bottom: 1px solid #f1f5f9;
    font-weight: bold;
    font-size: 15px;
    color: #1e293b;
}

QListWidget::item:hover { 
    background-color: #f8fafc; 
    color: #0284c7;
}

QListWidget::item:selected {
    background-color: #e0f2fe;
    color: #0369a1;
    border-left: 5px solid #0284c7;
}

QLineEdit {
    background-color: #ffffff;
    color: #0f172a;
    border: 1.5px solid #cbd5e1;
    padding: 5px;
    border-radius: 5px;
}
QLineEdit:focus {
    border: 1.5px solid #0284c7;
}

QMainWindow, QDialog { background-color: #f1f5f9; }
QWidget { color: #0f172a; font-family: "Segoe UI", Arial, sans-serif; font-size: 10pt; }

QPushButton {
    background-color: #ffffff;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px 10px;
    font-weight: bold;
    font-size: 11pt;
    color: #1e293b;
}
QPushButton:hover {
    background-color: #0284c7;
    color: #ffffff;
    border: 1.5px solid #0284c7;
}
QPushButton:pressed { 
    background-color: #0369a1; 
    color: #ffffff;
}

QComboBox {
    background-color: #ffffff;
    border: 1.5px solid #cbd5e1;
    padding: 4px 10px;
    border-radius: 6px;
    color: #0f172a;
    font-size: 11pt;
    font-weight: bold;
    min-height: 28px;
}
QComboBox:hover { border: 1.5px solid #0284c7; background-color: #f8fafc; }

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1.5px solid #cbd5e1;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    background-color: #f8fafc;
}
QComboBox::drop-down:hover {
    background-color: #e2e8f0;
}
QComboBox::down-arrow {
    image: url(asagi_ok_koyu.png);
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #0f172a;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
    border: 1px solid #cbd5e1;
    outline: none;
    padding: 4px;
}
QComboBox QAbstractItemView::item {
    min-height: 26px;
    padding: 4px 8px;
    color: #0f172a;
    background-color: #ffffff;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #f0f9ff;
    color: #0284c7;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #0284c7;
    color: #ffffff;
    font-weight: bold;
}

QCheckBox {
    color: #1e293b;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1.5px solid #94a3b8;
    background-color: #ffffff;
    border-radius: 3px;
}
QCheckBox::indicator:hover {
    border: 1.5px solid #0284c7;
}
QCheckBox::indicator:checked {
    background-color: #0284c7;
    border: 1.5px solid #0284c7;
}

QTabWidget::pane { border: 1px solid #cbd5e1; background: #ffffff; }
QTabBar::tab {
    background: #e2e8f0;
    color: #64748b;
    font-size: 11pt;
    font-weight: bold;
    min-height: 32px;
    min-width: 190px;
    padding: 4px 10px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border: 1px solid #cbd5e1;
    border-bottom: none;
}
QTabBar::tab:hover { background: #edf2f7; color: #0f172a; }
QTabBar::tab:selected {
    background: #ffffff;
    color: #0284c7;
    font-weight: bold;
    border-top: 3px solid #0284c7;
    border-bottom: 1px solid #ffffff;
}

QScrollBar:horizontal, QScrollBar:vertical {
    background-color: #f1f5f9;
    border: none;
    width: 12px;
    height: 12px;
}
QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
    background-color: #cbd5e1;
    border-radius: 6px;
    min-height: 20px;
    min-width: 20px;
}
QScrollBar::handle:hover { background-color: #94a3b8; }

QMdiArea, #tab_4 {
    background-color: #f8fafc;
    border: none;
}
"""

class AIPromptPenceresi(QtWidgets.QDialog):
    def __init__(self, prompt_metni, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yapay Zeka - Prompt Çıktısı")
        self.setMinimumSize(850, 650)
        self.aktif_tema = getattr(parent, 'aktif_tema', 'dark') if parent is not None else 'dark'

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Bilgi Etiketi
        self.lbl_bilgi = QtWidgets.QLabel("Aşağıdaki metni kopyalayarak yapay zeka arayüzüne yapıştırabilirsiniz:")
        layout.addWidget(self.lbl_bilgi)

        # Metin Kutusu (Sadece Okunabilir)
        self.txt_prompt = QtWidgets.QTextEdit()
        self.txt_prompt.setReadOnly(True)
        self.txt_prompt.setPlainText(prompt_metni)
        font = QtGui.QFont("Consolas", 10)
        self.txt_prompt.setFont(font)
        layout.addWidget(self.txt_prompt)

        # Alt Butonlar Layout
        btn_layout = QtWidgets.QHBoxLayout()

        self.btn_kopyala = QtWidgets.QPushButton("📋 Panoya Kopyala")
        self.btn_kopyala.setMinimumHeight(44)
        self.btn_kopyala.setCursor(QtCore.Qt.PointingHandCursor)

        self.btn_kapat = QtWidgets.QPushButton("Kapat")
        self.btn_kapat.setMinimumHeight(44)
        self.btn_kapat.setCursor(QtCore.Qt.PointingHandCursor)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_kopyala, 2)
        btn_layout.addWidget(self.btn_kapat, 1)

        layout.addLayout(btn_layout)

        # Sinyaller
        self.btn_kopyala.clicked.connect(self.panoya_kopyala)
        self.btn_kapat.clicked.connect(self.close)

        self.tema_uygula()

    def tema_uygula(self):
        if self.aktif_tema == "light":
            self.setStyleSheet("QDialog { background-color: #f8fafc; }")
            self.lbl_bilgi.setStyleSheet("font-weight: bold; font-size: 11pt; color: #0284c7; background: transparent;")
            self.txt_prompt.setStyleSheet("""
                QTextEdit {
                    background-color: #ffffff;
                    color: #0f172a;
                    border: 1.5px solid #cbd5e1;
                    border-radius: 6px;
                    padding: 12px;
                    selection-background-color: #0284c7;
                    selection-color: #ffffff;
                }
            """)
            self.btn_kopyala.setStyleSheet("""
                QPushButton {
                    background-color: #0284c7;
                    color: #ffffff;
                    font-weight: bold;
                    font-size: 11pt;
                    border-radius: 6px;
                    border: 1px solid #0284c7;
                    padding: 6px 14px;
                }
                QPushButton:hover {
                    background-color: #0369a1;
                    border-color: #0369a1;
                }
            """)
            self.btn_kapat.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #334155;
                    font-weight: bold;
                    font-size: 11pt;
                    border-radius: 6px;
                    border: 1.5px solid #cbd5e1;
                    padding: 6px 14px;
                }
                QPushButton:hover {
                    background-color: #f1f5f9;
                    color: #0f172a;
                }
            """)
        else:
            self.setStyleSheet("QDialog { background-color: #1e1e1e; }")
            self.lbl_bilgi.setStyleSheet("font-weight: bold; font-size: 11pt; color: #00ffcc; background: transparent;")
            self.txt_prompt.setStyleSheet("""
                QTextEdit {
                    background-color: #181818;
                    color: #e0e0e0;
                    border: 1px solid #333333;
                    border-radius: 6px;
                    padding: 12px;
                    selection-background-color: #00ffcc;
                    selection-color: #000000;
                }
            """)
            self.btn_kopyala.setStyleSheet("""
                QPushButton {
                    background-color: #00ffcc;
                    color: #000000;
                    font-weight: bold;
                    font-size: 11pt;
                    border-radius: 6px;
                    padding: 6px 14px;
                }
                QPushButton:hover {
                    background-color: #00ccaa;
                }
            """)
            self.btn_kapat.setStyleSheet("""
                QPushButton {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    font-weight: bold;
                    font-size: 11pt;
                    border-radius: 6px;
                    border: 1px solid #444444;
                    padding: 6px 14px;
                }
                QPushButton:hover {
                    background-color: #383838;
                }
            """)

    def panoya_kopyala(self):
        QtWidgets.QApplication.clipboard().setText(self.txt_prompt.toPlainText())
        self.btn_kopyala.setText("✅ Kopyalandı!")
        self.btn_kopyala.setStyleSheet("""
            QPushButton {
                background-color: #16a34a;
                color: #ffffff;
                font-weight: bold;
                font-size: 11pt;
                border-radius: 6px;
                padding: 6px 14px;
                border: 1px solid #16a34a;
            }
        """)
        # 2.5 Saniye sonra butonu eski haline getir
        QtCore.QTimer.singleShot(2500, self.kopyala_reset)

    def kopyala_reset(self):
        self.btn_kopyala.setText("📋 Panoya Kopyala")
        self.tema_uygula()









# ==============================================================================
# 6. YARDIMCI FONKSİYONLAR VE EKSEN DÖNÜŞTÜRÜCÜLER
# ==============================================================================

def kaynak_yolu(goreceli_yol):
    """
    @brief Dinamik kaynak dosyası mutlak yolunu çözümler.
    @details Uygulamanın geliştirme ortamında (.py) veya derlenmiş tekil
             yürütülebilir dosya (.exe / PyInstaller MEIPASS) olarak çalışmasına
             bağlı kalmaksızın kaynak dosyasının (logo, ikon vb.) doğru mutlak yolunu döner.
    @param goreceli_yol (str) Aranacak dosyanın göreceli dosya yolu.
    @return (str) Çözümlenmiş mutlak dosya yolu.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, goreceli_yol)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), goreceli_yol)


def csv_ayrac_tespit_et(dosya_yolu):
    """
    @brief CSV dosyasının ilk satırlarını analiz ederek ayraç karakterini (virgül, noktalı virgül, tab) otomatik tespit eder.
    @param dosya_yolu (str) Taranacak CSV dosya yolu.
    @return (str) Tespit edilen ayraç karakteri (varsayılan: ',').
    """
    try:
        with open(dosya_yolu, 'r', encoding='utf-8', errors='ignore') as f:
            for _ in range(5):
                line = f.readline()
                if line and line.strip():
                    sayi_noktali = line.count(';')
                    sayi_virgul = line.count(',')
                    sayi_tab = line.count('\t')
                    if sayi_noktali > sayi_virgul and sayi_noktali > sayi_tab:
                        return ';'
                    elif sayi_tab > sayi_virgul and sayi_tab > sayi_noktali:
                        return '\t'
                    elif sayi_virgul > 0:
                        return ','
    except Exception:
        pass
    return ','


class ZamanEkseniItem(pg.AxisItem):
    """
    @brief X Eksenindeki zaman indekslerini dinamik Saat:Dakika formatına çeviren özel eksen bileşeni.
    @details PyQtGraph AxisItem sınıfından türer. Ham zaman serisi indekslerini (Zaman_Index)
             ölçek seviyesine (Zoom / Pan) göre otomatik olarak gün, saat, dakika, saniye veya
             milisaniye formatına dönüştürerek eksen etiketlerini çizer.
    """

    def __init__(self, *args, **kwargs):
        """
        @brief ZamanEkseniItem sınıfı kurucu fonksiyonu.
        @param args Konumsal argümanlar (pg.AxisItem'a iletilir).
        @param kwargs İsimli argümanlar (pg.AxisItem'a iletilir).
        """
        super().__init__(*args, **kwargs)
        self.baslangic_zamani = None
        self.dt_saniye = 0.1  # Varsayılan 100ms örnekleme aralığı

    def tickStrings(self, values, scale, spacing):
        """
        @brief Eksen üzerindeki sayısal değerleri dinamik zaman metinlerine dönüştürür.
        @param values (list) Ekranda gösterilecek ham sayısal eksen değerleri.
        @param scale (float) Eksen ölçek katsayısı.
        @param spacing (float) İki çizgi arasındaki veri birimi mesafesi.
        @return (list of str) Formatlanmış zaman dizgileri listesi.
        """
        if self.baslangic_zamani is None:
            return super().tickStrings(values, scale, spacing)

        strings = []
        spacing_saniye = spacing * self.dt_saniye

        for val in values:
            if val < 1:
                strings.append("")
                continue

            try:
                gecen_saniye = (val - 1) * self.dt_saniye
                if abs(gecen_saniye) > 3153600000:  # 100 yıl güvenlik sınırı (taşmayı önler)
                    strings.append("")
                    continue

                anlik_zaman = self.baslangic_zamani + datetime.timedelta(seconds=gecen_saniye)

                # Zoom derinliğine göre dinamik format seçimi
                if spacing_saniye >= 86400:    # 1 günden büyük: Gün.Ay Saat:Dakika
                    strings.append(anlik_zaman.strftime("%d.%m %H:%M"))
                elif spacing_saniye >= 60:     # 1 dakikadan büyük: Saat:Dakika
                    strings.append(anlik_zaman.strftime("%H:%M"))
                elif spacing_saniye >= 1:      # 1 saniyeden büyük: Saat:Dakika:Saniye
                    strings.append(anlik_zaman.strftime("%H:%M:%S"))
                else:                          # 1 saniyenin altı (Yüksek Zoom): Milisaniye
                    strings.append(anlik_zaman.strftime("%H:%M:%S.%f")[:-5])
            except (OverflowError, ValueError, OSError):
                strings.append("")

        return strings


# ==============================================================================
# 7. VERİ İNDİRGEME VE MODELLEME ALGORİTMALARI
# ==============================================================================

def lttb_downsample(x, y, threshold=3000):
    """
    @brief Zaman serisi verisini şekil ve tepe/çukur kaybı olmadan LTTB ile indirger.
    @details Largest Triangle Three Buckets (LTTB) algoritmasını NumPy vektörizasyonu
             ile çalıştırarak milyonlarca veri noktasını karakteristik tepe, çukur ve
             geçiş noktalarını koruyarak hedef 'threshold' adet noktaya indirir.
             Bu işlem 3 Milyonluk veri setinde ~0.01 saniyede tamamlanır.

    @param x (np.ndarray) X ekseni sayısal indeks dizisi.
    @param y (np.ndarray) Y ekseni sensör ölçüm değerleri dizisi.
    @param threshold (int) Hedeflenen maksimum örnek sayısı (Varsayılan: 3000).
    @return tuple (np.ndarray, np.ndarray) İndirgenmiş (sampled_x, sampled_y) dizileri.
    """
    n = len(x)
    if threshold >= n or threshold <= 2:
        return x, y

    every = (n - 2) / (threshold - 2)
    sampled_x = np.empty(threshold, dtype=x.dtype)
    sampled_y = np.empty(threshold, dtype=y.dtype)

    sampled_x[0] = x[0]
    sampled_y[0] = y[0]
    sampled_x[-1] = x[-1]
    sampled_y[-1] = y[-1]

    for i in range(threshold - 2):
        start_b = int(np.floor((i + 0) * every) + 1)
        end_b = min(int(np.floor((i + 1) * every) + 1), n)

        start_c = int(np.floor((i + 1) * every) + 1)
        end_c = min(int(np.floor((i + 2) * every) + 1), n)

        avg_c_x = np.mean(x[start_c:end_c])
        avg_c_y = np.mean(y[start_c:end_c])

        point_a_x = sampled_x[i]
        point_a_y = sampled_y[i]

        pts_b_x = x[start_b:end_b]
        pts_b_y = y[start_b:end_b]

        # Vektörize Üçgen Alanı: 0.5 * | (Ax - Cx)*(By - Ay) - (Ax - Bx)*(Cy - Ay) |
        areas = np.abs(
            (point_a_x - avg_c_x) * (pts_b_y - point_a_y) -
            (point_a_x - pts_b_x) * (avg_c_y - point_a_y)
        )

        max_idx = np.argmax(areas)
        sampled_x[i + 1] = pts_b_x[max_idx]
        sampled_y[i + 1] = pts_b_y[max_idx]

    return sampled_x, sampled_y


class PandasModel(QtCore.QAbstractTableModel):
    """
    @brief Milyonlarca satırlık DataFrame'leri 0.001 saniyede yükleyen Sanal Tablo Modeli.
    @details QAbstractTableModel arayüzünü uygular. Tüm veriyi Qt bellek havuzuna kopyalamak
             yerine, sadece o an ekranda görünen satır ve sütunları talep üzerine (on-demand)
             sağlar. Hatalı satırları vektörel maske ile anında koyu kırmızıya boyar.
    """

    def __init__(self, df=pd.DataFrame(), hata_kategorileri=None, parent=None):
        """
        @brief PandasModel sınıfı kurucu fonksiyonu.
        @param df (pd.DataFrame) Tabloda görüntülenecek Pandas DataFrame nesnesi.
        @param hata_kategorileri (list) Hata durumunu belirten kolon isimleri listesi.
        @param parent (QObject) Ebeveyn nesne.
        """
        super().__init__(parent)
        self._df = df
        self._hata_kategorileri = hata_kategorileri or []

        # Hatalı satırları ışık hızında renklendirmek için Vektörel Hata Maskesi
        self._hata_mask = np.zeros(len(df), dtype=bool)
        if hasattr(self, '_df') and not self._df.empty:
            hedef_kolonlar = set(self._hata_kategorileri)
            for c in self._df.columns:
                if 'hata' in c.lower() or 'hatasi' in c.lower():
                    hedef_kolonlar.add(c)

            for h_col in hedef_kolonlar:
                if h_col in self._df.columns:
                    col_vals = self._df[h_col].astype(str).str.strip()
                    self._hata_mask |= col_vals.isin(['1', '1.0', 'True', 'true']).values

    def rowCount(self, parent=QtCore.QModelIndex()):
        """
        @brief Tablodaki toplam satır sayısını döner.
        @param parent (QModelIndex) Üst indeks (Tablo için geçersizdir).
        @return (int) Toplam satır sayısı.
        """
        return len(self._df) if not parent.isValid() else 0

    def columnCount(self, parent=QtCore.QModelIndex()):
        """
        @brief Tablodaki toplam sütun sayısını döner.
        @param parent (QModelIndex) Üst indeks.
        @return (int) Toplam sütun sayısı.
        """
        return len(self._df.columns) if not parent.isValid() else 0

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """
        @brief Belirtilen hücre için istenen veri veya görünüm özelliğini döner.
        @param index (QModelIndex) Hücre satır ve sütun indeksi.
        @param role (int) Qt Veri Rolü (Display, Background, Foreground vb.).
        @return Hücre içeriği veya stili.
        """
        if not index.isValid():
            return None

        r, c = index.row(), index.column()

        if role == QtCore.Qt.DisplayRole:
            val = self._df.iat[r, c]
            return str(val) if pd.notnull(val) else ""

        elif role == QtCore.Qt.BackgroundRole:
            if self._hata_mask[r]:
                return QtGui.QBrush(QtGui.QColor(180, 40, 40))  # Koyu Kırmızı (Hata)
            return None

        elif role == QtCore.Qt.ForegroundRole:
            if self._hata_mask[r]:
                return QtGui.QBrush(QtGui.QColor(255, 255, 255))
            return None

        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """
        @brief Tablo başlık verilerini (Kolon Adları ve Satır Numaraları) döner.
        @param section (int) Sütun veya Satır indeksi.
        @param orientation (Qt.Orientation) Yatay (Horizontal) veya Dikey (Vertical).
        @param role (int) Qt Veri Rolü.
        @return (str) Başlık metni.
        """
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return str(self._df.columns[section])
            elif orientation == QtCore.Qt.Vertical:
                return str(section + 1)
        return None




# ==============================================================================
# 8. VERİ YÜKLEME VE İLERLEME DİYALOĞU
# ==============================================================================

class YuklemeDialog(QtWidgets.QDialog):
    """
    @brief Veri dosyaları okunurken anlık ilerleme durumunu gösteren modern modal iletişim kutusu.
    """

    def __init__(self, parent=None):
        """
        @brief YuklemeDialog sınıfı kurucu fonksiyonu.
        @param parent (QWidget) Ebeveyn pencere nesnesi.
        """
        super().__init__(parent)
        self.setWindowTitle("Veriler Yükleniyor")
        self.setFixedSize(560, 165)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint)
        self.setModal(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        aktif_tema = getattr(parent, 'aktif_tema', 'dark') if parent is not None else 'dark'

        self.lbl_baslik = QtWidgets.QLabel("⏳ Veriler Yükleniyor ve Eşleştiriliyor...", self)
        self.lbl_status = QtWidgets.QLabel("Veri dosyaları okunmaya hazırlanıyor...", self)
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(26)

        if aktif_tema == "light":
            self.setStyleSheet("QDialog { background-color: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 8px; }")
            self.lbl_baslik.setStyleSheet("font-size: 11pt; font-weight: bold; color: #0284c7; background: transparent; border: none;")
            self.lbl_status.setStyleSheet("font-size: 10pt; color: #475569; background: transparent; border: none;")
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    background-color: #f1f5f9;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    text-align: center;
                    color: #0f172a;
                    font-weight: bold;
                    font-size: 10pt;
                }
                QProgressBar::chunk {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8);
                    border-radius: 5px;
                }
            """)
        else:
            self.setStyleSheet("QDialog { background-color: #1e1e1e; border: 1px solid #333333; border-radius: 8px; }")
            self.lbl_baslik.setStyleSheet("font-size: 11pt; font-weight: bold; color: #00ffcc; background: transparent; border: none;")
            self.lbl_status.setStyleSheet("font-size: 10pt; color: #e0e0e0; background: transparent; border: none;")
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    background-color: #2b2b2b;
                    border: 1px solid #444444;
                    border-radius: 6px;
                    text-align: center;
                    color: white;
                    font-weight: bold;
                    font-size: 10pt;
                }
                QProgressBar::chunk {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00aaff, stop:1 #00ffcc);
                    border-radius: 5px;
                }
            """)

        layout.addWidget(self.lbl_baslik)
        layout.addWidget(self.lbl_status)
        layout.addWidget(self.progress_bar)

    def guncelle(self, yuzde, metin):
        """
        @brief İlerleme çubuğu yüzdesini ve durum etiketini günceller.
        @param yuzde (int) 0-100 arası ilerleme yüzdesi.
        @param metin (str) Kullanıcıya gösterilecek durum açıklaması.
        """
        self.progress_bar.setValue(yuzde)
        self.lbl_status.setText(metin)


class YuklemeThread(QtCore.QThread):
    """
    @brief Büyük CSV/Excel dosyalarını arayüzü dondurmadan arka planda okuyan ve eşleştiren iş parçacığı (Thread).
    """
    progress_signal = QtCore.pyqtSignal(int, str)
    finished_signal = QtCore.pyqtSignal(object, list)
    error_signal = QtCore.pyqtSignal(str)

    def __init__(self, data_yolu, event_yolu, parent=None):
        """
        @brief YuklemeThread kurucu fonksiyonu.
        @param data_yolu (str) Sensör ölçümlerini içeren dosya yolu (CSV/Excel).
        @param event_yolu (str) Hata/Kriz olay kayıtlarını içeren dosya yolu (CSV/Excel).
        @param parent (QObject) Ebeveyn nesne.
        """
        super().__init__(parent)
        self.data_yolu = data_yolu
        self.event_yolu = event_yolu

    def run(self):
        """
        @brief Arka plan iş parçacığı ana yürütme döngüsü.
        @details Dosyaları parçalı (chunked) okur, zaman damgalarını hizalar ve
                 hata kolonlarını 0/1 şeklinde sensör veri çerçevesine entegre eder.
        """
        try:
            size_data = os.path.getsize(self.data_yolu) if os.path.exists(self.data_yolu) else 0
            size_event = os.path.getsize(self.event_yolu) if os.path.exists(self.event_yolu) else 0
            total_bytes = max(size_data + size_event, 1)
            mb_total = total_bytes / (1024 * 1024)

            # 1. DATA DOSYASI OKUMA
            data_chunks = []
            if self.data_yolu.lower().endswith('.csv'):
                ayrac_data = csv_ayrac_tespit_et(self.data_yolu)
                with open(self.data_yolu, 'r', encoding='utf-8', errors='ignore') as f1:
                    for chunk in pd.read_csv(f1, sep=ayrac_data, chunksize=50000):
                        data_chunks.append(chunk)
                        b_read = f1.tell()
                        pct = int((b_read / total_bytes) * 100)
                        mb_read = b_read / (1024 * 1024)
                        dosya_adi = os.path.basename(self.data_yolu)
                        self.progress_signal.emit(pct, f"📁 {dosya_adi} okunuyor... ({mb_read:.1f} MB / {mb_total:.1f} MB)")
                df_data = pd.concat(data_chunks, ignore_index=True)
            else:
                self.progress_signal.emit(30, "📁 Data Excel okunuyor...")
                df_data = pd.read_excel(self.data_yolu)

            # 2. EVENT DOSYASI OKUMA
            event_chunks = []
            if self.event_yolu.lower().endswith('.csv'):
                ayrac_event = csv_ayrac_tespit_et(self.event_yolu)
                with open(self.event_yolu, 'r', encoding='utf-8', errors='ignore') as f2:
                    for chunk in pd.read_csv(f2, sep=ayrac_event, chunksize=100000):
                        event_chunks.append(chunk)
                        b_read = size_data + f2.tell()
                        pct = min(int((b_read / total_bytes) * 100), 95)
                        mb_read = b_read / (1024 * 1024)
                        dosya_adi = os.path.basename(self.event_yolu)
                        self.progress_signal.emit(pct, f"⚡ {dosya_adi} okunuyor... ({mb_read:.1f} MB / {mb_total:.1f} MB)")
                df_event = pd.concat(event_chunks, ignore_index=True)
            else:
                self.progress_signal.emit(70, "⚡ Event Excel okunuyor...")
                df_event = pd.read_excel(self.event_yolu)

            # 3. ZAMAN EŞLEŞTİRME VE ENTEGRASYON
            self.progress_signal.emit(96, "🔄 Zaman İndeksleri ve Hata Blokları Eşleştiriliyor...")

            data_zaman_kolonu = df_data.columns[0]
            event_zaman_kolonu = df_event.columns[0]

            ilk_zaman_str = df_data.iloc[0][data_zaman_kolonu]
            baslangic_zamani = pd.to_datetime(ilk_zaman_str, errors='coerce')

            hata_kolonlari = [col for col in df_event.columns if col != event_zaman_kolonu]
            if not hata_kolonlari:
                hata_kolonlari = ["Hata_Durumu"]
                df_event["Hata_Durumu"] = 1

            for col in hata_kolonlari:
                if col not in df_data.columns:
                    df_data[col] = 0

            if baslangic_zamani is not pd.NaT:
                for hata_kolonu in hata_kolonlari:
                    aktif_olaylar = df_event[df_event[hata_kolonu] == 1]
                    if aktif_olaylar.empty:
                        continue

                    hatali_zamanlar = pd.to_datetime(aktif_olaylar[event_zaman_kolonu], errors='coerce')
                    valid_mask = hatali_zamanlar.notna()
                    if valid_mask.any():
                        fark_sec = (hatali_zamanlar[valid_mask] - baslangic_zamani).dt.total_seconds()
                        en_yakin_indexler = (fark_sec * 10).round().astype(np.int64)
                        en_yakin_indexler = en_yakin_indexler.clip(0, len(df_data) - 1)
                        col_idx = df_data.columns.get_loc(hata_kolonu)
                        df_data.iloc[en_yakin_indexler.values, col_idx] = 1

            df_data["Zaman_Index"] = range(1, len(df_data) + 1)
            df_data["Zaman_Gorsel"] = df_data[data_zaman_kolonu]

            self.progress_signal.emit(100, "✨ Yükleme Tamamlandı!")
            self.finished_signal.emit(df_data, hata_kolonlari)

        except Exception as e:
            self.error_signal.emit(str(e))


# ==============================================================================
# 9. DİYALOG VE ANALİZ PENCERELERİ
# ==============================================================================

class DosyaSecimPenceresi(QtWidgets.QDialog):
    """
    @brief Data ve Event dosyalarının seçilmesini sağlayan diyalog penceresi.
    """

    def __init__(self, parent=None):
        """
        @brief DosyaSecimPenceresi kurucu fonksiyonu.
        @param parent (QWidget) Ebeveyn pencere nesnesi.
        """
        super(DosyaSecimPenceresi, self).__init__(parent)
        self.ui = Ui_DosyaSecimDialog()
        self.ui.setupUi(self)

        self.ui.btn_data_sec.clicked.connect(self.data_dosyasi_sec)
        self.ui.btn_event_sec.clicked.connect(self.event_dosyasi_sec)
        self.ui.btn_yuklebirlestir.clicked.connect(self.verileriBirlestir)

    def data_dosyasi_sec(self):
        """
        @brief Sensör veri dosyasını seçmek için dosya gezginini açar.
        """
        dosya_yolu, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Data Record Dosyasını Seç", "",
            "Desteklenen Dosyalar (*.xlsx *.xls *.csv);;Excel Dosyaları (*.xlsx *.xls);;CSV Dosyaları (*.csv)"
        )
        if dosya_yolu:
            self.ui.txt_data_yolu.setText(dosya_yolu)

    def event_dosyasi_sec(self):
        """
        @brief Hata/Olay dosyasını seçmek için dosya gezginini açar.
        """
        dosya_yolu, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Event Record Dosyasını Seç", "",
            "Desteklenen Dosyalar (*.xlsx *.xls *.csv);;Excel Dosyaları (*.xlsx *.xls);;CSV Dosyaları (*.csv)"
        )
        if dosya_yolu:
            self.ui.txt_event_yolu.setText(dosya_yolu)

    def verileriBirlestir(self):
        """
        @brief Seçilen dosya yollarını doğrular ve ana pencerede birleştirme işlemini tetikler.
        """
        data_yolu = self.ui.txt_data_yolu.text()
        event_yolu = self.ui.txt_event_yolu.text()

        if not data_yolu or not event_yolu:
            QtWidgets.QMessageBox.warning(self, "Hata", "Lütfen hem Data hem de Event dosyasını seçiniz!")
            return

        ana_pencere = self.parent()
        self.accept()

        if ana_pencere is not None and hasattr(ana_pencere, 'verileri_yukle_ve_birlestir'):
            ana_pencere.verileri_yukle_ve_birlestir(data_yolu, event_yolu)


class LimitPenceresi(QtWidgets.QDialog):
    """
    @brief Sensörlerin Min/Max limit çizgilerinin belirlendiği ayar penceresi.
    """

    def __init__(self, parent=None, df=None):
        """
        @brief LimitPenceresi kurucu fonksiyonu.
        @param parent (QWidget) Ebeveyn pencere.
        @param df (pd.DataFrame) Sensör kolonlarını içeren DataFrame.
        """
        super(LimitPenceresi, self).__init__(parent)
        self.ui = Ui_MinMaxDialog()
        self.ui.setupUi(self)

        kolonlar = df.columns if df is not None else []
        self.ui.btn_limitUygula.clicked.connect(self.degisiklikleriUygula)

        if hasattr(self.ui, 'btn_limitKaldir'):
            self.ui.btn_limitKaldir.clicked.connect(self.limitleriKaldir)

        tanimli = getattr(parent, 'tanimli_sensorler', None)
        if tanimli:
            for sensor in tanimli:
                if sensor in kolonlar:
                    item = QtWidgets.QListWidgetItem(sensor)
                    item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                    item.setCheckState(QtCore.Qt.Unchecked)
                    self.ui.limit_sensor_listesi.addItem(item)
        else:
            for kolon in kolonlar:
                if kolon.startswith("S"):
                    item = QtWidgets.QListWidgetItem(kolon)
                    item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                    item.setCheckState(QtCore.Qt.Unchecked)
                    self.ui.limit_sensor_listesi.addItem(item)

    def degisiklikleriUygula(self):
        """
        @brief Seçilen sensör listesini ana pencereye iletir ve pencereyi kapatır.
        """
        secilenler = []
        for i in range(self.ui.limit_sensor_listesi.count()):
            item = self.ui.limit_sensor_listesi.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                secilenler.append(item.text())
        if self.parent() is not None and hasattr(self.parent(), 'HataGrafikMinMaxCiz'):
            self.parent().HataGrafikMinMaxCiz(secilenler)
        self.accept()

    def limitleriKaldir(self):
        """
        @brief Grafikteki tüm min/max limit çizgilerini temizler ve pencereyi kapatır.
        """
        if self.parent() is not None and hasattr(self.parent(), 'HataGrafikMinMaxCiz'):
            self.parent().HataGrafikMinMaxCiz([])  # Boş liste göndererek tüm limit çizgilerini anında siler
        self.accept()


class RadarPenceresi(QtWidgets.QDialog):
    """
    @brief Kriz anında sensör sapmalarını Z-Score matematiği ile hesaplayan Radar (Örümcek Ağı) Grafiği.
    """

    def __init__(self, df, hata_metni, baslangic, bitis, secili_sensorler, parent=None):
        """
        @brief RadarPenceresi kurucu fonksiyonu.
        @param df (pd.DataFrame) Veri seti.
        @param hata_metni (str) Seçili hatanın açıklama metni.
        @param baslangic (int) Kriz başlangıç satır indeksi.
        @param bitis (int) Kriz bitiş satır indeksi.
        @param secili_sensorler (list) Analiz edilecek sensörler.
        @param parent (QWidget) Ebeveyn pencere.
        """
        super().__init__(parent)
        self.ui = Ui_RadarDialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Z-Score Analizi")

        self.df = df
        self.hata_metni = hata_metni
        self.secili_sensorler = secili_sensorler
        self.baslangic = baslangic
        self.bitis = bitis

        aktif_tema = getattr(parent, 'aktif_tema', 'dark') if parent is not None else 'dark'
        if aktif_tema == "light":
            self.ui.card_info.setStyleSheet("QFrame { background-color: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 6px; padding: 4px 12px; }")
            self.ui.lbl_baslik_kucuk.setStyleSheet("color: #0284c7; border: none; background: transparent;")
            self.ui.lbl_HataAraligi.setStyleSheet("color: #0f172a; border: none; background: transparent;")
        else:
            self.ui.card_info.setStyleSheet("QFrame { background-color: #252526; border: 1px solid #3e3e42; border-radius: 6px; padding: 4px 12px; }")
            self.ui.lbl_baslik_kucuk.setStyleSheet("color: #00ffcc; border: none; background: transparent;")
            self.ui.lbl_HataAraligi.setStyleSheet("color: #ffffff; border: none; background: transparent;")

        self.ui.lbl_HataAraligi.setText(self.hata_metni)
        self.ui.btn_pngKaydetRadar.clicked.connect(self.png_kaydet)
        self.radar_ciz()

    def png_kaydet(self):
        """
        @brief Çizilen radar grafiğini PNG dosyası olarak kaydeder.
        """
        if hasattr(self, 'son_figur'):
            dosya_yolu, _ = QFileDialog.getSaveFileName(self, "Radar Kaydet", "", "PNG Dosyası (*.png)")
            if dosya_yolu:
                self.son_figur.savefig(dosya_yolu, facecolor='#1a1a2e', edgecolor='none')

    def radar_ciz(self):
        """
        @brief Kriz ve normal dönem arasındaki Z-Score farkını hesaplayıp radar grafiğini çizer.
        """
        skorlar = []
        gecerli_sensorler = []

        df_kriz = self.df.iloc[self.baslangic: self.bitis]

        if hasattr(self.parent(), 'hata_kategorileri') and self.parent().hata_kategorileri:
            hata_mask = (self.df[self.parent().hata_kategorileri] == 0).all(axis=1)
        else:
            hata_mask = self.df["Hata_Durumu"] == 0 if "Hata_Durumu" in self.df.columns else np.ones(len(self.df), dtype=bool)
        df_normal = self.df[hata_mask]

        for sensor in self.secili_sensorler:
            if sensor not in self.df.columns:
                continue
            kriz_ort = df_kriz[sensor].mean()
            normal_ort = df_normal[sensor].mean()
            normal_std = df_normal[sensor].std()

            z_score = abs(kriz_ort - normal_ort) / normal_std if normal_std > 0 else 0
            skorlar.append(z_score)
            gecerli_sensorler.append(sensor)

        if not skorlar:
            return

        skorlar += [skorlar[0]]
        gecerli_sensorler += [gecerli_sensorler[0]]
        acilar = np.linspace(0, 2 * np.pi, len(gecerli_sensorler))

        fig = Figure(figsize=(7, 7))
        fig.patch.set_facecolor('#1a1a2e')
        ax = fig.add_subplot(111, polar=True)
        ax.set_facecolor('#1a1a2e')

        ax.plot(acilar, skorlar, color='#f39c12', linewidth=2.5, linestyle='solid', zorder=3)
        ax.fill(acilar, skorlar, color='#f39c12', alpha=0.35, zorder=2)

        for i in range(len(acilar) - 1):
            ax.plot(acilar[i], skorlar[i], 'o', color='#f39c12', markersize=10,
                    markeredgecolor='white', markeredgewidth=2, zorder=5)

            deger = skorlar[i]
            etiket = "~0" if deger < 0.01 else f"{deger:.4f}"
            ax.text(acilar[i], skorlar[i] + (max(skorlar) * 0.08 if max(skorlar) > 0 else 0.1),
                    etiket, ha='center', va='bottom', fontsize=9, fontweight='bold', color='white',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='#2d2d50', edgecolor='none', alpha=0.8))

        ax.set_xticks(acilar[:-1])
        ax.set_xticklabels(gecerli_sensorler[:-1], color='#e0e0e0', fontsize=9, fontweight='bold')
        ax.tick_params(colors='#aaaaaa', labelsize=8)
        ax.grid(color='#4d4d6e', linestyle='-', linewidth=0.6, alpha=0.7)
        ax.spines['polar'].set_color('#4d4d6e')
        ax.set_title("Sensör Sapma Analizi (Z-Score)", color='white', pad=25, fontsize=13, fontweight='bold')
        fig.tight_layout()

        if self.ui.widget_Radar.layout() is not None:
            eski_layout = self.ui.widget_Radar.layout()
            for i in reversed(range(eski_layout.count())):
                eski_layout.itemAt(i).widget().setParent(None)
        else:
            self.ui.widget_Radar.setLayout(QtWidgets.QVBoxLayout())

        canvas = FigureCanvas(fig)
        self.ui.widget_Radar.layout().addWidget(canvas)
        self.son_figur = fig


class HeatmapPenceresi(QtWidgets.QDialog):
    """
    @brief Sensörler arası korelasyon matrisini interaktif ısı haritası (Heatmap) olarak çizen pencere.
    """

    def __init__(self, df, parent=None):
        """
        @brief HeatmapPenceresi kurucu fonksiyonu.
        @param df (pd.DataFrame) Sensör verilerini içeren DataFrame.
        @param parent (QWidget) Ebeveyn pencere.
        """
        super().__init__(parent)
        self.ui = Ui_HeatmapDialog()
        self.ui.setupUi(self)

        self.df = df

        self.kutu_modeli = QStandardItemModel(self.ui.combobx_kolon)

        cikarilacak = ["Zaman_Index", "Zaman_Gorsel", "Hata_Durumu", "Motor_No"]
        gecici_kolonlar = [col for col in self.df.columns if col not in cikarilacak]

        sayisal_df = self.df[gecici_kolonlar].select_dtypes(include=['float64', 'int64'])
        self.sensor_kolonlar = [col for col in sayisal_df.columns if sayisal_df[col].std() > 0]

        for kolon in self.sensor_kolonlar:
            oge = QStandardItem(kolon)
            oge.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            oge.setData(Qt.Unchecked, Qt.CheckStateRole)
            self.kutu_modeli.appendRow(oge)

        self.ui.combobx_kolon.setModel(self.kutu_modeli)
        self.ui.combobx_kolon.setPlaceholderText("Sensörleri Seçiniz...")

        self.ui.btn_uygula.clicked.connect(self.kolon_ekle)
        self.ui.btn_tumunuGoster.clicked.connect(self.tumunu_goster)
        self.ui.btn_pngKaydet.clicked.connect(self.png_kaydet)
        self.ui.btn_silme.clicked.connect(self.tumunu_Sil)

    def tumunu_Sil(self):
        """
        @brief Isı haritasındaki tüm seçimleri ve çizilmiş grafiği temizler.
        """
        for i in range(self.kutu_modeli.rowCount()):
            satir = self.kutu_modeli.item(i)
            satir.setData(Qt.Unchecked, Qt.CheckStateRole)

        if self.ui.widget_HeatMap.layout() is not None:
            eski_layout = self.ui.widget_HeatMap.layout()
            for i in reversed(range(eski_layout.count())):
                eski_layout.itemAt(i).widget().setParent(None)

        if hasattr(self, 'son_figur'):
            del self.son_figur

    def kolon_ekle(self):
        """
        @brief ComboBox'tan işaretlenen sensörlerle korelasyon grafiğini çizer.
        """
        secilen_isimler = []
        for i in range(self.kutu_modeli.rowCount()):
            oge = self.kutu_modeli.item(i)
            if oge.checkState() == Qt.Checked:
                secilen_isimler.append(oge.text())

        if len(secilen_isimler) >= 2:
            self.heatmap_ciz(secilen_isimler)

    def tumunu_goster(self):
        """
        @brief Tüm sensörleri işaretler ve komple korelasyon matrisini çizer.
        """
        for i in range(self.kutu_modeli.rowCount()):
            oge = self.kutu_modeli.item(i)
            oge.setData(Qt.Checked, Qt.CheckStateRole)
        self.heatmap_ciz(self.sensor_kolonlar)

    def heatmap_ciz(self, kolonlar):
        """
        @brief Seçilen kolonların korelasyon matrisini hesaplar ve Matplotlib ile çizer.
        @param kolonlar (list of str) Korelasyona dahil edilecek sensör adları.
        """
        sayisal_df = self.df[kolonlar].copy()
        sayisal_df = sayisal_df.select_dtypes(include=['float64', 'int64'])
        sayisal_df = sayisal_df.loc[:, sayisal_df.std() > 0]

        if len(sayisal_df.columns) < 2:
            return

        korelasyon_matrisi = sayisal_df.corr().dropna(axis=0, how='all').dropna(axis=1, how='all')
        guncel_kolonlar = list(korelasyon_matrisi.columns)

        fig = Figure(figsize=(9, 7))
        fig.patch.set_facecolor('#1a1a2e')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1a1a2e')

        im = ax.imshow(korelasyon_matrisi.values, cmap='coolwarm', vmin=-1, vmax=1)

        ax.set_xticks(np.arange(len(guncel_kolonlar)))
        ax.set_yticks(np.arange(len(guncel_kolonlar)))
        font_boyutu = 9 if len(guncel_kolonlar) < 15 else 7
        ax.set_xticklabels(guncel_kolonlar, rotation=45, ha='right', fontsize=font_boyutu, color='#e0e0e0')
        ax.set_yticklabels(guncel_kolonlar, fontsize=font_boyutu, color='#e0e0e0')

        for _, spine in ax.spines.items():
            spine.set_visible(False)
        ax.tick_params(which="both", bottom=False, left=False)

        ax.set_xticks(np.arange(len(guncel_kolonlar) + 1) - .5, minor=True)
        ax.set_yticks(np.arange(len(guncel_kolonlar) + 1) - .5, minor=True)
        ax.grid(which="minor", color="#1a1a2e", linestyle='-', linewidth=2)
        ax.tick_params(which="minor", bottom=False, left=False)

        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="4%", pad=0.18)
        cbar = fig.colorbar(im, cax=cax)
        cbar.outline.set_visible(False)
        cbar.set_label("Korelasyon Skoru", color='#e0e0e0', labelpad=12, fontsize=10, fontweight='bold')
        cbar.ax.yaxis.set_tick_params(color='#e0e0e0')
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#e0e0e0')

        if len(guncel_kolonlar) <= 12:
            for i in range(len(guncel_kolonlar)):
                for j in range(len(guncel_kolonlar)):
                    deger = korelasyon_matrisi.values[i, j]
                    yazi_rengi = "white" if abs(deger) > 0.5 else "#1a1a2e"
                    ax.text(j, i, f"{deger:.2f}", ha="center", va="center",
                            fontsize=8, color=yazi_rengi, fontweight='bold')

        ax.set_title("Sensörler Arası Korelasyon", color='white', pad=20, fontsize=14, fontweight='bold')
        fig.subplots_adjust(left=0.25, right=0.90, top=0.91, bottom=0.24)

        if self.ui.widget_HeatMap.layout() is not None:
            eski_layout = self.ui.widget_HeatMap.layout()
            for i in reversed(range(eski_layout.count())):
                eski_layout.itemAt(i).widget().setParent(None)
        else:
            self.ui.widget_HeatMap.setLayout(QtWidgets.QVBoxLayout())

        canvas = FigureCanvas(fig)
        self.ui.widget_HeatMap.layout().addWidget(canvas)
        self.son_figur = fig

    def png_kaydet(self):
        """
        @brief Çizilen ısı haritasını PNG formatında dışa aktarır.
        """
        if hasattr(self, 'son_figur'):
            dosya_yolu, _ = QFileDialog.getSaveFileName(self, "Heatmap Kaydet", "", "PNG Dosyası (*.png)")
            if dosya_yolu:
                self.son_figur.savefig(dosya_yolu, facecolor='#1a1a2e', edgecolor='none')


class AyarlarPenceresi(QtWidgets.QDialog):
    """
    @brief Tekil sensör limit parametrelerinin girildiği diyalog penceresi.
    """

    def __init__(self, aktif_cizgiler, kolonAdlari):
        """
        @brief AyarlarPenceresi kurucu fonksiyonu.
        @param aktif_cizgiler (list) Ana grafikte aktif sensör isimleri.
        @param kolonAdlari (list) Veri setindeki tüm kolon adları.
        """
        super().__init__()
        self.ui = Ui_LimitDialog()
        self.ui.setupUi(self)

        self.ui.cb_sensor.addItems(aktif_cizgiler)
        self.ui.btn_uygula.clicked.connect(self.veriKaydetme)
        self.ui.btn_LimitSil.clicked.connect(self.veriSilme)
        self.signalFlag = "İptal"

    def veriKaydetme(self):
        """
        @brief Limit değerlerini okur ve pencereyi onaylayarak kapatır.
        """
        self.signalFlag = "Uygula"
        self.secilenSensor = self.ui.cb_sensor.currentText()
        self.altLimit = float(self.ui.line_min.text())
        self.ustLimit = float(self.ui.line_max.text())
        self.accept()

    def veriSilme(self):
        """
        @brief Limit çizgilerini silme bayrağını ayarlar ve pencereyi kapatır.
        """
        self.signalFlag = "Temizle"
        self.accept()

    def CizgiSilme(self):
        """
        @brief Limit değişkenlerini sıfırlar.
        """
        self.altLimit = None
        self.ustLimit = None


# ==============================================================================
# 10. ANA UYGULAMA PENCERESİ (ANA PLATFORM)
# ==============================================================================

class AnaPencere(QMainWindow, Ui_MainWindow):
    """
    @brief FADEC Veri Görselleştirme ve Analiz Platformu Ana Penceresi.
    @details Tüm analiz sekmelerini (CSV Tablo, Hata Ayıklama, Detaylı Hata Analizi),
             LTTB hızlandırıcılarını, Drag-Release akıllı fare takipçisini ve
             grafik crosshair bileşenlerini yöneten ana merkez sınıf.
    """

    def __init__(self):
        """
        @brief AnaPencere kurucu fonksiyonu. Arayüzü ve tüm sinyalleri başlatır.
        """
        super().__init__()


        self.setupUi(self)

        self.LIMITLER={}
        self.parametreleri_yukle()
        self.splitter.setSizes([300, 500])
        if hasattr(self, 'splitter_ana_csv'):
            self.splitter_ana_csv.setSizes([550, 350])
        if hasattr(self, 'splitter_ust_grafik'):
            self.splitter_ust_grafik.setSizes([380, 1100])
        if hasattr(self, 'splitter_alt_tablo'):
            self.splitter_alt_tablo.setSizes([1200, 450])
        if hasattr(self, 'splitter_ana_hata'):
            self.splitter_ana_hata.setSizes([360, 1400])
        if hasattr(self, 'splitter_sol_listeler'):
            self.splitter_sol_listeler.setSizes([300, 500])
        if hasattr(self, 'splitter_genel'):
            self.splitter_genel.setSizes([280, 1800])

        self.tabWidget.tabBar().setElideMode(QtCore.Qt.ElideNone)
        self.tabWidget.setCurrentIndex(0)

        # Sağ Üst Köşe Araç Çubuğu (Kullanım Kılavuzu + Tema Değiştirme Butonları)
        self.corner_container = QtWidgets.QWidget()
        layout_corner = QtWidgets.QHBoxLayout(self.corner_container)
        layout_corner.setContentsMargins(0, 0, 8, 0)
        layout_corner.setSpacing(6)

        # 1. Kullanım Kılavuzu Butonu (ℹ)
        self.btn_kilavuz = QtWidgets.QPushButton("ℹ Kullanım Kılavuzu")
        self.btn_kilavuz.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_kilavuz.setStyleSheet("""
            QPushButton {
                background-color: #252525;
                color: #e0e0e0;
                border: 1.5px solid #444444;
                border-radius: 5px;
                padding: 5px 12px;
                font-weight: bold;
                font-size: 11px;
                margin-top: 2px;
                margin-bottom: 2px;
            }
            QPushButton:hover {
                background-color: #333333;
                color: #00ffcc;
                border: 1.5px solid #00ffcc;
            }
        """)

        # 2. Tema Değiştirme Butonu
        self.aktif_tema = "dark"
        self.btn_tema_degistir = QtWidgets.QPushButton("Tema: Dark")
        self.btn_tema_degistir.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_tema_degistir.setStyleSheet("""
            QPushButton {
                background-color: #252525;
                color: #00ffcc;
                border: 1.5px solid #00ffcc;
                border-radius: 5px;
                padding: 5px 14px;
                font-weight: bold;
                font-size: 11px;
                margin-top: 2px;
                margin-bottom: 2px;
            }
            QPushButton:hover {
                background-color: #00ffcc;
                color: #121212;
            }
        """)
        self.btn_tema_degistir.clicked.connect(self.tema_degistir)

        self.btn_kilavuz.clicked.connect(self.kilavuz_ac)

        layout_corner.addWidget(self.btn_kilavuz)
        layout_corner.addWidget(self.btn_tema_degistir)
        self.tabWidget.setCornerWidget(self.corner_container, QtCore.Qt.TopRightCorner)



        # Tablo ve Grafik Görünüm Ayarları
        if hasattr(self, 'tbl_log_oturumlar'):
            self.tbl_log_oturumlar.verticalHeader().setVisible(False)
            self.tbl_log_oturumlar.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
            self.tbl_log_oturumlar.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
            self.tbl_log_oturumlar.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
            self.tbl_log_oturumlar.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
            self.tbl_log_oturumlar.itemSelectionChanged.connect(self.oturum_tablosu_secim_filtrele)

            self.oturum_dosyalari = []
            self.baslangic_klasorunu_tara()
            if hasattr(self, 'btn_loglari_yukle'):
                self.btn_loglari_yukle.clicked.connect(self.secili_oturumu_yukle)




        self.tbl_istatistik.verticalHeader().setVisible(False)
        self.tbl_istatistik.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tbl_istatistik.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.hata_grafik.showGrid(x=True, y=True, alpha=0.3)


        # Hata Tablosunun Üstüne Şık Bilgi Başlığı (Banner) Ekleyelim
        if hasattr(self, 'hata_Tablo') and hasattr(self, 'splitter'):
            self.tablo_kapsayici = QtWidgets.QWidget()
            layout_kapsayici = QtWidgets.QVBoxLayout(self.tablo_kapsayici)
            layout_kapsayici.setContentsMargins(0, 0, 0, 0)
            layout_kapsayici.setSpacing(0)

            self.lbl_hata_tablo_baslik = QtWidgets.QLabel("📌 Hata Bloğu Seçilmedi (Soldaki listeden bir blok seçiniz)")
            self.lbl_hata_tablo_baslik.setStyleSheet("""
                QLabel {
                    background-color: #232328;
                    color: #00ffcc;
                    font-weight: bold;
                    font-size: 10pt;
                    padding: 6px 12px;
                    border: 1px solid #383842;
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
            """)
            layout_kapsayici.addWidget(self.lbl_hata_tablo_baslik)
            layout_kapsayici.addWidget(self.hata_Tablo)
            self.splitter.insertWidget(0, self.tablo_kapsayici)





        self.GenelHataBloklari.setBackground('#000000')
        self.GenelHataBloklari.showGrid(x=True, y=True, alpha=0.3)
        self.GenelHataBloklari.setLabel('bottom', "Zaman (İndeks)")

        # Buton Bağlantıları
        self.btn_genel_incele.clicked.connect(self.genel_grafik_ciz)
        self.btn_genel_tumunu_silme.clicked.connect(self.genel_secimleri_temizle)
        if hasattr(self, 'btn_genel_png'):
            self.btn_genel_png.clicked.connect(self.genel_grafigi_kaydet)
        self.btn_png_kaydet.clicked.connect(self.grafigiKaydet)
        self.btn_silme.clicked.connect(self.tamamensilme)
        self.btn_BolgeSec.clicked.connect(self.BolgeSecme)
        self.btn_Odak.clicked.connect(self.Odaklan)
        self.btn_Incele.clicked.connect(self.HataBloklariniCiz)
        self.btn_heatMap.clicked.connect(self.heatmapGoster)
        self.btn_Radar.clicked.connect(self.radar_goster)

        # --- YAPAY ZEKA BUTONU (SAĞ ÜST KÖŞE) ---
        self.btn_YapayZeka = QtWidgets.QPushButton("Prompt Üret", self)
        self.btn_YapayZeka.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_YapayZeka.setStyleSheet("""
            QPushButton {
                background-color: #264f78;
                color: #00ffcc;
                border: 1.5px solid #00ffcc;
                border-radius: 5px;
                padding: 5px 12px;
                font-weight: bold;
                font-size: 12px;
                margin-top: 2px;
            }
            QPushButton:hover {
                background-color: #00ffcc;
                color: #000000;
            }
        """)
        self.btn_YapayZeka.clicked.connect(self.yapay_zeka_analizi_baslat)
        layout_corner.addWidget(self.btn_YapayZeka) # Tema butonunun yanına ekler

        # --- PDF RAPORU BUTONU (SAĞ ÜST KÖŞE) ---
        self.btn_PdfRapor = QtWidgets.QPushButton("PDF Raporu", self)
        self.btn_PdfRapor.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_PdfRapor.setStyleSheet("""
            QPushButton {
                background-color: #1e3a5f;
                color: #38bdf8;
                border: 1.5px solid #38bdf8;
                border-radius: 5px;
                padding: 5px 12px;
                font-weight: bold;
                font-size: 12px;
                margin-top: 2px;
            }
            QPushButton:hover {
                background-color: #38bdf8;
                color: #0f172a;
            }
        """)
        self.btn_PdfRapor.clicked.connect(self.pdf_raporu_olustur)
        layout_corner.addWidget(self.btn_PdfRapor)
        # -----------------------------------------





        self.btn_minmax.clicked.connect(self.minmaxPenceresiniAc)
        self.btn_dosyaYukle.clicked.connect(self.DosyaPenceresiniAc)
        self.HataBlok_List.itemClicked.connect(self.hataBlokunaBasildi)
        self.btn_hata_silme.clicked.connect(self.hata_grafik_temizle)

        # Serbest Tuval Alanı (Free Canvas ScrollArea) Kurulumu
        if hasattr(self, 'mdi_area_dashboard'):
            parent_layout = self.mdi_area_dashboard.parentWidget().layout()
            self.mdi_area_dashboard.hide()
            self.mdi_area_dashboard.deleteLater()

            self.dashboard_scroll = QtWidgets.QScrollArea()
            self.dashboard_scroll.setWidgetResizable(False)
            self.dashboard_scroll.setStyleSheet("background-color: #0e0e10; border: none;")
            self.dashboard_scroll.viewport().setStyleSheet("background-color: #0e0e10;")

            # Özel Kareli Tuvalimizi Yerleştiriyoruz
            self.dashboard_container = DashboardTuval()
            self.dashboard_container.setMinimumSize(100, 100)
            self.dashboard_scroll.resizeEvent = lambda e: self.guncelle_tuval_boyutu()

            self.dashboard_scroll.setWidget(self.dashboard_container)
            parent_layout.addWidget(self.dashboard_scroll)

        if hasattr(self, 'btn_dashboard_grafik_ekle'):
            self.btn_dashboard_grafik_ekle.setText("Grafik Ekle")
            self.btn_dashboard_grafik_ekle.clicked.connect(self.dashboard_grafik_ekle_dialog)

        if hasattr(self, 'btn_dashboard_diz_karo'):
            self.btn_dashboard_diz_karo.setText("Yan Yana Diz")
            self.btn_dashboard_diz_karo.clicked.connect(self.dashboard_yan_yana_diz)

        if hasattr(self, 'btn_dashboard_diz_basamak'):
            self.btn_dashboard_diz_basamak.setText("Basamakla")
            self.btn_dashboard_diz_basamak.clicked.connect(self.dashboard_basamakla)

        if hasattr(self, 'btn_dashboard_temizle'):
            self.btn_dashboard_temizle.setText("Tümünü Kapat")
            self.btn_dashboard_temizle.clicked.connect(self.dashboard_tumunu_temizle)

        self.secimBolgesi = None
        self.df = None
        self.aktif_cizgiler = {}
        self.limit_cizgileri = []
        self.sensor_renk_sozlugu = {}

        self.analiz_grafigi.addLegend()
        self.analiz_grafigi.showGrid(x=True, y=True, alpha=0.3)
        self.analiz_grafigi.plotItem.setMenuEnabled(False)
        self.hata_grafik.plotItem.setMenuEnabled(False)
        self.GenelHataBloklari.plotItem.setMenuEnabled(False)

        # Tablo Seçim Optimizasyonu
        self.veri_tablosu.horizontalHeader().setHighlightSections(False)
        self.veri_tablosu.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.veri_tablosu.horizontalHeader().sectionClicked.connect(self.sutuna_tiklandi)

        # Crosshair (Fare Takip İmleçleri)
        self.hLine = pg.InfiniteLine(angle=0)
        self.hLine.setZValue(999)
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen((255, 255, 0, 180), width=1.5, style=QtCore.Qt.DashLine))
        self.vLine.setZValue(999)
        self.crosshair_yazi = pg.TextItem(anchor=(0, 1), color="white", fill=pg.mkBrush(15, 23, 42, 230), border=pg.mkPen('#00ffcc', width=1))
        self.crosshair_yazi.setZValue(1000)
        self.analiz_grafigi.addItem(self.hLine, ignoreBounds=True)
        self.analiz_grafigi.addItem(self.vLine, ignoreBounds=True)
        self.analiz_grafigi.addItem(self.crosshair_yazi, ignoreBounds=True)
        self.vLine.hide()
        self.hLine.hide()
        self.crosshair_yazi.hide()
        self.proxy = pg.SignalProxy(self.analiz_grafigi.scene().sigMouseMoved, rateLimit=120, slot=self.mouseHareketEtti)

        self.vLine_hata = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(color=(255, 255, 0, 150), width=1))
        self.vLine_hata.setZValue(999)
        self.hLine_hata = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen(color=(255, 255, 0, 150), width=1))
        self.hLine_hata.setZValue(999)
        self.crosshair_yazi_hata = pg.TextItem(anchor=(0, 1), color="white", fill=pg.mkBrush(15, 23, 42, 230), border=pg.mkPen('#00ffcc', width=1))
        self.crosshair_yazi_hata.setZValue(1000)
        self.hata_grafik.addItem(self.vLine_hata, ignoreBounds=True)
        self.hata_grafik.addItem(self.hLine_hata, ignoreBounds=True)
        self.hata_grafik.addItem(self.crosshair_yazi_hata, ignoreBounds=True)
        # Başlangıçta imleçleri gizle
        self.vLine_hata.hide()
        self.hLine_hata.hide()
        self.crosshair_yazi_hata.hide()
        self.proxy_hata = pg.SignalProxy(self.hata_grafik.scene().sigMouseMoved, rateLimit=120, slot=self.mouseHareketEtti_Hata)

        # LOD Zamanlayıcıları (Tab 1 & Tab 2)
        self.zoom_timer = QtCore.QTimer()
        self.zoom_timer.setSingleShot(True)
        self.zoom_timer.timeout.connect(self.grafik_lod_guncelle)
        self.analiz_grafigi.plotItem.vb.sigXRangeChanged.connect(lambda: self.zoom_timer.start(600))

        self.aktif_ham_veriler_hata = {}
        self.aktif_cizgiler_hata = {}
        self.zoom_timer_hata = QtCore.QTimer()
        self.zoom_timer_hata.setSingleShot(True)
        self.zoom_timer_hata.timeout.connect(self.grafik_lod_guncelle_hata)
        self.hata_grafik.plotItem.vb.sigXRangeChanged.connect(lambda: self.zoom_timer_hata.start(600))

        # ========== DETAYLI HATA ANALİZİ: AKILLI DRAG-RELEASE SİSTEMİ ==========
        self.aktif_ham_veriler_genel = {}
        self.aktif_cizgiler_genel = {}
        self.tum_timeline_verileri = []
        self.aktif_timeline_ogeleri = []
        self.aktif_timeline_scatter = {}
        self.timeline_bolgeleri = []
        self._surukleme_aktif = False

        self.zoom_timer_genel = QtCore.QTimer()
        self.zoom_timer_genel.setSingleShot(True)
        self.zoom_timer_genel.timeout.connect(self.grafik_lod_guncelle_genel)

        self.GenelHataBloklari.plotItem.vb.sigXRangeChanged.connect(
            lambda: self.zoom_timer_genel.start(350) if not self._surukleme_aktif else None
        )
        self.GenelHataBloklari.plotItem.setClipToView(True)

        # Fare Sürükleme ve Bırakma Kancası (Mouse Drag-Release Hook)
        vb = self.GenelHataBloklari.getViewBox()
        eski_mouse_drag = vb.mouseDragEvent


        # Serbest Çalışma Alanı (Dashboard) Başlatıcıları
        self.dashboard_kartlari = []


        def ozel_mouse_drag_event(ev, axis=None):
            if ev.isStart():
                self._surukleme_aktif = True
                for oge in self.aktif_timeline_ogeleri:
                    oge.setVisible(False)
                for s in self.aktif_timeline_scatter.values():
                    s.setVisible(False)

            if axis is not None:
                eski_mouse_drag(ev, axis=axis)
            else:
                eski_mouse_drag(ev)

            if ev.isFinish():
                self._surukleme_aktif = False
                self.grafik_lod_guncelle_genel()
                self.timeline_lod_guncelle()

        vb.mouseDragEvent = ozel_mouse_drag_event

        # X Eksenine Akıllı Zaman Dönüştürücüleri Bağla
        self.zaman_ekseni = ZamanEkseniItem(orientation='bottom')
        self.analiz_grafigi.plotItem.setAxisItems({'bottom': self.zaman_ekseni})

        self.zaman_ekseni_hata = ZamanEkseniItem(orientation='bottom')
        self.hata_grafik.plotItem.setAxisItems({'bottom': self.zaman_ekseni_hata})

        self.zaman_ekseni_genel = ZamanEkseniItem(orientation='bottom')
        self.GenelHataBloklari.plotItem.setAxisItems({'bottom': self.zaman_ekseni_genel})

    # ==========================================================================
    # 11. HATA GRAFİĞİ TEMİZLEME VE LOD GÜNCELLEMELERİ
    # ==========================================================================

    def hata_grafik_temizle(self):
        """
        @brief Hata ayıklama ekranındaki sensör seçimlerini, grafiği ve limit çizgilerini sıfırlar.
        """
        self.liste_sensor_secim.blockSignals(True)
        for i in range(self.liste_sensor_secim.count()):
            self.liste_sensor_secim.item(i).setCheckState(QtCore.Qt.Unchecked)
        self.liste_sensor_secim.blockSignals(False)

        for cizgi in self.aktif_cizgiler_hata.values():
            self.hata_grafik.removeItem(cizgi)
        self.aktif_cizgiler_hata.clear()
        self.aktif_ham_veriler_hata.clear()

        if hasattr(self, 'limit_cizgileri'):
            for cizgi in self.limit_cizgileri:
                self.hata_grafik.removeItem(cizgi)
            self.limit_cizgileri = []

        plot_item = self.hata_grafik.getPlotItem()
        if getattr(plot_item, 'legend', None) is not None:
            plot_item.legend.scene().removeItem(plot_item.legend)
            plot_item.legend = None
        self.hata_grafik.addLegend(offset=(10, 10))

        if hasattr(self, 'vLine_hata'):
            self.vLine_hata.hide()
        if hasattr(self, 'crosshair_yazi_hata'):
            self.crosshair_yazi_hata.hide()


    def grafik_lod_guncelle_genel(self):
        """
        @brief Genel Hata Blokları grafiğinde Zoom/Pan yapıldığında LTTB ile 150 FPS sağlar.
        """
        if not hasattr(self, 'aktif_cizgiler_genel') or not self.aktif_cizgiler_genel:
            return
        if not hasattr(self, 'aktif_ham_veriler_genel') or not self.aktif_ham_veriler_genel:
            return

        x_min, x_max = self.GenelHataBloklari.viewRange()[0]
        genislik = x_max - x_min
        buffer_min = x_min - genislik * 0.5
        buffer_max = x_max + genislik * 0.5

        for sensor, cizgi in self.aktif_cizgiler_genel.items():
            if sensor not in self.aktif_ham_veriler_genel:
                continue

            x_raw, y_raw = self.aktif_ham_veriler_genel[sensor]
            if len(x_raw) == 0:
                continue

            start_idx = max(0, np.searchsorted(x_raw, buffer_min, side='left'))
            end_idx = min(len(x_raw), np.searchsorted(x_raw, buffer_max, side='right'))

            gorunen_nokta = end_idx - start_idx
            if gorunen_nokta <= 0:
                continue

            x_slice = x_raw[start_idx:end_idx]
            y_slice = y_raw[start_idx:end_idx]

            if gorunen_nokta <= 3000:
                cizgi.setData(x_slice, y_slice)
            else:
                x_lttb, y_lttb = lttb_downsample(x_slice, y_slice, threshold=1500)
                cizgi.setData(x_lttb, y_lttb)

    def sensor_rengi_getir(self, sensor_adi):
        """
        @brief Sensörün kalıcı renk kodunu döner. Yoksa canlı bir RGB üretip hafızaya kaydeder.
        @param sensor_adi (str) Rengi istenen sensörün adı.
        @return (tuple) (R, G, B) renk üçlüsü.
        """
        if not hasattr(self, 'sensor_renk_sozlugu'):
            self.sensor_renk_sozlugu = {}

        if sensor_adi not in self.sensor_renk_sozlugu:
            r = random.randint(60, 255)
            g = random.randint(60, 255)
            b = random.randint(60, 255)
            self.sensor_renk_sozlugu[sensor_adi] = (r, g, b)

        return self.sensor_renk_sozlugu[sensor_adi]

    def grafik_lod_guncelle_hata(self):
        """
        @brief Hata ayıklama grafiğinde Zoom yapıldığında LTTB ile performansı 150 FPS'te tutar.
        """
        if not hasattr(self, 'aktif_cizgiler_hata') or not self.aktif_cizgiler_hata:
            return
        if not hasattr(self, 'aktif_ham_veriler_hata') or not self.aktif_ham_veriler_hata:
            return

        x_min, x_max = self.hata_grafik.viewRange()[0]
        genislik = x_max - x_min
        buffer_min = x_min - genislik * 0.5
        buffer_max = x_max + genislik * 0.5

        for sensor, cizgi in self.aktif_cizgiler_hata.items():
            if sensor not in self.aktif_ham_veriler_hata:
                continue

            x_raw, y_raw = self.aktif_ham_veriler_hata[sensor]
            if len(x_raw) == 0:
                continue

            start_idx = max(0, np.searchsorted(x_raw, buffer_min, side='left'))
            end_idx = min(len(x_raw), np.searchsorted(x_raw, buffer_max, side='right'))

            gorunen_nokta = end_idx - start_idx
            if gorunen_nokta <= 0:
                continue

            x_slice = x_raw[start_idx:end_idx]
            y_slice = y_raw[start_idx:end_idx]

            if gorunen_nokta <= 3000:
                cizgi.setData(x_slice, y_slice)
            else:
                x_lttb, y_lttb = lttb_downsample(x_slice, y_slice, threshold=1500)
                cizgi.setData(x_lttb, y_lttb)

    def grafik_lod_guncelle(self):
        """
        @brief Ana analiz grafiğinde Zoom/Pan yapıldığında LTTB ile dinamik LOD güncellemesi yapar.
        """
        if not hasattr(self, 'aktif_cizgiler') or not self.aktif_cizgiler:
            return
        if not hasattr(self, 'aktif_ham_veriler') or not self.aktif_ham_veriler:
            return

        x_min, x_max = self.analiz_grafigi.viewRange()[0]
        genislik = x_max - x_min
        buffer_min = x_min - genislik * 0.5
        buffer_max = x_max + genislik * 0.5

        start_idx = max(0, int(np.floor(buffer_min)) - 1)
        end_idx = min(len(self.df), int(np.ceil(buffer_max)) + 1)

        gorunen_nokta_sayisi = end_idx - start_idx
        if gorunen_nokta_sayisi <= 0:
            return

        for kolonadi, cizgi in self.aktif_cizgiler.items():
            if kolonadi not in self.aktif_ham_veriler:
                continue

            x_raw, y_raw = self.aktif_ham_veriler[kolonadi]
            x_slice = x_raw[start_idx:end_idx]
            y_slice = y_raw[start_idx:end_idx]

            if gorunen_nokta_sayisi <= 5000:
                cizgi.setData(x_slice, y_slice)
            else:
                x_lttb, y_lttb = lttb_downsample(x_slice, y_slice, threshold=1500)
                cizgi.setData(x_lttb, y_lttb)

    # ==========================================================================
    # 12. HATA BLOKLARI VE LİMİT İŞLEMLERİ
    # ==========================================================================

    def hataBlokunaBasildi(self):
        """
        @brief Listeden tıklanan hata bloğunun veri aralığını sağdaki Hata Tablosuna yükler.
        """
        secili = self.HataBlok_List.currentRow()
        if secili == -1:
            return

        secili_item = self.HataBlok_List.currentItem()
        blok_metni = secili_item.text() if secili_item else f"Blok {secili + 1}"

        # 🎯 ComboBox'tan seçili olan Hata Türünü al (Örn: Hata_Durumu3)
        secili_kategori = self.cmb_hataBloklari.currentText() if hasattr(self,
                                                                         'cmb_hataBloklari') and self.cmb_hataBloklari.currentText() else "Genel Hata"

        bas, bit = self.hataBloklarıİndeksleri[secili]
        blok_verisi = self.df.iloc[bas:bit]

        # 🔥 Tablo üstündeki başlık rozetini dinamik olarak güncelle
        if hasattr(self, 'lbl_hata_tablo_baslik'):
            toplam_satir = len(blok_verisi)
            self.lbl_hata_tablo_baslik.setText(f" Hata Türü: {secili_kategori}   |   {blok_metni}   |   {toplam_satir:,} Satır")

        hata_kats = getattr(self, 'hata_kategorileri', [])
        model = PandasModel(blok_verisi, hata_kategorileri=hata_kats)
        self.hata_Tablo.setModel(model)


    def HataGrafikMinMaxCiz(self, secilen_sensorler):
        """
        @brief Hata grafiğinde seçilen sensörler için önceden tanımlı min/max limit çizgilerini çizer.
        @param secilen_sensorler (list) Limitleri çizilecek sensör isimleri listesi.
        """
        if hasattr(self, 'limit_cizgileri'):
            for eski_cizgi in self.limit_cizgileri:
                self.hata_grafik.removeItem(eski_cizgi)
        self.limit_cizgileri = []
        self.secili_limit_sensorleri = secilen_sensorler
        limitler = getattr(self, 'LIMITLER', {})
        for sensor in secilen_sensorler:
            if sensor in self.LIMITLER:
                min_sinir, max_sinir = self.LIMITLER[sensor]

                cizgi_min = pg.InfiniteLine(angle=0, pen=pg.mkPen(color=(255, 127, 80), width=2))
                cizgi_min.setValue(min_sinir)
                self.hata_grafik.addItem(cizgi_min)
                self.limit_cizgileri.append(cizgi_min)

                cizgi_max = pg.InfiniteLine(angle=0, pen=pg.mkPen(color=(255, 127, 80), width=2))
                cizgi_max.setValue(max_sinir)
                self.hata_grafik.addItem(cizgi_max)
                self.limit_cizgileri.append(cizgi_max)







    def minmaxPenceresiniAc(self):
        """
        @brief Min/Max limit ayarlama iletişim penceresini açar.
        """
        self.pencere_limit = LimitPenceresi(self, self.df)
        self.pencere_limit.exec_()

    def DosyaPenceresiniAc(self):
        """
        @brief Data ve Event dosyası seçim penceresini açar.
        """
        self.pencere_dosya = DosyaSecimPenceresi(self)
        self.pencere_dosya.exec_()

    def verileri_yukle_ve_birlestir(self, data_yolu, event_yolu):
        """
        @brief Arka plan iş parçacığını (YuklemeThread) başlatır ve ilerleme diyaloğunu görüntüler.
        @param data_yolu (str) Sensör verisi dosya yolu.
        @param event_yolu (str) Olay verisi dosya yolu.
        """
        self.pencere_yukleme = YuklemeDialog(self)
        self.pencere_yukleme.show()

        self.thread_yukleme = YuklemeThread(data_yolu, event_yolu, parent=self)
        self.thread_yukleme.progress_signal.connect(self.pencere_yukleme.guncelle)
        self.thread_yukleme.finished_signal.connect(self._veriler_yuklendi)
        self.thread_yukleme.error_signal.connect(self._yukleme_hatasi)
        self.thread_yukleme.start()

    def _veriler_yuklendi(self, df_data, hata_kolonlari):
        """
        @brief Arka plan yüklemesi tamamlandığında tabloları ve eksenleri başlatan callback fonksiyonu.
        @param df_data (pd.DataFrame) Yüklenen ve birleştirilen ana veri seti.
        @param hata_kolonlari (list) Tespit edilen hata kolonlarının listesi.
        """
        self.df = df_data
        self.hata_kategorileri = hata_kolonlari

        self.veri_tablosu.setUpdatesEnabled(False)
        self.tabloyu_doldur()
        self.veri_tablosu.setUpdatesEnabled(True)

        self.HataBloklariAyikla()

        if hasattr(self, 'pencere_yukleme') and self.pencere_yukleme is not None:
            self.pencere_yukleme.close()

        if "Zaman_Gorsel" in self.df.columns and len(self.df) >= 2:
            t0 = pd.to_datetime(str(self.df.iloc[0]["Zaman_Gorsel"]))
            t1 = pd.to_datetime(str(self.df.iloc[1]["Zaman_Gorsel"]))
            self.zaman_ekseni.baslangic_zamani = t0

            fark = (t1 - t0).total_seconds()
            dt = fark if fark > 0 else 0.1
            self.zaman_ekseni.dt_saniye = dt
            self.zaman_ekseni_hata.baslangic_zamani = t0
            self.zaman_ekseni_hata.dt_saniye = dt
            self.zaman_ekseni_genel.baslangic_zamani = t0
            self.zaman_ekseni_genel.dt_saniye = dt

    def _yukleme_hatasi(self, hata_metni):
        """
        @brief Dosya yükleme hatası oluştuğunda kullanıcıya uyarı gösterir.
        @param hata_metni (str) Hata ayrıntı açıklaması.
        """
        if hasattr(self, 'pencere_yukleme') and self.pencere_yukleme is not None:
            self.pencere_yukleme.close()
        QtWidgets.QMessageBox.critical(self, "Yükleme Hatası", f"Veriler yüklenirken bir hata oluştu:\n{hata_metni}")

    def AyarlariAc(self):
        """
        @brief Limit ayarları penceresini açar ve uygulanan seçimlere göre limit çizgilerini günceller.
        """
        aktif_sensorler = list(self.aktif_cizgiler.keys())
        kolon_Adlari = [c for c in self.df.columns if c != "Zaman"]

        self.ayarpenceresi = AyarlarPenceresi(aktif_sensorler, kolon_Adlari)
        self.ayarpenceresi.exec_()
        self.gelenIslem = self.ayarpenceresi.signalFlag

        if self.gelenIslem == "Temizle":
            if hasattr(self, 'alt_cizgi') and self.alt_cizgi is not None:
                self.analiz_grafigi.removeItem(self.alt_cizgi)
                self.analiz_grafigi.removeItem(self.ust_cizgi)
                self.alt_cizgi = None
                self.ust_cizgi = None

        elif self.gelenIslem == "Uygula":
            self.gelenParametreİsmi = self.ayarpenceresi.secilenSensor
            self.gelenAltLimit = self.ayarpenceresi.altLimit
            self.gelenUstLimit = self.ayarpenceresi.ustLimit

            self.ust_cizgi = pg.InfiniteLine(angle=0, pos=self.gelenUstLimit, pen=mkPen('r', style=Qt.DashLine))
            self.alt_cizgi = pg.InfiniteLine(angle=0, pos=self.gelenAltLimit, pen=mkPen('r', style=Qt.DashLine))
            self.analiz_grafigi.addItem(self.ust_cizgi)
            self.analiz_grafigi.addItem(self.alt_cizgi)

    def HataBloklariAyikla(self):
        """
        @brief Veri setindeki 0->1 ve 1->0 durum geçişlerini vektörize bularak hata bloklarını gruplar.
        """
        self.HataBlok_List.clear()

        if hasattr(self, 'hata_kategorileri'):
            try:
                self.cmb_hataBloklari.currentIndexChanged.disconnect()
            except TypeError:
                pass

            self.cmb_hataBloklari.clear()
            self.cmb_hataBloklari.addItems(self.hata_kategorileri)
            self.cmb_hataBloklari.currentIndexChanged.connect(self.hataKategoriDegisti)

        self.tum_hata_bloklari = {}
        if not hasattr(self, 'hata_kategorileri'):
            self.hata_kategorileri = ["Hata_Durumu"]

        for kategori in self.hata_kategorileri:
            if kategori not in self.df.columns:
                continue

            hatalar = self.df[kategori].values
            padded = np.pad(hatalar, (1, 1), 'constant', constant_values=0)
            farklar = np.diff(padded)
            baslangicNoktalari = np.where(farklar == 1)[0]
            bitisler = np.where(farklar == -1)[0]

            bloklar = list(zip(baslangicNoktalari, bitisler))
            self.tum_hata_bloklari[kategori] = bloklar

        self.hataKategoriDegisti()

    # Geriye dönük uyumluluk takma adı
    HataBloklarıAyıkla = HataBloklariAyikla

    def hataKategoriDegisti(self):
        """
        @brief Hata kategorisi seçimi değiştiğinde ilgili bloğun tetiklenme listesini günceller.
        """
        self.HataBlok_List.clear()
        self.hataBloklarıİndeksleri = []

        secili_kategori = self.cmb_hataBloklari.currentText()
        # ComboBox değiştiğinde başlığı yeni kategoriyle hazırla
        if hasattr(self, 'lbl_hata_tablo_baslik'):
            self.lbl_hata_tablo_baslik.setText(f" Hata Türü: {secili_kategori}   |    Tabloyu doldurmak için soldaki listeden bir blok seçiniz")
        if not secili_kategori or secili_kategori not in self.tum_hata_bloklari:
            return

        bloklar = self.tum_hata_bloklari[secili_kategori]
        for indeks, (bas, bit) in enumerate(bloklar):
            baslangic_zamani = self.df.iloc[bas]["Zaman_Gorsel"]
            bitis_zamani = self.df.iloc[bit - 1]["Zaman_Gorsel"]
            metin = f"Blok {indeks + 1} | Tetiklenme: {baslangic_zamani} - Bitiş: {bitis_zamani}"
            self.HataBlok_List.addItem(metin)
            self.hataBloklarıİndeksleri.append((bas, bit))

        self.hata_tablosunu_doldur(secili_kategori)

    def HataBloklariniCiz(self):
        """
        @brief Seçili hata bloğu aralığını ve seçili sensörleri Hata Ayıklama grafiğine çizer.
        """
        self.seciliHata = self.HataBlok_List.currentRow()
        if self.seciliHata == -1:
            return

        baslangic, bitis = self.hataBloklarıİndeksleri[self.seciliHata]
        hatalıVeriler = self.df.iloc[baslangic:bitis]
        hatalıVerilerZamanAraligi = hatalıVeriler["Zaman_Index"].values

        self.secili_sensorler = []
        for i in range(self.liste_sensor_secim.count()):
            item = self.liste_sensor_secim.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                self.secili_sensorler.append(item.text())

        if not self.secili_sensorler:
            return

        self.hata_grafik.clear()

        plot_item = self.hata_grafik.getPlotItem()
        if getattr(plot_item, 'legend', None) is not None:
            plot_item.legend.scene().removeItem(plot_item.legend)
            plot_item.legend = None
        self.hata_grafik.addLegend(offset=(10, 10))

        self.vLine_hata.setZValue(999)
        self.hLine_hata.setZValue(999)
        self.crosshair_yazi_hata.setZValue(1000)
        self.hata_grafik.addItem(self.vLine_hata, ignoreBounds=True)
        self.hata_grafik.addItem(self.hLine_hata, ignoreBounds=True)
        self.hata_grafik.addItem(self.crosshair_yazi_hata, ignoreBounds=True)

        self.aktif_cizgiler_hata = {}
        self.aktif_ham_veriler_hata = {}

        for sensor in self.secili_sensorler:
            y_degerleri = hatalıVeriler[sensor].values
            self.aktif_ham_veriler_hata[sensor] = (hatalıVerilerZamanAraligi, y_degerleri)

            if len(hatalıVerilerZamanAraligi) > 3000:
                x_cizim, y_cizim = lttb_downsample(hatalıVerilerZamanAraligi, y_degerleri, threshold=1500)
            else:
                x_cizim, y_cizim = hatalıVerilerZamanAraligi, y_degerleri

            renk = self.sensor_rengi_getir(sensor)
            cizgi = self.hata_grafik.plot(
                x=x_cizim, y=y_cizim, name=sensor,
                pen=pg.mkPen(color=renk, width=1)
            )
            cizgi.setZValue(0)
            self.aktif_cizgiler_hata[sensor] = cizgi

        ilk_saniye = hatalıVerilerZamanAraligi[0]
        son_saniye = hatalıVerilerZamanAraligi[-1]
        self.hata_grafik.plotItem.vb.setXRange(ilk_saniye, son_saniye, padding=0.01)

        try:
            tum_y_min = min(float(np.nanmin(hatalıVeriler[s].values)) for s in self.secili_sensorler)
            tum_y_max = max(float(np.nanmax(hatalıVeriler[s].values)) for s in self.secili_sensorler)
            y_fark = tum_y_max - tum_y_min
            if y_fark == 0:
                y_fark = 1.0
            self.hata_grafik.plotItem.vb.setYRange(tum_y_min - y_fark * 0.08, tum_y_max + y_fark * 0.08, padding=0)
        except Exception:
            self.hata_grafik.enableAutoRange(axis=pg.ViewBox.YAxis)


    def radar_goster(self):
        """
        @brief Seçili hata bloğu ve işaretli sensörler için Z-Score Radar analiz penceresini açar.
        """
        self.seciliHata = self.HataBlok_List.currentRow()
        if self.seciliHata == -1:
            return

        hata_metni = self.HataBlok_List.currentItem().text()
        secili_sensorler = [
            self.liste_sensor_secim.item(i).text()
            for i in range(self.liste_sensor_secim.count())
            if self.liste_sensor_secim.item(i).checkState() == QtCore.Qt.Checked
        ]

        if not secili_sensorler:
            return

        baslangic, bitis = self.hataBloklarıİndeksleri[self.seciliHata]
        self.radarPenceresi = RadarPenceresi(self.df, hata_metni, baslangic, bitis, secili_sensorler, self)
        self.radarPenceresi.exec_()

    # ==========================================================================
    # 13. GRAFİK ETKİLEŞİM, ODAKLAMA VE KAYDETME
    # ==========================================================================

    def Odaklan(self):
        """
        @brief Seçili bölge sınırlarına (LinearRegionItem) X ekseninde odaklanır (Zoom In).
        """
        if self.secimBolgesi is not None:
            baslangixX, bitisx = self.secimBolgesi.getRegion()
            self.analiz_grafigi.setXRange(baslangixX, bitisx, padding=0)

    def BolgeSecme(self):
        """
        @brief Ana analiz grafiğinde interaktif bölge seçim arayüzünü açar veya kapatır (Toggle).
        """
        if self.secimBolgesi is None:
            self.secimBolgesi = pg.LinearRegionItem([50, 100])
            self.secimBolgesi.setBrush(pg.mkBrush(0, 255, 204, 30))
            self.secimBolgesi.setHoverBrush(pg.mkBrush(0, 255, 204, 70))
            self.analiz_grafigi.addItem(self.secimBolgesi)

            for kenarCizgisi in self.secimBolgesi.lines:
                kenarCizgisi.setPen(pg.mkPen(color=(0, 255, 204), width=3))
                kenarCizgisi.setHoverPen(pg.mkPen(color='r', width=5))
                kenarCizgisi.setCursor(Qt.SizeHorCursor)
        else:
            self.analiz_grafigi.removeItem(self.secimBolgesi)
            self.secimBolgesi = None

    def tamamensilme(self):
        """
        @brief Ana analiz grafiğindeki tüm sensör eğrilerini ve istatistik tablosunu temizler.
        """
        for cizgiNesnesi in self.aktif_cizgiler.values():
            self.analiz_grafigi.removeItem(cizgiNesnesi)
        self.aktif_cizgiler.clear()
        self.tbl_istatistik.setRowCount(0)
        if hasattr(self, 'vLine'):
            self.vLine.hide()
        if hasattr(self, 'crosshair_yazi'):
            self.crosshair_yazi.hide()

    def grafigiKaydet(self):
        """
        @brief Ana analiz grafiğini yüksek çözünürlüklü PNG formatında dışa aktarır.
        """
        dosya, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Grafiği Kaydet", "grafik.png", ".png")
        if not dosya:
            return

        exporter = ImageExporter(self.analiz_grafigi.plotItem)
        exporter.export(dosya)

    def genel_grafigi_kaydet(self):
        """
        @brief Genel Hata Analizi grafiğini yüksek çözünürlüklü PNG formatında dışa aktarır.
        """
        dosya, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Genel Hata Grafiğini Kaydet", "genel_hata_grafigi.png", "PNG Dosyası (*.png)")
        if not dosya:
            return

        exporter = ImageExporter(self.GenelHataBloklari.plotItem)
        exporter.export(dosya)

    def mouseHareketEtti(self, kordinat):
        """
        @brief Ana grafikte fare hareket ettiğinde crosshair ve anlık sensör değerleri etiketini günceller.
        @param kordinat (tuple) Fare sahne koordinatı.
        """
        if QtWidgets.QApplication.mouseButtons() != QtCore.Qt.NoButton:
            return
        if self.df is None or len(self.df) == 0:
            return

        # Çizili sensör yoksa crosshair gösterme
        if not getattr(self, 'aktif_cizgiler', None):
            if hasattr(self, 'vLine'):
                self.vLine.hide()
            if hasattr(self, 'crosshair_yazi'):
                self.crosshair_yazi.hide()
            return

        pos = kordinat[0]
        if self.analiz_grafigi.sceneBoundingRect().contains(pos):
            mouse_noktasi = self.analiz_grafigi.plotItem.vb.mapSceneToView(pos)
            try:
                gercekZaman = int(round(mouse_noktasi.x()))
            except (OverflowError, ValueError):
                return
            satir_idx = gercekZaman - 1

            if satir_idx < 0 or satir_idx >= len(self.df):
                return

            self.vLine.setPos(gercekZaman)
            self.vLine.show()
            self.hLine.setPos(-9999)

            if "Zaman_Gorsel" in self.df.columns:
                gorsel_saat = str(self.df.iat[satir_idx, self.df.columns.get_loc("Zaman_Gorsel")])
            else:
                gorsel_saat = str(gercekZaman)

            satirlar = [f"<span style='color: #38bdf8; font-weight: bold;'>Zaman: {gorsel_saat}</span><br>"]
            for kolonadi, cizgi_nesnesi in self.aktif_cizgiler.items():
                if kolonadi in self.df.columns:
                    col_idx = self.df.columns.get_loc(kolonadi)
                    deger = self.df.iat[satir_idx, col_idx]
                    renk = cizgi_nesnesi.opts['pen'].color().name()
                    satirlar.append(f"<span style='color: {renk};'>{kolonadi} : {deger:.2f}</span>")

            self.crosshair_yazi.setHtml("<br>".join(satirlar))
            self.crosshair_yazi.setPos(gercekZaman, mouse_noktasi.y())
            self.crosshair_yazi.show()

    def mouseHareketEtti_Hata(self, kordinat):
        """
        @brief Hata grafiğinde fare hareket ettiğinde crosshair ve limit aşım durumunu günceller.
        @param kordinat (tuple) Fare sahne koordinatı.
        """
        if self.df is None or len(self.df) == 0:
            return

        # Çizili hata eğrisi yoksa crosshair gösterme
        if not getattr(self, 'aktif_cizgiler_hata', None):
            if hasattr(self, 'vLine_hata'):
                self.vLine_hata.hide()
            if hasattr(self, 'crosshair_yazi_hata'):
                self.crosshair_yazi_hata.hide()
            return

        pos = kordinat[0]
        if self.hata_grafik.sceneBoundingRect().contains(pos):
            mouse_noktasi = self.hata_grafik.plotItem.vb.mapSceneToView(pos)
            try:
                gercekZaman = int(round(mouse_noktasi.x()))
            except (OverflowError, ValueError):
                return

            satir_idx = gercekZaman - 1
            if satir_idx < 0 or satir_idx >= len(self.df):
                return

            self.vLine_hata.setPos(gercekZaman)
            self.vLine_hata.show()
            self.hLine_hata.setPos(-9999)

            if "Zaman_Gorsel" in self.df.columns:
                gorsel_saat = str(self.df.iat[satir_idx, self.df.columns.get_loc("Zaman_Gorsel")])
            else:
                gorsel_saat = str(gercekZaman)

            gosterilecek_metin = f"<span style='color: #38bdf8; font-weight: bold;'>Zaman: {gorsel_saat}</span><br><br>"

            aktif_limitler = getattr(self, 'secili_limit_sensorleri', [])
            limit_sozlugu = getattr(self, 'LIMITLER', {})

            for kolonadi, cizgi_nesnesi in self.aktif_cizgiler_hata.items():
                if kolonadi in self.df.columns:
                    col_idx = self.df.columns.get_loc(kolonadi)
                    deger = self.df.iat[satir_idx, col_idx]
                    renk_kodu = cizgi_nesnesi.opts['pen'].color().name()

                    ek_metin = ""
                    if kolonadi in aktif_limitler and kolonadi in limit_sozlugu:
                        alt_lim, ust_lim = limit_sozlugu[kolonadi]
                        if deger > ust_lim:
                            sapma = deger - ust_lim
                            ek_metin = f" <b style='color: #FF4500;'>(Aşım: +{sapma:.2f})</b>"
                        elif deger < alt_lim:
                            sapma = alt_lim - deger
                            ek_metin = f" <b style='color: #FF4500;'>(Aşım: -{sapma:.2f})</b>"

                    gosterilecek_metin += f"<span style='color: {renk_kodu};'>{kolonadi} : {deger:.2f}{ek_metin}</span><br>"

            self.crosshair_yazi_hata.setHtml(gosterilecek_metin)
            self.crosshair_yazi_hata.setPos(gercekZaman, mouse_noktasi.y())
            self.crosshair_yazi_hata.show()

    # ==========================================================================
    # 14. TABLO VE SÜTUN ETKİLEŞİMİ (SANAL MODEL ENTEGRASYONU)
    # ==========================================================================

    def tabloyu_doldur(self):
        """
        @brief Ana veri tablosunu Sanal Model (PandasModel) ile doldurur ve kontrolleri hazırlar.
        """
        hata_kats = getattr(self, 'hata_kategorileri', [])
        model = PandasModel(self.df, hata_kategorileri=hata_kats)
        self.veri_tablosu.setModel(model)
        self.veri_tablosu.horizontalHeader().setHighlightSections(False)
        self.veri_tablosu.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        self.HataBloklariAyikla()

        if hasattr(self, 'hata_kategorileri') and len(self.hata_kategorileri) > 0:
            self.hata_tablosunu_doldur(self.hata_kategorileri[0])
        else:
            self.hata_tablosunu_doldur()

        self.liste_sensor_secim.clear()
        haric_tutulacaklar = ["Motor_No", "Zaman_Gorsel", "Zaman_Index"]
        if hasattr(self, 'hata_kategorileri'):
            haric_tutulacaklar.extend(self.hata_kategorileri)

        # Eğer JSON'da tanımlı sensörler varsa onları listele, yoksa tüm CSV kolonlarını listele:
        gosterilecek_sensorler = getattr(self, 'tanimli_sensorler', None)
        if not gosterilecek_sensorler:
            gosterilecek_sensorler = [col for col in self.df.columns if col not in haric_tutulacaklar]

        for kolon in gosterilecek_sensorler:
            if kolon in self.df.columns:
                item = QtWidgets.QListWidgetItem(kolon)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Unchecked)
                self.liste_sensor_secim.addItem(item)

        # Tab 3 Seçim Kontrollerini Doldur
        self.cmb_HataBloklariGenel.blockSignals(True)
        self.cmb_HataBloklariGenel.clear()

        model_combo = QtGui.QStandardItemModel()
        if hasattr(self, 'hata_kategorileri'):
            for hata in self.hata_kategorileri:
                item = QtGui.QStandardItem(hata)
                item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                item.setCheckState(QtCore.Qt.Unchecked)
                model_combo.appendRow(item)
        self.cmb_HataBloklariGenel.setModel(model_combo)
        self.cmb_HataBloklariGenel.blockSignals(False)

        self.list_sensorSecim.blockSignals(True)
        self.list_sensorSecim.clear()
        for kolon in self.df.columns:
            if kolon not in haric_tutulacaklar:
                item = QtWidgets.QListWidgetItem(kolon)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Unchecked)
                self.list_sensorSecim.addItem(item)
        self.list_sensorSecim.blockSignals(False)

    def hata_tablosunu_doldur(self, secilen_hata="Hata_Durumu"):
        """
        @brief Sadece seçilen hatanın aktif olduğu aralıkları filtreleyip Hata Tablosuna yansıtır.
        @param secilen_hata (str) Filtrelenecek hata kolonu adı.
        """
        if secilen_hata not in self.df.columns:
            return

        self.hatalıVeriler = self.df[self.df[secilen_hata] == 1]
        hata_kats = getattr(self, 'hata_kategorileri', [secilen_hata])
        model = PandasModel(self.hatalıVeriler, hata_kategorileri=hata_kats)
        self.hata_Tablo.setModel(model)
        self.hata_Tablo.setColumnHidden(2, True)

    def _on_range_changing(self):
        """
        @brief Sürükleme anında Tab 1 çizgilerini geçici olarak 500 noktaya indirir.
        """
        if not getattr(self, '_surukleme_basladi', False):
            self._surukleme_basladi = True
            if hasattr(self, 'aktif_ham_veriler') and self.aktif_ham_veriler:
                for kolonadi, cizgi in self.aktif_cizgiler.items():
                    if kolonadi not in self.aktif_ham_veriler:
                        continue
                    x_raw, y_raw = self.aktif_ham_veriler[kolonadi]
                    if len(x_raw) > 500:
                        x_kaba, y_kaba = lttb_downsample(x_raw, y_raw, threshold=500)
                        cizgi.setData(x_kaba, y_kaba)

        self.zoom_timer.start(150)

    def sutuna_tiklandi(self, sutun):
        """
        @brief Tablo başlığındaki sensör sütununa tıklandığında eğriyi çizer veya kaldırır (Toggle).
        @param sutun (int) Tıklanan sütun indeksi.
        """
        if self.df is None or len(self.df) == 0:
            return

        secilen_sutun = self.df.columns[sutun]
        if secilen_sutun in ["Motor_No", "Zaman_Gorsel", "Zaman_Index"]:
            return

        if not hasattr(self, 'aktif_ham_veriler'):
            self.aktif_ham_veriler = {}

        if secilen_sutun in self.aktif_cizgiler:
            # Eğriyi Kaldır
            self.analiz_grafigi.removeItem(self.aktif_cizgiler.pop(secilen_sutun))
            self.aktif_ham_veriler.pop(secilen_sutun, None)

            for satir in range(self.tbl_istatistik.rowCount()):
                item = self.tbl_istatistik.item(satir, 0)
                if item and item.text() == secilen_sutun:
                    self.tbl_istatistik.removeRow(satir)
                    break
        else:
            # LTTB ile Eğriyi Çiz
            x_raw = self.df["Zaman_Index"].to_numpy(dtype=np.float64, copy=False)
            y_raw = self.df[secilen_sutun].to_numpy(dtype=np.float64, copy=False)
            self.aktif_ham_veriler[secilen_sutun] = (x_raw, y_raw)

            x_cizim, y_cizim = lttb_downsample(x_raw, y_raw, threshold=1500)
            renk = self.sensor_rengi_getir(secilen_sutun)

            yeniCizgi = self.analiz_grafigi.plot(
                x=x_cizim, y=y_cizim,
                pen=pg.mkPen(color=renk, width=1),
                name=secilen_sutun
            )
            yeniCizgi.setZValue(0)
            self.aktif_cizgiler[secilen_sutun] = yeniCizgi

            # İstatistikleri Ekle
            val_min = float(np.nanmin(y_raw))
            val_max = float(np.nanmax(y_raw))
            val_mean = float(np.nanmean(y_raw))

            kacTaneSatir = self.tbl_istatistik.rowCount()
            self.tbl_istatistik.insertRow(kacTaneSatir)
            self.tbl_istatistik.setItem(kacTaneSatir, 0, QTableWidgetItem(secilen_sutun))
            self.tbl_istatistik.setItem(kacTaneSatir, 1, QTableWidgetItem(f"{val_min:.2f}"))
            self.tbl_istatistik.setItem(kacTaneSatir, 2, QTableWidgetItem(f"{val_max:.2f}"))
            self.tbl_istatistik.setItem(kacTaneSatir, 3, QTableWidgetItem(f"{val_mean:.2f}"))

        self.analiz_grafigi.setTitle(f" {secilen_sutun} - Zaman Analiz Grafiği", color="w", size="11pt")
        self.analiz_grafigi.autoRange()

    def HataBloklariUretme(self, total_satir):
        """
        @brief Test amaçlı rastgele yapay hata blokları üreten yardımcı metod.
        @param total_satir (int) Üretilecek toplam veri satır sayısı.
        @return (np.ndarray) 0 ve 1'lerden oluşan hata dizisi.
        """
        hata_kolonu = np.zeros(total_satir, dtype=int)
        hedef_hata_sayisi = int(total_satir * 0.3)
        HataSayisi = 0
        minHataAraligi = 180
        maxHataAraligi = 1080

        while HataSayisi < hedef_hata_sayisi:
            hataBloguUzunlugu = np.random.randint(minHataAraligi, maxHataAraligi)
            baslangicNoktasi = random.randint(0, total_satir - hataBloguUzunlugu - 1)
            bitis = baslangicNoktasi + hataBloguUzunlugu

            if np.sum(hata_kolonu[baslangicNoktasi:bitis]) == 0:
                hata_kolonu[baslangicNoktasi:bitis] = 1
                HataSayisi += hataBloguUzunlugu

        return hata_kolonu

    def heatmapGoster(self):
        """
        @brief Isı Haritası (Heatmap) analiz penceresini açar.
        """
        if self.df is None:
            return
        self.heatmap_arayuzu = HeatmapPenceresi(self.df, self)
        self.heatmap_arayuzu.exec_()

    # ==========================================================================
    # 15. DETAYLI HATA ANALİZİ (TAB 3)
    # ==========================================================================

    def genel_secimleri_temizle(self):
        """
        @brief Detaylı hata analizi sekmesindeki tüm sensör ve hata seçimlerini temizler.
        """
        model = self.cmb_HataBloklariGenel.model()
        if model is not None:
            model.blockSignals(True)
            for i in range(model.rowCount()):
                item = model.item(i)
                if item is not None:
                    item.setCheckState(QtCore.Qt.Unchecked)
            model.blockSignals(False)

        self.list_sensorSecim.blockSignals(True)
        for i in range(self.list_sensorSecim.count()):
            self.list_sensorSecim.item(i).setCheckState(QtCore.Qt.Unchecked)
        self.list_sensorSecim.blockSignals(False)

        self.GenelHataBloklari.clear()
        if hasattr(self, 'aktif_cizgiler_genel'):
            self.aktif_cizgiler_genel.clear()
        if hasattr(self, 'aktif_ham_veriler_genel'):
            self.aktif_ham_veriler_genel.clear()

        plot_item = self.GenelHataBloklari.getPlotItem()
        if getattr(plot_item, 'legend', None) is not None:
            plot_item.legend.scene().removeItem(plot_item.legend)
            plot_item.legend = None
        self.GenelHataBloklari.addLegend(offset=(10, 10))

    def genel_grafik_ciz(self):
        """
        @brief Detaylı Hata Analizi grafiğini LTTB sensörleri, kırmızı bloklar ve dikey lazer çizgileriyle çizer.
        """
        self.GenelHataBloklari.clear()

        if not hasattr(self, 'tum_timeline_verileri'):
            self.tum_timeline_verileri = []
        self.tum_timeline_verileri.clear()

        if not hasattr(self, 'aktif_timeline_ogeleri'):
            self.aktif_timeline_ogeleri = []
        self.aktif_timeline_ogeleri.clear()

        if not hasattr(self, 'aktif_timeline_scatter'):
            self.aktif_timeline_scatter = {}
        self.aktif_timeline_scatter.clear()

        plot_item = self.GenelHataBloklari.getPlotItem()
        if getattr(plot_item, 'legend', None) is not None:
            plot_item.legend.scene().removeItem(plot_item.legend)
            plot_item.legend = None
        self.GenelHataBloklari.addLegend(offset=(10, 10))

        secili_hatalar = []
        model = self.cmb_HataBloklariGenel.model()
        if model is not None:
            for i in range(model.rowCount()):
                item = model.item(i)
                if item.checkState() == QtCore.Qt.Checked:
                    secili_hatalar.append(item.text())

        if not secili_hatalar and self.cmb_HataBloklariGenel.currentText():
            secili_hatalar = [self.cmb_HataBloklariGenel.currentText()]

        if not secili_hatalar:
            return

        secili_sensorler = [
            self.list_sensorSecim.item(i).text()
            for i in range(self.list_sensorSecim.count())
            if self.list_sensorSecim.item(i).checkState() == QtCore.Qt.Checked
        ]

        if not secili_sensorler:
            return

        zaman_indexleri = self.df["Zaman_Index"].values
        self.aktif_cizgiler_genel = {}
        self.aktif_ham_veriler_genel = {}

        global_min = float('inf')
        global_max = float('-inf')

        for sensor in secili_sensorler:
            sensor_verisi = self.df[sensor].values
            s_min = np.min(sensor_verisi)
            s_max = np.max(sensor_verisi)
            if s_min < global_min: global_min = s_min
            if s_max > global_max: global_max = s_max

            self.aktif_ham_veriler_genel[sensor] = (zaman_indexleri, sensor_verisi)

            if len(zaman_indexleri) > 3000:
                x_cizim, y_cizim = lttb_downsample(zaman_indexleri, sensor_verisi, threshold=1500)
            else:
                x_cizim, y_cizim = zaman_indexleri, sensor_verisi

            renk = self.sensor_rengi_getir(sensor)
            cizgi = self.GenelHataBloklari.plot(
                x_cizim, y_cizim,
                pen=pg.mkPen(color=renk, width=1),
                name=sensor
            )
            self.aktif_cizgiler_genel[sensor] = cizgi

        fark = global_max - global_min if global_max != global_min else 10

        for hata_index, secili_hata in enumerate(secili_hatalar):
            if secili_hata not in self.df.columns:
                continue

            hata_kolonu_verisi = self.df[secili_hata].values
            farklar = np.diff(hata_kolonu_verisi)
            farklar = np.insert(farklar, 0, 0)

            baslangic_indexleri = np.where(farklar == 1)[0]
            bitis_indexleri = np.where(farklar == -1)[0]

            # Şeffaf Kırmızı Bölgeler
            for bas_idx in baslangic_indexleri:
                ilgili_bitisler = bitis_indexleri[bitis_indexleri > bas_idx]
                bit_idx = ilgili_bitisler[0] if len(ilgili_bitisler) > 0 else len(self.df) - 1
                x_bas = zaman_indexleri[bas_idx]
                x_bit = zaman_indexleri[bit_idx]
                bolge = QtWidgets.QGraphicsRectItem(
                    QtCore.QRectF(x_bas, global_min, x_bit - x_bas, global_max - global_min))
                bolge.setBrush(pg.mkBrush(255, 0, 0, 35))
                bolge.setPen(pg.mkPen(None))
                bolge.setZValue(-50)
                self.GenelHataBloklari.addItem(bolge, ignoreBounds=True)

            # Dikey Lazer Çizgileri ve Veri Toplama
            def timeline_veri_topla(indexler, durum_metni, renk_kodu):
                if len(indexler) == 0: return

                x_cizgiler = []
                y_cizgiler = []
                for idx in indexler:
                    x_val = zaman_indexleri[idx]
                    x_cizgiler.extend([x_val, x_val])
                    y_cizgiler.extend([global_min - (fark * 0.15), global_max])

                cizgi_bilesik = self.GenelHataBloklari.plot(
                    x=np.array(x_cizgiler),
                    y=np.array(y_cizgiler),
                    connect='pairs',
                    pen=pg.mkPen(color=renk_kodu, width=1)
                )
                cizgi_bilesik.setDownsampling(ds=False, auto=False)
                cizgi_bilesik.setClipToView(False)
                cizgi_bilesik.setZValue(10)

                for idx in indexler:
                    sensor_degerleri = {}
                    for sensor in secili_sensorler:
                        su_anki = self.df[sensor].values[idx]
                        onceki = self.df[sensor].values[idx - 1] if idx > 0 else su_anki
                        sensor_degerleri[sensor] = {"deger": su_anki, "delta": su_anki - onceki}

                    bilgi = {
                        "x": zaman_indexleri[idx],
                        "hata_adi": secili_hata,
                        "durum": durum_metni,
                        "zaman": self.df["Zaman_Gorsel"].iloc[idx],
                        "sensor_degerleri": sensor_degerleri,
                        "renk": renk_kodu,
                        "stack_level": hata_index
                    }
                    self.tum_timeline_verileri.append(bilgi)

            timeline_veri_topla(baslangic_indexleri, f"{secili_hata} Başladı!", "#ff3f34")
            timeline_veri_topla(bitis_indexleri, f"{secili_hata} Bitti!", "#0be881")

        if global_min != float('inf') and global_max != float('-inf'):
            y_alt_marjin = global_min - (fark * 0.18)
            y_ust_marjin = global_max + (fark * 0.05)
            self.GenelHataBloklari.setYRange(y_alt_marjin, y_ust_marjin, padding=0)

        self.timeline_lod_guncelle()

    def grafik_nokta_tiklandi(self, plot, points):
        """
        @brief Timeline hata noktasına tıklandığında anlık tüm sensör değerlerini ve değişimlerini gösterir.
        @param plot (PlotItem) Tıklanan grafik nesnesi.
        @param points (list of SpotItem) Tıklanan nokta nesneleri.
        """
        if hasattr(self, 'son_bilgi_kutusu') and self.son_bilgi_kutusu is not None:
            self.GenelHataBloklari.removeItem(self.son_bilgi_kutusu)

        nokta = points[0]
        veri = nokta.data()
        if type(veri).__module__ == 'numpy':
            veri = {name: veri[name] for name in veri.dtype.names}

        nokta_id = f"{veri.get('zaman', '')}_{veri.get('durum', '')}"
        if hasattr(self, 'son_tiklanan_nokta_id') and self.son_tiklanan_nokta_id == nokta_id:
            self.son_bilgi_kutusu = None
            self.son_tiklanan_nokta_id = None
            return

        sensor_html = ""
        for s_adi, s_veri in veri.get('sensor_degerleri', {}).items():
            delta = s_veri['delta']
            delta_renk = "#2ecc71" if delta > 0 else ("#e74c3c" if delta < 0 else "#bdc3c7")
            delta_metni = f"+{delta:.2f}" if delta > 0 else f"{delta:.2f}"
            sensor_html += f"&bull; <span style='color: #3498db;'>{s_adi}:</span> <b style='color: #f1c40f;'>{s_veri['deger']:.2f}</b> <span style='color:{delta_renk}; font-size:11px;'>({delta_metni})</span><br>"

        html_metin = f"""
        <div style='background-color: rgba(30, 39, 46, 0.95); border: 2px solid {veri['renk']}; border-radius: 8px; padding: 10px; color: white; font-family: Arial; font-size: 13px;'>
            <b style='color: {veri['renk']}; font-size: 15px;'>{veri['durum']}</b><br><br>
            <span style='color: #bdc3c7;'>Zaman:</span> {veri['zaman']}<br>
            <span style='color: #bdc3c7;'><b>Anlık Sensör Değerleri:</b></span><br>
            {sensor_html}
        </div>
        """

        bilgi_kutusu = pg.TextItem(html=html_metin, anchor=(0.5, 1.2))
        bilgi_kutusu.setPos(nokta.pos())
        self.GenelHataBloklari.addItem(bilgi_kutusu)
        self.son_bilgi_kutusu = bilgi_kutusu
        self.son_tiklanan_nokta_id = nokta_id

    def timeline_lod_guncelle(self):
        """
        @brief Sadece görünen aralıktaki hata noktalarını ve yazılarını çizer; fare bırakıldığında anında güncellenir.
        """
        if not hasattr(self, 'tum_timeline_verileri') or not self.tum_timeline_verileri:
            return

        view_range = self.GenelHataBloklari.viewRange()
        x_min, x_max = view_range[0]
        y_min, y_max = view_range[1]

        fark_y = y_max - y_min
        y_taban = y_min + (fark_y * 0.02)
        katman_araligi = fark_y * 0.04

        x_genislik = max(x_max - x_min, 1)
        x_buf_min = x_min - x_genislik * 0.1
        x_buf_max = x_max + x_genislik * 0.1

        gorunur = [k for k in self.tum_timeline_verileri
                   if x_buf_min <= k['x'] <= x_buf_max]

        for oge in self.aktif_timeline_ogeleri:
            try:
                self.GenelHataBloklari.removeItem(oge)
            except Exception:
                pass
        self.aktif_timeline_ogeleri.clear()

        pencere_px = max(self.GenelHataBloklari.width(), 1)
        indeks_per_px = x_genislik / pencere_px
        min_px_mesafe = 70 * indeks_per_px

        son_x_per_kategori = {}

        for k in gorunur:
            x_pos = k['x']
            stack = k['stack_level']
            hata_y = y_taban + (stack * katman_araligi)
            son_x = son_x_per_kategori.get(stack, -1e18)

            if (x_pos - son_x) >= min_px_mesafe or indeks_per_px < 300:
                yazi = pg.TextItem(text=k['hata_adi'], color=k['renk'], anchor=(0.5, 1))
                yazi.setPos(x_pos, hata_y)
                yazi.setZValue(20)
                self.GenelHataBloklari.addItem(yazi, ignoreBounds=True)
                self.aktif_timeline_ogeleri.append(yazi)
                son_x_per_kategori[stack] = x_pos

        renk_gruplari = {}
        for k in gorunur:
            stack = k['stack_level']
            hata_y = y_taban + (stack * katman_araligi)
            renk = k['renk']
            if renk not in renk_gruplari:
                renk_gruplari[renk] = {'x': [], 'y': [], 'data': []}
            renk_gruplari[renk]['x'].append(k['x'])
            renk_gruplari[renk]['y'].append(hata_y)
            renk_gruplari[renk]['data'].append(k)

        for renk, grup in renk_gruplari.items():
            if renk not in self.aktif_timeline_scatter:
                scatter = pg.ScatterPlotItem(size=12, brush=pg.mkBrush(renk))
                scatter.sigClicked.connect(self.grafik_nokta_tiklandi)
                scatter.setZValue(20)
                self.GenelHataBloklari.addItem(scatter, ignoreBounds=True)
                self.aktif_timeline_scatter[renk] = scatter

            self.aktif_timeline_scatter[renk].setData(
                x=grup['x'], y=grup['y'], data=grup['data'])
            self.aktif_timeline_scatter[renk].setVisible(True)

        for renk, scatter in self.aktif_timeline_scatter.items():
            if renk not in renk_gruplari:
                scatter.setData(x=[], y=[])

    def baslangic_klasorunu_tara(self):
        """
        @brief C++'tan gelen klasör argümanını veya varsayılan yolu algılar ve taratır.
        """
        # 1. C++'tan veya terminalden bir yol gönderildi mi?
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]) and os.path.isdir(sys.argv[1]):
            hedef_klasor = sys.argv[1]
        # 2. Gönderilmediyse varsayılan klasörlere bak:
        elif os.path.exists(r"C:\kayıtlar"):
            hedef_klasor = r"C:\kayıtlar"
        elif os.path.exists(r"C:\kayitlar"):
            hedef_klasor = r"C:\kayitlar"
        else:
            # Geliştirme ortamı / geçerli klasör
            hedef_klasor = os.path.dirname(os.path.abspath(__file__))

        self.klasoru_tara_ve_listele(hedef_klasor)

    def klasoru_tara_ve_listele(self, klasor_yolu):
        """
        @brief Belirtilen klasördeki CSV dosyalarını tarar, dataN ve eventN çiftlerini akıllı eşleştirip sol tabloya doldurur.
        @param klasor_yolu (str) Taranacak klasörün dosya yolu.
        """
        import re
        if not hasattr(self, 'tbl_log_oturumlar'):
            return
        if not os.path.exists(klasor_yolu) or not os.path.isdir(klasor_yolu):
            return

        self.tbl_log_oturumlar.setRowCount(0)
        self.oturum_dosyalari.clear()

        tum_csvler = [f for f in os.listdir(klasor_yolu) if f.lower().endswith('.csv')]
        if not tum_csvler:
            return

        data_dosyalari = {}
        event_dosyalari = {}

        # Dosya isimlerini regex ile ayrıştır:
        # Örnek: "01_01_2025_18_16_00_data1.csv" -> Tarih: "01_01_2025_18_16_00", No: "1"
        for dosya in tum_csvler:
            tam_yol = os.path.join(klasor_yolu, dosya)
            dosya_kucuk = dosya.lower()

            match = re.search(r"^(.*?)(?:_|\b)(data|event)(\d*)\.csv$", dosya_kucuk)
            if match:
                on_ek = match.group(1).rstrip("_")
                tur = match.group(2)
                numara = match.group(3)
                anahtar = f"{on_ek}__{numara}"
                if tur == "data":
                    data_dosyalari[anahtar] = (tam_yol, dosya)
                else:
                    event_dosyalari[anahtar] = (tam_yol, dosya)
            else:
                # Farklı isimli genel dosyalar için yedek eşleme
                if "data" in dosya_kucuk:
                    anahtar = dosya_kucuk.replace("data", "ANAHTAR")
                    data_dosyalari[anahtar] = (tam_yol, dosya)
                elif "event" in dosya_kucuk:
                    anahtar = dosya_kucuk.replace("event", "ANAHTAR")
                    event_dosyalari[anahtar] = (tam_yol, dosya)

        # Tüm çift anahtarlarını sırala ve sol tabloya yaz
        tum_anahtarlar = sorted(list(set(list(data_dosyalari.keys()) + list(event_dosyalari.keys()))))

        for anahtar in tum_anahtarlar:
            data_yol, data_ad = data_dosyalari.get(anahtar, (None, "-"))
            event_yol, event_ad = event_dosyalari.get(anahtar, (None, "-"))

            self.oturum_dosyalari.append({
                "data_yolu": data_yol,
                "event_yolu": event_yol,
                "data_adi": data_ad,
                "event_adi": event_ad
            })

            satir = self.tbl_log_oturumlar.rowCount()
            self.tbl_log_oturumlar.insertRow(satir)

            item_data = QtWidgets.QTableWidgetItem(data_ad)
            item_data.setTextAlignment(QtCore.Qt.AlignCenter)
            item_event = QtWidgets.QTableWidgetItem(event_ad)
            item_event.setTextAlignment(QtCore.Qt.AlignCenter)

            self.tbl_log_oturumlar.setItem(satir, 0, item_data)
            self.tbl_log_oturumlar.setItem(satir, 1, item_event)

    def oturum_tablosu_secim_filtrele(self):
        """
        @brief Fareyle sürükleme veya tıklama anında Data Log ve Event Log sütunlarında
        en fazla 1'er hücrenin seçili kalmasını dinamik olarak filtreler.
        """
        secili_itemler = self.tbl_log_oturumlar.selectedItems()
        if not secili_itemler:
            return

        current_item = self.tbl_log_oturumlar.currentItem()
        if not current_item:
            return

        current_col = current_item.column()
        current_row = current_item.row()

        self.tbl_log_oturumlar.blockSignals(True)
        for item in secili_itemler:
            if item.column() == current_col and item.row() != current_row:
                item.setSelected(False)
        self.tbl_log_oturumlar.blockSignals(False)

    def secili_oturumu_yukle(self):
        """
        @brief Bağımsız olarak seçilen 1 adet Data Log ve 1 adet Event Log dosyasını birleştirip yükler.
        """
        secili_itemler = self.tbl_log_oturumlar.selectedItems()

        secili_data_itemler = [it for it in secili_itemler if it.column() == 0]
        secili_event_itemler = [it for it in secili_itemler if it.column() == 1]

        # 1. Kontrol: Hiçbir şey seçilmediyse
        if not secili_data_itemler and not secili_event_itemler:
            QtWidgets.QMessageBox.warning(
                self, "Seçim Yapılmadı",
                "Lütfen tablodan yüklemek istediğiniz Data Log ve/veya Event Log dosyasını seçiniz."
            )
            return

        # 2. Kontrol: Birden fazla Data Log seçildiyse uyar ve durdur
        if len(secili_data_itemler) > 1:
            QtWidgets.QMessageBox.warning(
                self, "Hatalı Seçim",
                f"Birden fazla ({len(secili_data_itemler)} adet) Data Log seçemezsiniz!\nLütfen sadece 1 adet Data Log seçiniz."
            )
            return

        # 3. Kontrol: Birden fazla Event Log seçildiyse uyar ve durdur
        if len(secili_event_itemler) > 1:
            QtWidgets.QMessageBox.warning(
                self, "Hatalı Seçim",
                f"Birden fazla ({len(secili_event_itemler)} adet) Event Log seçemezsiniz!\nLütfen sadece 1 adet Event Log seçiniz."
            )
            return

        # 4. Dosya yollarını al
        data_yolu = None
        event_yolu = None

        if secili_data_itemler:
            satir_data = secili_data_itemler[0].row()
            if 0 <= satir_data < len(self.oturum_dosyalari):
                data_yolu = self.oturum_dosyalari[satir_data]["data_yolu"]

        if secili_event_itemler:
            satir_event = secili_event_itemler[0].row()
            if 0 <= satir_event < len(self.oturum_dosyalari):
                event_yolu = self.oturum_dosyalari[satir_event]["event_yolu"]

        if not data_yolu or not os.path.exists(data_yolu):
            QtWidgets.QMessageBox.warning(
                self,
                "Dosya Bulunamadı",
                "Lütfen geçerli bir Data Log dosyası seçiniz."
            )
            return

        # Yükleme başladığında tablodaki tüm seçimleri sıfırla/temizle
        self.tbl_log_oturumlar.clearSelection()

        # Arka planda birleştirme ve yükleme motorunu çalıştırır
        self.verileri_yukle_ve_birlestir(data_yolu, event_yolu)

    def parametreleri_yukle(self):
        """
        @brief C++'tan gelen klasördeki veya argümandaki parameters.json dosyasını otomatik okur.
        """
        import sys
        import json

        json_yolu = None

        # 1. C++'tan bir argüman (sys.argv) geldi mi?
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            gelen_yol = sys.argv[1]

            # Eğer C++ bir klasör yolu gönderdiyse (Örn: "C:/kayıtlar"):
            if os.path.isdir(gelen_yol):
                aday_json = os.path.join(gelen_yol, "parameters.json")
                if os.path.exists(aday_json):
                    json_yolu = aday_json
            # Eğer C++ doğrudan .json dosyasını gönderdiyse:
            elif gelen_yol.lower().endswith(".json"):
                json_yolu = gelen_yol

        # 2. C++ bir şey göndermediyse varsayılan yerlere bak (Fallback):
        if not json_yolu:
            olasi_yollar = [
                r"C:\kayıtlar\parameters.json",
                r"C:\kayitlar\parameters.json",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "parameters.json")
            ]
            for yol in olasi_yollar:
                if os.path.exists(yol):
                    json_yolu = yol
                    break

        # 3. Dosya bulunduysa oku ve limitleri / sensörleri hafızaya al:
        if json_yolu and os.path.exists(json_yolu):
            try:
                with open(json_yolu, 'r', encoding='utf-8') as f:
                    param_data = json.load(f)
                    self.LIMITLER = {k: (float(v[0]), float(v[1])) for k, v in param_data.items() if len(v) >= 2}
                    self.tanimli_sensorler = list(param_data.keys())
                    print(
                        f"C++ / Klasör üzerinden {len(self.tanimli_sensorler)} adet sensör ve limit başarıyla yüklendi: {json_yolu}")
            except Exception as e:
                print(f"JSON okuma hatası: {e}")


    # ==========================================================================
    # 🌟 SERBEST ÇALIŞMA ALANI (DASHBOARD) YÖNETİCİSİ
    # ==========================================================================

    def dashboard_grafik_ekle_dialog(self):
        """
        @brief Kullanıcıya sensör seçtiren ve ızgaraya yeni bir SensorGrafikKarti ekleyen metot.
        """
        if self.df is None or self.df.empty:
            QtWidgets.QMessageBox.warning(self, "Veri Yüklü Değil", "Lütfen önce 1. Sekmeden bir test oturumu veya CSV dosyası yükleyiniz.")
            return

        # Kullanılabilir sensör listesini hazırla
        haric = ["Motor_No", "Zaman_Gorsel", "Zaman_Index"]
        if hasattr(self, 'hata_kategorileri'):
            haric.extend(self.hata_kategorileri)

        tanimli = getattr(self, 'tanimli_sensorler', None)
        if tanimli:
            sensor_listesi = [s for s in tanimli if s in self.df.columns]
        else:
            sensor_listesi = [col for col in self.df.columns if col not in haric]

        if not sensor_listesi:
            QtWidgets.QMessageBox.information(self, "Sensör Bulunamadı", "Görüntülenebilecek uygun bir sensör kolonu bulunamadı.")
            return

        # Sensör Seçim Açılır Kutusu (QInputDialog - Türkçe Butonlar)
        dialog = QtWidgets.QInputDialog(self)
        dialog.setWindowTitle("Grafik Ekle")
        dialog.setLabelText("Görüntülemek istediğiniz sensörü seçiniz:")
        dialog.setComboBoxItems(sensor_listesi)
        dialog.setComboBoxEditable(False)
        dialog.setOkButtonText("Oluştur")
        dialog.setCancelButtonText("Vazgeç")
        
        ok = (dialog.exec_() == QtWidgets.QDialog.Accepted)
        secilen_sensor = dialog.textValue()
        if not ok or not secilen_sensor:
            return

        # Limitleri ve rengi belirle
        limit_sozlugu = getattr(self, 'LIMITLER', {})
        limitler = limit_sozlugu.get(secilen_sensor, None)
        renk = self.sensor_rengi_getir(secilen_sensor)

        # Yeni Grafik Kartını Üret (C#'taki: new SensorGrafikKarti)
        # Yeni Grafik Kartını doğrudan Tuval'in (dashboard_container) içine üret
        kart = SensorGrafikKarti(
            sensor_adi=secilen_sensor,
            df=self.df,
            parent=self.dashboard_container,
            limitler=limitler,
            cizgi_rengi=renk,
            tema=self.aktif_tema
        )

        # Kartı 25px ızgaraya uygun başlangıç koordinatına yerleştir
        mevcut_kartlar = self.dashboard_container.findChildren(SensorGrafikKarti)
        idx = len(mevcut_kartlar) - 1
        offset = (idx * 50) % 300
        kart.setGeometry(50 + offset, 50 + offset, 550, 350)
        kart.show()
        kart.raise_()

    def dashboard_tumunu_temizle(self):
        """ Serbest Çalışma Alanındaki tüm grafikleri siler. """
        if hasattr(self, 'dashboard_container'):
            for kart in self.dashboard_container.findChildren(SensorGrafikKarti):
                kart.setParent(None)
                kart.deleteLater()

    def dashboard_yan_yana_diz(self):
        """ Kartları tuval üzerinde 2 sütunlu düzenli bir ızgara şeklinde dizer. """
        if not hasattr(self, 'dashboard_container'):
            return

        kartlar = self.dashboard_container.findChildren(SensorGrafikKarti)
        for i, kart in enumerate(kartlar):
            satir = i // 2  # Her satırda 2 grafik
            sutun = i % 2

            # Her kart 550x350 boyutunda. Aralara 25px boşluk bırakıyoruz
            x = 25 + (sutun * 575)
            y = 25 + (satir * 375)

            kart.setGeometry(x, y, 550, 350)
            kart.raise_()
            self.guncelle_tuval_boyutu()

    def dashboard_basamakla(self):
        """ Kartları klasik Windows stiliyle çapraz (basamaklı) üst üste dizer. """
        if not hasattr(self, 'dashboard_container'):
            return

        kartlar = self.dashboard_container.findChildren(SensorGrafikKarti)
        for i, kart in enumerate(kartlar):
            # Her yeni kartı 50px sağa ve aşağı kaydır
            x = 25 + (i * 50)
            y = 25 + (i * 50)

            kart.setGeometry(x, y, 550, 350)
            kart.raise_()  # Son ekleneni en üste al
            self.guncelle_tuval_boyutu()

    def guncelle_tuval_boyutu(self, sadece_buyut=False):
        """ Kartların konumuna göre tuvali dinamik olarak boyutlandırır. """
        if not hasattr(self, 'dashboard_container') or not hasattr(self, 'dashboard_scroll'):
            return

        viewport_w = self.dashboard_scroll.viewport().width()
        viewport_h = self.dashboard_scroll.viewport().height()

        max_x = viewport_w
        max_y = viewport_h

        for kart in self.dashboard_container.findChildren(SensorGrafikKarti):
            kart_sag = kart.x() + kart.width() + 50
            kart_alt = kart.y() + kart.height() + 50
            max_x = max(max_x, kart_sag)
            max_y = max(max_y, kart_alt)

        # Sadece Büyütme Modu Aktifse: Eski boyuttan daha küçüğe inmesine izin verme
        if sadece_buyut:
            eski_w = self.dashboard_container.width()
            eski_h = self.dashboard_container.height()
            max_x = max(max_x, eski_w)
            max_y = max(max_y, eski_h)

        self.dashboard_container.setFixedSize(max_x, max_y)



    def kilavuz_ac(self):
        """
        @brief FADEC Kullanım Kılavuzu PDF dosyasını sistemin varsayılan PDF görüntüleyicisinde açar.
        """
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtCore import QUrl

        # 1. Öncelikli aday dosya yollarını tara (Proje klasörü & PyInstaller MEIPASS uyumlu)
        aday_yollar = [
            kaynak_yolu("Fadec Dökümantasyon.pdf"),
            kaynak_yolu("Fadec Dokumantasyon.pdf"),
            kaynak_yolu("Kullanim_Kilavuzu.pdf"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "Fadec Dökümantasyon.pdf"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "Fadec Dokumantasyon.pdf"),
            os.path.join(os.path.expanduser("~"), "Desktop", "Fadec Dökümantasyon.pdf"),
            os.path.join(os.path.expanduser("~"), "Desktop", "Fadec Dokumantasyon.pdf"),
        ]

        hedef_pdf = None
        for yol in aday_yollar:
            if os.path.exists(yol):
                hedef_pdf = os.path.abspath(yol)
                break

        # 2. Eğer özel isimle bulunamazsa, proje veya masaüstündeki ilk uygun PDF'i bul
        if not hedef_pdf:
            proje_dizini = os.path.dirname(os.path.abspath(__file__))
            for dosya in os.listdir(proje_dizini):
                if dosya.lower().endswith(".pdf") and ("fadec" in dosya.lower() or "dökümantasyon" in dosya.lower() or "dokumantasyon" in dosya.lower() or "kilavuz" in dosya.lower()):
                    hedef_pdf = os.path.abspath(os.path.join(proje_dizini, dosya))
                    break

        if hedef_pdf and os.path.exists(hedef_pdf):
            # Qt'nin dahili, platform bağımsız dosya açıcısıyla varsayılan PDF okuyucuda aç
            basarili = QDesktopServices.openUrl(QUrl.fromLocalFile(hedef_pdf))
            if not basarili:
                # Windows için alternatif dosya açılışı
                try:
                    os.startfile(hedef_pdf)
                except Exception as e:
                    QtWidgets.QMessageBox.warning(
                        self, "Açılış Hatası",
                        f"PDF dosyası açılırken bir sorun oluştu:\n{e}"
                    )
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "Kılavuz Bulunamadı",
                "Kullanım Kılavuzu PDF dosyası bulunamadı!\n\n"
                "Lütfen 'Fadec Dökümantasyon.pdf' dosyasının proje dizininde olduğundan emin olunuz."
            )

    def tema_degistir(self):
        """
        @brief Dark ve Light tema arasında geçişi yöneten ana metot.
        """
        if self.aktif_tema == "dark":
            self.aktif_tema = "light"
            self.btn_tema_degistir.setText("Tema: Light")
            self.btn_tema_degistir.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #0284c7;
                    border: 1.5px solid #0284c7;
                    border-radius: 5px;
                    padding: 5px 14px;
                    font-weight: bold;
                    font-size: 11px;
                    margin-top: 2px;
                    margin-bottom: 2px;
                }
                QPushButton:hover {
                    background-color: #0284c7;
                    color: #ffffff;
                }
            """)
            if hasattr(self, 'btn_kilavuz'):
                self.btn_kilavuz.setStyleSheet("""
                    QPushButton {
                        background-color: #ffffff;
                        color: #1e293b;
                        border: 1.5px solid #cbd5e1;
                        border-radius: 5px;
                        padding: 5px 12px;
                        font-weight: bold;
                        font-size: 11px;
                        margin-top: 2px;
                        margin-bottom: 2px;
                    }
                    QPushButton:hover {
                        background-color: #f1f5f9;
                        color: #0284c7;
                        border: 1.5px solid #0284c7;
                    }
                """)
            if hasattr(self, 'btn_YapayZeka'):
                self.btn_YapayZeka.setStyleSheet("""
                    QPushButton {
                        background-color: #ffffff;
                        color: #0284c7;
                        border: 1.5px solid #0284c7;
                        border-radius: 5px;
                        padding: 5px 12px;
                        font-weight: bold;
                        font-size: 12px;
                        margin-top: 2px;
                        margin-bottom: 2px;
                    }
                    QPushButton:hover {
                        background-color: #0284c7;
                        color: #ffffff;
                    }
                """)
            if hasattr(self, 'btn_PdfRapor'):
                self.btn_PdfRapor.setStyleSheet("""
                    QPushButton {
                        background-color: #ffffff;
                        color: #0369a1;
                        border: 1.5px solid #0369a1;
                        border-radius: 5px;
                        padding: 5px 12px;
                        font-weight: bold;
                        font-size: 12px;
                        margin-top: 2px;
                        margin-bottom: 2px;
                    }
                    QPushButton:hover {
                        background-color: #0369a1;
                        color: #ffffff;
                    }
                """)
            QtWidgets.qApp.setStyleSheet(ACIK_TEMA_QSS)

            # Dinamik Hata Bilgi Başlığı (Banner) Açık Tema
            if hasattr(self, 'lbl_hata_tablo_baslik'):
                self.lbl_hata_tablo_baslik.setStyleSheet("""
                    QLabel {
                        background-color: #f0f9ff;
                        color: #0369a1;
                        border: 1px solid #bae6fd;
                        border-bottom: 2px solid #0284c7;
                        border-top-left-radius: 6px;
                        border-top-right-radius: 6px;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        font-size: 11pt;
                        font-weight: bold;
                        padding: 6px 12px;
                    }
                """)

            # Dashboard Scroll ve Viewport Açık Tema
            if hasattr(self, 'dashboard_scroll'):
                self.dashboard_scroll.setStyleSheet("background-color: #f8fafc; border: none;")
                self.dashboard_scroll.viewport().setStyleSheet("background-color: #f8fafc;")

            # PyQtGraph Grafikleri Açık Tema (Beyaz Zemin, Koyu Eksenler)
            grafikler = [getattr(self, 'analiz_grafigi', None), getattr(self, 'hata_grafik', None), getattr(self, 'GenelHataBloklari', None)]
            for g in grafikler:
                if g is not None:
                    g.setBackground('#ffffff')
                    g.getAxis('bottom').setPen(pg.mkPen(color='#94a3b8', width=1))
                    g.getAxis('left').setPen(pg.mkPen(color='#94a3b8', width=1))
                    g.getAxis('bottom').setTextPen(pg.mkPen(color='#334155'))
                    g.getAxis('left').setTextPen(pg.mkPen(color='#334155'))
                    g.showGrid(x=True, y=True, alpha=0.2)

            # Crosshair Açık Tema (Şık koyu rozet, mavi vurgulu çizgi)
            if hasattr(self, 'vLine'):
                self.vLine.setPen(pg.mkPen('#0284c7', width=1.5, style=QtCore.Qt.DashLine))
            if hasattr(self, 'vLine_hata'):
                self.vLine_hata.setPen(pg.mkPen('#0284c7', width=1.5, style=QtCore.Qt.DashLine))
            if hasattr(self, 'crosshair_yazi'):
                self.crosshair_yazi.fill = pg.mkBrush(30, 41, 59, 130)
                self.crosshair_yazi.border = pg.mkPen('#0284c7', width=1.5)
            if hasattr(self, 'crosshair_yazi_hata'):
                self.crosshair_yazi_hata.fill = pg.mkBrush(30, 41, 59, 130)
                self.crosshair_yazi_hata.border = pg.mkPen('#0284c7', width=1.5)

            # Serbest Tuval ve Kartları Açık Temaya Güncelle
            if hasattr(self, 'dashboard_container') and hasattr(self.dashboard_container, 'tema_guncelle'):
                self.dashboard_container.tema_guncelle("light")
            if hasattr(self, 'dashboard_container'):
                for kart in self.dashboard_container.findChildren(SensorGrafikKarti):
                    kart.tema_guncelle("light")

        else:
            self.aktif_tema = "dark"
            self.btn_tema_degistir.setText("Tema: Dark")
            self.btn_tema_degistir.setStyleSheet("""
                QPushButton {
                    background-color: #252525;
                    color: #00ffcc;
                    border: 1.5px solid #00ffcc;
                    border-radius: 5px;
                    padding: 5px 14px;
                    font-weight: bold;
                    font-size: 11px;
                    margin-top: 2px;
                    margin-bottom: 2px;
                }
                QPushButton:hover {
                    background-color: #00ffcc;
                    color: #121212;
                }
            """)
            if hasattr(self, 'btn_kilavuz'):
                self.btn_kilavuz.setStyleSheet("""
                    QPushButton {
                        background-color: #252525;
                        color: #e0e0e0;
                        border: 1.5px solid #444444;
                        border-radius: 5px;
                        padding: 5px 12px;
                        font-weight: bold;
                        font-size: 11px;
                        margin-top: 2px;
                        margin-bottom: 2px;
                    }
                    QPushButton:hover {
                        background-color: #333333;
                        color: #00ffcc;
                        border: 1.5px solid #00ffcc;
                    }
                """)
            if hasattr(self, 'btn_YapayZeka'):
                self.btn_YapayZeka.setStyleSheet("""
                    QPushButton {
                        background-color: #264f78;
                        color: #00ffcc;
                        border: 1.5px solid #00ffcc;
                        border-radius: 5px;
                        padding: 5px 12px;
                        font-weight: bold;
                        font-size: 12px;
                        margin-top: 2px;
                        margin-bottom: 2px;
                    }
                    QPushButton:hover {
                        background-color: #00ffcc;
                        color: #000000;
                    }
                """)
            if hasattr(self, 'btn_PdfRapor'):
                self.btn_PdfRapor.setStyleSheet("""
                    QPushButton {
                        background-color: #1e3a5f;
                        color: #38bdf8;
                        border: 1.5px solid #38bdf8;
                        border-radius: 5px;
                        padding: 5px 12px;
                        font-weight: bold;
                        font-size: 12px;
                        margin-top: 2px;
                        margin-bottom: 2px;
                    }
                    QPushButton:hover {
                        background-color: #38bdf8;
                        color: #0f172a;
                    }
                """)
            QtWidgets.qApp.setStyleSheet(KOYU_TEMA_QSS)

            # Dinamik Hata Bilgi Başlığı (Banner) Koyu Tema
            if hasattr(self, 'lbl_hata_tablo_baslik'):
                self.lbl_hata_tablo_baslik.setStyleSheet("""
                    QLabel {
                        background-color: #181818;
                        color: #00ffcc;
                        border: 1px solid #333333;
                        border-bottom: 2px solid #00ffcc;
                        border-top-left-radius: 6px;
                        border-top-right-radius: 6px;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        font-size: 11pt;
                        font-weight: bold;
                        padding: 6px 12px;
                    }
                """)

            # Dashboard Scroll ve Viewport Koyu Tema
            if hasattr(self, 'dashboard_scroll'):
                self.dashboard_scroll.setStyleSheet("background-color: #0e0e10; border: none;")
                self.dashboard_scroll.viewport().setStyleSheet("background-color: #0e0e10;")

            # PyQtGraph Grafikleri Koyu Tema (Siyah Zemin, Açık Eksenler)
            grafikler = [getattr(self, 'analiz_grafigi', None), getattr(self, 'hata_grafik', None), getattr(self, 'GenelHataBloklari', None)]
            for g in grafikler:
                if g is not None:
                    g.setBackground('#000000')
                    g.getAxis('bottom').setPen(pg.mkPen(color='#666666', width=1))
                    g.getAxis('left').setPen(pg.mkPen(color='#666666', width=1))
                    g.getAxis('bottom').setTextPen(pg.mkPen(color='#d4d4d4'))
                    g.getAxis('left').setTextPen(pg.mkPen(color='#d4d4d4'))
                    g.showGrid(x=True, y=True, alpha=0.3)

            # Crosshair Koyu Tema
            if hasattr(self, 'vLine'):
                self.vLine.setPen(pg.mkPen((255, 255, 0, 180), width=1.5, style=QtCore.Qt.DashLine))
            if hasattr(self, 'vLine_hata'):
                self.vLine_hata.setPen(pg.mkPen((255, 255, 0, 180), width=1.5, style=QtCore.Qt.DashLine))
            if hasattr(self, 'crosshair_yazi'):
                self.crosshair_yazi.fill = pg.mkBrush(0, 0, 0, 200)
                self.crosshair_yazi.border = pg.mkPen('#00ffcc', width=1)
            if hasattr(self, 'crosshair_yazi_hata'):
                self.crosshair_yazi_hata.fill = pg.mkBrush(0, 0, 0, 200)
                self.crosshair_yazi_hata.border = pg.mkPen('#00ffcc', width=1)

            # Serbest Tuval ve Kartları Koyu Temaya Güncelle
            if hasattr(self, 'dashboard_container') and hasattr(self.dashboard_container, 'tema_guncelle'):
                self.dashboard_container.tema_guncelle("dark")
            if hasattr(self, 'dashboard_container'):
                for kart in self.dashboard_container.findChildren(SensorGrafikKarti):
                    kart.tema_guncelle("dark")

    def yapay_zeka_analizi_baslat(self):
        """
        @brief AI Promptunu oluşturur ve kopyalama penceresini ekrana getirir.
        """
        # --- DÜZELTİLEN KISIM BAŞLANGICI ---
        if getattr(self, 'df', None) is None or self.df.empty:
            QtWidgets.QMessageBox.warning(self, "Uyarı", "Lütfen önce veri yükleyin!")
            return

        if getattr(self, 'hata_kategorileri', None) is None or not self.hata_kategorileri:
            QtWidgets.QMessageBox.warning(self, "Uyarı",
                                          "Hata kategorileri bulunamadı! Lütfen hata loglarının yüklendiğinden emin olun.")
            return
        # --- DÜZELTİLEN KISIM BİTİŞİ ---

        try:
            # 1. Bekleme imlecini aç
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

            # 2. Builder sınıfını ai.py'den çağır ve çalıştır (Limitleri de gönderiyoruz)
            limit_sozlugu = getattr(self, 'LIMITLER', {})
            builder = AIPromptBuilder(df_data=self.df, hata_kategorileri=self.hata_kategorileri, limitler=limit_sozlugu)
            uretilen_prompt = builder.prompt_derle()

            # 3. İmleci normale döndür
            QtWidgets.QApplication.restoreOverrideCursor()

            # 4. Pencereyi aç
            dialog = AIPromptPenceresi(uretilen_prompt, parent=self)
            dialog.exec_()

        except Exception as e:
            QtWidgets.QApplication.restoreOverrideCursor()
            QtWidgets.QMessageBox.critical(self, "Hata", f"Yapay Zeka analizi sırasında bir hata oluştu:\n\n{str(e)}")

    def pdf_raporu_olustur(self):
        """
        @brief Telemetri verilerini analiz ederek otomatik A4 PDF test ve teşhis raporu oluşturur.
        """
        if getattr(self, 'df', None) is None or self.df.empty:
            QtWidgets.QMessageBox.warning(self, "Uyarı", "Lütfen önce bir veri seti yükleyiniz!")
            return

        # Varsayılan dosya adı önerisi
        simdi_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        varsayilan_yol = f"FADEC_Test_Raporu_{simdi_str}.pdf"

        dosya_yolu, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "PDF Test Raporunu Kaydet", varsayilan_yol, "PDF Dosyası (*.pdf)"
        )

        if not dosya_yolu:
            return

        try:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

            oturum_adi = "Aktif Telemetri Test Oturumu"
            if hasattr(self, 'tbl_log_oturumlar') and self.tbl_log_oturumlar.currentRow() != -1:
                row = self.tbl_log_oturumlar.currentRow()
                item = self.tbl_log_oturumlar.item(row, 0)
                if item and item.text():
                    oturum_adi = item.text()

            motor = PDFRaporMotoru(
                df=self.df,
                hata_kategorileri=getattr(self, 'hata_kategorileri', []),
                limitler=getattr(self, 'LIMITLER', {}),
                oturum_adi=oturum_adi
            )
            basarili, mesaj = motor.pdf_kaydet(dosya_yolu)
        except Exception as e:
            basarili = False
            mesaj = f"Beklenmeyen bir hata oluştu:\n{str(e)}"
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

        if basarili:
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle("Rapor Oluşturuldu")
            msg_box.setText(f"Test ve Teşhis Raporu başarıyla oluşturuldu:\n\n{dosya_yolu}\n\nRaporu şimdi açmak ister misiniz?")
            msg_box.setIcon(QtWidgets.QMessageBox.Question)
            btn_evet = msg_box.addButton("Evet", QtWidgets.QMessageBox.YesRole)
            btn_hayir = msg_box.addButton("Hayır", QtWidgets.QMessageBox.NoRole)
            msg_box.setDefaultButton(btn_evet)
            msg_box.exec_()
            if msg_box.clickedButton() == btn_evet:
                try:
                    QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(dosya_yolu))
                except Exception:
                    os.startfile(dosya_yolu)
        else:
            QtWidgets.QMessageBox.critical(self, "Rapor Hatası", mesaj)

# ==============================================================================
# 16. UYGULAMA BAŞLATMA (ENTRY POINT)
# ==============================================================================

if __name__ == "__main__":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("fadec.telemetry.analyzer.1.0")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setStyleSheet(KOYU_TEMA_QSS)

    # ComboBox için Şık Turkuaz Aşağı Ok İkonu Üret (Koyu Tema)
    if not os.path.exists("asagi_ok.png"):
        pix = QtGui.QPixmap(16, 16)
        pix.fill(QtGui.QColor(0, 0, 0, 0))
        p = QtGui.QPainter(pix)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(QtGui.QColor("#00ffcc"), 2.5, QtCore.Qt.SolidLine)
        p.setPen(pen)
        p.drawLine(3, 6, 8, 11)
        p.drawLine(8, 11, 13, 6)
        p.end()
        pix.save("asagi_ok.png")

    # ComboBox için Koyu Mavi Aşağı Ok İkonu Üret (Açık Tema)
    if not os.path.exists("asagi_ok_koyu.png"):
        pix_koyu = QtGui.QPixmap(16, 16)
        pix_koyu.fill(QtGui.QColor(0, 0, 0, 0))
        p = QtGui.QPainter(pix_koyu)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(QtGui.QColor("#0284c7"), 2.5, QtCore.Qt.SolidLine)
        p.setPen(pen)
        p.drawLine(3, 6, 8, 11)
        p.drawLine(8, 11, 13, 6)
        p.end()
        pix_koyu.save("asagi_ok_koyu.png")

    pencere = AnaPencere()
    pencere.show()
    pencere.showMaximized()

    sys.exit(app.exec_())