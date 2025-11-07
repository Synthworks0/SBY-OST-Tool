# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

app_datas = [
    ('../../../qml/main.qml', 'qml'),
    ('../../../qml/MainContent.qml', 'qml'),
    ('../../../qml/components', 'qml/components'),
    ('../../../resources', 'resources'),
    ('../../../runtime_config.json', '.'),
]

hidden_imports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtQml',
    'PySide6.QtQuick',
    'PySide6.QtQuickControls2',
    'PySide6.QtQuickLayouts',
    'PySide6.QtQuickTemplates2',
    'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets',
    'PySide6.QtGraphicalEffects',
    'PySide6.QtOpenGL',
]

a = Analysis(
    ['../../../main.py'],
    pathex=['.'],
    binaries=[],
    datas=app_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SBY_OST_Tool_Remote',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Get the directory where this spec file is located
spec_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
icon_path = os.path.join(spec_root, 'icon.icns')
icon_file = icon_path if os.path.exists(icon_path) else None
if not icon_file:
    print(f"Warning: icon.icns not found at {icon_path}. App will not have a custom icon.")

app = BUNDLE(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='SBY_OST_Tool_Remote.app',
    icon=icon_file,
    bundle_identifier='com.synthworks.sbyosttool.remote',
    info_plist={
        'CFBundleShortVersionString': '3.0.0',
        'CFBundleVersion': '3',
        'CFBundleGetInfoString': 'SBY OST Tool (Streaming)',
        'NSHighResolutionCapable': 'True',
        'NSRequiresAquaSystemAppearance': 'False',
        'LSApplicationCategoryType': 'public.app-category.utilities',
        'LSMinimumSystemVersion': '10.15',
    },
    append_pkg=False
)
