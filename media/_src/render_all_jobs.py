"""Renderiza TODOS os jobs com paleta: corpo (cloth pal 0) + cabeca (hair 1).

Saida: media/_src/jobs/{nome}.png (idle 8 direcoes) + media/_src/jobs.html
"""
import os
import sys

sys.path.insert(0, "tools")
import spr_reader as S
import act_reader as A
from PIL import Image

PY = r"C:/Users/Eduardo F/Downloads"
CELL = (200, 240)
HEAD_N = 2
HAIR_COLOR = 1
# paletas extraidas com nomes corretos (grf_index.py, fonte: data-custom.grf)
PAL_LIMPA = r"C:/Users/Eduardo F/Downloads/palette_limpa"
OUT = "media/_src/jobs"

moj = lambda s: s.encode("euc-kr").decode("cp1252")


def body_pal(name_gen, c):
    p = f"{PAL_LIMPA}/몸/{name_gen}_{c}.pal"
    if os.path.exists(p):
        return p
    return f"{PY}/palette/¸ö/{moj(name_gen)}_{c}.pal"


def hair_pal(head_n, gen, c):
    p = f"{PAL_LIMPA}/머리/머리{head_n}_{gen}_{c}.pal"
    if os.path.exists(p):
        return p
    return f"{PY}/palette/¸Ó¸®/¸Ó¸®{head_n}_{moj(gen)}_{c}.pal"


def compose(body_actor, head_actor, ai, fi):
    img = Image.new("RGBA", CELL, (0, 0, 0, 0))
    cx, cy = CELL[0] // 2, CELL[1] // 2
    body_spr, body_act = body_actor
    bframe = body_act["actions"][ai]["frames"][fi]
    anchors = bframe.get("anchors") or []

    def draw(spr, act, ai_, fi_):
        for layer in act["actions"][ai_]["frames"][fi_]["layers"]:
            idx = layer["spr_index"]
            if idx < 0 or idx >= len(spr["images"]):
                continue
            lx, ly = layer["x"], layer["y"]
            sp = spr["images"][idx]
            if layer["mirror"]:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            if layer["rotation"]:
                sp = sp.rotate(-layer["rotation"], expand=True)
            sx, sy = layer["scale_x"], layer["scale_y"]
            if (sx, sy) != (1.0, 1.0):
                sp = sp.resize((max(1, int(sp.width * sx)),
                                max(1, int(sp.height * sy))), Image.NEAREST)
            img.alpha_composite(sp, (int(cx + lx - sp.width / 2),
                                     int(cy + ly - sp.height / 2)))

    draw(body_spr, body_act, ai, fi)

    # Cabeca: o cliente "costura" a ancora da cabeca na ancora do corpo
    # (head_pos = anchor_corpo - anchor_cabeca + xy_layer). Para ACTs antigos
    # sem ancora em um dos lados, cai no xy do head act puro.
    hact = head_actor[1]
    hframe = hact["actions"][ai]["frames"][fi]
    hanchors = hframe.get("anchors") or []
    if anchors and hanchors:
        ba_, ha_ = anchors[0], hanchors[0]
        for layer in hframe["layers"]:
            idx = layer["spr_index"]
            if idx < 0 or idx >= len(head_actor[0]["images"]):
                continue
            sp = head_actor[0]["images"][idx]
            if layer["mirror"]:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            if layer["rotation"]:
                sp = sp.rotate(-layer["rotation"], expand=True)
            sx, sy = layer["scale_x"], layer["scale_y"]
            if (sx, sy) != (1.0, 1.0):
                sp = sp.resize((max(1, int(sp.width * sx)),
                                max(1, int(sp.height * sy))), Image.NEAREST)
            lx = ba_["x"] - ha_["x"] + layer["x"]
            ly = ba_["y"] - ha_["y"] + layer["y"]
            img.alpha_composite(sp, (int(cx + lx - sp.width / 2),
                                     int(cy + ly - sp.height / 2)))
    else:
        draw(head_actor[0], head_actor[1], ai, fi)
    return img


def sheet(frames, cols, out, scale=1):
    rows = (len(frames) + cols - 1) // cols
    im = Image.new("RGBA", (cols * CELL[0], rows * CELL[1]), (235, 235, 235, 255))
    for i, fr in enumerate(frames):
        im.alpha_composite(fr, ((i % cols) * CELL[0], (i // cols) * CELL[1]))
    im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    im.save(out)


os.makedirs(OUT, exist_ok=True)
figs = []
erros = []
for gen in ("남", "여"):
    body_dir = f"{PY}/sprite/인간족/몸통/{gen}"
    for f in sorted(os.listdir(body_dir)):
        if not f.endswith(".spr"):
            continue
        name = f[:-4]
        try:
            if not os.path.exists(body_pal(name, 0)):
                continue  # sem paleta de roupa nem limpa nem mojibake
            safe = name.encode("utf-8", "ignore").decode("utf-8")
            out_png = f"{OUT}/{safe}-pal0.png"
            rel = f"jobs/{safe}-pal0.png"
            if os.path.exists(out_png):
                figs.append((name, gen, rel))
                continue
            cloth_pal = body_pal(name, 0)
            hpal = hair_pal(HEAD_N, gen, HAIR_COLOR)
            bs = S.read_spr(body_dir + "/" + f, S.load_pal(cloth_pal))
            head_dir = f"{PY}/sprite/인간족/머리통/{gen}"
            hs = S.read_spr(f"{head_dir}/{HEAD_N}_{gen}.spr", S.load_pal(hpal))
            body_act = A.read_act(body_dir + "/" + name + ".act")
            head_act = A.read_act(f"{head_dir}/{HEAD_N}_{gen}.act")
            n = len(body_act["actions"][0]["frames"])
            frames = []
            for ai in range(8):
                for fi in range(min(n, len(body_act["actions"][ai]["frames"]))):
                    frames.append(compose((bs, body_act), (hs, head_act), ai, fi))
            sheet(frames, n, out_png)
            figs.append((name, gen, rel))
        except Exception as e:
            erros.append((name, str(e)[:80]))

with open("media/_src/jobs.html", "w", encoding="utf-8") as fh:
    fh.write('<!doctype html>\n<meta charset="utf-8">\n<title>Jobs completos</title>\n'
             '<body style="background:#222;color:#eee;font-family:sans-serif">\n'
             '<h1>Todos os jobs — corpo+cabeça, clothes 0, cabelo 2/cor '
             + str(HAIR_COLOR) + '</h1>\n'
             '<style>figure{display:inline-block;margin:8px;vertical-align:top}'
             'figcaption{color:#8cf;font-size:12px}img{image-rendering:pixelated}</style>\n')
    for name, gen, rel in figs:
        fh.write(f'<figure><figcaption>{name}</figcaption>'
                 f'<img loading="lazy" src="{rel}"></figure>\n')
    # composicoes mortas (render_dead.py): 8 dirs de arcebispo 남/여
    dead = sorted(os.listdir("media/_src/dead")) \
        if os.path.isdir("media/_src/dead") else []
    if dead:
        fh.write('<h2>Arcebispo morto (actions 56-63)</h2>\n')
        for f in dead:
            if f.endswith(".png") and f != "archbishop-dead-grid.png":
                fh.write(f'<figure><figcaption>{f[:-4]}</figcaption>'
                         f'<img loading="lazy" src="dead/{f}"></figure>\n')
    fh.write('</body>')

print("renders ok:", len(figs))
print("erros:", len(erros))
for n, e in erros[:20]:
    print("  ", n.encode("unicode_escape").decode()[:60], "|", e)
