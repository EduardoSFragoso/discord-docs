"""Indice v2 do custom_decoded com nomes higienizados (v2 do algoritmo).

Cada parte do nome quebrado eh SUFIXO de string da parte real (o strip
comeu bytes do comeco). Match: por nome de arquivo + sufixo
componente-a-componente + juizo final por md5 de payload.
"""
import collections
import hashlib
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, 'tools')
from grf_extract import Grf

DL = r'C:\Users\Eduardo F\Downloads'
custom_path = os.path.join(DL, 'custom_decoded.grf')

g = Grf(custom_path)

broken = set()
for nome in g.entries:
    if not all(ord(c) < 256 for c in nome):
        continue
    try:
        nome.encode('latin-1').decode('cp949')
    except UnicodeDecodeError:
        broken.add(nome)
print('quebrados:', len(broken), 'de', len(g.entries))

classic = Grf(os.path.join(DL, 'classic_decoded.grf'))
bons = [n for n in list(g.entries) + list(classic.entries) if n not in broken]

by_name = collections.defaultdict(set)
for nome in bons:
    parts = nome.lower().split('\\')
    by_name[parts[-1]].add(tuple(parts))
print('bons:', len(bons), '| nomes de arquivo distintos:', len(by_name))

fixes = {}
n_part = n_md5 = n_unico = n_sem = 0
hashcache = {}
for nome in broken:
    raw = nome.encode('latin-1')
    fixado = None
    for i in range(1, min(8, len(raw))):
        try:
            fixado = raw[i:].decode('cp949')
            break
        except UnicodeDecodeError:
            continue
    if fixado is None:
        n_sem += 1
        continue
    parts = fixado.lower().split('\\')
    cands = by_name.get(parts[-1], ())
    viaveis = []
    for cp in cands:
        if len(cp) < len(parts):
            continue
        ok = True
        for j in range(1, len(parts) + 1):  # do fim pro comeco
            bp = parts[-j]
            cpv = cp[-j]
            if cpv != bp and not cpv.endswith(bp):
                ok = False
                break
        if ok:
            viaveis.append('\\'.join(cp))
    if not viaveis:
        n_sem += 1
        continue
    uniq = sorted(set(viaveis))
    if len(uniq) == 1:
        fixes[nome] = uniq[0]
        n_unico += 1
        continue
    md5_prop = hashlib.md5(g.read(nome)).hexdigest()
    hit = None
    for c in uniq:
        if c in hashcache:
            h = hashcache[c]
        else:
            try:
                h = hashcache[c] = hashlib.md5(g.read(c)).hexdigest()
            except Exception:
                continue
        if h == md5_prop:
            hit = c
            break
    if hit is not None:
        fixes[nome] = hit
        n_md5 += 1
    else:
        n_part += 1

print(f'unico={n_unico} md5={n_md5} multi-sem-md5={n_part} sem-candidato={n_sem}')

out = {'grf': custom_path, 'entries': {}}
colisoes = 0
for nome, (srclen, saligned, declen, srcpos, ftype) in g.entries.items():
    final = fixes.get(nome, nome)
    low = final.lower()
    if low in out['entries']:
        colisoes += 1
        continue
    out['entries'][final] = [srcpos, srclen, saligned, declen, ftype]
print('colisoes descartadas:', colisoes, '| entradas finais:', len(out['entries']))
with open(r'media\_src\grf_index\custom_v2.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
print('salvo media/_src/grf_index/custom_v2.json')
