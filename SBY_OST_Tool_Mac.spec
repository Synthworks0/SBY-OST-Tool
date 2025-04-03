# -*- mode: python ; coding: utf-8 -*-

import os

# Function to check for datas existence and handle case sensitivity
def get_datas():
    datas_list = []
    # Check Components/components
    components_dir = 'Components'
    if not os.path.exists(components_dir) and os.path.exists('components'):
        components_dir = 'components'
    if os.path.exists(components_dir):
        datas_list.append((components_dir, components_dir)) # Keep relative path in bundle
    else:
         print(f"Warning: '{components_dir}' or 'components' directory not found.")

    # Check resources/Resources
    resources_dir = 'resources'
    if not os.path.exists(resources_dir) and os.path.exists('Resources'):
        resources_dir = 'Resources'
    if os.path.exists(resources_dir):
        datas_list.append((resources_dir, resources_dir)) # Keep relative path in bundle
    else:
         print(f"Warning: '{resources_dir}' or 'Resources' directory not found.")

    # Add QML files if they exist
    if os.path.exists('main.qml'):
        datas_list.append(('main.qml', '.'))
    else:
        print("Warning: 'main.qml' not found.")
    if os.path.exists('MainContent.qml'):
        datas_list.append(('MainContent.qml', '.'))
    else:
        print("Warning: 'MainContent.qml' not found.")

    # We only need icon.ico temporarily for conversion, not in the final datas
    # if os.path.exists('icon.ico'):
    #     datas_list.append(('icon.ico', '.')) # Removed - icon handled separately

    return datas_list

app_datas = get_datas()

a = Analysis(
    ['rename.py'],
    pathex=[],
    binaries=[], # Keep binaries empty unless you have specific non-python libs to force include
    datas=app_datas, # Use the dynamically generated list
    hiddenimports=['PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtMultimedia'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    # Binaries and datas are handled by the BUNDLE on macOS
    [], # Keep binaries list empty here
    exclude_binaries=True, # Exclude binaries automatically found by Analysis from EXE
    name='SBY_OST_Tool', # Base executable name
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False, # Setting UPX to False - often problematic with macOS signing/universal
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch='universal2', # Target universal binary
    codesign_identity=None,
    entitlements_file=None,
)

# Use icon.icns if available (created by the workflow)
icon_file = 'icon.icns' if os.path.exists('icon.icns') else None
if not icon_file:
    print("Warning: icon.icns not found. App will not have a custom icon.")

app = BUNDLE(
    exe,
    # a.binaries, # Let PyInstaller handle system/Qt binaries unless needed
    # a.datas,    # Use the result from Analysis datas=app_datas
    name='SBY_OST_Tool.app', # The final .app name
    icon=icon_file,
    bundle_identifier='com.synthworks.sbyosttool',
    info_plist={
        'CFBundleShortVersionString': '1.0.0', # Consider updating this version automatically
        'CFBundleVersion': '1', # Build number
        'CFBundleGetInfoString': 'SBY OST Tool',
        'NSHighResolutionCapable': 'True',
        'NSRequiresAquaSystemAppearance': 'False', # Allows dark/light mode switching
        'LSApplicationCategoryType': 'public.app-category.utilities',
        'LSMinimumSystemVersion': '10.15', # Set minimum required macOS
    },
    #  Explicitly include collected binaries & datas in BUNDLE
    # This ensures frameworks and data files are placed correctly within the .app structure
    bundle_files = a.binaries + a.datas,
)
