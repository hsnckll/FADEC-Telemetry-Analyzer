# -*- coding: utf-8 -*-
"""
@file grafik_class.py
@brief Serbest Çalışma Alanı için bağımsız, modüler Sensör Grafik Kartı bileşeni (UserControl).
"""

import os
import time
import numpy as np
import pandas as pd
import pyqtgraph as pg
import pyqtgraph.exporters
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from matplotlib import animation
from numba import njit
import datetime

pg.setConfigOptions(useOpenGL=True)


@njit
def lttb_downsample(x, y, threshold=1500):
    """
    @brief LTTB (Largest Triangle Three Buckets) görsel veri küçültme algoritması.
    """
    if len(x) <= threshold or threshold < 3:
        return x, y

    out_x = np.zeros(threshold, dtype=x.dtype)
    out_y = np.zeros(threshold, dtype=y.dtype)

    out_x[0] = x[0]
    out_y[0] = y[0]

    bucket_size = (len(x) - 2) / (threshold - 2)
    a = 0

    for i in range(threshold - 2):
        b_start = int((i + 1) * bucket_size) + 1
        b_end = min(int((i + 2) * bucket_size) + 1, len(x))
        c_start = int((i + 2) * bucket_size) + 1
        c_end = min(int((i + 3) * bucket_size) + 1, len(x))

        avg_c_x = np.mean(x[c_start:c_end]) if c_start < c_end else x[-1]
        avg_c_y = np.mean(y[c_start:c_end]) if c_start < c_end else y[-1]

        max_area = -1.0
        best_index = b_start

        for j in range(b_start, b_end):
            area = abs(
                (x[a] - avg_c_x) * (y[j] - y[a]) -
                (x[a] - x[j]) * (avg_c_y - y[a])
            ) * 0.5

            if area > max_area:
                max_area = area
                best_index = j

        out_x[i + 1] = x[best_index]
        out_y[i + 1] = y[best_index]
        a = best_index

    out_x[-1] = x[-1]
    out_y[-1] = y[-1]
    return out_x, out_y


def kareli_izgara_deseni_olustur(grid_size=25, bg_color="#000000", line_color="#1a1a1a"):
    """
    @brief Koyu renkli, şık mühendislik kareli ızgara deseni üretir.
    """
    pix = QtGui.QPixmap(grid_size, grid_size)
    pix.fill(QtGui.QColor(bg_color))
    painter = QtGui.QPainter(pix)
    pen = QtGui.QPen(QtGui.QColor(line_color), 1, QtCore.Qt.SolidLine)
    painter.setPen(pen)
    painter.drawLine(grid_size - 1, 0, grid_size - 1, grid_size - 1)
    painter.drawLine(0, grid_size - 1, grid_size - 1, grid_size - 1)
    painter.end()
    return QtGui.QBrush(pix)


