# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

# Function to collect all files from a directory recursively
def collect_directory(dir_path, target_dir):
    collected_data = []
    if os.path.exists(dir_path):
        # Walk through the directory and collect all files
        for root, _, files in os.walk(dir_path):
            for file in files:
                source_path = os.path.join(root, file)
                # Calculate the relative path for the destination
                dest_path = os.path.join(target_dir, os.path.relpath(root, os.path.dirname(dir_path)))
                collected_data.append((source_path, dest_path))
    return collected_data

# Collect data files with case-insensitive fallback
app_datas = []

# Process Components folder
components_dir = 'Components'
if not os.path.exists(components_dir) and os.path.exists('components'):
    components_dir = 'components'
if os.path.exists(components_dir):
    app_datas.extend(collect_directory(components_dir, components_dir))
else:
    print(f"Warning: '{components_dir}' or 'components' directory not found.")

# Process resources folder
resources_dir = 'resources'
if not os.path.exists(resources_dir) and os.path.exists('Resources'):
    resources_dir = 'Resources'
if os.path.exists(resources_dir):
    app_datas.extend(collect_directory(resources_dir, resources_dir))
else:
    print(f"Warning: '{resources_dir}' or 'Resources' directory not found.")

# Add QML files
if os.path.exists('main.qml'):
    app_datas.append(('main.qml', '.'))
else:
    print("Warning: 'main.qml' not found.")
if os.path.exists('MainContent.qml'):
    app_datas.append(('MainContent.qml', '.'))
else:
    print("Warning: 'MainContent.qml' not found.")

# Add icon for later use
if os.path.exists('icon.ico'):
    app_datas.append(('icon.ico', '.'))

a = Analysis(
    ['rename.py'],
    pathex=['.'],
    binaries=[],
    datas=app_datas,
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
    upx=False,  # Disable UPX for macOS
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    codesign_identity=None,
    entitlements_file=None,
)

# Check for icon.icns
icon_file = 'icon.icns' if os.path.exists('icon.icns') else None
if not icon_file:
    print("Warning: icon.icns not found. App will not have a custom icon.")

# Create BUNDLE with proper binary and data file inclusion
app = BUNDLE(
    exe,
    a.binaries,      # Include binaries
    a.zipfiles,      # Include zipfiles
    a.datas,         # Include data files explicitly
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
)
