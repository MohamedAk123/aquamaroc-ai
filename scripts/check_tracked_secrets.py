"""Garde-fou minimal ; ne remplace pas un scanner de secrets complet."""

import subprocess
from pathlib import PurePosixPath

files = subprocess.check_output(["git", "ls-files", "-z"], text=True).split("\0")
bad = [
    f
    for f in files
    if f
    and (
        (
            PurePosixPath(f).name.startswith(".env")
            and PurePosixPath(f).name not in {".env.example", ".env.prod.example"}
        )
        or PurePosixPath(f).suffix.lower() in {".pem", ".key"}
    )
]
if bad:
    raise SystemExit("Fichiers sensibles versionnés : " + ", ".join(bad))
print("Aucun fichier .env réel ou clé privée versionné")
