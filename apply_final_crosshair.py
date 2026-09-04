# -*- coding: utf-8 -*-
import codecs
import re

filepath = 'C:/Users/petti/FadecDataVisualization/grafik_class.py'
with codecs.open(filepath, 'r', 'utf-8') as f:
    content = f.read()

pattern = re.compile(r'    def crosshair_gizle\(self\):.*?def fare_hareket_etti\(self, evt\):', re.DOTALL)

new_code = '''    def crosshair_gizle(self):
        """ Crosshair imlecini kapatır. """
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
        """ 
        Verilen koordinatlara göre Crosshair'i günceller.
        from_group=True ise sadece dikey çizgi hareket eder, metin gizlenir (Performans + Temiz Görünüm).
        """
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
                if hasattr(self, 'crosshair_yazi'):
                    if not self.crosshair_yazi.isVisible():
                        self.crosshair_yazi.show()
                    
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
                        yazi_rengi = "#000000" if getattr(self, 'tema', 'dark') == 'light' else "#ffffff"
                        self.crosshair_yazi.setHtml(f"<b style='color:{self.cizgi_rengi};'>{self.sensor_adi}</b> : <b style='color:{yazi_rengi};'>{deger:.2f}</b>")
                    
                    # Kullanıcının isteği: Sadece aktif grafikte görünsün ve veri çizgisinin hizasında (deger) olsun
                    self.crosshair_yazi.setPos(gercekZaman, deger)

    def fare_hareket_etti(self, evt):'''

new_content = pattern.sub(new_code, content)
with codecs.open(filepath, 'w', 'utf-8') as f:
    f.write(new_content)
print('Done!')
