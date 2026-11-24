# Handoff — Discord Docs (YAGPDB, mídia, sprites RO)

## Sprites Ragnarok direto da fonte (pipeline novo, maio/2026)

- **Fonte**: GRF do Latam extraído pelo GRF Editor v1.9.1.8 (Tokei) para
  `C:\Users\Eduardo F\Downloads\sprite\` (~7GB, ~194k arquivos).
  Nomes de pasta coreanos viram mojibake na extração (ex.: `ÀÌ¸®Áö`,
  `¸ó½ºÅÍ` = monsters) — inofensivo, os `.spr`/`.act` que interessam têm
  nomes latin (baphomet, 4_*, etc.).
- **Decodificador**: `tools/spr_reader.py` (copia: `media/_src/`) — lê `.spr` v1.2 (paleta RLE)
  e exporta PNG/contact sheet. Testado com `npc/baphomet.spr` (43 frames,
  pixel-perfect). Formato de referência: `libgrf/sprite.c`
  (OpenKore/neoncube) — magic `SP 01 02`, imagens no offset 8,
  por imagem w/h/compressed_len **u16**, RLE com byte-0 = contagem de
  zeros, paleta nos últimos 1024 bytes.
- **Pendências do leitor**: suporte a `.spr` 2.1+ (imagens RGBA zlib e
  TGA). O parser de `.act` existe e funciona: `tools/act_reader.py` (copia: `media/_src/`)
  (v2.0-2.5, lê actions/frames/layers com offsets, mirror, escala e
  rotação; `render_frame`/`export_action`/`export_act_grid` pra render).
  Mapa de ações de monstro: 0-7 idle, 8-15 walk, 16-23 attack,
  24-31 flinch (6f), 32 die (5f), por direção. Spec de referência:
  `media/_src/act_spec.md` (gitignored) (rdw-archive ACT.MD) + baphomet.act v2.1!? (kRO
  Latam): stride fixo 72B/frame c/ 1 layer, bloco 8B unknown entre
  layers e soundId (o loader do GRF Editor omite), sensível a região
  fantasma de actions declaradas no header (parser lê parcial).
  O "arcebispo morto" não apareceu com nome latin no dump (procurar
  NPC/QS ou sheets da web).
- **Preview atual**: composição de `baphomet-up.png` feita com as
  sheets antigas; a imagem final aprovada está em `media/baphomet-up.png`
  e publicada (raw link no GitHub). Caso precise refazer usar os frames
  do GRF: baphomet = `Downloads/sprite/npc/baphomet.spr`.
  O "arcebispo morto" não apareceu com nome latin no dump (procurar
  NPC/QS ou sheets da web).

## Infra

- Backup do laro na VM: cron 04:00 UTC, script `~/backup_laro.sh`
  (pg_dump → gzip → PAR OCI → healthchecks). Falha pontual em
  24/11/2026 resolvida; crontab agora redireciona pra
  `~/backup_laro/cron.log` (`>> ... 2>&1`) pra não falhar em silêncio.
