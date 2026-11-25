"""Extrator de arquivos de um .grf do Ragnarok direto (leva quebras de nomezinho).

Suporta GRF v2xx/v3xx (header 0x2E, tabela zlib) com a obfuscacao do kRO:

  - Header: "Master of Magic\\0" (16B) @0x00, key u32 @0x10, len1 @0x14,
    len2 @0x18, nome 14B @0x1C, campo u32 @0x26 (entrys reais = valor-7),
    versao u32 @0x2A. Em 0x2E: [u32 compressed][u32 raw] + zlib da tabela.
  - Entrada da tabela: nome nulo-terminado (bytes cp949), depois
    srclen u32, srclen_aligned u32, declen u32, srcpos u32 em ofs2+13,
    mais tipo u8 em ofs2+12; total de 17 bytes apos o nome.
  - Flags: 0x01 file; 0x02 dados cifrados periodicamente (DES+shuffle);
    0x04 so os primeiros 20 blocos de 8B cifrados.
  - O "DES" do RO e o pseudo-DES do eAthena/rAthena (des.cpp): tabelas
    fixas, sem chave. Nao e DES padrao.

Uso:
    python grf_extract.py <arquivo.grf> --list "data\\palette"
    python grf_extract.py <arquivo.grf> <destino> "data\\palette" ["data\\sprite\\npc" ...]
"""
import os
import struct
import sys
import zlib

FILE = 0x01
MIXED = 0x02
HEADER = 0x04
BLOCK = 8

MASK = (0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01)

IP_TABLE = (58, 50, 42, 34, 26, 18, 10, 2, 60, 52, 44, 36, 28, 20, 12, 4,
            62, 54, 46, 38, 30, 22, 14, 6, 64, 56, 48, 40, 32, 24, 16, 8,
            57, 49, 41, 33, 25, 17, 9, 1, 59, 51, 43, 35, 27, 19, 11, 3,
            61, 53, 45, 37, 29, 21, 13, 5, 63, 55, 47, 39, 31, 23, 15, 7)

FP_TABLE = (40, 8, 48, 16, 56, 24, 64, 32, 39, 7, 47, 15, 55, 23, 63, 31,
            38, 6, 46, 14, 54, 22, 62, 30, 37, 5, 45, 13, 53, 21, 61, 29,
            36, 4, 44, 12, 52, 20, 60, 28, 35, 3, 43, 11, 51, 19, 59, 27,
            34, 2, 42, 10, 50, 18, 58, 26, 33, 1, 41, 9, 49, 17, 57, 25)

TP_TABLE = (16, 7, 20, 21, 29, 12, 28, 17, 1, 15, 23, 26, 5, 18, 31, 10,
            2, 8, 24, 14, 32, 27, 3, 9, 19, 13, 30, 6, 22, 11, 4, 25)

