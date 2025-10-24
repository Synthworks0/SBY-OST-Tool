# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import get_package_paths

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
app_binaries = []
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

try:
    pyside6_pkg_dir = get_package_paths('PySide6')[1]
    qt_plugins_root = os.path.join(pyside6_pkg_dir, 'Qt', 'plugins')
    multimedia_plugin_dir = os.path.join(qt_plugins_root, 'multimedia')
    if os.path.isdir(multimedia_plugin_dir):
        for name in os.listdir(multimedia_plugin_dir):
            if name.endswith('.dylib') and ('ffmpeg' in name or 'darwin' in name or 'avfoundation' in name):
                src = os.path.join(multimedia_plugin_dir, name)
                dest = os.path.join('PySide6', 'Qt', 'plugins', 'multimedia')
                app_binaries.append((src, dest))
except Exception as exc:
    print(f"Warning: unable to collect multimedia plugins: {exc}")

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
    binaries=app_binaries,
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
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='SBY_OST_Tool_Remote',
)

# Create the .app bundle
icon_file = 'icon.icns' if os.path.exists('icon.icns') else None
app = BUNDLE(
    coll,
    name='SBY_OST_Tool_Remote.app',
    icon=icon_file,
    bundle_identifier='com.synthworks.sbyosttool.remote',
    info_plist={
        'CFBundleExecutable': 'SBY_OST_Tool_Remote',
        'CFBundleName': 'SBY OST Tool',
        'CFBundleShortVersionString': '3.0.0',
        'CFBundleVersion': '3',
        'CFBundleGetInfoString': 'SBY OST Tool (Streaming)',
        'NSHighResolutionCapable': 'True',
        'NSRequiresAquaSystemAppearance': 'False',
        'LSApplicationCategoryType': 'public.app-category.utilities',
        'LSMinimumSystemVersion': '10.15',
    },
)
