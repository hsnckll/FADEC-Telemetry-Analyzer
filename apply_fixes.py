# -*- coding: utf-8 -*-
import codecs

filepath = 'C:/Users/petti/FadecDataVisualization/grafik_class.py'
with codecs.open(filepath, 'r', 'utf-8') as f:
    content = f.read()

# 1. rateLimit
content = content.replace('rateLimit=120', 'rateLimit=60')

# 2. odak_bolgesi = None in __init__
content = content.replace(
    'self.grup_id = None',
    'self.grup_id = None\n        self.odak_bolgesi = None'
)

# 3. crosshair methods
old_crosshair = '''    def crosshair_gizle(self):
        \"\"\" Crosshair imlecini kapatır. \"\"\"
        if hasattr(self, 'vLine') and self.vLine.isVisible():
            self.vLine.hide()
        if hasattr(self, 'hLine') and self.hLine.isVisible():
            self.hLine.hide()
        if hasattr(self, 'crosshair_yazi') and self.crosshair_yazi.isVisible():
            self.crosshair_yazi.hide()

    def crosshair_guncelle(self, mx, my, gercekZaman, is_scatter=False, from_group=False):
        \"\"\" Verilen koordinatlara göre Crosshair'i günceller. HTML render cache optimizasyonu kullanır. \"\"\"
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
            self.crosshair_yazi.setPos(gercekZaman, y_pos)'''

new_crosshair = '''    def crosshair_gizle(self):
        \"\"\" Crosshair imlecini kapatır. \"\"\"
        if hasattr(self, 'vLine') and self.vLine.isVisible():
            self.vLine.hide()
        if hasattr(self, 'hLine') and self.hLine.isVisible():
            self.hLine.hide()
        if hasattr(self, 'crosshair_yazi') and self.crosshair_yazi.isVisible():
            self.crosshair_yazi.hide()
            
        # Cache'i sıfırla ki tekrar grafiğe girdiğinde render etsin
        self._son_guncel_x = None
        self._son_guncel_idx = None
        self._son_grup_zaman = None
        self._son_vline_pos = None

    def crosshair_guncelle(self, mx, my, gercekZaman, is_scatter=False, from_group=False):
        \"\"\" 
        Verilen koordinatlara göre Crosshair'i günceller.
        from_group=True ise sadece dikey çizgi hareket eder, metin gizlenir (Ultra Performans).
        \"\"\"
        if from_group:
            if getattr(self, '_son_grup_zaman', None) == gercekZaman:
                return
            self._son_grup_zaman = gercekZaman

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
                
            if hasattr(self, 'vLine'): self.vLine.setPos(best_x)
            if hasattr(self, 'hLine'): self.hLine.setPos(best_y)
            
            if from_group:
                if hasattr(self, 'crosshair_yazi') and self.crosshair_yazi.isVisible():
                    self.crosshair_yazi.hide()
            else:
                if hasattr(self, 'crosshair_yazi') and not self.crosshair_yazi.isVisible():
                    self.crosshair_yazi.show()
                    
                if getattr(self, '_son_guncel_idx', None) != min_idx:
                    self._son_guncel_idx = min_idx
                    self.crosshair_yazi.setColor(QtGui.QColor(self.cizgi_rengi))
                    self.crosshair_yazi.setText(f"X: {best_x:.2f}\\nY: {best_y:.2f}")
                self.crosshair_yazi.setPos(best_x, best_y)
        else:
            satir_idx = gercekZaman - 1
            if satir_idx < 0 or satir_idx >= len(self.ham_y):
                self.crosshair_gizle()
                return

            if hasattr(self, 'vLine'):
                if not self.vLine.isVisible():
                    self.vLine.show()
                if getattr(self, '_son_vline_pos', None) != gercekZaman:
                    self.vLine.setPos(gercekZaman)
                    self._son_vline_pos = gercekZaman

            if from_group:
                if hasattr(self, 'crosshair_yazi') and self.crosshair_yazi.isVisible():
                    self.crosshair_yazi.hide()
            else:
                if hasattr(self, 'crosshair_yazi'):
                    if not self.crosshair_yazi.isVisible():
                        self.crosshair_yazi.show()

                    deger = self.ham_y[satir_idx]
                    
                    if getattr(self, '_son_guncel_x', None) != gercekZaman:
                        self._son_guncel_x = gercekZaman
                        self.crosshair_yazi.setColor(QtGui.QColor(self.cizgi_rengi))
                        self.crosshair_yazi.setText(f"{self.sensor_adi} : {deger:.2f}")
                    
                    self.crosshair_yazi.setPos(gercekZaman, my)'''

content = content.replace(old_crosshair, new_crosshair)

