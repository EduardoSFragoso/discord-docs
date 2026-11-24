"""Leitor de .act Ragnarok Online + renderizador de frames (act + spr).

Fontes para as tabelas de layout:
  - rdw-archive/RagnarokFileFormats, ACT.MD (spec pormenorizada do 2.5+)
  - GRFEditor, GRF/FileFormats/ActFormat/ActConverter.cs (referencia geral)
  - Reversa do baphomet.act (v2.1, kRO/Latam "Event Horizon") pro ritmo
    das versoes antigas, que a repo do GRF Editor omite.

Header:
  'AC' + 2 bytes versao: byte[3] = major, byte[2] = minor (05 02 = 2.5)
  u16 nActions no offset 4; >= 2.5: 10B reservados (dados comecam @16),
  < 2.5: os dados comecam em 16 na pratica (u32 count + 10B).

Layout (v2.1 calibrada, 1 layer/frame = 72B cravados):
  frame = [32B ranges][u32 nLayers][layers][???][u32 soundId]
  layer < 2.4: x, y, sprIdx, mirror(4), color RGBA, f32 scaleX (24B)
  layer 2.4: + f32 scaleY, s32 rotation, s32 sprType (40B)
  layer >= 2.5: + s32 w, s32 h (48B, w/h tmb vem do SPR)
  >= 2.5: nao tem bloco extra (soundId logo apos as layers) + anchors:
          u32 nAnchors + nAnchors x (4B unknown, int x, int y, int attr)
  < 2.5: 8B de "unknown" entre layers e soundId
          >= 2.4: cauda fixa de 24B = soundId + nAnchors + 1 anchor de 16B
  Depois das actions: >= 2.1: u32 nSounds + nomes de 40B;
                      >= 2.2: f32 speed por action.

Gotchas descobertos na reversa:
  - A "regiao fantasma": .act da 3a geracao pode declarar mais actions
    (u16) do que existem; o resto e tabela nao referenciada e o parser
    desalinha nele — lemos com try/except e seguimos com o que vale.
  - "ranges" (attack/fit) conter lixo (ponteiro) neste formato, tanto faz.
"""
import struct
from PIL import Image


def read_act(path):
    b = open(path, "rb").read()
    if b[:2] != b"AC":
        raise ValueError("nao e um .act")
    major, minor = b[3], b[2]
    version = major + minor / 10.0
    (n_actions,) = struct.unpack_from("<H", b, 4)

    is_25p = version >= 2.5
    pos = 16

    actions = []
    partial = False
    sounds, speeds = [], []
    try:
        for _ in range(n_actions):
            (n_frames,) = struct.unpack_from("<I", b, pos)
            pos += 4
            frames = []
            for _f in range(n_frames):
                pos += 32  # ranges
                (n_layers,) = struct.unpack_from("<I", b, pos)
                pos += 4
                if n_layers < 0 or n_layers > 128:
                    raise ValueError(f"nLayers suspeito ({n_layers})")
                layers = []
                for _l in range(n_layers):
                    x, y, spr_index, mirror = struct.unpack_from("<iiii", b, pos)
                    pos += 16
                    color = (255, 255, 255, 255)
                    scale_x = scale_y = 1.0
                    rotation, spr_type = 0, 0
                    if version >= 2.0:
                        color = struct.unpack_from("<4B", b, pos)
                        pos += 4
                        (scale_x,) = struct.unpack_from("<f", b, pos)
                        pos += 4
                    if version >= 2.4:
                        (scale_y, rotation, spr_type) = struct.unpack_from("<fii", b, pos)
                        pos += 12
                    if is_25p:
                        pos += 8  # w/h duplicados do SPR, ignoramos
                    layers.append({
                        "x": x, "y": y, "spr_index": spr_index,
                        "mirror": bool(mirror), "color": color,
                        "scale_x": scale_x, "scale_y": scale_y,
                        "rotation": rotation, "spr_type": spr_type,
                    })
                if is_25p:
                    (sound_id,) = struct.unpack_from("<i", b, pos)
                    pos += 4  # soundId (v >= 2.0)
                    (n_anchors,) = struct.unpack_from("<I", b, pos)
                    pos += 4
                    anchors = []
                    for _a in range(n_anchors):
                        unk, ax, ay, attr = struct.unpack_from("<Iiii", b, pos)
                        pos += 16
                        anchors.append({"unknown": unk, "x": ax, "y": ay,
                                        "attr": attr})
                else:
                    anchors = []
                    # v2.0-2.4: soundId + 8B unknown, ritmo fixo de 72B/frame
                    (sound_id,) = struct.unpack_from("<i", b, pos)
                    if version >= 2.4:
                        # v2.4 (sprites de player do bRO/Latam): cauda FIXA de
                        # 24B = soundId + nAnchors + 1 anchor de 16B. A ancora
                        # "costura" cabeca/arma/escudo na ancora do frame do
                        # CORPO (head_pos = anchor_corpo - anchor_cabeca +
                        # xy_layer). Alguns atores têm lixo no nAnchors:
                        # fallback pros 20B fixos.
                        pos += 4
                        (n_anc,) = struct.unpack_from("<I", b, pos)
                        if n_anc == 1:
                            pos += 4
                            unk, ax, ay, attr = struct.unpack_from(
                                "<Iiii", b, pos)
                            pos += 16
                            anchors.append({"unknown": unk, "x": ax, "y": ay,
                                            "attr": attr})
                        else:
                            pos += 20
                    else:
                        pos += 4 + 8
                        if version >= 2.3:
                            (n_anchors,) = struct.unpack_from("<I", b, pos)
                            pos += 4 + n_anchors * 16
                frames.append({"layers": layers, "sound": sound_id,
                               "anchors": anchors})
            actions.append({"frames": frames})
    except (ValueError, struct.error):
        partial = True  # regiao fantasma atingida, mantemos as acoes validas

    if not partial and version >= 2.1:
        try:
            (n_sounds,) = struct.unpack_from("<I", b, pos)
            pos += 4
            for _ in range(n_sounds):
                sounds.append(b[pos : pos + 40].split(b"\0")[0].decode("latin-1"))
                pos += 40
            if version >= 2.2:
                for _a in range(len(actions)):
                    (speed,) = struct.unpack_from("<f", b, pos)
                    speeds.append(round(speed, 3))
                    pos += 4
        except struct.error:
            pass

    return {"version": version, "actions": actions,
            "sounds": sounds, "speeds": speeds, "partial": partial}


