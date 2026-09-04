# -*- coding: utf-8 -*-
import codecs

filepath = 'C:/Users/petti/FadecDataVisualization/grafik_class.py'
with codecs.open(filepath, 'r', 'utf-8') as f:
    content = f.read()

bad_str = 'self.crosshair_yazi.setText(f"X: {best_x:.2f}\\r\\nY: {best_y:.2f}")'
bad_str2 = 'self.crosshair_yazi.setText(f"X: {best_x:.2f}\\nY: {best_y:.2f}")'

if bad_str in content:
    content = content.replace(bad_str, 'self.crosshair_yazi.setText(f"X: {best_x:.2f}\\\\nY: {best_y:.2f}")')
if bad_str2 in content:
    content = content.replace(bad_str2, 'self.crosshair_yazi.setText(f"X: {best_x:.2f}\\\\nY: {best_y:.2f}")')

with codecs.open(filepath, 'w', 'utf-8') as f:
    f.write(content)

print('Fixed newline issue.')
