# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('parameters.json', '.'),
        ('Fadec Kullanım Kılavuzu.pdf', '.'),
        ('*.ui', '.'),
        ('*.png', '.')
    ],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtOpenGL',
        'PyQt5.QtPrintSupport',
        'PyQt5.uic',
        'PyQt5.sip',
        'pyqtgraph',
        'pyqtgraph.exporters',
        'pandas',
        'numpy',
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.figure',
        'matplotlib.backends.backend_qt5agg',
        'mpl_toolkits.axes_grid1',
        'generate_pdf',
        'grafik_class',
        'ai',
        'heatmap_penceresi',
        'radar_penceresi',
        'minmax_python',
        'limit_ayarlari_python',
        'dosya_secim_python',
        'arayuz_python'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FADEC_Telemetry_Analyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FADEC_Telemetry_Analyzer',
)
