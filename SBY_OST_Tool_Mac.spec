# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import get_package_paths

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

# Components -> Contents/Resources/components
components_dir = 'components' if os.path.exists('components') else 'Components'
if os.path.exists(components_dir):
    app_datas.extend(collect_directory_to_resources(components_dir, 'components'))
else:
    print("Warning: components directory not found.")

# Resources -> Contents/Resources/resources
if os.path.exists('resources'):
    app_datas.extend(collect_directory_to_resources('resources', 'resources'))
else:
    print("Warning: resources directory not found.")

soundtrack_dir = os.path.join('soundtrack_tool', 'assets', 'SBY Soundtracks')
if os.path.exists(soundtrack_dir):
    app_datas.extend(collect_directory_to_resources(soundtrack_dir, 'soundtrack_tool/assets/SBY Soundtracks'))
else:
    print('Warning: soundtrack library not found.')
# QML at top-level (PyInstaller will place in Contents/Resources)
if os.path.exists('main.qml'):
    app_datas.append(('main.qml', '.'))
else:
    print("Warning: main.qml not found.")
if os.path.exists('MainContent.qml'):
    app_datas.append(('MainContent.qml', '.'))
else:
    print("Warning: MainContent.qml not found.")

# Icons used at runtime
if os.path.exists('icon.ico'):
    app_datas.append(('icon.ico', '.'))

if os.path.exists('runtime_config.json'):
    app_datas.append(('runtime_config.json', '.'))

# Force-bundle Qt Multimedia FFmpeg backend plugin and its FFmpeg runtime libraries
try:
    pyside6_pkg_dir = get_package_paths('PySide6')[1]
    qt_plugins_root = os.path.join(pyside6_pkg_dir, 'Qt', 'plugins')
    multimedia_plugin_dir = os.path.join(qt_plugins_root, 'multimedia')
    if os.path.isdir(multimedia_plugin_dir):
        for name in os.listdir(multimedia_plugin_dir):
            # Keep only ffmpeg and AVFoundation backends to reduce size
            if name.endswith('.dylib') and ('ffmpeg' in name or 'darwin' in name or 'avfoundation' in name):
                src = os.path.join(multimedia_plugin_dir, name)
                dest = os.path.join('PySide6', 'Qt', 'plugins', 'multimedia')
                app_datas.append((src, dest))
                print(f"Bundling Qt multimedia plugin: {name}")
    else:
        print("Warning: Qt multimedia plugin directory not found; relying on PyInstaller hooks.")

    # Ensure platform plugins (esp. libqcocoa.dylib) are bundled
    platforms_plugin_dir = os.path.join(qt_plugins_root, 'platforms')
    if os.path.isdir(platforms_plugin_dir):
        for name in os.listdir(platforms_plugin_dir):
            if name.endswith('.dylib'):
                src = os.path.join(platforms_plugin_dir, name)
                dest = os.path.join('PySide6', 'Qt', 'plugins', 'platforms')
                app_datas.append((src, dest))
                print(f"Bundling Qt platform plugin: {name}")
    else:
        print("Warning: Qt platforms plugin directory not found; relying on PyInstaller hooks.")

    # Imageformats plugins - limit to PNG and JPEG
    imageformats_dir = os.path.join(qt_plugins_root, 'imageformats')
    if os.path.isdir(imageformats_dir):
        for name in os.listdir(imageformats_dir):
            if name in ('libqpng.dylib', 'libqjpeg.dylib'):
                src = os.path.join(imageformats_dir, name)
                dest = os.path.join('PySide6', 'Qt', 'plugins', 'imageformats')
                app_datas.append((src, dest))
                print(f"Bundling Qt imageformats plugin: {name}")
    else:
        print("Warning: Qt imageformats plugin directory not found; relying on PyInstaller hooks.")

    # Add FFmpeg libs that the plugin depends on; place under PySide6/Qt/lib so @rpath resolves via ../../lib
    qt_lib_root = os.path.join(pyside6_pkg_dir, 'Qt', 'lib')
    if os.path.isdir(qt_lib_root):
        needed_prefixes = (
            'libav', 'libsw',  # FFmpeg core libs
            'libz', 'libbz2', 'liblzma', 'libzstd',  # common compression deps
            'libiconv', 'libcharset',  # text/locale deps
        )
        for name in os.listdir(qt_lib_root):
            if name.endswith('.dylib') and name.startswith(needed_prefixes):
                src = os.path.join(qt_lib_root, name)
                dest = os.path.join('PySide6', 'Qt', 'lib')
                app_datas.append((src, dest))
                print(f"Bundling runtime library: {name}")

    # Bundle required QML modules used by the app (limit set)
    qml_root = os.path.join(pyside6_pkg_dir, 'Qt', 'qml')
    def collect_qml_module(module_name):
        module_dir = os.path.join(qml_root, module_name)
        if os.path.isdir(module_dir):
            for root, _, files in os.walk(module_dir):
                for f in files:
                    src = os.path.join(root, f)
                    rel = os.path.relpath(root, qml_root)
                    dest = os.path.join('PySide6', 'Qt', 'qml', rel)
                    app_datas.append((src, dest))
            print(f"Bundling QML module: {module_name}")
        else:
            print(f"Warning: QML module not found: {module_name}")

    # Modules referenced in QML (minimal set)
    collect_qml_module('Qt5Compat/GraphicalEffects')
    collect_qml_module('QtMultimedia')
    collect_qml_module('QtQuick/Controls')
    collect_qml_module('QtQuick/Controls/Material')
    collect_qml_module('QtQuick/Layouts')
    collect_qml_module('QtQuick/Window')
except Exception as e:
    print(f"Warning: failed to force-bundle Qt multimedia ffmpeg plugin/libs: {e}")

a = Analysis(
    ['rename.py'],
    pathex=['.'],
    binaries=[],
    datas=app_datas,
    hiddenimports=[
        'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtMultimedia',
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
icon_file = 'icon.icns' if os.path.exists('icon.icns') else None
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