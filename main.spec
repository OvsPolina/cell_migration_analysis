# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

project_path = Path.cwd()
block_cipher = None

a = Analysis(
    ['main.py'],                               # start point
    pathex=[str(project_path)],                # path to the root of project
    binaries=[],
    datas=[
        ('__init__.py', '.'),
        ('logs', 'logs'),                      
        ('ui', 'ui'),                          
        ('src', 'src'),                        
    ],
    hiddenimports=[],                          
    hookspath=[],                              
    runtime_hooks=[],                          
    excludes=[],                               
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='CellMigrationApp',                  # name
    debug=False,
    strip=False,
    upx=True,
    console=False                             # False — GUI-app, no console
)

app = BUNDLE(
    exe,  # ← передаём его сюда
    name='CellMigrationApp.app',
    bundle_identifier='com.example.cellmigration',
    icon=None,
    info_plist={
        'NSHighResolutionCapable': 'True',
    },
)
