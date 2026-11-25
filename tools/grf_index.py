"""Indexador de .grf: tabela com NOMES CORRETOS (cp949) + leitura direta.

O GRF em si já tem os nomes certos em bytes cp949 — a fonte do mojibake era
a hora de salvar/extrair. Este indexador:

  python grf_index.py build  <arquivo.grf> <saida.json> [--prefix data\\palette]
  python grf_index.py sample <arquivo.grf>            # mostra como os nomes veem
  python grf_index.py extract <arquivo.grf> <indice.json> <prefixo> <destino>

No extract, os paths são salvos com os nomes corretos (UTF-8 no disco NTFS).
"""
import json
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grf_extract import Grf, MIXED, HEADER, grf_decode


def build(grf_path, out_json, prefix=None):
    g = Grf(grf_path)
    idx = {}
    for name, (srclen, saligned, declen, srcpos, ftype) in g.entries.items():
        if prefix and not name.lower().startswith(
                prefix.replace("/", "\\").lower()):
            continue
        idx[name] = [srcpos, srclen, saligned, declen, ftype]
    os.makedirs(os.path.dirname(os.path.abspath(out_json)), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"grf": os.path.abspath(grf_path),
                   "count": len(idx), "entries": idx},
                  f, ensure_ascii=False, separators=(",", ":"))
    print(f"indexado {len(idx)} arquivos -> {out_json}")


class GrfIndex:
    """Leitura direta por offset, sem re-parse do GRF."""

    def __init__(self, json_path):
        with open(json_path, encoding="utf-8") as f:
            self.meta = json.load(f)
        self.entries = self.meta["entries"]
        self.f = open(self.meta["grf"], "rb")

    def read(self, name):
        e = self.entries.get(name) or self.entries.get(
            name.replace("/", "\\",).lower())
        if not e:
            for k in self.entries:
                if k.lower() == name.lower().replace("/", "\\"):
                    e = self.entries[k]
                    break
        if not e:
            raise KeyError(name)
        srcpos, srclen, saligned, declen, ftype = e
        self.f.seek(srcpos)
        data = self.f.read(saligned)
        if ftype & (MIXED | HEADER):
            data = grf_decode(data, declen, ftype)
        return zlib.decompress(data[:srclen])


def sample(grf_path):
    g = Grf(grf_path)
    names = sorted(g.entries)
    print(f"{os.path.basename(grf_path)}: {len(names)} entradas")
    for n in names[:8]:
        print("  ", n.encode("unicode_escape").decode()[:70])
    dos = [n for n in names if not n.lower().startswith("data\\")]
    print(f"  sem prefixo data\\: {len(dos)}")
    for n in dos[:5]:
        print("   *", n.encode("unicode_escape").decode()[:70])


def extract(grf_path, json_path, prefix, dest):
    gi = GrfIndex(json_path)
    # primary: ler pelo Grf (decode DES etc.); index serve pra listar
    g = Grf(grf_path) if grf_path else None
    pref = prefix.replace("/", "\\").rstrip("\\") + "\\"
    pref_data = "data\\" + pref
    n = 0
    for name in sorted(gi.entries):
        low = name.lower()
        strip = None
        if low.startswith(pref_data):
            strip = pref_data
        elif low.startswith(pref):
            strip = pref
        else:
            continue
        rel = name[len(strip):]
        out = os.path.join(dest, *rel.split("\\"))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        try:
            data = g.read(name) if g else gi.read(name)
            with open(out, "wb") as f:
                f.write(data)
            n += 1
        except Exception as e:
            print(f"  ERRO {name}: {e}")
    print(f"extraido {n} arquivos -> {dest}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "build":
        build(sys.argv[2], sys.argv[3],
              sys.argv[4].replace("--prefix ", "") if len(sys.argv) > 4
              else None)
    elif cmd == "sample":
        sample(sys.argv[2])
    elif cmd == "extract":
        extract(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
