# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['IRis-Lens.py'],
             pathex=['C:\\Users\\RaphaelHorvath\\Documents\\GitHub\\python_scripts\\common_libraries'],
             binaries=[],
             datas=[('Logo.png', '.'), ('Logo_IR.png', '.')],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='IRis-Lens',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None , icon='C:\\Users\\RaphaelHorvath\\Documents\\GitHub\\python_scripts\\common_libraries\\heterodyne_postprocessing\\utilities\\Logo_IR.ico')
