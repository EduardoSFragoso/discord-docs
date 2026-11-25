"""Composicao "morto" (actions 56-63 do body act, 1 frame cada, 8 dirs).

Renderiza corpo+cabeca ja costurados para cada direcao do arcebispo, salva
frames individuais em media/_src/dead/ e um contact sheet. Reuso estilo
baphomet-up.png. Nao importa render_all_jobs (que executa o lote todo no
import) — o compose() vem duplicado daqui.

Run (do ROOT do repo): python media/_src/render_dead.py
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
DEAD_ACTIONS = list(range(56, 64))   # die/freeze: 1 frame por direcao
DIRS = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]
OUT = "media/_src/dead"

moj = lambda s: s.encode("euc-kr").decode("cp1252")

hpals = f"{PY}/palette/¸Ó¸®"


def load_actor(job, gen):
    """Devolve ((spr, act) corpo, (spr, act) cabeca) com paletas padrao."""
    cloth_pal = f"{PY}/palette/¸ö/{moj(job)}_{moj(gen)}_0.pal"
    hpal = sorted(p for p in os.listdir(hpals)
                  if p.startswith(f"¸Ó¸®{HEAD_N}_{moj(gen)}_")
                  and p.endswith(f"_{HAIR_COLOR}.pal"))
    if not hpal:
        raise FileNotFoundError("hair pal")
    body_dir = f"{PY}/sprite/인간족/몸통/{gen}"
    head_dir = f"{PY}/sprite/인간족/머리통/{gen}"
    bs = S.read_spr(f"{body_dir}/{job}_{gen}.spr", S.load_pal(cloth_pal))
    ba = A.read_act(f"{body_dir}/{job}_{gen}.act")
    hs = S.read_spr(f"{head_dir}/{HEAD_N}_{gen}.spr",
                    S.load_pal(f"{hpals}/{hpal[0]}"))
    ha = A.read_act(f"{head_dir}/{HEAD_N}_{gen}.act")
    return (bs, ba), (hs, ha)


def compose(body_actor, head_actor, ai, fi):
    """Costura cabeca no corpo via ancoras de ACT (igual render_all_jobs)."""
    img = Image.new("RGBA", CELL, (0, 0, 0, 0))
    cx, cy = CELL[0] // 2, CELL[1] // 2
    body_spr, body_act = body_actor
    bframe = body_act["actions"][ai]["frames"][fi]
    anchors = bframe.get("anchors") or []

    def place(sp, lx, ly):
        img.alpha_composite(sp, (int(cx + lx - sp.width / 2),
                                 int(cy + ly - sp.height / 2)))

    def prep(sp, layer):
        if layer["mirror"]:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        if layer["rotation"]:
            sp = sp.rotate(-layer["rotation"], expand=True)
        sx, sy = layer["scale_x"], layer["scale_y"]
        if (sx, sy) != (1.0, 1.0):
            sp = sp.resize((max(1, int(sp.width * sx)),
                            max(1, int(sp.height * sy))), Image.NEAREST)
        return sp

    for layer in bframe["layers"]:
        idx = layer["spr_index"]
        if 0 <= idx < len(body_spr["images"]):
            place(prep(body_spr["images"][idx], layer),
                  layer["x"], layer["y"])

    hact = head_actor[1]
    hframe = hact["actions"][ai]["frames"][fi]
    hanchors = hframe.get("anchors") or []
    head_spr = head_actor[0]
    if anchors and hanchors:
        ba_, ha_ = anchors[0], hanchors[0]
        for layer in hframe["layers"]:
            idx = layer["spr_index"]
            if 0 <= idx < len(head_spr["images"]):
                place(prep(head_spr["images"][idx], layer),
                      ba_["x"] - ha_["x"] + layer["x"],
                      ba_["y"] - ha_["y"] + layer["y"])
    else:
        for layer in hframe["layers"]:
            idx = layer["spr_index"]
            if 0 <= idx < len(head_spr["images"]):
                place(prep(head_spr["images"][idx], layer),
                      layer["x"], layer["y"])
    return img


os.makedirs(OUT, exist_ok=True)
frames = []
names = []
for gen in ("남", "여"):
    body, head = load_actor("아크비숍", gen)
    tag = "m" if gen == "남" else "f"
    for di, ai in enumerate(DEAD_ACTIONS):
        img = compose(body, head, ai, 0)
        path = f"{OUT}/arch_{tag}_d{di:02d}_{DIRS[di]}.png"
        img.save(path)
        frames.append(img)
        names.append(os.path.basename(path))

cols, rows = 8, 2
sheet = Image.new("RGBA", (cols * CELL[0], rows * CELL[1]),
                  (235, 235, 235, 255))
for i, fr in enumerate(frames):
    sheet.alpha_composite(fr, ((i % cols) * CELL[0], (i // cols) * CELL[1]))
# recorte vertical na area de conteudo (margem 6px), largura inteira —
# bbox calculado na FOLHA inteira, senao a 2a linha (feminino) some no corte
bbox = sheet.getbbox()
top = max(0, bbox[1] - 6)
bottom = min(sheet.height, bbox[3] + 6)
sheet = sheet.crop((0, top, sheet.width, bottom))
sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
sheet.save(f"{OUT}/archbishop-dead-grid.png")

print("ok:", len(frames), "frames + grid ->", OUT)
for n in names:
    print(" ", n)
