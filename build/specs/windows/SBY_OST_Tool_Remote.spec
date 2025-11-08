# -*- mode: python ; coding: utf-8 -*-

import os
def existing(path): return os.path.exists(path)

common_datas = [
    ('../../../qml/main.qml', 'qml'),
    ('../../../qml/MainContent.qml', 'qml'),
    ('../../../qml/components', 'qml/components'),
    ('../../../resources/icons', 'resources/icons'),
    ('../../../runtime_config.json', '.'),
]

hidden_imports = [
    'PySide6.QtQml',
    'PySide6.QtQuick',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtMultimedia',
]

a = Analysis(
    ['../../../main.py'],
    pathex=[],
    binaries=[],
    datas=common_datas + [('../../../icon.ico', '.')],
    hiddenimports=hidden_imports,
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
    name='SBY OST Tool Remote',
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
    icon='../../../icon.ico',
    uac_admin=False,
    uac_uiaccess=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SBY OST Tool Remote',
)