# 4. menu_ac options
old_menu = '''        if getattr(self, 'grup_id', None) is not None:
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
            self.kapat()'''

new_menu = '''        if getattr(self, 'grup_id', None) is not None:
            act_grubu_dagit = menu.addAction("✂️ Grubu Dağıt (Unlink)")
            menu.addSeparator()

        odak_aktif = getattr(self, 'odak_bolgesi', None) is not None
        odak_text = "Kapat" if odak_aktif else "Aç"
        if getattr(self, 'grup_id', None) is not None:
            act_odak = menu.addAction(f"🎯 Gruba Odak Bölgesi {odak_text}")
        else:
            act_odak = menu.addAction(f"🎯 Odak Bölgesi {odak_text}")
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
        elif secilen == act_odak:
            self.odak_bolgesi_tetikle(not odak_aktif)
        elif secilen == act_limit_sil:
            self.limit_cizgilerini_temizle()
        elif secilen == act_png:
            self.png_kaydet()
        elif secilen == act_reset:
            self.plot_widget.plotItem.vb.autoRange(padding=0.02)
        elif secilen == act_kapat:
            self.kapat()'''
            
content = content.replace(old_menu, new_menu)

# 5. Add focus methods at the bottom
focus_methods = '''
    # ==========================================================================
    # 🎯 ODAK BÖLGESİ (REGION OF INTEREST - ROI) YÖNETİMİ
    # ==========================================================================
    def odak_bolgesi_tetikle(self, aktif):
        """ Grup varsa hepsine, yoksa sadece kendine odak bölgesi (LinearRegionItem) uygular """
        if getattr(self, 'grup_id', None) is not None:
            tuval = self.parent()
            grup = [c for c in tuval.findChildren(SensorGrafikKarti) if getattr(c, 'grup_id', None) == self.grup_id]
            
            ortak_x_min = 0
            ortak_x_max = 100
            if aktif and self.ham_y is not None and len(self.ham_y) > 0:
                toplam = len(self.ham_y)
                ortak_x_min = int(toplam * 0.4)
                ortak_x_max = int(toplam * 0.6)
                
            for peer in grup:
                peer.odak_bolgesi_ayarla(aktif, ortak_x_min, ortak_x_max)
        else:
            x_min, x_max = 0, 100
            if aktif and self.ham_y is not None and len(self.ham_y) > 0:
                toplam = len(self.ham_y)
                x_min = int(toplam * 0.4)
                x_max = int(toplam * 0.6)
            self.odak_bolgesi_ayarla(aktif, x_min, x_max)

    def odak_bolgesi_ayarla(self, aktif, x_min=0, x_max=100):
        if aktif:
            if getattr(self, 'odak_bolgesi', None) is None:
                self.odak_bolgesi = pg.LinearRegionItem([x_min, x_max])
                self.odak_bolgesi.setBrush(pg.mkBrush(0, 255, 204, 30))
                self.odak_bolgesi.setHoverBrush(pg.mkBrush(0, 255, 204, 70))
                
                # Sınır çizgilerini turkuaz yap
                for kenarCizgisi in self.odak_bolgesi.lines:
                    kenarCizgisi.setPen(pg.mkPen('#00ffcc', width=1.5))
                    
                self.plot_widget.addItem(self.odak_bolgesi)
                self.odak_bolgesi.sigRegionChanged.connect(self.odak_degisti_senkronize_et)
        else:
            if getattr(self, 'odak_bolgesi', None) is not None:
                self.plot_widget.removeItem(self.odak_bolgesi)
                self.odak_bolgesi = None

    def odak_degisti_senkronize_et(self, region_item):
        if getattr(self, '_odak_guncelleniyor', False):
            return
            
        yeni_sinirlar = region_item.getRegion()
        
        if getattr(self, 'grup_id', None) is not None:
            if hasattr(self, '_grup_cache') and getattr(self, '_grup_cache_id', None) == self.grup_id:
                grup = self._grup_cache
            else:
                tuval = self.parent()
                grup = [c for c in tuval.findChildren(SensorGrafikKarti) if getattr(c, 'grup_id', None) == self.grup_id]
                self._grup_cache = grup
                self._grup_cache_id = self.grup_id
                
            for peer in grup:
                if peer != self and getattr(peer, 'odak_bolgesi', None) is not None:
                    peer._odak_guncelleniyor = True
                    peer.odak_bolgesi.setRegion(yeni_sinirlar)
                    peer._odak_guncelleniyor = False
'''

if 'odak_bolgesi_tetikle' not in content:
    content += focus_methods

with codecs.open(filepath, 'w', 'utf-8') as f:
    f.write(content)

print('File updated successfully.')
