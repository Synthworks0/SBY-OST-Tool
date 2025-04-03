    # -*- mode: python ; coding: utf-8 -*-

    import os

    a = Analysis(
        ['rename.py'],
        pathex=[],
        binaries=[],
        datas=[('main.qml', '.'), ('MainContent.qml', '.'), ('Components', 'Components'), ('resources', 'resources'), ('icon.ico', '.')],
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
        [],
        exclude_binaries=True,
        name='SBY_OST_Tool',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True, # Note: UPX might cause issues with universal/signed binaries, consider removing if problems arise
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=True,
        target_arch='universal2', # <-- Add this line
        codesign_identity=None,
        entitlements_file=None,
    )

    # Use icon.icns if available
    icon_file = 'icon.icns' if os.path.exists('icon.icns') else None

    app = BUNDLE(
        exe,
        a.binaries,
        a.datas,
        name='SBY_OST_Tool.app',
        icon=icon_file,
        bundle_identifier='com.synthworks.sbyosttool',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleGetInfoString': 'SBY OST Tool',
            'NSHighResolutionCapable': 'True',
            'NSRequiresAquaSystemAppearance': 'False',
            'LSApplicationCategoryType': 'public.app-category.utilities',
            'LSMinimumSystemVersion': '10.15',
        },
    )
