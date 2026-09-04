# -*- coding: utf-8 -*-
import codecs

filepath = 'C:/Users/petti/FadecDataVisualization/grafik_class.py'
with codecs.open(filepath, 'r', 'utf-8') as f:
    content = f.read()

old_menu = '''        if secili_sayisi > 1 and getattr(self, 'is_selected', False):
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
            self.kapat()'''

# Actually, the file has the GARBLED text in it because git checkout reverted to the garbled state!!
# Let's just use regex to replace from "if secili_sayisi > 1" up to "self.kapat()"

import re

pattern = re.compile(r'        if secili_sayisi > 1.*?elif secilen == act_kapat:\s*self\.kapat\(\)', re.DOTALL)

new_menu = '''        if secili_sayisi > 1 and getattr(self, 'is_selected', False):
            act_grupla = menu.addAction("🔗 Seçili Grafikleri Grupla (Stack & Sync)")
        if getattr(self, 'grup_id', None) is not None:
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

content = pattern.sub(new_menu, content)

with codecs.open(filepath, 'w', 'utf-8') as f:
    f.write(content)

print('Menu fixed!')
