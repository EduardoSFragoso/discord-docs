# -*- coding: utf-8 -*-
"""Gera GIFs dos emoticons do kRO a partir de emotion.spr + emotion.act.

- Sprites sao 100% paletados, alpha binaria (255 ou 0) e <= ~90 cores ->
  GIF global-paletado sem quantizacao: mapeamento exato, pixel a pixel.
- Duracao por frame: 150/speed ms (convencao roBrowser para o campo
  speed do ACT >= 2.2); speed faltando/0 -> 150 ms (~6.7fps).
- Canvas por acao: bounding box comum de todas as frames + 2px de folga.

Saida: media/emotes/emote_XXX.gif (XXX = indice da action no ACT)
       + manifest.json.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from act_reader import read_act          # noqa: E402
from spr_reader import read_spr          # noqa: E402

SRC = os.path.normpath(os.path.join(HERE, "..", "media", "_src", "emotes"))
OUT = os.path.normpath(os.path.join(HERE, "..", "media", "emotes"))
os.makedirs(OUT, exist_ok=True)


def action_canvas(act, spr, ai):
    layers = [l for f in act["actions"][ai]["frames"] for l in f["layers"]
              if 0 <= l["spr_index"] < len(spr["images"])]
    if not layers:
        return None
    wmax = max(abs(l["x"]) + spr["images"][l["spr_index"]].width // 2 + 2
               for l in layers)
    hmax = max(abs(l["y"]) + spr["images"][l["spr_index"]].height // 2 + 2
               for l in layers)
    return 2 * wmax, 2 * hmax


def render_frame_exact(act, spr, ai, fi, canvas):
    """Composicao RGBA pixel-exata: como toda layer e opaca (alpha 255)
    ou vazia, paste com mascara preserva cor e alpha sem blending."""
    frame = act["actions"][ai]["frames"][fi]
    layers = [l for l in frame["layers"]
              if 0 <= l["spr_index"] < len(spr["images"])]
    W, H = canvas
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for l in layers:
        sprite = spr["images"][l["spr_index"]]
        if l["mirror"]:
            sprite = sprite.transpose(Image.FLIP_LEFT_RIGHT)
        sx, sy = l["scale_x"], l["scale_y"]
        if (sx, sy) != (1.0, 1.0):
            sprite = sprite.resize(
                (max(1, int(sprite.width * sx)),
                 max(1, int(sprite.height * sy))), Image.NEAREST)
        px = int(W // 2 + l["x"] - sprite.width / 2)
        py = int(H // 2 + l["y"] - sprite.height / 2)
        img.paste(sprite, (px, py), sprite)
    return img


def main():
    act = read_act(os.path.join(SRC, "emotion.act"))
    spr = read_spr(os.path.join(SRC, "emotion.spr"))
    imgs = spr["images"]

    # paleta global exata (cores opacas de todo o SPR)
    colors = set()
    for im in imgs:
        arr = np.asarray(im)
        colors.update(set(map(tuple, arr[..., :3][arr[..., 3] > 0]
                              .reshape(-1, 3))))
    colors = sorted(colors)
    print(f"{len(imgs)} sprites, {len(colors)} cores globais")
    if len(colors) > 255:
        raise SystemExit(f"mais de 255 cores ({len(colors)})")

    pal = {c: i + 1 for i, c in enumerate(colors)}  # 0 = transparente
    pal_rgba = [(0, 0, 0)] + list(colors)

    n_gifs = 0
    for ai, action in enumerate(act["actions"]):
        n_fr = len(action["frames"])
        if not n_fr:
            continue
        speed = act["speeds"][ai] if ai < len(act["speeds"]) else 0
        dur = max(20, round(150 / speed)) if speed and speed > 0 else 150

        # renderiza frames uteis (com pelo menos 1 layer), canvas fixo
        canvas = action_canvas(act, spr, ai)
        if canvas is None:
            continue
        rendered = []
        for fi in range(n_fr):
            fr = render_frame_exact(act, spr, ai, fi, canvas)
            if fr is not None:
                rendered.append(fr)
        if not rendered:
            continue

        # bounding box comum de todas as frames
        masks = np.stack([np.asarray(im)[..., 3] > 0 for im in rendered])
        union = Image.fromarray((masks.any(axis=0) * 255).astype(np.uint8))
        bbox = union.getbbox()
        if bbox is None:
            continue
        l = max(0, bbox[0] - 2); t = max(0, bbox[1] - 2)
        r = bbox[2] + 2; b = bbox[3] + 2

        p_frames = []
        for im in rendered:
            crop = np.asarray(im.crop((l, t, r, b)))
            idx = np.zeros(crop.shape[:2], np.uint8)
            opaque = crop[..., 3] > 0
            rgb = crop[..., :3]
            for c, i in pal.items():
                m = (opaque & (rgb[..., 0] == c[0])
                     & (rgb[..., 1] == c[1]) & (rgb[..., 2] == c[2]))
                if m.any():
                    idx[m] = i
            pimg = Image.frombytes(
                "P", idx.shape[::-1], idx.tobytes(), "raw", "P", 0, 1)
            pimg.putpalette([v for c in pal_rgba for v in c])
            p_frames.append(pimg)

        out_gif = os.path.join(OUT, f"emote_{ai:03d}.gif")
        p_frames[0].save(
            out_gif, save_all=True, append_images=p_frames[1:],
            duration=dur, loop=0, transparency=0, disposal=2,
            optimize=False)

        n_gifs += 1
        print(f"emote_{ai:03d}.gif  {len(p_frames):3d} frames  "
              f"{r - l}x{b - t}px  {dur}ms/frame  speed={speed}")

    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as fp:
        json.dump({"n_gifs": n_gifs}, fp)
    print(f"OK: {n_gifs} GIFs em {OUT}")


if __name__ == "__main__":
    main()
