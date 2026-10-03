"""Klaipeda Robo — KU Robotics Club šriftas (Chakra Petch pagrindu, SIL OFL 1.1).
   Klaipeda Robo:        pirmoji O / o kiekviename žodyje → mūsų akis (raudonas žiedas + antenos).
   Klaipeda Robo Color:  pirmoji — akis; kitos O / o turi antenas paeiliui geltona, mėlyna, žalia.
   Spalvos — pačiame šrifte (COLR/CPAL); be spalvų palaikymo matosi vienspalvis kontūras.
   Tiesiogiai: U+E000 = O-akis, U+E001 = o-akis.
   python build_klaipeda_robo.py   →  dist/*.ttf, *.woff2, OFL.txt
"""
import math, copy
from pathlib import Path
from fontTools.ttLib import TTFont, newTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.colorLib.builder import buildCOLR, buildCPAL
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent

HERE = Path(__file__).parent
SRC, DIST = HERE / 'src', HERE / 'dist'
RED, YEL, BLUE, GREEN = (0xEE, 0x41, 0x36), (0xFF, 0xC5, 0x31), (0x2F, 0x80, 0xED), (0x2B, 0xB6, 0x73)
K = 0.5522847498
GAPS = 20                                                     # kiek raidžių tarp O dar „mato“ taisyklės (žodžio ilgis)
VERSION = '1.000'


# ── kontūrai ──
def circle(pen, cx, cy, r, cw=True):
    k = r * K
    if cw:   # pagal laikrodžio rodyklę (y aukštyn): viršus → dešinė → apačia → kairė
        pts = [((cx + k, cy + r), (cx + r, cy + k), (cx + r, cy)), ((cx + r, cy - k), (cx + k, cy - r), (cx, cy - r)),
               ((cx - k, cy - r), (cx - r, cy - k), (cx - r, cy)), ((cx - r, cy + k), (cx - k, cy + r), (cx, cy + r))]
    else:
        pts = [((cx - k, cy + r), (cx - r, cy + k), (cx - r, cy)), ((cx - r, cy - k), (cx - k, cy - r), (cx, cy - r)),
               ((cx + k, cy - r), (cx + r, cy - k), (cx + r, cy)), ((cx + r, cy + k), (cx + k, cy + r), (cx, cy + r))]
    pen.moveTo((cx, cy + r))
    for c in pts:
        pen.curveTo(*c)
    pen.closePath()


def capsule(pen, cx, cy, w, h, ang):
    """Vertikali kapsulė (apvalūs galai), pasukta ang laipsnių prieš laikrodžio rodyklę apie centrą; kontūras pagal laikrodžio rodyklę."""
    r = w / 2; L = h / 2 - r; k = r * K
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    T = lambda x, y: (cx + x * ca - y * sa, cy + x * sa + y * ca)
    pen.moveTo(T(0, L + r))
    pen.curveTo(T(k, L + r), T(r, L + k), T(r, L))
    pen.lineTo(T(r, -L))
    pen.curveTo(T(r, -L - k), T(k, -L - r), T(0, -L - r))
    pen.curveTo(T(-k, -L - r), T(-r, -L - k), T(-r, -L))
    pen.lineTo(T(-r, L))
    pen.curveTo(T(-r, L + k), T(-k, L + r), T(0, L + r))
    pen.closePath()


def make_glyph(draw):
    tp = TTGlyphPen(None); draw(Cu2QuPen(tp, max_err=0.8, reverse_direction=False)); return tp.glyph()


def eye_parts(D, stroke, y0, aw, ah, gap, xc):
    """Akis: žiedas (skersmuo D, apačia y0, centras xc) ir dvi antenos virš jo (V forma, ±24°)."""
    R = D / 2; cy = y0 + R
    ring = lambda p: (circle(p, xc, cy, R, True), circle(p, xc, cy, R - stroke, False))
    top = y0 + D
    acy = top + gap + ah / 2
    off = R - 0.06 * D / 0.74 - aw / 2                        # kaip CSS: antenos .06em nuo žiedo krašto
    ants = lambda p: (capsule(p, xc - off, acy, aw, ah, 24), capsule(p, xc + off, acy, aw, ah, -24))
    return ring, ants


