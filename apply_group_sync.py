# -*- coding: utf-8 -*-
import codecs
import re

filepath = 'C:/Users/petti/FadecDataVisualization/grafik_class.py'
with codecs.open(filepath, 'r', 'utf-8') as f:
    content = f.read()

# Replace the event execution block in menu_ac
old_block_pattern = re.compile(r'        if secilen == act_limit_uygula:.*?self\.kapat\(\)', re.DOTALL)

new_block = '''        def grup_aksiyonu(func):
            if getattr(self, 'grup_id', None) is not None:
                grup = [c for c in tuval.findChildren(SensorGrafikKarti) if getattr(c, 'grup_id', None) == self.grup_id]
                for kart in grup:
                    func(kart)
            else:
                func(self)

        if secilen == act_limit_uygula:
            grup_aksiyonu(lambda k: k.limitleri_uygula())
        elif act_grupla and secilen == act_grupla:
            tuval.grafikleri_grupla()
        elif act_grubu_dagit and secilen == act_grubu_dagit:
            tuval.grubu_dagit(self.grup_id)
        elif secilen == act_odak:
            self.odak_bolgesi_tetikle(not odak_aktif)
        elif secilen == act_limit_sil:
            grup_aksiyonu(lambda k: k.limit_cizgilerini_temizle())
        elif secilen == act_png:
            self.png_kaydet()  # PNG kaydetme sadece tıklanan grafik için mantıklıdır (çoklu diyalog açmamak için)
        elif secilen == act_reset:
            grup_aksiyonu(lambda k: k.plot_widget.plotItem.vb.autoRange(padding=0.02))
        elif secilen == act_kapat:
            grup_aksiyonu(lambda k: k.kapat())'''

content = old_block_pattern.sub(new_block, content)

with codecs.open(filepath, 'w', 'utf-8') as f:
    f.write(content)

print('Group actions synced successfully.')
