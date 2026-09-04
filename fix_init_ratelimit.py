# -*- coding: utf-8 -*-
import codecs
filepath = 'C:/Users/petti/FadecDataVisualization/grafik_class.py'
with codecs.open(filepath, 'r', 'utf-8') as f:
    content = f.read()

if 'rateLimit=120' in content:
    content = content.replace('rateLimit=120', 'rateLimit=60')
    
if 'self.odak_bolgesi = None' not in content:
    content = content.replace('self.grup_id = None', 'self.grup_id = None\n        self.odak_bolgesi = None')

with codecs.open(filepath, 'w', 'utf-8') as f:
    f.write(content)

print('rateLimit and init fixed!')
