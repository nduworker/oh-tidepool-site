"""Regenerate the landing page's static QR codes: python3 scripts/make-qr.py (needs `pip install segno`)."""
import segno

CODES = {
    "assets/qr-app-store.svg": "https://apps.apple.com/app/id6813742028",
}

for path, url in CODES.items():
    segno.make(url, error="m", micro=False).save(path, scale=8, border=4, dark="#113d4b", light="#ffffff", xmldecl=False, svgns=True)
    print(path, url)
