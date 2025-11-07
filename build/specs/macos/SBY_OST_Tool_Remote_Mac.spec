# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

def collect_directory_to_resources(dir_path, bundle_subdir):
    collected = []
    if not os.path.exists(dir_path):
        return collected
    for root, _, files in os.walk(dir_path):
        for file in files:
            src = os.path.join(root, file)
            rel = os.path.relpath(root, dir_path)
            dest = os.path.join(bundle_subdir, rel)
            collected.append((src, dest))
    return collected

app_datas = []
components_dir = '../../../qml/components' if os.path.exists('../../../qml/components') else '../../../qml/Components'
if os.path.exists(components_dir):
    app_datas.extend(collect_directory_to_resources(components_dir, 'qml/components'))
else:
    print("Warning: components directory not found.")

if os.path.exists('../../../resources'):
    app_datas.extend(collect_directory_to_resources('../../../resources', 'resources'))
else:
    print("Warning: resources directory not found.")

if os.path.exists('../../../qml/main.qml'):
    app_datas.append(('../../../qml/main.qml', 'qml'))
else:
    print("Warning: main.qml not found.")
if os.path.exists('../../../qml/MainContent.qml'):
    app_datas.append(('../../../qml/MainContent.qml', 'qml'))
else:
    print("Warning: MainContent.qml not found.")

if os.path.exists('../../../build/icons/icon.ico'):
    app_datas.append(('../../../build/icons/icon.ico', '.'))

app_datas.append(('../../../runtime_config.json', '.'))


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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
icon_file = '../../../icon.icns' if os.path.exists('../../../icon.icns') else None
if not icon_file:
    print("Warning: icon.icns not found. App will not have a custom icon.")

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
