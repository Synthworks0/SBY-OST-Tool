# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['rename.py'],
    pathex=['.'],
    binaries=[],
    datas=[('main.qml', '.'), ('MainContent.qml', '.'), ('Components', 'Components'), ('resources', 'resources'), ('icon.ico', '.')],
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
    [],
    exclude_binaries=True,
    name='SBY_OST_Tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Use icon.icns if available, otherwise use icon.ico
import os
from PyInstaller.utils.hooks import Tree

icon_file = 'icon.icns' if os.path.exists('icon.icns') else None

app = BUNDLE(
    exe,
    [],
    name='SBY_OST_Tool.app',
    icon=icon_file,
    bundle_identifier='com.synthworks.sbyosttool',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1',
        'CFBundleGetInfoString': 'SBY OST Tool',
        'NSHighResolutionCapable': 'True',
        'NSRequiresAquaSystemAppearance': 'False',
        'LSApplicationCategoryType': 'public.app-category.utilities',
        'LSMinimumSystemVersion': '10.15'
    },
    bundle_files=a.binaries + a.datas,
)

# In the get_datas function, replace the components directory block with:
components_dir = 'Components'
if not os.path.isdir(components_dir) and os.path.isdir('components'):
    components_dir = 'components'
if os.path.isdir(components_dir):
    datas_list += Tree(components_dir, prefix=components_dir).toc
else:
    print(f"Warning: '{components_dir}' or 'components' directory not found.")

# Similarly, replace the resources directory block with:
resources_dir = 'resources'
if not os.path.isdir(resources_dir) and os.path.isdir('Resources'):
    resources_dir = 'Resources'
if os.path.isdir(resources_dir):
    datas_list += Tree(resources_dir, prefix=resources_dir).toc
else:
    print(f"Warning: '{resources_dir}' or 'Resources' directory not found.")
