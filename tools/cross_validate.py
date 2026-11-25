import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, 'tools')
import json, hashlib, os, random
from grf_extract import Grf

DL = r'C:\Users\Eduardo F\Downloads'
j = json.load(open(r'media\_src\grf_index\official_fresh.json', encoding='utf-8'))
ent = j['entries']
g = Grf(os.path.join(DL, 'official_data.grf'))

random.seed(99)
ok = diff = falta = nao_sprite = 0
for nome in random.sample(list(ent), 300):
    if not nome.startswith('data\\sprite\\'):
        nao_sprite += 1
        continue
    rel = nome[len('data\\sprite\\'):]
    if any(0xAC00 <= ord(c) <= 0xD7A3 for c in rel):
        try:
            rel = rel.encode('euc-kr').decode('cp1252')
        except Exception:
            continue
    p = os.path.join(DL, 'sprite2', *rel.split('\\'))
    if not os.path.exists(p):
        falta += 1
        continue
    md5_pasta = hashlib.md5(open(p, 'rb').read()).hexdigest()
    md5_grf = hashlib.md5(g.read(nome)).hexdigest()
    if md5_pasta == md5_grf:
        ok += 1
    else:
        diff += 1
        if diff < 4:
            print('DIF:', ascii(nome[:70]))
print(f'pasta vs GRF: iguais={ok} diferentes={diff} falta={falta} nao-sprite={nao_sprite} /300')
