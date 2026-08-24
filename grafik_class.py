# -*- coding: utf-8 -*-
"""
@file grafik_class.py
@brief Serbest Çalışma Alanı için bağımsız, modüler Sensör Grafik Kartı bileşeni (UserControl).
"""

import os
import numpy as np
import pandas as pd
import pyqtgraph as pg
import pyqtgraph.exporters
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from matplotlib import animation
from numba import njit
import datetime

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


def kareli_izgara_deseni_olustur(grid_size=25, bg_color="#0e0e10", line_color="#202026"):
    """
    @brief QMdiArea için koyu renkli, şık mühendislik kareli ızgara deseni üretir.
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


class GridMdiSubWindow(QtWidgets.QMdiSubWindow):
    """
    @brief Hareket ettirildiğinde veya boyutlandırıldığında 25px kareli ızgaraya manyetik olarak yapışan (Snap-to-Grid) MDI penceresi.
    """
    GRID_SIZE = 25

    def __init__(self, parent=None):
        super().__init__(parent)
        self._snapping = False
        self._otomatik_diziliyor = False
        # Çerçevesiz, temiz görünüm için OS frame'ini kaldır
        self.setWindowFlags(QtCore.Qt.SubWindow | QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: transparent;")

    def moveEvent(self, ev):
        super().moveEvent(ev)
        if not self._snapping and not getattr(self, '_otomatik_diziliyor', False):
            self._snapping = True
            p = self.pos()
            sx = round(p.x() / self.GRID_SIZE) * self.GRID_SIZE
            sy = round(p.y() / self.GRID_SIZE) * self.GRID_SIZE
            if (p.x(), p.y()) != (sx, sy):
                super().move(int(sx), int(sy))
            self._snapping = False

        # MDI Scrollbar Alanını Otomatik Genişlet
        if not getattr(self, '_otomatik_diziliyor', False):
            mdi = self.mdiArea()
            if mdi and hasattr(mdi, 'guncelle_kaydirma_araligi'):
                mdi.guncelle_kaydirma_araligi()

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if not self._snapping and not getattr(self, '_otomatik_diziliyor', False):
            self._snapping = True
            sz = self.size()
            sw = max(self.minimumWidth(), round(sz.width() / self.GRID_SIZE) * self.GRID_SIZE)
            sh = max(self.minimumHeight(), round(sz.height() / self.GRID_SIZE) * self.GRID_SIZE)
            if (sz.width(), sz.height()) != (sw, sh):
                super().resize(int(sw), int(sh))
            self._snapping = False

        # MDI Scrollbar Alanını Otomatik Genişlet
        if not getattr(self, '_otomatik_diziliyor', False):
            mdi = self.mdiArea()
            if mdi and hasattr(mdi, 'guncelle_kaydirma_araligi'):
                mdi.guncelle_kaydirma_araligi()


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

    def __init__(self, sensor_adi, df, parent=None, limitler=None, cizgi_rengi="#00ffcc"):
        """
        @brief Kurucu fonksiyon (Constructor).
        """
        super().__init__(parent)
        self.sensor_adi = sensor_adi
        self.df = df
        self.limitler = limitler
        self.cizgi_rengi = cizgi_rengi
        self.limit_cizgileri = []
        self.ham_x = None
        self.ham_y = None
        self._surukleme_basladi = False

        # LOD Zamanlayıcısı (Ana Pencere analiz_grafigi ile 1-e-1 Birebir Aynı Mimari)
        self.zoom_timer = QtCore.QTimer(self)
        self.zoom_timer.setSingleShot(True)
        self.zoom_timer.timeout.connect(self.grafik_lod_guncelle)
        self.init_ui()
        self.ciz()

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
        self.header_frame.setStyleSheet("background-color: #252526; border-bottom: 1px solid #333333; border-left: 4px solid #00ffcc; border-top: none; border-right: none;")
        self.header_frame.setFixedHeight(30)
        layout_header = QtWidgets.QHBoxLayout(self.header_frame)
        layout_header.setContentsMargins(10, 0, 5, 0)
        layout_header.setSpacing(5)
        
        lbl_baslik = QtWidgets.QLabel(f" {self.sensor_adi} ")
        font_baslik = QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold)
        lbl_baslik.setFont(font_baslik)
        # Sensör ismini de temaya uygun turkuaz yapıyoruz
        lbl_baslik.setStyleSheet("color: #00ffcc; background-color: transparent; border: none;")
        layout_header.addWidget(lbl_baslik)
        
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
        pg.setConfigOption('antialias', False)  # Performans (Droplanma) sorunu için Anti-Aliasing kapatıldı
        vb = SensorGrafikViewBox(kart=self)
        self.zaman_ekseni = ZamanEkseniItem(orientation='bottom')
        self.plot_widget = pg.PlotWidget(viewBox=vb, axisItems={'bottom': self.zaman_ekseni})
        self.plot_widget.setBackground('#121214')  # Daha yumuşak koyu gri arka plan
        
        # Grid ve Eksen Stilleri (Daha zarif)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.4)
        self.plot_widget.setStyleSheet("border: 1px solid #2a2a2d; border-radius: 4px;")

        axis_font = QtGui.QFont("Segoe UI", 8)
        
        # X Ekseni
        axis_bottom = self.plot_widget.getAxis('bottom')
        axis_bottom.setLabel("Zaman (İndeks)", color='#888888')
        axis_bottom.setPen(pg.mkPen(color='#333333', width=1))
        axis_bottom.setTextPen(pg.mkPen(color='#777777'))
        axis_bottom.setTickFont(axis_font)
        
        # Y Ekseni
        axis_left = self.plot_widget.getAxis('left')
        axis_left.setPen(pg.mkPen(color='#333333', width=1))
        axis_left.setTextPen(pg.mkPen(color='#777777'))
        axis_left.setTickFont(axis_font)

        self.plot_widget.plotItem.vb.sigXRangeChanged.connect(lambda: self.zoom_timer.start(600))

        # Daha belirgin Crosshair
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#888888', width=1, style=Qt.DashLine))
        
        # Kullanıcının isteği: Arka plan saydam (siyah kutu yok), sadece yazı
        self.crosshair_yazi = pg.TextItem(anchor=(0, 1), color="#ffffff", fill=pg.mkBrush(0, 0, 0, 0))
        self.crosshair_yazi.setFont(QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold))
        
        # Z-Index Ayarı: İmlecin ve yazının grafiğin (çizgilerin) altında kalmasını önler
        self.vLine.setZValue(1000)
        self.crosshair_yazi.setZValue(1001)
        
        self.plot_widget.addItem(self.vLine, ignoreBounds=True)
        self.plot_widget.addItem(self.crosshair_yazi, ignoreBounds=True)
        
        # Fare hareketlerini algılayıp crosshair (imleç) değerlerini güncellemek için bağlantı
        self.proxy = pg.SignalProxy(self.plot_widget.scene().sigMouseMoved, rateLimit=60, slot=self.fare_hareket_etti)

        layout_icerik.addWidget(self.plot_widget)
        
        # --- Özel Yeniden Boyutlandırma Tutamacı ---
        self.resize_handle = QtWidgets.QLabel("◢")
        self.resize_handle.setStyleSheet("color: #666666; font-size: 10px; background-color: transparent; border: none;")
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

    def baslik_basildi(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_start_pos = event.globalPos()
            self.mdi_parent = self.parentWidget()
            while self.mdi_parent is not None and not isinstance(self.mdi_parent, QtWidgets.QMdiSubWindow):
                self.mdi_parent = self.mdi_parent.parentWidget()
            if self.mdi_parent is not None:
                self.window_start_pos = self.mdi_parent.pos()

    def baslik_suruklendi(self, event):
        if event.buttons() == QtCore.Qt.LeftButton and hasattr(self, 'drag_start_pos') and hasattr(self, 'mdi_parent') and self.mdi_parent is not None:
            delta = event.globalPos() - self.drag_start_pos
            self.mdi_parent.move(self.window_start_pos + delta)

    def resize_basildi(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.resize_drag_start_pos = event.globalPos()
            self.mdi_parent = self.parentWidget()
            while self.mdi_parent is not None and not isinstance(self.mdi_parent, QtWidgets.QMdiSubWindow):
                self.mdi_parent = self.mdi_parent.parentWidget()
            if self.mdi_parent is not None:
                self.window_start_size = self.mdi_parent.size()

    def resize_suruklendi(self, event):
        if event.buttons() == QtCore.Qt.LeftButton and hasattr(self, 'resize_drag_start_pos') and hasattr(self, 'mdi_parent') and self.mdi_parent is not None:
            delta = event.globalPos() - self.resize_drag_start_pos
            yeni_genislik = max(self.mdi_parent.minimumWidth(), self.window_start_size.width() + delta.x())
            yeni_yukseklik = max(self.mdi_parent.minimumHeight(), self.window_start_size.height() + delta.y())
            self.mdi_parent.resize(yeni_genislik, yeni_yukseklik)

    def ciz(self):
        """
        @brief Sensör verisini LTTB downsampling ile çizer ve istatistikleri hesaplar.
        """
        if self.df is None or self.sensor_adi not in self.df.columns:
            return

        x_raw = self.df["Zaman_Index"].to_numpy(dtype=np.float64, copy=False) if "Zaman_Index" in self.df.columns else np.arange(len(self.df), dtype=np.float64)
        y_raw = self.df[self.sensor_adi].to_numpy(dtype=np.float64, copy=False)

        if "Zaman_Gorsel" in self.df.columns:
            try:
                ilk_zaman = self.df["Zaman_Gorsel"].iloc[0]
                if isinstance(ilk_zaman, str):
                    self.zaman_ekseni.baslangic_zamani = pd.to_datetime(ilk_zaman, errors='coerce')
                else:
                    self.zaman_ekseni.baslangic_zamani = ilk_zaman
            except Exception:
                pass

        self.ham_x = x_raw
        self.ham_y = y_raw

        # İstatistikleri hesapla
        try:
            val_min = float(np.nanmin(y_raw))
            val_max = float(np.nanmax(y_raw))
            val_avg = float(np.nanmean(y_raw))
            # Şık HTML rozet stili
            self.lbl_istatistik.setText(
                f"<span style='color:#777777;'>Min:</span> <b style='color:#cccccc;'>{val_min:.2f}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"<span style='color:#777777;'>Max:</span> <b style='color:#cccccc;'>{val_max:.2f}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"<span style='color:#777777;'>Ort:</span> <b style='color:#cccccc;'>{val_avg:.2f}</b>"
            )
        except Exception:
            pass

        # LTTB ile çiz
        if len(x_raw) > 1500:
            x_down, y_down = lttb_downsample(x_raw, y_raw, threshold=1500)
        else:
            x_down, y_down = x_raw, y_raw

        self.cizgi = self.plot_widget.plot(
            x=x_down, y=y_down,
            pen=pg.mkPen(color=self.cizgi_rengi, width=1.5),  # Daha kalın ve belirgin çizgi
            name=self.sensor_adi
        )

        self.cizgi.setDownsampling(ds=False, auto=False)
        self.cizgi.setClipToView(False)

        # Otomatik limit çizgisi varsa çiz
        if self.limitler and len(self.limitler) >= 2:
            self.limit_cizgilerini_guncelle(self.limitler[0], self.limitler[1])

    def grafik_lod_guncelle(self):
        """
        @brief Ana analiz grafiğinde Zoom/Pan yapıldığında LTTB ile dinamik LOD güncellemesi yapar.
        (Ana penceredeki grafik_lod_guncelle ile 1-e-1 Birebir Aynı)
        """
        if self.ham_x is None or self.ham_y is None:
            return

        x_min, x_max = self.plot_widget.viewRange()[0]
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

    def fare_hareket_etti(self, evt):
        """
        @brief Ana grafikteki gibi hızlı ve pürüzsüz fare takip imleci.
        """
        if QtWidgets.QApplication.mouseButtons() != QtCore.Qt.NoButton:
            return
        if self.df is None or len(self.df) == 0:
            return

        pos = evt[0]
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_noktasi = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            try:
                gercekZaman = int(round(mouse_noktasi.x()))
            except (OverflowError, ValueError):
                return

            satir_idx = gercekZaman - 1
            if satir_idx < 0 or satir_idx >= len(self.df):
                return

            self.vLine.setPos(gercekZaman)
            deger = self.df.iat[satir_idx, self.df.columns.get_loc(self.sensor_adi)]
            self.crosshair_yazi.setHtml(f"<b style='color:{self.cizgi_rengi};'>{self.sensor_adi}</b> : {deger:.2f}")
            self.crosshair_yazi.setPos(gercekZaman, mouse_noktasi.y())

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
        menu.setStyleSheet("""
            QMenu {
                background-color: #252526;
                color: #ffffff;
                border: 1px solid #444444;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
            }
            QMenu::item:selected {
                background-color: #00ffcc;
                color: #000000;
                font-weight: bold;
            }
        """)

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
        elif secilen == act_limit_sil:
            self.limit_cizgilerini_temizle()
        elif secilen == act_png:
            self.png_kaydet()
        elif secilen == act_reset:
            self.plot_widget.plotItem.vb.autoRange(padding=0.02, animate=False)
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
        parent_widget = self.parentWidget()
        if parent_widget and hasattr(parent_widget, 'close'):
            parent_widget.close()
        else:
            self.deleteLater()