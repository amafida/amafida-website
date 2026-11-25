#!/usr/bin/env python3
"""Aktualitäts-Check für amafida.de

Prüft, ob Zahlen, Jahreszahlen und saisonale Inhalte auf der Website noch stimmen.

    python3 .github/scripts/aktualitaet.py          # nur prüfen
    python3 .github/scripts/aktualitaet.py --fix    # Zahlen und ©-Jahr selbst korrigieren, Rest melden

Quelle der Wahrheit ist der Katalog /scoledo/materialien/. Daraus werden gezählt:
    neu, pakete, kunst, gratis, sachunterricht (inkl. Demokratie und KI),
    werkstaetten, kunststunden, alle (ohne den Abschnitt „Neu“)

Geprüft wird:
  Fehler   – Zahlen in <span data-zaehle="…">, die nicht zum Katalog passen   (--fix behebt)
  Fehler   – Abschnittszähler im Katalog, die nicht zur Zahl der Karten passen  (--fix behebt)
  Fehler   – ©-Jahr im Fuß, das nicht dem aktuellen Jahr entspricht             (--fix behebt)
  Fehler   – Inhalte mit data-gueltig-bis="JJJJ-MM-TT", deren Datum vorbei ist
  Fehler   – Neu- und Gratis-Materialien auf /links/, die nicht zum Katalog passen
  Hinweis  – vergangene Jahreszahlen im sichtbaren Text (z. B. „Mein Jahr 2026“ im Jahr 2027)

Für Tests lässt sich das Datum setzen: AKTUALITAET_HEUTE=2027-01-05
"""
import datetime
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KATALOG = ROOT / 'scoledo' / 'materialien' / 'index.html'
LINKS = ROOT / 'links' / 'index.html'
FIX = '--fix' in sys.argv
GH = os.environ.get('GITHUB_ACTIONS') == 'true'
HEUTE = datetime.date.fromisoformat(os.environ['AKTUALITAET_HEUTE']) if os.environ.get('AKTUALITAET_HEUTE') else datetime.date.today()

fehler, hinweise, behoben = [], [], []


def seiten():
    for p in sorted(ROOT.rglob('index.html')):
        rel = p.relative_to(ROOT)
        if rel.parts[0] in ('.git', 'social'):
            continue
        yield p


def rel(p):
    return str(p.relative_to(ROOT))