def render_frame(act, spr, ai, fi, canvas=(200, 200), origin=None):
    """Compoe um frame (acao ai, frame fi) num canvas RGBA."""
    img = Image.new("RGBA", canvas, (40, 40, 46, 0))
    cx, cy = canvas[0] // 2, canvas[1] // 2
    if origin:
        cx, cy = origin
    for layer in act["actions"][ai]["frames"][fi]["layers"]:
        idx = layer["spr_index"]
        if idx < 0 or idx >= len(spr["images"]):
            continue  # layer vazia (index -1), o cliente pula
        sprite = spr["images"][idx]
        if layer["mirror"]:
            sprite = sprite.transpose(Image.FLIP_LEFT_RIGHT)
        if layer["rotation"]:
            sprite = sprite.rotate(-layer["rotation"], expand=True)
        sx, sy = layer["scale_x"], layer["scale_y"]
        if (sx, sy) != (1.0, 1.0):
            sprite = sprite.resize((max(1, int(sprite.width * sx)),
                                    max(1, int(sprite.height * sy))),
                                   Image.NEAREST)
        img.alpha_composite(sprite, (int(cx + layer["x"] - sprite.width / 2),
                                     int(cy + layer["y"] - sprite.height / 2)))
    return img


def export_action(act, spr, ai, out_png, scale=2, cell=(140, 160)):
    """Monta um contact sheet de todos os frames de uma acao."""
    frames = act["actions"][ai]["frames"]
    n = len(frames)
    w, h = cell
    cols = min(n, 10)
    rows = (n + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * w, rows * h), (40, 40, 46, 255))
    for i in range(n):
        fr = render_frame(act, spr, ai, i, (w, h))
        x = (i % cols) * w + (w - fr.width) // 2
        y = (i // cols) * h + (h - fr.height) // 2
        sheet.alpha_composite(fr, (x, y))
    sheet = sheet.resize((sheet.width * scale, sheet.height * scale),
                         Image.NEAREST)
    sheet.save(out_png)
    return n


def export_act_grid(act, spr, out_png, actions, frames, scale=2,
                    cell=(170, 200), origin="ground"):
    """Grade de snapshots: linha = frame idx, coluna = acao."""
    w, h = cell
    cols, rows = len(actions), len(frames)
    sheet = Image.new("RGBA", (cols * w, rows * h), (40, 40, 46, 255))
    for c, ai in enumerate(actions):
        n = len(act["actions"][ai]["frames"]) if ai < len(act["actions"]) else 0
        for r, fo in enumerate(frames):
            if not n:
                continue
            f = fo % n
            if origin == "ground":
                o = (w // 2, h - 24)
            else:
                o = (w // 2, h // 2)
            fr = render_frame(act, spr, ai, f, (w, h), o)
            sheet.alpha_composite(fr, (c * w, r * h))
    sheet = sheet.resize((sheet.width * scale, sheet.height * scale),
                         Image.NEAREST)
    sheet.save(out_png)
    return len(actions) * len(frames)
