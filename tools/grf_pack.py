"""Repacka GRFs em um unico GRF com nomes corretos (cp949) na tabela.

Uso:
    python grf_pack.py <saida.grf> <base.json> <override.json> [mais.json ...]

  - base/override = JSONs do grf_index.py; o ULTIMO JSON da linha de comando
    e o primario: todos os seus arquivos entram (ordem de carga do client);
    os demais entram com o que ainda couber ate o teto de offset u32
    (~4.29 GB do formato), menores primeiro.
  - Payloads zlib copiados verbatim (sem recompressao); so a tabela e
    recomposta, com os nomes corretos.
  - Payloads de conteudo identico (mesmo hash md5) so sao gravados uma vez;
    todos os nomes apontam pro mesmo offset. Isso deduplica o overlap entre
    GRFs e mantem o total dentro do limite de 4 GiB do formato (offset u32).
  - Layout (nao-ofuscado): [header 0x2E][8B lens @0x2E][tabela zlib @0x36]
    [payloads apos a tabela]. Duas fases: (1) le os payloads (dedup md5) e
    monta/comprime a tabela; (2) escreve tudo SEQUENCIALMENTE, sem seek -
    escrita pos-seek em arquivo esparso >2GB zeirava a regiao da tabela
    neste ambiente.
"""
import hashlib
import json
import os
import struct
import sys
import time
import zlib

MAX_ENTRY = 256 * 1024 * 1024

# Reserva fixa pro bloco da tabela (cabe a tabela de ~350k entradas
# comprimida com folga). Area de payloads em posicao fixa quebra a
# circularidade do formato: srcpos entra na tabela, mas o tamanho comprimido
# da tabela so se sabe depois de monta-la.
TABLE_RESERVE = 64 * 1024 * 1024

HEADER_MODE = b"Master of Magic Game Data Ver V1.0"


def load(json_path):
    with open(json_path, encoding="utf-8") as f:
        m = json.load(f)
    return m["grf"], m["entries"]