class DashboardTuval(QtWidgets.QWidget):
    """
    @brief 25px kareli mühendislik ızgara desenine sahip serbest tuval.
    Çoklu grafik seçimi için QRubberBand (Seçim Kutusu) desteği içerir.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.izgara_brush = kareli_izgara_deseni_olustur(25)
        # Seçim Kutusu (Rubber Band)
        self.rubberBand = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        self.origin = QtCore.QPoint()

    def tema_guncelle(self, tema="dark"):
        if tema == "light":
            self.izgara_brush = kareli_izgara_deseni_olustur(25, bg_color="#f8fafc", line_color="#e2e8f0")
        else:
            self.izgara_brush = kareli_izgara_deseni_olustur(25, bg_color="#000000", line_color="#1a1a1a")
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(event.rect(), self.izgara_brush)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            # Boşluğa tıklandığında seçimi başlat ve eski seçimi temizle
            self.origin = event.pos()
            self.rubberBand.setGeometry(QtCore.QRect(self.origin, QtCore.QSize()))
            self.rubberBand.show()
            self.secimi_temizle()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.origin.isNull():
            # Sürükleme anında dikdörtgeni genişlet/daralt
            self.rubberBand.setGeometry(QtCore.QRect(self.origin, event.pos()).normalized())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.rubberBand.hide()
            secim_alani = self.rubberBand.geometry()
            
            # Eğer kullanıcı sadece tek bir tık yaptıysa (genişlik/yükseklik çok küçükse) iptal et
            if secim_alani.width() > 5 and secim_alani.height() > 5:
                # Kesişen grafikleri bul
                for child in self.findChildren(SensorGrafikKarti):
                    # intersects() fonksiyonu nesnelerin birbiriyle teması var mı diye bakar
                    if secim_alani.intersects(child.geometry()):
                        child.secimi_ayarla(True)
            self.origin = QtCore.QPoint()
        super().mouseReleaseEvent(event)

    def secimi_temizle(self):
        """ Dashboard üzerindeki tüm seçili grafikleri temizler. """
        for child in self.findChildren(SensorGrafikKarti):
            if getattr(child, 'is_selected', False):
                child.secimi_ayarla(False)

    def secili_grafikler(self):
        """ Seçili olan tüm grafikleri liste olarak döner. """
        return [c for c in self.findChildren(SensorGrafikKarti) if getattr(c, 'is_selected', False)]

    def grafikleri_grupla(self):
        """ Seçili grafikleri alt alta tek bir pano (stack) olarak dizer ve eksenlerini (XLink) senkronize eder. """
        secililer = self.secili_grafikler()
        if len(secililer) <= 1:
            return
            
        import uuid
        yeni_grup_id = uuid.uuid4().hex
        
        # Y koordinatına göre yukarıdan aşağıya sırala
        secililer.sort(key=lambda k: k.pos().y())
        
        ref_kart = secililer[0]
        hedef_x = ref_kart.pos().x()
        hedef_w = ref_kart.width()
        mevcut_y = ref_kart.pos().y()
        
        for kart in secililer:
            kart.grup_id = yeni_grup_id
            # Genişliği ve X'i eşitle, tam altına yerleştir
            kart.setGeometry(hedef_x, mevcut_y, hedef_w, kart.height())
            mevcut_y += kart.height() - 1  # İnce, şık bir bitişiklik için -1 px
            
            # X Eksenlerini birbirine bağla (Sync Zoom/Pan)
            if kart != ref_kart:
                kart.plot_widget.setXLink(ref_kart.plot_widget)
                
            kart.secimi_ayarla(False)
            kart.tuvali_guncelle(sadece_buyut=False)
            
    def grubu_dagit(self, grup_id):
        """ Belirtilen gruba ait tüm grafiklerin bağını ve kilidini (XLink) koparır. """
        if not grup_id:
            return
        for child in self.findChildren(SensorGrafikKarti):
            if getattr(child, 'grup_id', None) == grup_id:
                child.grup_id = None
                child.plot_widget.setXLink(None)

    def grubu_yeniden_diz(self, grup_id):
        """ Gruptaki bir grafiğin boyutu değiştiğinde üst üste binmelerini önlemek için yeniden hizalar. """
        if not grup_id:
            return
            
        grup_elemanlari = [c for c in self.findChildren(SensorGrafikKarti) if getattr(c, 'grup_id', None) == grup_id]
        if not grup_elemanlari:
            return
            
        # Y eksenine göre yukarıdan aşağıya sırala
        grup_elemanlari.sort(key=lambda k: k.pos().y())
        
        ref_kart = grup_elemanlari[0]
        hedef_x = ref_kart.pos().x()
        mevcut_y = ref_kart.pos().y()
        
        for kart in grup_elemanlari:
            kart.move(hedef_x, mevcut_y)
            mevcut_y += kart.height() - 1


class SensorGrafikViewBox(pg.ViewBox):
    """
    @brief PyQtGraph'ın dahili tıklama ve sürükleme motorunu kullanan özel ViewBox.
    Sağ tıkla keskinleştirme / ölçekleme / sürükleme yapıldığında menü ASLA tetiklenmez.
    Yalnızca grafiğe tek tıklandığında menüyü açar.
    """

    def __init__(self, kart=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kart = kart

    def raiseContextMenu(self, ev):
        if self.kart is not None and hasattr(self.kart, 'menu_ac'):
            self.kart.menu_ac(QtGui.QCursor.pos())
        ev.accept()


class ZamanEkseniItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.baslangic_zamani = None
        self.dt_saniye = 0.1  # Varsayılan 100ms

    def tickStrings(self, values, scale, spacing):
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
                if abs(gecen_saniye) > 3153600000:
                    strings.append("")
                    continue

                anlik_zaman = self.baslangic_zamani + datetime.timedelta(seconds=gecen_saniye)

                if spacing_saniye >= 86400:
                    strings.append(anlik_zaman.strftime("%d.%m %H:%M"))
                elif spacing_saniye >= 60:
                    strings.append(anlik_zaman.strftime("%H:%M"))
                elif spacing_saniye >= 1:
                    strings.append(anlik_zaman.strftime("%H:%M:%S"))
                else:
                    strings.append(anlik_zaman.strftime("%H:%M:%S.%f")[:-5])
            except (OverflowError, ValueError, OSError):
                strings.append("")

        return strings


class SensorGrafikKarti(QtWidgets.QFrame):
    """
    @brief Tek bir sensörün grafiğini, limitlerini ve sağ tık kontrollerini yöneten modüler kart.
    (C#'taki UserControl mantığı - 144 FPS Akıcı Performans)
    """

    # Kapatıldığında ana pencereye haber veren sinyal (C#'taki Event)
    kapandi_signal = QtCore.pyqtSignal(object)

    def __init__(self, sensor_adi, df, parent=None, limitler=None, cizgi_rengi="#00ffcc", tema="dark", grafik_tipi="line", x_sensor_adi=None):
        """
        @brief Kurucu fonksiyon (Constructor).
        """
        super().__init__(parent)
        self.sensor_adi = sensor_adi
        self.df = df
        self.limitler = limitler
        self.cizgi_rengi = cizgi_rengi
        self.tema = tema
        self.grafik_tipi = grafik_tipi
        self.x_sensor_adi = x_sensor_adi
        self.limit_cizgileri = []
        self.ham_x = None
        self.ham_y = None
        self._surukleme_basladi = False
        self.grup_id = None

        # LOD Zamanlayıcısı (Ana Pencere analiz_grafigi ile 1-e-1 Birebir Aynı Mimari)
        self.zoom_timer = QtCore.QTimer(self)
        self.zoom_timer.setSingleShot(True)
        self.zoom_timer.timeout.connect(self.grafik_lod_guncelle)
        self.init_ui()
        self.ciz()
        self.tema_guncelle(self.tema)

    def init_ui(self):
        """
        @brief Kartın görsel arayüzünü (Başlık çubuğu + Grafik alanı) inşa eder.
        """

        self.setMinimumSize(QtCore.QSize(300, 200))
        self.setStyleSheet("""
            SensorGrafikKarti {
                background-color: #1a1a1a;
                border: 1px solid #333333;
            }
        """)

        layout_ana = QtWidgets.QVBoxLayout(self)
        layout_ana.setContentsMargins(0, 0, 0, 0)
        layout_ana.setSpacing(0)

        # --- Özel, Şık ve Koyu Temalı Başlık Çubuğu ---
        self.header_frame = QtWidgets.QFrame()
        # Kullanıcının istediği turkuaz renkli aksan çizgisi (border-left)
        self.header_frame.setStyleSheet(
            "background-color: #252526; border-bottom: 1px solid #333333; border-left: 4px solid #00ffcc; border-top: none; border-right: none;")
        self.header_frame.setFixedHeight(30)
        layout_header = QtWidgets.QHBoxLayout(self.header_frame)
        layout_header.setContentsMargins(10, 0, 5, 0)
        layout_header.setSpacing(5)

        baslik_metni = f" {self.sensor_adi} " if self.grafik_tipi == "line" else f" Y: {self.sensor_adi} | X: {self.x_sensor_adi} "
        self.lbl_baslik = QtWidgets.QLabel(baslik_metni)
        font_baslik = QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold)
        self.lbl_baslik.setFont(font_baslik)
        # Sensör ismini de temaya uygun turkuaz yapıyoruz
        self.lbl_baslik.setStyleSheet("color: #00ffcc; background-color: transparent; border: none;")
        layout_header.addWidget(self.lbl_baslik)

        layout_header.addStretch()

        btn_kapat = QtWidgets.QPushButton("✕")
        btn_kapat.setFixedSize(24, 24)
        btn_kapat.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        btn_kapat.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #aaaaaa; border: none; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e81123; color: white; border-radius: 2px;
            }
        """)
        btn_kapat.clicked.connect(self.kapat)
        layout_header.addWidget(btn_kapat)

        # Başlık sürükleme olayları (Pencereyi taşımak için)
        self.header_frame.mousePressEvent = self.baslik_basildi
        self.header_frame.mouseMoveEvent = self.baslik_suruklendi

        layout_ana.addWidget(self.header_frame)

        # --- İçerik Bölümü ---
        icerik_frame = QtWidgets.QFrame()
        icerik_frame.setStyleSheet("border: none; background-color: transparent;")
        layout_icerik = QtWidgets.QVBoxLayout(icerik_frame)
        layout_icerik.setContentsMargins(6, 6, 6, 6)
        layout_icerik.setSpacing(4)

        # 2. Üst İstatistik ve Bilgi Şeridi
        layout_ust = QtWidgets.QHBoxLayout()
        layout_ust.setSpacing(8)

        self.lbl_istatistik = QtWidgets.QLabel("")
        font_stat = QtGui.QFont("Segoe UI", 9)
        self.lbl_istatistik.setFont(font_stat)
        self.lbl_istatistik.setStyleSheet("background-color: transparent; border: none; padding-left: 4px;")
        layout_ust.addWidget(self.lbl_istatistik)

        layout_ust.addStretch()
        layout_icerik.addLayout(layout_ust)

        # 3. PyQtGraph Çizim Alanı (Özel ViewBox ile)
        vb = SensorGrafikViewBox(kart=self)
        if getattr(self, "grafik_tipi", "line") == "line":
            self.zaman_ekseni = ZamanEkseniItem(orientation='bottom')
            self.plot_widget = pg.PlotWidget(viewBox=vb, axisItems={'bottom': self.zaman_ekseni})
        else:
            self.plot_widget = pg.PlotWidget(viewBox=vb)
            
        self.plot_widget.setBackground('#121214')

        # Grid ve Eksen Stilleri (Daha zarif)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.4)
        self.plot_widget.setStyleSheet("border: 1px solid #2a2a2d; border-radius: 4px;")

        axis_font = QtGui.QFont("Segoe UI", 8)

        # X Ekseni
        axis_bottom = self.plot_widget.getAxis('bottom')
        axis_bottom.setLabel("Zaman", color='#888888')
        axis_bottom.setPen(pg.mkPen(color='#333333', width=1))
        axis_bottom.setTextPen(pg.mkPen(color='#777777'))
        axis_bottom.setTickFont(axis_font)

        # Y Ekseni
        axis_left = self.plot_widget.getAxis('left')
        axis_left.setPen(pg.mkPen(color='#333333', width=1))
        axis_left.setTextPen(pg.mkPen(color='#777777'))
        axis_left.setTickFont(axis_font)

        self.plot_widget.plotItem.vb.sigXRangeChanged.connect(lambda: self.zoom_timer.start(1000))

        # Daha belirgin Crosshair
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#888888', width=1, style=Qt.DashLine))
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('#888888', width=1, style=Qt.DashLine))

        # Kullanıcının isteği: Arka plan saydam (siyah kutu yok), sadece yazı
        self.crosshair_yazi = pg.TextItem(anchor=(0, 1), color="#ffffff", fill=pg.mkBrush(0, 0, 0, 0))
        self.crosshair_yazi.setFont(QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold))

        # Z-Index Ayarı: İmlecin ve yazının grafiğin (çizgilerin) altında kalmasını önler
        self.vLine.setZValue(1000)
        self.hLine.setZValue(1000)
        self.crosshair_yazi.setZValue(1001)

        self.plot_widget.addItem(self.vLine, ignoreBounds=True)
        self.plot_widget.addItem(self.hLine, ignoreBounds=True)
        self.hLine.hide()
        self.plot_widget.addItem(self.crosshair_yazi, ignoreBounds=True)

        # Fare hareketlerini algılayıp crosshair (imleç) değerlerini güncellemek için bağlantı
        self.proxy = pg.SignalProxy(self.plot_widget.scene().sigMouseMoved, rateLimit=120, slot=self.fare_hareket_etti)

        layout_icerik.addWidget(self.plot_widget)

        # --- Özel Yeniden Boyutlandırma Tutamacı ---
        self.resize_handle = QtWidgets.QLabel("◢")
        self.resize_handle.setStyleSheet(
            "color: #666666; font-size: 10px; background-color: transparent; border: none;")
        self.resize_handle.setCursor(QtGui.QCursor(QtCore.Qt.SizeFDiagCursor))
        self.resize_handle.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)
        self.resize_handle.mousePressEvent = self.resize_basildi
        self.resize_handle.mouseMoveEvent = self.resize_suruklendi

        layout_alt = QtWidgets.QHBoxLayout()
        layout_alt.setContentsMargins(0, 0, 0, 0)
        layout_alt.addStretch()
        layout_alt.addWidget(self.resize_handle)
        layout_icerik.addLayout(layout_alt)

        layout_ana.addWidget(icerik_frame)

        # Başlık sürükleme olayları (Pencereyi taşımak için)
        self.header_frame.mousePressEvent = self.baslik_basildi
        self.header_frame.mouseMoveEvent = self.baslik_suruklendi
        self.header_frame.mouseReleaseEvent = self.baslik_birakildi  # <--- BU YENİ

        # ... biraz aşağıda boyutlandırma olayları var:
        self.resize_handle.mousePressEvent = self.resize_basildi
        self.resize_handle.mouseMoveEvent = self.resize_suruklendi
        self.resize_handle.mouseReleaseEvent = self.resize_birakildi

        # Başlangıç temasını uygula
        self.tema_guncelle(self.tema)

    def mousePressEvent(self, event):
        """ Karta tıklandığı an onu en üst katmana (öne) getirir. """
        self.raise_()
        super().mousePressEvent(event)

    def secimi_ayarla(self, secili: bool):
        """ Kartın seçili olma durumunu (Görsel) ayarlar. """
        self.is_selected = secili
        tema = getattr(self, 'tema', 'dark')
        
        if secili:
            border_color = "#00ffcc"
            header_bg = "#2e2e30" if tema == 'dark' else "#e2e8f0"
            border_w = "2px"
            left_w = "6px"
        else:
            border_color = "#2a2a2d" if tema == 'dark' else "#cbd5e1"
            header_bg = "#252526" if tema == 'dark' else "#f1f5f9"
            border_w = "1px"
            left_w = "4px"
            
        self.plot_widget.setStyleSheet(f"border: {border_w} solid {border_color}; border-radius: 4px;")
        self.header_frame.setStyleSheet(f"background-color: {header_bg}; border-bottom: 1px solid {border_color}; border-left: {left_w} solid #00ffcc; border-top: none; border-right: none;")

    def baslik_basildi(self, event):
        """ Başlığa tıklandığında sürükleme başlangıç koordinatlarını kaydeder. Grup taşıma için seçili grafikleri belirler. """
        if event.button() == QtCore.Qt.LeftButton:
            self.raise_()
            self.drag_start_pos = event.globalPos()
            self.window_start_pos = self.pos()
            
            tuval = self.parent()
            # Eğer seçili DEĞİLSE, diğer seçimleri iptal et ve sadece bunu seçili yap (Klasik Windows davranışı)
            if not getattr(self, 'is_selected', False):
                if hasattr(tuval, 'secimi_temizle'):
                    tuval.secimi_temizle()
                self.secimi_ayarla(True)
            
            # Seçili olan tüm grafikleri bul ve başlangıç koordinatlarını hafızaya al
            self._grup_baslangic = {}
            if hasattr(tuval, 'secili_grafikler'):
                for kart in tuval.secili_grafikler():
                    self._grup_baslangic[kart] = kart.pos()

    def baslik_suruklendi(self, event):
        """ Başlık sürüklendikçe, eğer grup varsa tüm grubu 25px ızgaraya hizalayarak taşır. """
        if event.buttons() == QtCore.Qt.LeftButton and hasattr(self, 'drag_start_pos'):
            delta = event.globalPos() - self.drag_start_pos
            ham_x = self.window_start_pos.x() + delta.x()
            ham_y = self.window_start_pos.y() + delta.y()

            # 🔥 25px Manyetik Izgara Hizalaması (Ana Kart İçin)
            snap_x = max(0, round(ham_x / 25) * 25)
            snap_y = max(0, round(ham_y / 25) * 25)
            
            snapped_delta_x = snap_x - self.window_start_pos.x()
            snapped_delta_y = snap_y - self.window_start_pos.y()

            # Grubu taşı
            if hasattr(self, '_grup_baslangic') and self._grup_baslangic:
                for kart, b_pos in self._grup_baslangic.items():
                    yeni_x = max(0, b_pos.x() + snapped_delta_x)
                    yeni_y = max(0, b_pos.y() + snapped_delta_y)
                    kart.move(int(yeni_x), int(yeni_y))
                    kart.tuvali_guncelle(sadece_buyut=True)
            else:
                self.move(int(snap_x), int(snap_y))
                self.tuvali_guncelle(sadece_buyut=True)

    def resize_basildi(self, event):
        """ Boyutlandırma tutamacına basıldığında başlangıç boyutunu kaydeder. """
        if event.button() == QtCore.Qt.LeftButton:
            self.raise_()
            self.resize_drag_start_pos = event.globalPos()
            self.window_start_size = self.size()

    def resize_suruklendi(self, event):
        """ Tutamaç sürüklendikçe kartı 25px ızgara adımlarıyla büyütüp küçültür. Grup varsa tüm grubu eşit boyutlandırır. """
        if event.buttons() == QtCore.Qt.LeftButton and hasattr(self, 'resize_drag_start_pos'):
            delta = event.globalPos() - self.resize_drag_start_pos
            ham_w = self.window_start_size.width() + delta.x()
            ham_h = self.window_start_size.height() + delta.y()

            # 🔥 25px Boyutlandırma Hizalaması
            snap_w = max(self.minimumWidth(), round(ham_w / 25) * 25)
            snap_h = max(self.minimumHeight(), round(ham_h / 25) * 25)

            if getattr(self, 'grup_id', None) is not None:
                tuval = self.parent()
                grup_elemanlari = [c for c in tuval.findChildren(SensorGrafikKarti) if getattr(c, 'grup_id', None) == self.grup_id]
                
                # Kendi boyutunu değiştir
                self.resize(int(snap_w), int(snap_h))
                
                # Diğerlerinin de boyutunu eşitle
                for kart in grup_elemanlari:
                    if kart != self:
                        kart.resize(int(snap_w), int(snap_h))
                        kart.tuvali_guncelle(sadece_buyut=True)
                        
                # Boyutlar değiştiği için üst üste binmesinler diye grubu yeniden diz
                if hasattr(tuval, 'grubu_yeniden_diz'):
                    tuval.grubu_yeniden_diz(self.grup_id)
            else:
                self.resize(int(snap_w), int(snap_h))
                
            self.tuvali_guncelle(sadece_buyut=True)

    def baslik_birakildi(self, event):
        """ Başlık sürüklemesi bittiğinde tuvalin fazlalıklarını kırpar. """
        if hasattr(self, '_grup_baslangic') and self._grup_baslangic:
            for kart in self._grup_baslangic.keys():
                kart.tuvali_guncelle(sadece_buyut=False)
            self._grup_baslangic = {}
        else:
            self.tuvali_guncelle(sadece_buyut=False)

    def resize_birakildi(self, event):
        """ Boyutlandırma bittiğinde tuvalin fazlalıklarını kırpar. Grup varsa gruptaki tüm kartları günceller. """
        if getattr(self, 'grup_id', None) is not None:
            tuval = self.parent()
            grup_elemanlari = [c for c in tuval.findChildren(SensorGrafikKarti) if getattr(c, 'grup_id', None) == self.grup_id]
            for kart in grup_elemanlari:
                kart.tuvali_guncelle(sadece_buyut=False)
        else:
            self.tuvali_guncelle(sadece_buyut=False)

    def ciz(self):
        """
        @brief Sensör verisini LTTB veya Scatter için dilimleme ile çizer.
        """
        if self.df is None or self.sensor_adi not in self.df.columns:
            return
            
        if self.grafik_tipi == "scatter" and (not self.x_sensor_adi or self.x_sensor_adi not in self.df.columns):
            return

        t_basla = time.perf_counter()

        if self.grafik_tipi == "line":
            x_raw = self.df["Zaman_Index"].to_numpy(dtype=np.float64, copy=False) if "Zaman_Index" in self.df.columns else np.arange(len(self.df), dtype=np.float64)
        else:
            x_raw = self.df[self.x_sensor_adi].to_numpy(dtype=np.float64, copy=False)
            
        y_raw = self.df[self.sensor_adi].to_numpy(dtype=np.float64, copy=False)

        if self.grafik_tipi == "line" and "Zaman_Gorsel" in self.df.columns and len(self.df) >= 2:
            try:
                t0 = pd.to_datetime(str(self.df.iloc[0]["Zaman_Gorsel"]))
                t1 = pd.to_datetime(str(self.df.iloc[1]["Zaman_Gorsel"]))
                self.zaman_ekseni.baslangic_zamani = t0
                fark = (t1 - t0).total_seconds()
                self.zaman_ekseni.dt_saniye = fark if fark > 0 else 0.1
            except Exception:
                pass

        self.ham_x = x_raw
        self.ham_y = y_raw

        # İstatistikleri hesapla
        try:
            val_min = float(np.nanmin(y_raw))
            val_max = float(np.nanmax(y_raw))
            val_avg = float(np.nanmean(y_raw))
            # Şık HTML rozet stili (Temaya duyarlı)
            if getattr(self, 'tema', 'dark') == 'light':
                self.lbl_istatistik.setText(
                    f"<span style='color:#64748b;'>Min:</span> <b style='color:#0f172a;'>{val_min:.2f}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
                    f"<span style='color:#64748b;'>Max:</span> <b style='color:#0f172a;'>{val_max:.2f}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
                    f"<span style='color:#64748b;'>Ort:</span> <b style='color:#0f172a;'>{val_avg:.2f}</b>"
                )
            else:
                self.lbl_istatistik.setText(
                    f"<span style='color:#777777;'>Min:</span> <b style='color:#cccccc;'>{val_min:.2f}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
                    f"<span style='color:#777777;'>Max:</span> <b style='color:#cccccc;'>{val_max:.2f}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
                    f"<span style='color:#777777;'>Ort:</span> <b style='color:#cccccc;'>{val_avg:.2f}</b>"
                )
        except Exception:
            pass

        t_lttb_basla = time.perf_counter()
        
        if self.grafik_tipi == "line":
            if len(x_raw) > 1500:
                x_down, y_down = lttb_downsample(x_raw, y_raw, threshold=1500)
            else:
                x_down, y_down = x_raw, y_raw
            
            self.cizgi = self.plot_widget.plot(
                x=x_down, y=y_down,
                pen=pg.mkPen(color=self.cizgi_rengi, width=1.5),
                name=self.sensor_adi
            )
        else:
            # Scatter Plot: basit dilimleme (slice) ile hızlı render
            step = max(1, len(x_raw) // 1500)
            x_down = x_raw[::step]
            y_down = y_raw[::step]
            
            self.cizgi = self.plot_widget.plot(
                x=x_down, y=y_down,
                pen=None,
                symbol='o',
                symbolSize=4,
                symbolPen=None,
                symbolBrush=self.cizgi_rengi,
                name=self.sensor_adi
            )

        self.cizgi.setDownsampling(ds=False, auto=False)
        self.cizgi.setClipToView(False)
        t_lttb_bitis = time.perf_counter()

        t_bitis = time.perf_counter()

        # KULLANICI ISTEGI: Grafikler oluşturulurken limit çizgileri otomatik gelmesin, 
        # sadece sağ tıkla istendiğinde eklensin.
        # if self.limitler and len(self.limitler) >= 2:
        #     self.limit_cizgilerini_guncelle(self.limitler[0], self.limitler[1])

        lttb_ms = (t_lttb_bitis - t_lttb_basla) * 1000
        toplam_ms = (t_bitis - t_basla) * 1000

    def grafik_lod_guncelle(self):
        """
        @brief Dinamik LOD güncellemesi yapar. Scatter plot için bounding box filtreleme kullanır.
        """
        if self.ham_x is None or self.ham_y is None:
            return

        x_min, x_max = self.plot_widget.viewRange()[0]
        
        if getattr(self, 'grafik_tipi', 'line') == 'line':
            genislik = x_max - x_min
            buffer_min = x_min - genislik * 0.5
            buffer_max = x_max + genislik * 0.5
    
            start_idx = max(0, int(np.floor(buffer_min)) - 1)
            end_idx = min(len(self.ham_x), int(np.ceil(buffer_max)) + 1)
    
            gorunen_nokta_sayisi = end_idx - start_idx
            if gorunen_nokta_sayisi <= 0:
                return
    
            x_slice = self.ham_x[start_idx:end_idx]
            y_slice = self.ham_y[start_idx:end_idx]
    
            if gorunen_nokta_sayisi <= 3000:
                self.cizgi.setData(x_slice, y_slice)
            else:
                x_lttb, y_lttb = lttb_downsample(x_slice, y_slice, threshold=1500)
                self.cizgi.setData(x_lttb, y_lttb)
        else:
            y_min, y_max = self.plot_widget.viewRange()[1]
            x_range = x_max - x_min
            y_range = y_max - y_min
            
            mask = (self.ham_x >= x_min - x_range) & (self.ham_x <= x_max + x_range) & \
                   (self.ham_y >= y_min - y_range) & (self.ham_y <= y_max + y_range)
            
            x_slice = self.ham_x[mask]
            y_slice = self.ham_y[mask]
            
            if len(x_slice) > 1500:
                step = max(1, len(x_slice) // 1500)
                x_slice = x_slice[::step]
                y_slice = y_slice[::step]
                
            self.cizgi.setData(x_slice, y_slice)

    def crosshair_gizle(self):
        """ Crosshair imlecini kapatır. """
        if hasattr(self, 'vLine') and self.vLine.isVisible():
            self.vLine.hide()
        if hasattr(self, 'hLine') and self.hLine.isVisible():
            self.hLine.hide()
        if hasattr(self, 'crosshair_yazi') and self.crosshair_yazi.isVisible():
            self.crosshair_yazi.hide()

    def crosshair_guncelle(self, mx, my, gercekZaman, is_scatter=False, from_group=False):
        """ Verilen koordinatlara göre Crosshair'i günceller. HTML render cache optimizasyonu kullanır. """
        if is_scatter:
            x_data, y_data = self.cizgi.getData()
            if x_data is None or len(x_data) == 0:
                return
                
            x_range = max(1e-6, np.ptp(x_data))
            y_range = max(1e-6, np.ptp(y_data))
            dist = ((x_data - mx) / x_range)**2 + ((y_data - my) / y_range)**2
            min_idx = np.argmin(dist)
            
            best_x = x_data[min_idx]
            best_y = y_data[min_idx]
            
            if hasattr(self, 'vLine') and not self.vLine.isVisible():
                self.vLine.show()
            if hasattr(self, 'hLine') and not self.hLine.isVisible():
                self.hLine.show()
            if hasattr(self, 'crosshair_yazi') and not self.crosshair_yazi.isVisible():
                self.crosshair_yazi.show()
                
            if hasattr(self, 'vLine'): self.vLine.setPos(best_x)
            if hasattr(self, 'hLine'): self.hLine.setPos(best_y)
            
            # OPTİMİZASYON: Sadece indeks değiştiyse ağır HTML render işlemini yap (FPS'yi kurtarır)
            if getattr(self, '_son_guncel_idx', None) != min_idx:
                self._son_guncel_idx = min_idx
                yazi_rengi = "#000000" if getattr(self, 'tema', 'dark') == 'light' else "#ffffff"
                self.crosshair_yazi.setHtml(
                    f"<div style='padding: 2px;'>"
                    f"<b style='color:{self.cizgi_rengi};'>Y ({self.sensor_adi})</b>: <b style='color:{yazi_rengi};'>{best_y:.2f}</b><br>"
                    f"<b style='color:#00ffcc;'>X ({self.x_sensor_adi})</b>: <b style='color:{yazi_rengi};'>{best_x:.2f}</b>"
                    f"</div>"
                )
            self.crosshair_yazi.setPos(best_x, best_y)
        else:
            satir_idx = gercekZaman - 1
            if satir_idx < 0 or satir_idx >= len(self.ham_y):
                self.crosshair_gizle()
                return

            if hasattr(self, 'vLine') and not self.vLine.isVisible():
                self.vLine.show()
            if hasattr(self, 'crosshair_yazi') and not self.crosshair_yazi.isVisible():
                self.crosshair_yazi.show()

            if hasattr(self, 'vLine'): self.vLine.setPos(gercekZaman)
            deger = self.ham_y[satir_idx]

            # OPTİMİZASYON: Zaman indeksi değişmediyse aynı HTML stringini tekrar render etme!
            if getattr(self, '_son_guncel_x', None) != gercekZaman:
                self._son_guncel_x = gercekZaman
                yazi_rengi = "#000000" if getattr(self, 'tema', 'dark') == 'light' else "#ffffff"
                self.crosshair_yazi.setHtml(f"<b style='color:{self.cizgi_rengi};'>{self.sensor_adi}</b> : <b style='color:{yazi_rengi};'>{deger:.2f}</b>")
            
            # Gruptan gelen tetiklemelerde, crosshair yazısını kendi eksenindeki değere sabitle
            y_pos = deger if from_group else my
            self.crosshair_yazi.setPos(gercekZaman, y_pos)

    def fare_hareket_etti(self, evt):
        """
        @brief Yüksek performanslı, saf NumPy tabanlı akıllı fare takip imleci.
        Grup içi senkronizasyonlarda önbellek (cache) kullanarak kasmaları %90 oranında önler.
        """
        if QtWidgets.QApplication.mouseButtons() != QtCore.Qt.NoButton:
            return

        if self.ham_y is None or len(self.ham_y) == 0:
            return

        pos = evt[0]
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_noktasi = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            mx, my = mouse_noktasi.x(), mouse_noktasi.y()
            
            is_scatter = getattr(self, 'grafik_tipi', 'line') == 'scatter'
            try:
                gercekZaman = int(round(mx))
            except (OverflowError, ValueError):
                gercekZaman = 0

            # Kendi Crosshair'ini güncelle
            self.crosshair_guncelle(mx, my, gercekZaman, is_scatter=is_scatter, from_group=False)

            # --- GRUP (STACK & SYNC) SENKRONİZASYONU ---
            if getattr(self, 'grup_id', None) is not None:
                # OPTİMİZASYON: 120Hz hızda tüm Qt widget ağacını aramak felaket yavaşlatır!
                # Grubu bir kere bul ve önbelleğe (cache) al.
                if not hasattr(self, '_grup_cache') or getattr(self, '_grup_cache_id', None) != self.grup_id:
                    tuval = self.parent()
                    self._grup_cache = [c for c in tuval.findChildren(SensorGrafikKarti) if getattr(c, 'grup_id', None) == self.grup_id]
                    self._grup_cache_id = self.grup_id
                    
                for child in self._grup_cache:
                    if child != self:
                        child_is_scatter = getattr(child, 'grafik_tipi', 'line') == 'scatter'
                        child.crosshair_guncelle(mx, my, gercekZaman, is_scatter=child_is_scatter, from_group=True)
        else:
            self.crosshair_gizle()
            if getattr(self, 'grup_id', None) is not None:
                if hasattr(self, '_grup_cache') and getattr(self, '_grup_cache_id', None) == self.grup_id:
                    for child in self._grup_cache:
                        if child != self:
                            child.crosshair_gizle()

    # ==========================================================================
    # 🖱️ AKILLI SAĞ TIK MENÜSÜ (Sürükleme anında açılmaz, tek tıkta açılır)
    # ==========================================================================
    def contextMenuEvent(self, event):
        """
        @brief Qt'nin varsayılan contextMenuEvent tetiklemesini engeller (Sürükleme sonrası açılmayı önler).
        """
        event.ignore()

    def menu_ac(self, global_pos=None):
        """
        @brief Grafiğin profesyonel açılır kontrol menüsünü görüntüler.
        """
        if global_pos is None:
            global_pos = QtGui.QCursor.pos()
        menu = QtWidgets.QMenu(self)
        if getattr(self, 'tema', 'dark') == 'light':
            menu.setStyleSheet("""
                QMenu {
                    background-color: #ffffff;
                    color: #0f172a;
                    border: 1.5px solid #cbd5e1;
                    padding: 4px;
                    border-radius: 6px;
                }
                QMenu::item {
                    padding: 7px 22px;
                    color: #1e293b;
                    font-weight: 500;
                    border-radius: 4px;
                }
                QMenu::item:selected {
                    background-color: #0284c7;
                    color: #ffffff;
                    font-weight: bold;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #e2e8f0;
                    margin: 4px 8px;
                }
            """)
        else:
            menu.setStyleSheet("""
                QMenu {
                    background-color: #252526;
                    color: #ffffff;
                    border: 1px solid #444444;
                    padding: 4px;
                    border-radius: 6px;
                }
                QMenu::item {
                    padding: 7px 22px;
                    color: #e0e0e0;
                    border-radius: 4px;
                }
                QMenu::item:selected {
                    background-color: #00ffcc;
                    color: #000000;
                    font-weight: bold;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #333333;
                    margin: 4px 8px;
                }
            """)

        tuval = self.parent()
        secili_sayisi = len(tuval.secili_grafikler()) if hasattr(tuval, 'secili_grafikler') else 0
        
        act_grupla = None
        act_grubu_dagit = None
        
        if secili_sayisi > 1 and getattr(self, 'is_selected', False):
            act_grupla = menu.addAction("🔗 Seçili Grafikleri Grupla (Stack & Sync)")
        if getattr(self, 'grup_id', None) is not None:
            act_grubu_dagit = menu.addAction("✂️ Grubu Dağıt (Unlink)")
            menu.addSeparator()

        act_limit_uygula = menu.addAction("⚙️ Tanımlı Limitleri Göster")
        act_limit_sil = menu.addAction("❌ Limit Çizgilerini Kaldır")
        menu.addSeparator()
        act_png = menu.addAction("📷 PNG Olarak Kaydet")
        act_reset = menu.addAction("🔄 Otomatik Odaklan (Reset Zoom)")
        menu.addSeparator()
        act_kapat = menu.addAction("🗑️ Bu Grafiği Kapat")

        secilen = menu.exec_(global_pos)

        if secilen == act_limit_uygula:
            self.limitleri_uygula()
        elif act_grupla and secilen == act_grupla:
            tuval.grafikleri_grupla()
        elif act_grubu_dagit and secilen == act_grubu_dagit:
            tuval.grubu_dagit(self.grup_id)
        elif secilen == act_limit_sil:
            self.limit_cizgilerini_temizle()
        elif secilen == act_png:
            self.png_kaydet()
        elif secilen == act_reset:
            self.plot_widget.plotItem.vb.autoRange(padding=0.02)
        elif secilen == act_kapat:
            self.kapat()

    def limitleri_uygula(self):
        """
        @brief C++/JSON (parameters.json) üzerinden gelen tanımlı resmi limit değerlerini grafiğe çizer.
        """
        limit_degerleri = None
        if self.limitler and len(self.limitler) >= 2:
            limit_degerleri = self.limitler
        elif self.parent() and hasattr(self.parent(), 'LIMITLER'):
            limit_degerleri = self.parent().LIMITLER.get(self.sensor_adi, None)

        if limit_degerleri and len(limit_degerleri) >= 2:
            self.limit_cizgilerini_guncelle(limit_degerleri[0], limit_degerleri[1])
        else:
            QtWidgets.QMessageBox.information(
                self,
                "Limit Bulunamadı",
                f"'{self.sensor_adi}' için sistemde tanımlanmış bir limit değeri (parameters.json) bulunamadı."
            )

    def limit_cizgilerini_guncelle(self, min_val, max_val):
        """
        @brief Grafiğin üzerine yatay kesikli limit çizgilerini çizer.
        """
        self.limit_cizgilerini_temizle()

        pen_limit = pg.mkPen(color=(255, 69, 0), width=1.5, style=Qt.DashLine)
        c_min = pg.InfiniteLine(angle=0, pos=min_val, pen=pen_limit)
        c_max = pg.InfiniteLine(angle=0, pos=max_val, pen=pen_limit)

        self.plot_widget.addItem(c_min)
        self.plot_widget.addItem(c_max)
        self.limit_cizgileri.extend([c_min, c_max])

    def limit_cizgilerini_temizle(self):
        """
        @brief Çizilmiş olan limit çizgilerini temizler.
        """
        for c in self.limit_cizgileri:
            self.plot_widget.removeItem(c)
        self.limit_cizgileri.clear()

    def png_kaydet(self):
        """
        @brief Sadece bu grafiği yüksek çözünürlüklü PNG olarak dışa aktarır.
        """
        dosya_yolu, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, f"{self.sensor_adi} Grafiğini Kaydet", f"{self.sensor_adi}.png", "PNG Dosyası (*.png)"
        )
        if dosya_yolu:
            exporter = pg.exporters.ImageExporter(self.plot_widget.plotItem)
            exporter.parameters()['width'] = 1920
            exporter.export(dosya_yolu)

    def kapat(self):
        """
        @brief Kendini ve varsa MDI penceresini kapatır.
        """
        self.kapandi_signal.emit(self)
        self.setParent(None)
        self.deleteLater()

        self.tuvali_guncelle()

    def tuvali_guncelle(self, sadece_buyut=False):
        ana_pencere = self.window()
        if hasattr(ana_pencere, 'guncelle_tuval_boyutu'):
            ana_pencere.guncelle_tuval_boyutu(sadece_buyut=sadece_buyut)

    def tema_guncelle(self, tema="dark"):
        """
        @brief Kartın temasını (açık/koyu) dinamik günceller.
        """
        self.tema = tema
        if tema == "light":
            self.setStyleSheet("""
                SensorGrafikKarti {
                    background-color: #ffffff;
                    border: 1.5px solid #cbd5e1;
                    border-radius: 6px;
                }
            """)
            self.header_frame.setStyleSheet("background-color: #f1f5f9; border-bottom: 1px solid #cbd5e1; border-left: 4px solid #0284c7; border-top: none; border-right: none;")
            if hasattr(self, 'lbl_baslik'):
                self.lbl_baslik.setStyleSheet("color: #0369a1; background-color: transparent; border: none;")
            if hasattr(self, 'lbl_istatistik') and hasattr(self, 'ham_y') and self.ham_y is not None:
                try:
                    import numpy as np
                    val_min = float(np.nanmin(self.ham_y))
                    val_max = float(np.nanmax(self.ham_y))
                    val_avg = float(np.nanmean(self.ham_y))
                    self.lbl_istatistik.setText(
                        f"<span style='color:#64748b;'>Min:</span> <b style='color:#0f172a;'>{val_min:.2f}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
                        f"<span style='color:#64748b;'>Max:</span> <b style='color:#0f172a;'>{val_max:.2f}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
                        f"<span style='color:#64748b;'>Ort:</span> <b style='color:#0f172a;'>{val_avg:.2f}</b>"
                    )
                except Exception:
                    pass
            self.plot_widget.setBackground('#ffffff')
            self.plot_widget.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 4px;")
            self.plot_widget.getAxis('bottom').setPen(pg.mkPen(color='#94a3b8', width=1))
            self.plot_widget.getAxis('left').setPen(pg.mkPen(color='#94a3b8', width=1))
            self.plot_widget.getAxis('bottom').setTextPen(pg.mkPen(color='#334155'))
            self.plot_widget.getAxis('left').setTextPen(pg.mkPen(color='#334155'))
            self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
            if hasattr(self, 'vLine'):
                self.vLine.setPen(pg.mkPen('#0284c7', width=1.5, style=Qt.DashLine))
            if hasattr(self, 'crosshair_yazi'):
                self.crosshair_yazi.fill = pg.mkBrush(None)
                self.crosshair_yazi.border = pg.mkPen(None)
        else:
            self.setStyleSheet("""
                SensorGrafikKarti {
                    background-color: #1a1a1a;
                    border: 1px solid #333333;
                    border-radius: 0px;
                }
            """)
            self.header_frame.setStyleSheet("background-color: #252526; border-bottom: 1px solid #333333; border-left: 4px solid #00ffcc; border-top: none; border-right: none;")
            if hasattr(self, 'lbl_baslik'):
                self.lbl_baslik.setStyleSheet("color: #00ffcc; background-color: transparent; border: none;")
            if hasattr(self, 'lbl_istatistik') and hasattr(self, 'ham_y') and self.ham_y is not None:
                try:
                    import numpy as np
                    val_min = float(np.nanmin(self.ham_y))
                    val_max = float(np.nanmax(self.ham_y))
                    val_avg = float(np.nanmean(self.ham_y))
                    self.lbl_istatistik.setText(
                        f"<span style='color:#777777;'>Min:</span> <b style='color:#cccccc;'>{val_min:.2f}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
                        f"<span style='color:#777777;'>Max:</span> <b style='color:#cccccc;'>{val_max:.2f}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
                        f"<span style='color:#777777;'>Ort:</span> <b style='color:#cccccc;'>{val_avg:.2f}</b>"
                    )
                except Exception:
                    pass
            self.plot_widget.setBackground('#121214')
            self.plot_widget.setStyleSheet("border: 1px solid #2a2a2d; border-radius: 4px;")
            self.plot_widget.getAxis('bottom').setPen(pg.mkPen(color='#333333', width=1))
            self.plot_widget.getAxis('left').setPen(pg.mkPen(color='#333333', width=1))
            self.plot_widget.getAxis('bottom').setTextPen(pg.mkPen(color='#777777'))
            self.plot_widget.getAxis('left').setTextPen(pg.mkPen(color='#777777'))
            self.plot_widget.showGrid(x=True, y=True, alpha=0.4)
            if hasattr(self, 'vLine'):
                self.vLine.setPen(pg.mkPen((255, 255, 0, 180), width=1.5, style=Qt.DashLine))
            if hasattr(self, 'crosshair_yazi'):
                self.crosshair_yazi.fill = pg.mkBrush(None)
                self.crosshair_yazi.border = pg.mkPen(None)