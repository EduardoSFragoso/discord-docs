"""Leitor de sprites Ragnarok Online (.spr v1.2, paleta RLE) -> PNG.

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
"""
import struct
from PIL import Image


def read_spr(path):
    b = open(path, "rb").read()
    assert b[:4] == b"SP\x01\x02", "formato nao suportado (esperado SPR 1.2)"
    n_images = struct.unpack_from("<H", b, 4)[0]

    raw_pal = b[len(b) - 1024 :]
    palette = [tuple(reversed(raw_pal[i * 4 : i * 4 + 3])) + (255,)
               for i in range(256)]

    images = []
    pos = 8
    for _ in range(n_images):
        w, h, clen = struct.unpack_from("<HHH", b, pos)
        data = b[pos + 6 : pos + 6 + clen]
        pos += 6 + clen
        images.append((w, h, data))

    return {
        "images": [decode_pal_image(w, h, data, palette) for w, h, data in images],
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


def decode_pal_image(w, h, data, palette):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    flat = rle_expand(data, w * h)
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