def main():
    out_path = sys.argv[1]
    jsons = sys.argv[2:]
    primary_grf = None  # grf do ultimo json: entra por completo
    merged = {}
    sizes = {}
    for json_path in jsons:  # ultimo vence conflitos de nome
        grf, e = load(json_path)
        primary_grf = grf
        try:
            sizes[grf] = os.path.getsize(grf)
        except OSError:
            sizes[grf] = 0
        for name, v in e.items():
            try:
                srcpos, srclen, saligned, declen, ftype = v
            except (ValueError, TypeError):
                continue
            # registros-garbage do resync: tamanhos absurdos ou apontando
            # fora do arquivo sao descartados
            if not (0 <= ftype <= 127):
                continue
            if srclen <= 0 or saligned <= 0 or declen <= 0:
                continue
            if srclen > saligned or saligned > MAX_ENTRY or declen > MAX_ENTRY:
                continue
            if srcpos < 0 or srcpos + saligned > sizes[grf]:
                continue
            merged[name] = (grf, srcpos, srclen, saligned, declen, ftype)

    # primario primeiro (em ordem de nome); extras (so os grfs anteriores)
    # menores primeiro, para encaixar o maximo no teto de offset u32
    BUDGET = 0xFFFF0000  # teto do field (offset relativo), ~4.29 GB
    primary = [n for n, v in merged.items() if v[0] == primary_grf]
    extras = [n for n, v in merged.items() if v[0] != primary_grf]
    primary.sort()
    extras.sort(key=lambda n: merged[n][3])

    t0 = time.time()
    tmp = out_path + ".part"
    handles = {}

    def blob_of(grf_path, srcpos, saligned):
        f = handles.get(grf_path)
        if f is None:
            f = handles[grf_path] = open(grf_path, "rb")
        f.seek(srcpos)
        return f.read(saligned)

    # ---- fase 1: le os payloads (dedup md5), monta a tabela ----
    items = []       # (name_cp949, rec)
    slots = []       # (grf_path, srcpos, saligned) unicos, em ordem
    slot_field = {}  # md5 -> field (offset relativo) ja atribuido
    pos = 0x36 + TABLE_RESERVE
    n = 0
    dedup = 0
    skipped = 0
    for name in primary + extras:
        grf_path, srcpos, srclen, saligned, declen, ftype = merged[name]
        field_next = pos - 0x2E + saligned
        if name not in primary and field_next > BUDGET:
            skipped += 1
            continue  # extra que nao cabe ate o teto
        try:
            nb = name.encode("cp949") + b"\x00"
        except UnicodeEncodeError:
            # name com bytes fora do cp949: latin-1 devolve os bytes 1:1
            nb = name.encode("latin-1") + b"\x00"
        try:
            blob = blob_of(grf_path, srcpos, saligned)
        except (OSError, ValueError) as e:
            print(f"  pulando {name!r}: {e}")
            continue
        if len(blob) != saligned:
            print(f"  pulando {name!r}: leitura curta "
                  f"({len(blob)}/{saligned})")
            continue
        h = hashlib.md5(blob).digest()
        if h in slot_field:
            field = slot_field[h]
            dedup += 1
        else:
            field = pos - 0x2E  # offset do payload, relativo ao fim do header
            if field > 0xFFFFFFFF:
                raise SystemExit("ERRO: total passa do limite do formato "
                                 f"(4 GiB) no payload {name!r}")
            slot_field[h] = field
            slots.append((grf_path, srcpos, saligned))
            pos += saligned
        rec = struct.pack("<III", srclen, saligned, declen)
        rec += bytes([ftype]) + struct.pack("<I", field)
        items.append((nb, rec))
        n += 1
        if n % 50000 == 0:
            print(f"  fase1: {n} payloads, {pos / 1e9:.2f} GB, "
                  f"{time.time() - t0:.0f}s")
    for f in handles.values():
        f.close()

    raw = bytearray()
    for nb, rec in items:
        raw += nb + rec
    print(f"payloads: {n} ({pos / 1e9:.2f} GB, {dedup} deduplicados, "
          f"{skipped} extras fora do teto), "
          f"tabela bruta {len(raw) / 1e6:.1f} MB - comprimindo...")
    comp = zlib.compress(bytes(raw), 6)
    if len(comp) > TABLE_RESERVE:
        raise SystemExit(f"ERRO: tabela comprimida ({len(comp)}B) passa "
                         f"da reserva ({TABLE_RESERVE}B)")

    # ---- fase 2: escrita 100% sequencial, sem seek ----
    with open(tmp, "wb") as out:
        header = bytearray(0x36)
        # header[0:15] = HEADER_MODE cresceria o bytearray (slice-assign
        # redimensiona!) e empurraria a tabela 19B alem do 0x36
        header[0:15] = HEADER_MODE[:15]
        # fill 00,01,..,0E @0x0F-0x1D: constante em todo GRF real kRO
        header[0x0F:0x1E] = bytes(range(0x0F))
        # offset da tabela RELATIVO a 0x2E (spec do zgrf/GRF Editor):
        # leitor faz seek(u32@0x1E + 0x2E) e la encontra [clen][ulen]+zlib.
        # Nossa tabela usa os lens de 0x2E -> relativo = 0.
        struct.pack_into("<I", header, 0x1E, 0)
        struct.pack_into("<I", header, 0x22, 0)      # seed (filecount = raw - seed - 7)
        struct.pack_into("<I", header, 0x26, n + 7)  # count (valor+7)
        struct.pack_into("<I", header, 0x2A, 0x200)  # versao
        struct.pack_into("<II", header, 0x2E, len(comp), len(raw))
        out.write(bytes(header))
        out.write(comp)
        pad = TABLE_RESERVE - len(comp)
        while pad > 0:
            c = out.write(b"\x00" * min(pad, 1 << 20))
            pad -= c
        handles2 = {}
        wr = 0
        for grf_path, srcpos, saligned in slots:
            f = handles2.get(grf_path)
            if f is None:
                f = handles2[grf_path] = open(grf_path, "rb")
            f.seek(srcpos)
            blob = f.read(saligned)
            if len(blob) != saligned:
                raise SystemExit(f"ERRO fase 2: leitura curta "
                                 f"({len(blob)}/{saligned}) {grf_path}")
            out.write(blob)
            wr += 1
            if wr % 50000 == 0:
                print(f"  fase2: {wr} payloads, "
                      f"{out.tell() / 1e9:.2f} GB, {time.time() - t0:.0f}s")
        for f in handles2.values():
            f.close()
    size = os.path.getsize(tmp)
    if size != pos:
        print(f"  aviso: tamanho final {size} != contabilidade {pos} "
              f"(delta {size - pos}B; benigno se os offsets batem)")
    os.replace(tmp, out_path)
    # verificacao real: o leitor do projeto abre e conta as entradas
    import grf_extract
    g = grf_extract.Grf(out_path)
    ok = len(g.entries) == n
    g.f.close()
    if not ok:
        raise SystemExit(f"ERRO: o leitor acha {len(g.entries)} entradas, "
                         f"esperado {n}")
    print(f"OK {out_path}: {n} arquivos, {size / 1e9:.2f} GB, "
          f"{dedup} deduplicados, {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
