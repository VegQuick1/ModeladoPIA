from pathlib import Path
import importlib.util
import sys


project_dir = Path(SPECPATH)

hidden_imports = [
    "PIL._tkinter_finder",
]

customtkinter_spec = importlib.util.find_spec("customtkinter")
added_files = []
if customtkinter_spec and customtkinter_spec.submodule_search_locations:
    customtkinter_dir = Path(next(iter(customtkinter_spec.submodule_search_locations)))
    added_files.append((str(customtkinter_dir / "assets"), "customtkinter/assets"))

assets_dir = project_dir / "assets"
if assets_dir.is_dir():
    added_files.append((str(assets_dir), "assets"))

analysis = Analysis(
    [str(project_dir / "main.py")],
    pathex=[str(project_dir)],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="Expediente Montecarlo",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Expediente Montecarlo",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Expediente Montecarlo.app",
        bundle_identifier="com.vegquick.expediente-montecarlo",
        info_plist={
            "CFBundleName": "Expediente Montecarlo",
            "CFBundleDisplayName": "Expediente Montecarlo",
            "CFBundleShortVersionString": "1.0",
            "NSHighResolutionCapable": True,
        },
    )