def sichtbar(src):
    s = re.sub(r'<(style|script)\b.*?</\1>', ' ', src, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = s.replace('&nbsp;', ' ').replace('&amp;', '&')
    return re.sub(r'\s+', ' ', s)


# ---------- Katalog zählen ----------
kat = KATALOG.read_text(encoding='utf-8')
abschnitte = {}  # id -> (gruppe, [(href, art)])
for sid, gruppe, block in re.findall(r'<section class="cat" id="([^"]+)" data-g="([^"]+)"[^>]*>(.*?)</section>', kat, re.S):
    karten = re.findall(r'<a class="item" href="([^"]+)"[^>]*>.*?<span class="im">(.*?)</span>', block, re.S)
    abschnitte[sid] = (gruppe, karten)

if not abschnitte:
    print('Katalog nicht gefunden oder leer:', rel(KATALOG))
    sys.exit(1)

def anzahl_gruppe(g):
    return sum(len(k) for gr, k in abschnitte.values() if gr == g)

kunst = abschnitte.get('kunst', ('', []))[1]
ZAEHLER = {
    'neu': len(abschnitte.get('neu', ('', []))[1]),
    'pakete': anzahl_gruppe('pakete'),
    'kunst': anzahl_gruppe('kunst'),
    'gratis': anzahl_gruppe('gratis'),
    'sachunterricht': anzahl_gruppe('sachunterricht'),
    'werkstaetten': sum(1 for _, art in kunst if art.startswith('Werkstatt')),
    'kunststunden': sum(1 for _, art in kunst if art.startswith('5 Kunststunden')),
}
ZAEHLER['alle'] = sum(len(k) for sid, (g, k) in abschnitte.items() if sid != 'neu')


# ---------- Prüfungen je Seite ----------
for p in seiten():
    src = p.read_text(encoding='utf-8')
    neu_src = src

    # 1) Zahlen im Text
    def zahl(m):
        name, wert = m.group(1), int(m.group(2))
        soll = ZAEHLER.get(name)
        if soll is None:
            fehler.append((p, f'Unbekannter Zähler data-zaehle="{name}" (erlaubt: {", ".join(sorted(ZAEHLER))})'))
            return m.group(0)
        if wert != soll:
            if FIX:
                behoben.append((p, f'{name}: {wert} → {soll}'))
                return f'<span data-zaehle="{name}">{soll}</span>'
            fehler.append((p, f'Zahl „{name}“ steht auf {wert}, im Katalog sind es {soll}'))
        return m.group(0)
    neu_src = re.sub(r'<span data-zaehle="([a-z]+)">(\d+)</span>', zahl, neu_src)

    # 2) Abschnittszähler im Katalog
    if p == KATALOG:
        for sid, (g, karten) in abschnitte.items():
            m = re.search(rf'(<h2 id="h-{sid}">[^<]*<span class="cnt">)(\d+)(</span>)', neu_src)
            if m and int(m.group(2)) != len(karten):
                if FIX:
                    behoben.append((p, f'Abschnitt {sid}: {m.group(2)} → {len(karten)}'))
                    neu_src = neu_src.replace(m.group(0), f'{m.group(1)}{len(karten)}{m.group(3)}')
                else:
                    fehler.append((p, f'Abschnitt „{sid}“ zeigt {m.group(2)}, hat aber {len(karten)} Karten'))

    # 3) ©-Jahr
    def copy(m):
        if int(m.group(1)) != HEUTE.year:
            if FIX:
                behoben.append((p, f'© {m.group(1)} → © {HEUTE.year}'))
                return f'© {HEUTE.year}'
            fehler.append((p, f'Fußzeile zeigt © {m.group(1)}, aktuell ist {HEUTE.year}'))
        return m.group(0)
    neu_src = re.sub(r'©\s*(\d{4})', copy, neu_src)

    # 4) Saisonale Inhalte
    for datum, rest in re.findall(r'data-gueltig-bis="(\d{4}-\d{2}-\d{2})"(.*?)</a>', neu_src, re.S):
        if HEUTE > datetime.date.fromisoformat(datum):
            text = sichtbar('<x ' + rest)[:70].strip()
            fehler.append((p, f'Abgelaufen seit {datum}: „{text}“ austauschen oder Datum verlängern'))

    # 5) Vergangene Jahreszahlen im sichtbaren Text
    text = re.sub(r'©\s*\d{4}', '', sichtbar(neu_src))
    if not rel(p).startswith(('impressum', 'datenschutz')):
        for m in re.finditer(r'\b(20\d{2})\b', text):
            if int(m.group(1)) < HEUTE.year:
                ausschnitt = text[max(0, m.start() - 30):m.end() + 20].strip()
                hinweise.append((p, f'Vergangene Jahreszahl {m.group(1)}: „…{ausschnitt}…“'))

    if FIX and neu_src != src:
        p.write_text(neu_src, encoding='utf-8')


# ---------- /links/ gegen Katalog ----------
if LINKS.exists():
    lsrc = LINKS.read_text(encoding='utf-8')
    for sid in ('neu', 'gratis'):
        m = re.search(rf'<section id="{sid}">(.*?)</section>', lsrc, re.S)
        if not m:
            continue
        auf_links = set(re.findall(r'<a class="card" href="([^"]+)"', m.group(1)))
        im_katalog = {h for h, _ in abschnitte.get(sid, ('', []))[1]}
        for h in sorted(im_katalog - auf_links):
            fehler.append((LINKS, f'„{sid}“: im Katalog, aber nicht auf /links/: {h.split("/")[-1][:60]}'))
        for h in sorted(auf_links - im_katalog):
            fehler.append((LINKS, f'„{sid}“: auf /links/, aber nicht im Katalog: {h.split("/")[-1][:60]}'))


# ---------- Ausgabe ----------
print(f'Aktualitäts-Check amafida.de · Stand {HEUTE.isoformat()}')
print('Katalog: ' + ', '.join(f'{k} {v}' for k, v in ZAEHLER.items()))
for p, msg in behoben:
    print(f'  behoben  {rel(p)}: {msg}')
for p, msg in fehler:
    print(f'::error file={rel(p)}::{msg}' if GH else f'  FEHLER   {rel(p)}: {msg}')
for p, msg in hinweise:
    print(f'::warning file={rel(p)}::{msg}' if GH else f'  Hinweis  {rel(p)}: {msg}')
if not fehler and not hinweise:
    print('Alles aktuell.')
elif not fehler:
    print(f'{len(hinweise)} Hinweis(e), keine Fehler.')
else:
    print(f'{len(fehler)} Fehler, {len(hinweise)} Hinweis(e).' + ('' if FIX else ' Zahlen und ©-Jahr behebt: python3 .github/scripts/aktualitaet.py --fix'))
sys.exit(1 if fehler else 0)