def build(weight, color):
    f = TTFont(SRC / f'ChakraPetch-{weight}.ttf')
    glyf, hmtx, cmap_tables = f['glyf'], f['hmtx'], f['cmap']
    order = f.getGlyphOrder()
    stroke = 150 if weight == 'Bold' else 132
    # didžioji akis: žiedas 720 (y −10…710), antenos 100×300, tarpas 80; mažoji — pagal x aukštį
    U = dict(D=720, stroke=stroke, y0=-10, aw=100, ah=300, gap=80, side=45)
    L = dict(D=520, stroke=round(stroke * 0.82), y0=-10, aw=76, ah=225, gap=62, side=40)
    new = {}

    def add(name, g, adv, lsb=None):
        new[name] = (g, adv)

    for case, P, base in (('O', U, 'O'), ('o', L, 'o')):
        adv = P['D'] + 2 * P['side']; xc = adv / 2
        ring, ants = eye_parts(P['D'], P['stroke'], P['y0'], P['aw'], P['ah'], P['gap'], xc)
        add(f'{case}.eye.ring', make_glyph(ring), adv)
        add(f'{case}.eye.ant', make_glyph(ants), adv)
        add(f'{case}.eye', make_glyph(lambda p: (ring(p), ants(p))), adv)
        # antenos virš įprastos O (spalvotam variantui)
        badv = hmtx[base][0]; bxc = badv / 2
        bD = (glyf[base].xMax - glyf[base].xMin) if hasattr(glyf[base], 'xMax') else P['D']
        btop = 700 if case == 'O' else 498
        _, bants = eye_parts(P['D'] * 0.92, P['stroke'], btop - P['D'] * 0.92, P['aw'], P['ah'], P['gap'], bxc)
        add(f'{case}.ant', make_glyph(bants), badv)
        for i in (1, 2, 3):                                   # O.v1..v3 — kontūras (atsarginis) = O + antenos
            def dv(p, base=base, bants=bants):
                gs = f.getGlyphSet(); gs[base].draw(p); bants(p)
            add(f'{case}.v{i}', make_glyph(dv), badv)

    for name, (g, adv) in new.items():
        glyf[name] = g; g.recalcBounds(glyf)                  # glyf[...] pats prideda vardą į glifų eilę
        hmtx[name] = (int(round(adv)), int(getattr(g, 'xMin', 0)))
    f.setGlyphOrder(list(glyf.glyphOrder))
    for t in cmap_tables.tables:
        if t.isUnicode():
            t.cmap[0xE000] = 'O.eye'; t.cmap[0xE001] = 'o.eye'
    if 'GDEF' in f and f['GDEF'].table.GlyphClassDef:
        for name in new:
            f['GDEF'].table.GlyphClassDef.classDefs[name] = 1

    # ── GSUB: calt (pridedamas prie esamų features) ──
    cmap = f.getBestCmap()
    letters = sorted(set(g for c, g in cmap.items() if chr(c).isalpha()))
    Ofam = ['O', 'o', 'O.eye', 'o.eye'] + [f'{c}.v{i}' for c in 'Oo' for i in (1, 2, 3)]
    letters = sorted(set(letters) | set(Ofam))
    noO = [g for g in letters if g not in Ofam]
    fea = ['@L = [%s];' % ' '.join(letters), '@NO = [%s];' % ' '.join(noO), '@OO = [%s];' % ' '.join(Ofam), '@RAW = [O o];']
    fea += ['lookup EYE { sub O by O.eye; sub o by o.eye; } EYE;']
    for i in (1, 2, 3):
        fea += [f'lookup V{i} {{ sub O by O.v{i}; sub o by o.v{i}; }} V{i};']
    fea += ['feature calt {', ' lookup FIRSTO {']                # pirmoji O žodyje → akis
    for k in range(GAPS + 1):
        fea.append('  ignore sub @OO %s@RAW\';' % ('@L ' * k))
    fea += ['  sub @RAW\' lookup EYE;', ' } FIRSTO;']
    if color:                                                   # kitos O — antenos paeiliui: geltona, mėlyna, žalia, geltona…
        prev = {'eye': '[O.eye o.eye]', 1: '[O.v1 o.v1]', 2: '[O.v2 o.v2]', 3: '[O.v3 o.v3]'}
        seq = [('eye', 1), (1, 2), (2, 3), (3, 1), (1, 2), (2, 3), (3, 1), (1, 2)]
        for n, (src, dst) in enumerate(seq):
            fea.append(f' lookup CYC{n} {{')
            for k in range(GAPS + 1):
                fea.append('  sub %s %s@RAW\' lookup V%d;' % (prev[src], '@NO ' * k, dst))
            fea.append(f' }} CYC{n};')
    fea.append('} calt;')
    # tos pačios taisyklės ir „rlig“: Chrome su letter-spacing išjungia calt, o rlig (privalomos) — ne
    names = ['FIRSTO'] + ([f'CYC{n}' for n in range(8)] if color else [])
    fea.append('feature rlig { %s } rlig;' % ' '.join(f'lookup {n};' for n in names))
    tmp = copy.deepcopy(f)
    del tmp['GSUB']
    addOpenTypeFeaturesFromString(tmp, '\n'.join(fea), tables=['GSUB'])
    graft_gsub(f, tmp['GSUB'])

    # ── spalvos ──
    lay = {'O.eye': [('O.eye.ring', 0), ('O.eye.ant', 0xFFFF)], 'o.eye': [('o.eye.ring', 0), ('o.eye.ant', 0xFFFF)]}
    for c in 'Oo':
        for i, pal in ((1, 1), (2, 2), (3, 3)):
            lay[f'{c}.v{i}'] = [(c, 0xFFFF), (f'{c}.ant', pal)]
    f['COLR'] = buildCOLR(lay)
    f['CPAL'] = buildCPAL([[tuple(v / 255 for v in RED) + (1.0,), tuple(v / 255 for v in YEL) + (1.0,), tuple(v / 255 for v in BLUE) + (1.0,), tuple(v / 255 for v in GREEN) + (1.0,)]])

    # ── pavadinimai / licencija ──
    fam = 'Klaipeda Robo Color' if color else 'Klaipeda Robo'
    ps = fam.replace(' ', '') + '-' + weight
    nm = f['name']
    orig_copy = nm.getDebugName(0)
    for rec in list(nm.names):
        if rec.nameID in (1, 2, 3, 4, 5, 6, 16, 17, 21, 22, 25):
            nm.removeNames(nameID=rec.nameID)
    S = lambda i, s: nm.setName(s, i, 3, 1, 0x409) or nm.setName(s, i, 1, 0, 0)
    S(0, f'Copyright 2026 KU Robotics Club (Klaipeda Robo). Based on Chakra Petch: {orig_copy}')
    S(1, fam if weight in ('Bold',) else f'{fam} {weight}'); S(2, 'Bold' if weight == 'Bold' else 'Regular')
    S(16, fam); S(17, weight)
    S(3, f'{VERSION};KURC;{ps}'); S(4, f'{fam} {weight}'); S(5, f'Version {VERSION}'); S(6, ps)
    S(13, 'This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: https://openfontlicense.org')
    S(14, 'https://openfontlicense.org')
    f['OS/2'].achVendID = 'KURC'
    f['head'].fontRevision = float(VERSION)
    for t in ('DSIG',):
        if t in f:
            del f[t]
    DIST.mkdir(exist_ok=True)
    out = DIST / f'{ps}.ttf'
    f.save(out)
    f.flavor = 'woff2'; f.save(DIST / f'{ps}.woff2')
    return out


