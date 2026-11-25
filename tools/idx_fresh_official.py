import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, 'tools')
import json, os
from grf_extract import Grf

DL = r'C:\Users\Eduardo F\Downloads'
grf_path = os.path.join(DL, 'official_data.grf')
g = Grf(grf_path)
print('entries lidas:', len(g.entries))

queb = 0
tipos = {}
for n, (srclen, saligned, declen, srcpos, ftype) in g.entries.items():
    if not all(ord(c) < 256 for c in n):
        continue
    try:
        n.encode('latin-1').decode('cp949')
    except UnicodeDecodeError:
        queb += 1
for t in (1, 2, 4, 5):
    tipos[t] = sum(1 for v in g.entries.values() if v[4] == t)
print('tipos ftype:', tipos)
print('nomes fora do cp949 (young-broken):', queb)

out = {'grf': grf_path, 'entries': {}}
for n, (srclen, saligned, declen, srcpos, ftype) in g.entries.items():
    out['entries'][n] = [srcpos, srclen, saligned, declen, ftype]
p = r'media\_src\grf_index\official_fresh.json'
with open(p, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False)
print('salvo:', p, len(out['entries']))
