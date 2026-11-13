#!/usr/bin/env python3
"""Stage only public application assets for GitHub Pages."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'_site'
DEST.mkdir(exist_ok=True)
for name in ['index.html','app.js','style.css','sw.js','manifest.webmanifest','icon.svg','icon-192.png','icon-512.png','.nojekyll']:
    shutil.copy2(ROOT/name,DEST/name)
shutil.copytree(ROOT/'fonts',DEST/'fonts',dirs_exist_ok=True)
print(DEST)
