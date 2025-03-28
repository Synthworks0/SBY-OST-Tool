# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

# Verify if directories exist and adjust case if needed
components_dir = 'Components'
if not os.path.exists(components_dir) and os.path.exists('components'):
    components_dir = 'components'

resources_dir = 'resources'
if not os.path.exists(resources_dir) and os.path.exists('Resources'):
    resources_dir = 'Resources'

# Build the datas list with only existing files
datas = []
for file_or_dir, dest in [
    ('main.qml', '.'), 
    ('MainContent.qml', '.'), 
    (components_dir, components_dir), 
    (resources_dir, resources_dir), 
    ('icon.ico', '.')
]:
    if os.path.exists(file_or_dir):
        datas.append((file_or_dir, dest))
    else:
        print(f"Warning: {file_or_dir} not found, skipping in build")

a = Analysis(
    ['rename.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtMultimedia'],
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
    a.binaries,
    a.datas,
    [],
    name='SBY_OST_Tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)