# tabelas S do pseudo-DES do eAthena (NOM sao as S-boxes padrao do DES)
S_TABLE = (
    (0xef, 0x03, 0x41, 0xfd, 0xd8, 0x74, 0x1e, 0x47, 0x26, 0xef, 0xfb, 0x22,
     0xb3, 0xd8, 0x84, 0x1e, 0x39, 0xac, 0xa7, 0x60, 0x62, 0xc1, 0xcd, 0xba,
     0x5c, 0x96, 0x90, 0x59, 0x05, 0x3b, 0x7a, 0x85, 0x40, 0xfd, 0x1e, 0xc8,
     0xe7, 0x8a, 0x8b, 0x21, 0xda, 0x43, 0x64, 0x9f, 0x2d, 0x14, 0xb1, 0x72,
     0xf5, 0x5b, 0xc8, 0xb6, 0x9c, 0x37, 0x76, 0xec, 0x39, 0xa0, 0xa3, 0x05,
     0x52, 0x6e, 0x0f, 0xd9),
    (0xa7, 0xdd, 0x0d, 0x78, 0x9e, 0x0b, 0xe3, 0x95, 0x60, 0x36, 0x36, 0x4f,
     0xf9, 0x60, 0x5a, 0xa3, 0x11, 0x24, 0xd2, 0x87, 0xc8, 0x52, 0x75, 0xec,
     0xbb, 0xc1, 0x4c, 0xba, 0x24, 0xfe, 0x8f, 0x19, 0xda, 0x13, 0x66, 0xaf,
     0x49, 0xd0, 0x90, 0x06, 0x8c, 0x6a, 0xfb, 0x91, 0x37, 0x8d, 0x0d, 0x78,
     0xbf, 0x49, 0x11, 0xf4, 0x23, 0xe5, 0xce, 0x3b, 0x55, 0xbc, 0xa2, 0x57,
     0xe8, 0x22, 0x74, 0xce),
    (0x2c, 0xea, 0xc1, 0xbf, 0x4a, 0x24, 0x1f, 0xc2, 0x79, 0x47, 0xa2, 0x7c,
     0xb6, 0xd9, 0x68, 0x15, 0x80, 0x56, 0x5d, 0x01, 0x33, 0xfd, 0xf4, 0xae,
     0xde, 0x30, 0x07, 0x9b, 0xe5, 0x83, 0x9b, 0x68, 0x49, 0xb4, 0x2e, 0x83,
     0x1f, 0xc2, 0xb5, 0x7c, 0xa2, 0x19, 0xd8, 0xe5, 0x7c, 0x2f, 0x83, 0xda,
     0xf7, 0x6b, 0x90, 0xfe, 0xc4, 0x01, 0x5a, 0x97, 0x61, 0xa6, 0x3d, 0x40,
     0x0b, 0x58, 0xe6, 0x3d),
    (0x4d, 0xd1, 0xb2, 0x0f, 0x28, 0xbd, 0xe4, 0x78, 0xf6, 0x4a, 0x0f, 0x93,
     0x8b, 0x17, 0xd1, 0xa4, 0x3a, 0xec, 0xc9, 0x35, 0x93, 0x56, 0x7e, 0xcb,
     0x55, 0x20, 0xa0, 0xfe, 0x6c, 0x89, 0x17, 0x62, 0x17, 0x62, 0x4b, 0xb1,
     0xb4, 0xde, 0xd1, 0x87, 0xc9, 0x14, 0x3c, 0x4a, 0x7e, 0xa8, 0xe2, 0x7d,
     0xa0, 0x9f, 0xf6, 0x5c, 0x6a, 0x09, 0x8d, 0xf0, 0x0f, 0xe3, 0x53, 0x25,
     0x95, 0x36, 0x28, 0xcb),
)

# substituicao do shuffle: eh propria e simetrica (x->y, y->x)
SUBST = {0x00: 0x2B, 0x2B: 0x00, 0x6C: 0x80, 0x80: 0x6C, 0x01: 0x68,
         0x68: 0x01, 0x48: 0x77, 0x77: 0x48, 0x60: 0xFF, 0xFF: 0x60,
         0xB9: 0xC0, 0xC0: 0xB9, 0xFE: 0xEB, 0xEB: 0xFE}


def _perm_bits(block, table, src_base=0):
    """Aplica uma permutacao de bits (estilo IP/FP do des.cpp)."""
    out = bytearray(8)
    for i, t in enumerate(table):
        j = t - 1
        if block[src_base + (j >> 3)] & MASK[j & 7]:
            out[i >> 3] |= MASK[i & 7]
    return out


def _e_expand(block):
    """Expansao E: le o bloco todo (usa bytes 4..7, com wrap no 7)."""
    r = block
    return bytes((
        ((r[7] << 5) | (r[4] >> 3)) & 0x3f,
        ((r[4] << 1) | (r[5] >> 7)) & 0x3f,
        ((r[4] << 5) | (r[5] >> 3)) & 0x3f,
        ((r[5] << 1) | (r[6] >> 7)) & 0x3f,
        ((r[5] << 5) | (r[6] >> 3)) & 0x3f,
        ((r[6] << 1) | (r[7] >> 7)) & 0x3f,
        ((r[6] << 5) | (r[7] >> 3)) & 0x3f,
        ((r[7] << 1) | (r[4] >> 7)) & 0x3f,
    ))


def _sbox4(exp):
    return bytes(
        (S_TABLE[i][exp[i * 2]] & 0xF0) | (S_TABLE[i][exp[i * 2 + 1]] & 0x0F)
        for i in range(4))


def _tp(sbox):
    """Transposicao P: le bytes 0..3 e escreve em 4..7."""
    out = bytearray(4)
    for i, t in enumerate(TP_TABLE):
        j = t - 1
        if sbox[j >> 3] & MASK[j & 7]:
            out[i >> 3] |= MASK[i & 7]
    return out


def des_decrypt_block(block):
    src = _perm_bits(block, IP_TABLE)
    exp = _e_expand(src)
    s = _sbox4(exp)
    f = _tp(s)
    out = bytes(src[4:8])  # novo L = R antigo
    out += bytes(a ^ b for a, b in zip(src[0:4], f))  # novo R = L xor f(R)
    return _perm_bits(out, FP_TABLE)


