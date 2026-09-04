# -*- coding: utf-8 -*-
import codecs

filepath = 'C:/Users/petti/FadecDataVisualization/grafik_class.py'
with codecs.open(filepath, 'r', 'utf-8') as f:
    content = f.read()

replacements = {
    'ğŸ”— SeÃ§ili Grafikleri Grupla': '🔗 Seçili Grafikleri Grupla',
    'âœ‚ï¸  Grubu DaÄŸÄ±t': '✂️ Grubu Dağıt',
    'ğŸŽ¯ Gruba Odak BÃ¶lgesi': '🎯 Gruba Odak Bölgesi',
    'ğŸŽ¯ Odak BÃ¶lgesi': '🎯 Odak Bölgesi',
    'âš™ï¸  TanÄ±mlÄ± Limitleri GÃ¶ster': '⚙️ Tanımlı Limitleri Göster',
    'â Œ Limit Ã‡izgilerini KaldÄ±r': '❌ Limit Çizgilerini Kaldır',
    'ğŸ“· PNG Olarak Kaydet': '📷 PNG Olarak Kaydet',
    'ğŸ”„ Otomatik Odaklan': '🔄 Otomatik Odaklan',
    'ğŸ—‘ï¸  Bu GrafiÄŸi Kapat': '🗑️ Bu Grafiği Kapat',
    '?? ODAK BÖLGESİ': '🎯 ODAK BÖLGESİ'
}

for bad, good in replacements.items():
    content = content.replace(bad, good)

# Fix the missing odak_text line
if 'odak_text =' not in content:
    old_str = "odak_aktif = getattr(self, 'odak_bolgesi', None) is not None"
    new_str = "odak_aktif = getattr(self, 'odak_bolgesi', None) is not None\n        odak_text = 'Kapat' if odak_aktif else 'Aç'"
    content = content.replace(old_str, new_str)

with codecs.open(filepath, 'w', 'utf-8') as f:
    f.write(content)

print('Fixed encoding issues.')
