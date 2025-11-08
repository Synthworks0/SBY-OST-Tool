# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

app_datas = [
    ('../../../qml/main.qml', 'qml'),
    ('../../../qml/MainContent.qml', 'qml'),
    ('../../../qml/components', 'qml/components'),
    ('../../../resources', 'resources'),
    ('../../../soundtrack_tool/assets/SBY Soundtracks', 'soundtrack_tool/assets/SBY Soundtracks'),
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
    name='SBY OST Tool',
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

# Icon file is expected at the project root (use absolute path)
icon_path = os.path.abspath('icon.icns')
icon_file = icon_path if os.path.exists(icon_path) else None
if not icon_file:
    print("Warning: icon.icns not found. App will not have a custom icon.")
else:
    print(f"Using icon file: {icon_file}")

app = BUNDLE(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='SBY OST Tool.app',
    icon=icon_file,
    bundle_identifier='com.synthworks.sbyosttool',
    info_plist={
        'CFBundleShortVersionString': '3.0.0',
        'CFBundleVersion': '3',
        'CFBundleGetInfoString': 'SBY OST Tool',
        'NSHighResolutionCapable': 'True',
        'NSRequiresAquaSystemAppearance': 'False',
        'LSApplicationCategoryType': 'public.app-category.utilities',
        'LSMinimumSystemVersion': '10.15',
        'LSArchitecturePriority': ['x86_64', 'arm64'] if exe.target_arch is None else [exe.target_arch],
        'LSRequiresNativeExecution': True
    },
    append_pkg=False
)