def grf_shuffle_dec(block):
    s = block
    # out.b[0..6] = src->[3,4,6,0,1,2,5]; out.b[7] = subst(src[7])
    return bytes((s[3], s[4], s[6], s[0], s[1], s[2], s[5],
                  SUBST.get(s[7], s[7])))


def _cycle_for(declen):
    """Tamanho do gap entre blocos cifrados, por digitos do tamanho real."""
    digits = len(str(declen)) if declen else 1
    if digits < 3:
        return 1
    if digits < 5:
        return digits + 1
    if digits < 7:
        return digits + 9
    return digits + 15


def grf_decode(data, declen, ftype):
    b = bytearray(data)
    nblocks = len(b) // BLOCK
    if not nblocks:
        return bytes(b)

    def des_at(i):
        b[i * 8:(i + 1) * 8] = des_decrypt_block(b[i * 8:(i + 1) * 8])

    for i in range(min(20, nblocks)):
        des_at(i)

    if ftype & MIXED:
        cycle = _cycle_for(declen)
        j = -1
        for i in range(20, nblocks):
            if i % cycle == 0:
                des_at(i)
                continue
            j += 1
            if j and j % 7 == 0:
                b[i * 8:(i + 1) * 8] = grf_shuffle_dec(b[i * 8:(i + 1) * 8])

    return bytes(b)


