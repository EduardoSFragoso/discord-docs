"""Leitor de sprites Ragnarok Online (.spr v1.2 e v2.0) -> PNG.

Formato v1.2 (fonte de verdade: libgrf/sprite.c, OpenKore/neoncube):
  - magic "SP" 01 02
  - u16 numero de imagens
  - 2 bytes nulos de padding
  - por imagem: u16 w, u16 h, u16 compressed_len, bytes RLE
  - no fim: paleta 256x4 em ordem BGRA (ultimos 1024 bytes)
RLE (expansao): byte 0 -> proximo byte n = n pixels zero (transparente);
                qualquer outro byte e literal.
A stream expandida e w*h bytes de cima pra baixo; indice 0 da paleta
fica transparente na exportacao.

Formato v2.0 (revertido empiricamente; 64/65 flores do dump validam):
  - magic "SP" 00 02
  - igual v1.2, mas SEM RLE e SEM compressed_len: entrada e so
    u16 w, u16 h, seguida de w*h bytes crus de indice de paleta.
  - n_imagens == 0 e possivel (arquivo degenerado, ex. ef_snow.spr).
  - SPR 2.1+ (RGBA zlib / TGA) nao existe neste GRF (varredura de
    86.593 arquivos: 86528 v1.2, 65 v2.0) e ficou fora de escopo.
"""
import struct
from PIL import Image


def load_pal(path):
    """Carrega uma paleta externa de 1024 bytes BGRA (data/palette do GRF)."""
    return _parse_palette(open(path, "rb").read())


def _parse_palette(raw_pal):
    return [tuple(reversed(raw_pal[i * 4: i * 4 + 3])) + (255,)
            for i in range(256)]


def read_spr(path, palette=None):
    b = open(path, "rb").read()
    if b[:4] == b"SP\x01\x02":
        rle = True
    elif b[:4] == b"SP\x00\x02":
        rle = False
    else:
        raise ValueError(
            f"formato nao suportado: {b[:4]!r} (esperado SPR 1.2 ou 2.0)")

    n_images = struct.unpack_from("<H", b, 4)[0]

    raw_pal = b[len(b) - 1024:]
    palette = _parse_palette(raw_pal) if palette is None else palette

    images = []
    pos = 8
    for _ in range(n_images):
        if rle:
            w, h, clen = struct.unpack_from("<HHH", b, pos)
            data = b[pos + 6: pos + 6 + clen]
            pos += 6 + clen
        else:
            w, h = struct.unpack_from("<HH", b, pos)
            data = b[pos + 4: pos + 4 + w * h]
            pos += 4 + w * h
        images.append((w, h, data))

    return {
        "images": [decode_pal_image(w, h, data, palette, rle)
                   for w, h, data in images],
        "palette": palette,
    }


def rle_expand(data, n_pixels):
    out = bytearray()
    i = 0
    while len(out) < n_pixels and i < len(data):
        c = data[i]
        i += 1
        if c == 0:
            n = data[i]
            i += 1
            out.extend([0] * n)
        else:
            out.append(c)
    # completa com transparente se a stream terminou antes
    if len(out) < n_pixels:
        out.extend([0] * (n_pixels - len(out)))
    return out


def decode_pal_image(w, h, data, palette, rle=True):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    flat = rle_expand(data, w * h) if rle else data
    img.putdata([
        (0, 0, 0, 0) if i == 0 else palette[i] for i in flat
    ])
    return img


def export_sprite_frame(path, out_png, scale=2):
    spr = read_spr(path)
    n = len(spr["images"])
    wmax = max(im.width for im in spr["images"])
    hmax = max(im.height for im in spr["images"])
    cols = min(n, 10)
    rows = (n + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * wmax, rows * hmax), (40, 40, 46, 255))
    for i, im in enumerate(spr["images"]):
        x = (i % cols) * wmax + (wmax - im.width) // 2
        y = (i // cols) * hmax + (hmax - im.height) // 2
        sheet.alpha_composite(im, (x, y))
    sheet = sheet.resize((sheet.width * scale, sheet.height * scale),
                         Image.NEAREST)
    sheet.save(out_png)
    return n, wmax, hmax


if __name__ == "__main__":
    import sys
    n, w, h = export_sprite_frame(sys.argv[1], sys.argv[2])
    print(f"{n} imagens, maior {w}x{h}")
