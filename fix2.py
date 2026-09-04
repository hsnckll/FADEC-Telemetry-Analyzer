import codecs
import re

filepath = 'C:/Users/petti/FadecDataVisualization/grafik_class.py'
with codecs.open(filepath, 'r', 'utf-8') as f:
    content = f.read()

content = re.sub(r'self\.crosshair_yazi\.setText\(f\"X: \{best_x:\.2f\}\r?\nY: \{best_y:\.2f\}\"\)', 'self.crosshair_yazi.setText(f\"X: {best_x:.2f}\\\\nY: {best_y:.2f}\")', content)

with codecs.open(filepath, 'w', 'utf-8') as f:
    f.write(content)
print('Done.')
