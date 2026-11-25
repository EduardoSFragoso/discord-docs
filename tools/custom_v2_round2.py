"""Rodada 2 do indice v2: para nomes ainda crus, repara o PREFIXO DE PASTAS
via arvore de parent-paths conhecidos (componente a componente, sufixo de
string). O nome do arquivo (ultimo segmento) nao se mexe.
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, 'tools')
from grf_extract import Grf

DL = r'C:\Users\Eduardo F\Downloads'
custom_path = os.path.join(DL, 'custom_decoded.grf')
classic = Grf(os.path.join(DL, 'classic_decoded.grf'))
entries = json.load(open(r'media\_src\grf_index\custom_v2.json',
                         encoding='utf-8'))['entries']

# parent-paths reais conhecidos (custom v1 + classic)
tree_paths = set()
for n in list(classic.entries) + list(entries):
    parts = n.split('\\')
    for d in range(2, len(parts) - 1):
        tree_paths.add('\\'.join(parts[:d + 1]))
by_depth = {}
for p in tree_paths:
    by_depth.setdefault(p.count('\\'), set()).add(p)
print('parent-paths conhecidos:', len(tree_paths))


def norm(nome):
    """(nome_decodavel, ok)"""
    if not all(ord(c) < 256 for c in nome):
        return nome, True
    try:
        nome.encode('latin-1').decode('cp949')
        return nome, True
    except UnicodeDecodeError:
        pass
    raw = nome.encode('latin-1')
    for i in range(1, min(8, len(raw))):
        try:
            return raw[i:].decode('cp949'), False
        except UnicodeDecodeError:
            continue
    return nome, True


def fix_parent(base):
    if not base.lower().startswith('data\\'):
        tenta = ('data\\texture\\' + base, base)
    else:
        tenta = (base,)
    todos = []
    for b in tenta:
        parts = b.split('\\')
        interior = parts[:-1]
        cands = by_depth.get(len(interior) - 1, ())
        # profundidade: path 'data\texture\미리' tem 2 '\' e len(interior)=3
        cands = by_depth.get(len(interior) - 1, ())
        hits = [p for p in cands if all(
            pc.endswith(ic) for pc, ic in zip(p.split('\\'), interior))]
        todos += hits
    uniq = sorted(set(todos))
    if len(uniq) == 1:
        return uniq[0] + '\\' + base.split('\\')[-1]
    return None


fixadas = cruas = 0
novas = {}
for nome, vals in entries.items():
    base, ok = norm(nome)
    if ok:
        novas[nome] = vals
        continue
    p = fix_parent(base)
    if p is None:
        novas[nome] = vals
        cruas += 1
    else:
        novas[p] = vals
        fixadas += 1
print(f'rodada2: pastas reparadas={fixadas}, mantidas-cruas={cruas}')

fin = {}
cols = set()
for nome, vals in novas.items():
    low = nome.lower()
    if low in cols:
        continue
    cols.add(low)
    fin[nome] = vals
print('colisoes descartadas:', len(novas) - len(fin), '| entradas finais:', len(fin))
with open(r'media\_src\grf_index\custom_v2.json', 'w', encoding='utf-8') as f:
    json.dump({'grf': custom_path, 'entries': fin}, f,
              ensure_ascii=False, separators=(',', ':'))
print('salvo media/_src/grf_index/custom_v2.json')
