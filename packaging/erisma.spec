# PyInstaller spec — builds dist/Erisma/Erisma.exe (one folder, no console)
# pyinstaller packaging/erisma.spec --noconfirm
import os
from PyInstaller.utils.hooks import collect_submodules

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
datas = [(os.path.join(ROOT, "erisma", "web", "static"), os.path.join("erisma", "web", "static")),
         (os.path.join(ROOT, "erisma", "data"), os.path.join("erisma", "data"))]
hidden = collect_submodules("erisma") + collect_submodules("uvicorn")

a = Analysis([os.path.join(SPECPATH, "launcher.py")], pathex=[ROOT], datas=datas, hiddenimports=hidden, noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Erisma", console=False,
          icon="erisma.ico" if __import__("os").path.exists("erisma.ico") else None)
coll = COLLECT(exe, a.binaries, a.datas, name="Erisma")