def graft_gsub(f, new_gsub):
    """Prideda naujo GSUB lookups ir 'calt' feature prie esamo GSUB (originalūs features lieka)."""
    G = f['GSUB'].table; N = new_gsub.table
    off = len(G.LookupList.Lookup)
    for lk in N.LookupList.Lookup:
        for st in lk.SubTable:
            for attr in ('SubstLookupRecord',):
                for rs in (getattr(st, 'ChainSubRuleSet', None) or []) + (getattr(st, 'ChainSubClassSet', None) or []):
                    if rs is None:
                        continue
                    for r in (getattr(rs, 'ChainSubRule', None) or getattr(rs, 'ChainSubClassRule', None) or []):
                        for rec in r.SubstLookupRecord:
                            rec.LookupListIndex += off
                for rec in (getattr(st, 'SubstLookupRecord', None) or []):
                    rec.LookupListIndex += off
        G.LookupList.Lookup.append(lk)
    G.LookupList.LookupCount = len(G.LookupList.Lookup)
    recs = G.FeatureList.FeatureRecord
    n0 = len(recs)
    for fr_new in [fr for fr in N.FeatureList.FeatureRecord if fr.FeatureTag in ('calt', 'rlig')]:
        for i in range(len(fr_new.Feature.LookupListIndex)):
            fr_new.Feature.LookupListIndex[i] += off
        fr_new.Feature.LookupCount = len(fr_new.Feature.LookupListIndex)
        recs.append(fr_new)
    idx = sorted(range(len(recs)), key=lambda i: (recs[i].FeatureTag, i))   # FeatureList turi būti surikiuotas pagal žymę
    remap = {old: new for new, old in enumerate(idx)}
    G.FeatureList.FeatureRecord = [recs[i] for i in idx]; G.FeatureList.FeatureCount = len(recs)
    added = [remap[i] for i in range(n0, len(recs))]
    for sr in G.ScriptList.ScriptRecord:
        lss = [sr.Script.DefaultLangSys] + [l.LangSys for l in sr.Script.LangSysRecord]
        for ls in lss:
            if ls is None:
                continue
            ls.FeatureIndex = sorted(remap[i] for i in ls.FeatureIndex) + added
            ls.FeatureIndex = sorted(set(ls.FeatureIndex))
            ls.FeatureCount = len(ls.FeatureIndex)


if __name__ == '__main__':
    for color in (False, True):
        for w in ('Bold', 'SemiBold'):
            print('ok', build(w, color).name)
    lic = (SRC / 'OFL.txt').read_text(encoding='utf-8')
    (DIST / 'OFL.txt').write_text('Copyright 2026 KU Robotics Club (Klaipeda Robo fonts)\n' + lic, encoding='utf-8')
