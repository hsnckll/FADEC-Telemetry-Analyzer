# -*- coding: utf-8 -*-
import codecs

filepath = 'C:/Users/petti/FadecDataVisualization/grafik_class.py'
with codecs.open(filepath, 'r', 'utf-8') as f:
    content = f.read()

content = content.replace('self.crosshair_yazi.setPos(gercekZaman, deger)', 'self.crosshair_yazi.setPos(gercekZaman, my)')

with codecs.open(filepath, 'w', 'utf-8') as f:
    f.write(content)

print('Restored setPos to use my instead of deger.')
