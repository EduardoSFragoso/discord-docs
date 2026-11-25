# Emoticons do kRO → GIF (lossless)

Fonte: `data\sprite\이팩트\emotion.spr` + `emotion.act` (kRO 2022,
extraídos de `G:\Ragnarok\data.grf` — fonte viva, não precisa guardar
nenhum GRF pra regenerar).

## Arquivos

- `emote_XXX.gif` — emoticon puro, pixel a pixel.
  **A regra: `emote_XXX.gif` = comando `/e(XXX+1)`** (action 0 → `/e1`,
  action 97 → `/e98`). Alinhamento confirmado contra os balões de
  texto renderizados (e16="Thanks", e18="Sorry", e27="Help",
  e46="congratulations").
- `legenda_emotes.png` — folha com os 98 emotes renderizados e o `/eN`
  de cada um. Prévia com um frame do meio de cada animação.
- `manifest.json` — metadados simples.

## Perda zero (sim, de verdade)

- Os .spr são **paletados de 8 bits** (paleta ≤ 256, só 140 cores
  distintas em todo o arquivo) e **toda a transparência é binária**
  (alpha 255 ou 0 — conferido pixel a pixel no SPR inteiro).
- GIF também é paletado: saída usa **paleta global única exata**, sem
  quantização, sem dithering, transparência = índice 0.
  Cada pixel do GIF é o pixel do sprite original.
- O timing vem do próprio `.act`: campo `speed` da versão ≥ 2.2,
  duração por frame = `150/speed` ms (convenção roBrowser).

## Regenerar

```
python media/_src/emotes_gift.py
```

(requere só Pillow + numpy; lê os .spr/.act extraídos em
`media/_src/emotes/`, que podem ser re-extraídos do GRF do G: havendo
atualização do jogo)