class Grf:
    def __init__(self, path):
        self.f = open(path, "rb")
        self.snapshots = []  # so no modo multi-snapshot
        h = self.f.read(0x2E)
        # servers costumam renomear o magic ("Event Horizon" etc.); o que
        # importa e o layout (key/len1/len2/nome em offsets fixos)
        if h[:15] != b"Master of Magic" and struct.unpack_from(
                "<I", h, 0x2A)[0] not in (0x100, 0x101, 0x102, 0x103,
                                          0x200, 0x201, 0x202, 0x203,
                                          0x300):
            raise AssertionError("nao e GRF (magic '%s', ver 0x%x)"
                                 % (h[:15].decode('latin-1'),
                                    struct.unpack_from("<I", h, 0x2A)[0]))
        self.version = struct.unpack_from("<I", h, 0x2A)[0]
        self.entry_count = struct.unpack_from("<I", h, 0x26)[0]
        self.f.seek(0x2E)
        rl, el = struct.unpack("<II", self.f.read(8))
        try:
            table = zlib.decompress(self.f.read(rl))
        except zlib.error:
            table = b""
        self.entries = {}  # nome unicode -> (srclen, saligned, declen, srcpos, ftype)
        try:
            self._parse_table(table)
        except (struct.error, ValueError):
            table = b""
        if not self.entries:
            # header nao padrao (GRFs repackados, ex. kRO Latam 2020): a tabela
            # vem partida em varios snapshots zlib espalhados pelo arquivo.
            # Uniao dos snapshots; na leitura tenta snapshot por snapshot.
            print("tabela padrao invalida -> scan por snapshots da tabela...")
            self.snapshots = []
            for table in self._scan_tables():
                try:
                    snap = {}
                    ofs = 0
                    n = len(table)
                    while ofs < n - 17:
                        end = table.find(b"\x00", ofs)
                        if end == -1:
                            break
                        try:
                            try:
                                fname = table[ofs:end].decode("cp949")
                            except UnicodeDecodeError:
                                # bytes fora do cp949: latin-1 preserva 1:1
                                fname = table[ofs:end].decode("latin-1")
                            srclen, saligned, declen = struct.unpack_from(
                                "<III", table, end + 1)
                            ftype = table[end + 13]
                            srcpos, = struct.unpack_from("<I", table, end + 14)
                        except (struct.error, ValueError):
                            break
                        e = self._entry(fname, srclen, saligned, declen,
                                        ftype, srcpos)
                        if e is not None:
                            snap[fname] = e
                            ofs = end + 18
                        else:
                            nxt = table.find(b"data\\", ofs + 1)
                            if nxt == -1:
                                break
                            ofs = nxt
                    self.snapshots.append(snap)
                except (struct.error, ValueError):
                    pass
            self.snapshots.sort(key=len)
            for snap in self.snapshots:
                self.entries.update(snap)
            print(f"  scan: {len(self.snapshots)} snapshots, "
                  f"uniao = {len(self.entries)} arquivos")
        self._real_count = self.entry_count - 7

    def _parse_table(self, table):
        ofs = 0
        n = len(table)
        while ofs < n - 17:
            end = table.find(b"\x00", ofs)
            if end == -1:
                break
            e = None
            fname = ""
            try:
                try:
                    fname = table[ofs:end].decode("cp949")
                except UnicodeDecodeError:
                    # bytes fora do cp949: latin-1 preserva 1:1
                    fname = table[ofs:end].decode("latin-1")
                srclen, saligned, declen = struct.unpack_from(
                    "<III", table, end + 1)
                ftype = table[end + 13]
                srcpos, = struct.unpack_from("<I", table, end + 14)
                e = self._entry(fname, srclen, saligned, declen, ftype, srcpos)
            except (struct.error, ValueError):
                break
            if e is not None:
                self.entries[fname] = e
                ofs = end + 18
            else:
                # registro partido (repacks/snapshots): resincroniza no proximo
                # caminho conhecido
                nxt = table.find(b"data\\", ofs + 1)
                if nxt == -1:
                    break
                ofs = nxt

    @staticmethod
    def _entry(fname, srclen, saligned, declen, ftype, srcpos):
        # registro sao 17 bytes APOS o nome; saligned absurdos ou negativos
        # indicam registro partido
        if srclen < 0 or saligned < 0 or declen < 0 or srcpos < 0:
            return None
        if saligned > srclen + 7 or declen > 2_000_000_000:
            return None
        if not (ftype & FILE):
            return None
        return (srclen, saligned, declen, srcpos + 0x2E, ftype)

    def _scan_tables(self):
        """Devolve a lista de tabelas (snapshots) zlib encontradas no arquivo
        (GRFs em que o header foi reescrito e perde o offset da tabela)."""
        CHUNK = 16 * 1024 * 1024
        f = self.f
        f.seek(0)
        found = {}
        prev_tail = b""
        while True:
            mark = f.tell()
            buf = f.read(CHUNK)
            if not buf:
                break
            data = prev_tail + buf
            for magic in (b"\x78\x9c", b"\x78\xda", b"\x78\x01",
                          b"\x78\x5e", b"\x78\x5d"):
                i = data.find(magic)
                while i != -1:
                    try:
                        d = zlib.decompressobj()
                        pre = d.decompress(data[i:i + 4096])
                        # pre-filtro: comeca com caminho "data\\" e tem varios
                        if pre.startswith(b"data\\") and pre.count(b"data\\") > 32:
                            d2 = zlib.decompressobj()
                            out = d2.decompress(data[i:])
                            while not d2.eof and len(out) < 64 * 1024 * 1024:
                                nxt = f.read(CHUNK)
                                if not nxt:
                                    break
                                out += d2.decompress(nxt)
                            if len(out) > 100000:
                                found[out[:256] + b"|" + str(len(out)).encode()] \
                                    = out
                    except Exception:
                        pass
                    f.seek(mark + len(buf))
                    i = data.find(magic, i + 1)
            f.seek(mark + len(buf))
            prev_tail = buf[-0x1000:]
        f.seek(0)
        tables = list(found.values())
        print(f"  scan: {len(tables)} snapshots distintos")
        return tables

    def _read_via_snapshots(self, name):
        """Le tentando cada snapshot que tem o arquivo (GRF multi-snapshot)."""
        f = self.f
        for snap in reversed(self.snapshots):  # mais recente (maior) primeiro
            info = snap.get(name)
            if not info:
                continue
            srclen, saligned, declen, srcpos, ftype = info
            try:
                f.seek(srcpos)
                data = f.read(saligned)
                if ftype & (MIXED | HEADER):
                    data = grf_decode(data, declen, ftype)
                data = zlib.decompress(data[:srclen])
                if len(data) == declen:
                    return data
            except (zlib.error, OSError):
                continue
        raise KeyError(f"nenhum snapshot serve o arquivo {name!r}")

    def list_prefix(self, prefix):
        prefix = prefix.replace("/", "\\").lower()
        return [n for n in self.entries if n.lower().startswith(prefix)]

    def read(self, name):
        if self.snapshots:
            return self._read_via_snapshots(name)
        srclen, saligned, declen, srcpos, ftype = self.entries[name]
        self.f.seek(srcpos)
        data = self.f.read(saligned)
        if ftype & (MIXED | HEADER):
            data = grf_decode(data, declen, ftype)
        return zlib.decompress(data[:srclen])


