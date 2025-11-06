# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

def collect_directory_to_resources(dir_path, bundle_subdir):
    """Collect files under dir_path for inclusion in Contents/Resources/<bundle_subdir>/...

    NOTE: The dest should be relative to Contents/Resources. Ensure we do not add
    an extra 'Resources' level to avoid double nesting.
    """
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

# Collect data files with case-insensitive fallback
app_datas = []

# Components -> Contents/Resources/qml/components
components_dir = '../../../qml/components' if os.path.exists('../../../qml/components') else '../../../qml/Components'
if os.path.exists(components_dir):
    app_datas.extend(collect_directory_to_resources(components_dir, 'qml/components'))
else:
    print("Warning: components directory not found.")

# Resources -> Contents/Resources/resources
if os.path.exists('../../../resources'):
    app_datas.extend(collect_directory_to_resources('../../../resources', 'resources'))
else:
    print("Warning: resources directory not found.")

soundtrack_dir = os.path.join('../../../soundtrack_tool', 'assets', 'SBY Soundtracks')
if os.path.exists(soundtrack_dir):
    app_datas.extend(collect_directory_to_resources(soundtrack_dir, 'soundtrack_tool/assets/SBY Soundtracks'))
else:
    print('Warning: soundtrack library not found.')
# QML in qml/ subdirectory (PyInstaller will place in Contents/Resources/qml)
if os.path.exists('../../../qml/main.qml'):
    app_datas.append(('../../../qml/main.qml', 'qml'))
else:
    print("Warning: main.qml not found.")
if os.path.exists('../../../qml/MainContent.qml'):
    app_datas.append(('../../../qml/MainContent.qml', 'qml'))
else:
    print("Warning: MainContent.qml not found.")

# Icons used at runtime
if os.path.exists('../../../build/icons/icon.ico'):
    app_datas.append(('../../../build/icons/icon.ico', '.'))

app_datas.append(('../../../runtime_config.json', '.'))

a = Analysis(
    ['../../../main.py'],
    pathex=['.'],
    binaries=[],
    datas=app_datas,
    hiddenimports=[
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
        # Ensure platform/backends get tracked
        'PySide6.QtOpenGL',
    ],
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
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Check for icon.icns
icon_file = '../../../icon.icns' if os.path.exists('../../../icon.icns') else None
if not icon_file:
    print("Warning: icon.icns not found. App will not have a custom icon.")

app = BUNDLE(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
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
        'LSMinimumSystemVersion': '10.15',
        'LSArchitecturePriority': ['x86_64', 'arm64'] if exe.target_arch is None else [exe.target_arch],
        'LSRequiresNativeExecution': True
    },
    append_pkg=False
)