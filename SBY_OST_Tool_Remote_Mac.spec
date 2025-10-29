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
components_dir = 'components' if os.path.exists('components') else 'Components'
if os.path.exists(components_dir):
    app_datas.extend(collect_directory_to_resources(components_dir, 'components'))
else:
    print("Warning: components directory not found.")

if os.path.exists('resources'):
    app_datas.extend(collect_directory_to_resources('resources', 'resources'))
else:
    print("Warning: resources directory not found.")

if os.path.exists('main.qml'):
    app_datas.append(('main.qml', '.'))
else:
    print("Warning: main.qml not found.")
if os.path.exists('MainContent.qml'):
    app_datas.append(('MainContent.qml', '.'))
else:
    print("Warning: MainContent.qml not found.")

if os.path.exists('icon.ico'):
    app_datas.append(('icon.ico', '.'))

if os.path.exists('runtime_config.json'):
    app_datas.append(('runtime_config.json', '.'))


hidden_imports = [
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

# CRITICAL FIX: Remove PySide6 data files from Resources
# PyInstaller hooks auto-collect PySide6 data to a.datas (goes to Resources)
# But binaries already go to Frameworks via a.binaries
# Having PySide6 in BOTH locations causes crashes and "damaged app" errors
a.datas = [x for x in a.datas if not x[0].startswith('PySide6/')]
print(f"Filtered out PySide6 data files from Resources to prevent duplication")

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
icon_file = 'icon.icns' if os.path.exists('icon.icns') else None
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
