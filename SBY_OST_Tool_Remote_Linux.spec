# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

components_dir = 'components' if os.path.exists('components') else 'Components'
resources_dir = 'resources' if os.path.exists('resources') else 'Resources'
icons_dir = os.path.join(resources_dir, 'icons')

def existing(path: str) -> bool:
    return os.path.exists(path)

def include(path: str, dest: str):
    if existing(path):
        return (path, dest)
    print(f"Warning: {path} not found, skipping in build")
    return None

candidate_datas = [
    include('main.qml', '.'),
    include('MainContent.qml', '.'),
    include(components_dir, 'components'),
    include(icons_dir, 'resources/icons'),
    include('icon.ico', '.'),
    include('runtime_config.json', '.'),
]

datas = [entry for entry in candidate_datas if entry]

hiddenimports = [
    'PySide6.QtQml',
    'PySide6.QtQuick',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtMultimedia',
]

a = Analysis(
    ['rename.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if existing('icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SBY_OST_Tool_Remote',
)