def main():
    if len(sys.argv) < 3:
        sys.exit("uso: grf_extract.py <arquivo.grf> [--probe | --list prefixo] | "
                 "[destino prefixo [prefixo...]]")
    grf_path = sys.argv[1]
    print(f"abrindo {grf_path}...")
    if sys.argv[2] == "--probe":
        with open(grf_path, "rb") as f:
            h = f.read(0x100)
        raw = h[0x2E:0x36]
        print("eheader cru:", raw.hex(), struct.unpack("<II", raw))
        dec = des_decrypt_block(raw)
        print("eheader des :", dec.hex(), struct.unpack("<II", dec))
        print("bloco @0x36 des:", des_decrypt_block(h[0x36:0x3E]).hex())
        fsz = os.path.getsize(grf_path)
        for nome, v in (("cru", struct.unpack("<II", raw)),
                        ("des", struct.unpack("<II", dec))):
            comp, rawlen = v
            print(f"  {nome}: sane={0 < comp < fsz and comp <= rawlen < fsz}")
        # busca a stream zlib da tabela nos primeiros 16 MB
        window = open(grf_path, "rb").read(16 * 1024 * 1024)
        for magic in (b"\x78\x9c", b"\x78\xda", b"\x78\x01", b"\x78\x5e"):
            i = window.find(magic)
            while i != -1:
                try:
                    d = zlib.decompressobj()
                    out = d.decompress(window[i:i + 65536])
                    if len(out) > 4096 and b"data" in out[:20000]:
                        print(f"ZLIB VALIDA @ {hex(i)} -> "
                              f"{out[:60]!r}")
                except Exception:
                    pass
                i = window.find(magic, i + 1)
        print("scan concluido")
        # variante 0x63: decifra 20 primeiros blocos DES de 0x2E e re-varre
        window = open(grf_path, "rb").read(16 * 1024 * 1024)
        dec = bytearray(window)
        for i in range(20):
            o = 0x2E + i * 8
            dec[o:o + 8] = des_decrypt_block(dec[o:o + 8])
        dec = bytes(dec)
        for magic in (b"\x78\x9c", b"\x78\xda", b"\x78\x01", b"\x78\x5e"):
            i = dec.find(magic)
            while i != -1:
                try:
                    d = zlib.decompressobj()
                    out = d.decompress(dec[i:i + 65536])
                    if len(out) > 4096:
                        print(f"ZLIB pos-DES @ {hex(i)} -> {out[:60]!r}")
                        # analisa o formato da tabela
                        big = d.decompress(b"\x00" * 0)  # noop
                        stream = zlib.decompressobj()
                        out2 = stream.decompress(dec[i:i + 65536])
                        out2 += stream.flush() if False else b""
                        # continua decomprimindo em blocos atecabar
                        acc = bytearray(out2)
                        pos = i + 65536
                        while not stream.eof and pos < len(dec) and len(acc) < 6 * 1024 * 1024:
                            try:
                                acc += stream.decompress(dec[pos:pos + 262144])
                            except Exception:
                                pass
                            pos += 262144
                        txt = bytes(acc[:2 * 1024 * 1024])
                        linhas = txt.split(b"\n")
                        print("total de linhas (amostra 2MB):", len(linhas))
                        for ln in linhas[:8]:
                            print("  LINHA:", ln[:110])
                        # tenta decodificar campos b64
                        import base64
                        for ln in linhas[1:4]:
                            for fld in ln.split(b","):
                                if len(fld) > 4:
                                    try:
                                        decf = base64.b64decode(fld + b"==")
                                        if all(32 <= c < 127 for c in decf):
                                            print("     campo:", fld, "->", decf)
                                    except Exception:
                                        pass
                        break
                except Exception:
                    pass
                i = dec.find(magic, i + 1)
        print("scan pos-DES concluido")
        return
    g = Grf(grf_path)
    print(f"versao 0x{g.version:04x}, entradas reais: {g._real_count}, "
          f"totais (inclui dirs): {len(g.entries)}")
    rest = sys.argv[2:]
    if rest[0] == "--list":
        hits = g.list_prefix(rest[1])
        prefix = rest[1].lower()
        for h in hits[:80]:
            print(h.encode("unicode_escape").decode())
        print(f"--- {len(hits)} resultados")
        return
    dest = rest[0]
    made = 0
    for prefix in rest[1:]:
        names = g.list_prefix(prefix)
        for i, name in enumerate(names):
            rel = name.split("data\\", 1)[-1] if name.lower().startswith("data") else name
            out = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            try:
                data = g.read(name)
            except Exception as e:
                print(f"FALHOU {name!r}: {e}")
                continue
            with open(out, "wb") as fp:
                fp.write(data)
            made += 1
            if made % 500 == 0:
                print(f"  {made} arquivos...")
    print(f"OK: {made} arquivos em {dest}")


if __name__ == "__main__":
    main()
